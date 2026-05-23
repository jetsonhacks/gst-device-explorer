"""ALSA audio device discovery probes."""

from __future__ import annotations

import re
import shutil
import subprocess

from gst_device_explorer.core.models import Device


ARECORD = "arecord"
APLAY = "aplay"


def discover_alsa_audio_inputs() -> list[Device]:
    """Discover ALSA capture devices using arecord."""

    return _discover_alsa_devices(command=ARECORD, kind="audio_input")


def discover_alsa_audio_outputs() -> list[Device]:
    """Discover ALSA playback devices using aplay."""

    return _discover_alsa_devices(command=APLAY, kind="audio_output")


def _discover_alsa_devices(command: str, kind: str) -> list[Device]:
    if shutil.which(command) is None:
        return []

    result = _run_alsa_command([command, "-l"])
    if result is None or result.returncode != 0:
        return []

    return _parse_alsa_device_list(result.stdout, kind=kind, source=command)


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
