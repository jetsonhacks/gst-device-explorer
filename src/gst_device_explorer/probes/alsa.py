"""ALSA audio device discovery probes."""

from __future__ import annotations

import re
import shutil
import subprocess

from gst_device_explorer.core.models import Capability, Device


ARECORD = "arecord"
APLAY = "aplay"


def discover_alsa_audio_inputs() -> list[Device]:
    """Discover ALSA capture devices using arecord."""

    return _discover_alsa_devices(command=ARECORD, kind="audio_input", probe_hw_params=True)


def discover_alsa_audio_outputs() -> list[Device]:
    """Discover ALSA playback devices using aplay."""

    return _discover_alsa_devices(command=APLAY, kind="audio_output")


def _discover_alsa_devices(command: str, kind: str, *, probe_hw_params: bool = False) -> list[Device]:
    if shutil.which(command) is None:
        return []

    result = _run_alsa_command([command, "-l"])
    if result is None or result.returncode != 0:
        return []

    devices = _parse_alsa_device_list(result.stdout, kind=kind, source=command)
    if not probe_hw_params:
        return devices
    return [_with_hw_params(device, command=command) for device in devices]


def _run_alsa_command(command: list[str]) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.SubprocessError, OSError):
        return None


def _parse_alsa_device_list(output: str, kind: str, source: str) -> list[Device]:
    devices: list[Device] = []
    pattern = re.compile(
        r"^card\s+(\d+):\s+([^\[]+)\[([^\]]+)\],\s+"
        r"device\s+(\d+):\s+([^\[]+)\[([^\]]+)\]"
    )

    for line in output.splitlines():
        match = pattern.search(line.strip())
        if match is None:
            continue

        card_number = int(match.group(1))
        card_id = match.group(2).strip()
        card_name = match.group(3).strip()
        device_number = int(match.group(4))
        device_id = match.group(5).strip()
        device_name = match.group(6).strip()
        alsa_device = f"hw:{card_number},{device_number}"

        devices.append(
            Device(
                id=alsa_device,
                kind=kind,
                name=f"{card_name}: {device_name}",
                metadata={
                    "backend": "alsa",
                    "source": source,
                    "card_number": card_number,
                    "device_number": device_number,
                    "card_id": card_id,
                    "device_id": device_id,
                    "card_name": card_name,
                    "device_name": device_name,
                    "alsa_device": alsa_device,
                },
            )
        )

    return devices


def _with_hw_params(device: Device, command: str) -> Device:
    alsa_device = str(device.metadata.get("alsa_device", device.id))
    result = _run_alsa_command([command, "--dump-hw-params", "-D", alsa_device])
    if result is None:
        return device

    capability = _parse_audio_hw_params("\n".join(part for part in (result.stdout, result.stderr) if part))
    if capability is None:
        return device

    return Device(
        id=device.id,
        kind=device.kind,
        name=device.name,
        capabilities=[*device.capabilities, capability],
        metadata=device.metadata,
    )


def _parse_audio_hw_params(output: str) -> Capability | None:
    values: dict[str, str] = {}
    for raw_line in output.splitlines():
        if ":" not in raw_line:
            continue
        key, raw_value = raw_line.split(":", 1)
        value = raw_value.strip()
        if not value:
            continue

        normalized_key = key.strip().lower()
        if normalized_key == "format":
            values["format"] = _format_alsa_values(value, normalize_format=True)
        elif normalized_key == "rate":
            values["rate"] = _format_alsa_values(value)
        elif normalized_key == "channels":
            values["channels"] = _format_alsa_values(value)

    if not values:
        return None
    return Capability(name="audio_format", values=values, source="arecord --dump-hw-params")


def _format_alsa_values(value: str, *, normalize_format: bool = False) -> str:
    value = value.strip()
    range_match = re.fullmatch(r"\[\s*([^\s]+)\s+([^\s]+)\s*\]", value)
    if range_match is not None:
        return f"{range_match.group(1)}-{range_match.group(2)}"

    items = value.split()
    if normalize_format:
        items = [_normalize_gst_audio_format(item) for item in items]
    if len(items) > 1:
        return ", ".join(items)
    if items:
        return items[0]
    return value


def _normalize_gst_audio_format(value: str) -> str:
    return value.replace("_", "")
