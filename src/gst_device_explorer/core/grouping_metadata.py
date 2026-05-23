"""Build grouping-engine inputs from discovered devices."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from gst_device_explorer.core.grouping import GroupableDevice
from gst_device_explorer.core.models import Device, DeviceRef


USB_TOPOLOGY_PATTERN = re.compile(r"^\d+-\d+(?:\.\d+)*$")
ALSA_DEVICE_PATTERN = re.compile(r"^hw:(\d+),(\d+)$")

GROUPING_METADATA_KEYS = [
    "alsa_card",
    "alsa_device",
    "alsa_card_name",
    "usb_parent_path",
    "usb_vendor_id",
    "usb_product_id",
    "usb_product",
    "usb_manufacturer",
    "usb_serial",
]


def build_groupable_devices(
    devices: list[Device],
    sysfs_video4linux_root: str | Path = "/sys/class/video4linux",
    sysfs_sound_root: str | Path = "/sys/class/sound",
) -> list[GroupableDevice]:
    """Convert discovered devices into grouping-engine input records."""

    return [
        groupable
        for device in devices
        if (
            groupable := _build_groupable_device(
                device,
                sysfs_video4linux_root=Path(sysfs_video4linux_root),
                sysfs_sound_root=Path(sysfs_sound_root),
            )
        )
        is not None
    ]


def _build_groupable_device(
    device: Device,
    sysfs_video4linux_root: Path,
    sysfs_sound_root: Path,
) -> GroupableDevice | None:
    if device.kind == "video_input":
        return _v4l2_groupable_device(device, sysfs_video4linux_root)
    if device.kind == "audio_input":
        return _alsa_groupable_device(
            device,
            role="audio-input",
            sysfs_sound_root=sysfs_sound_root,
        )
    if device.kind == "audio_output":
        return _alsa_groupable_device(
            device,
            role="audio-output",
            sysfs_sound_root=sysfs_sound_root,
        )
    return None


def _v4l2_groupable_device(
    device: Device,
    sysfs_video4linux_root: Path,
) -> GroupableDevice:
    path = _metadata_string(device.metadata.get("path")) or device.id
    node_name = _metadata_string(device.metadata.get("node_name")) or Path(path).name
    sysfs_node = sysfs_video4linux_root / node_name
    metadata = _copy_grouping_metadata(device.metadata)

    sysfs_name = _read_text_file(sysfs_node / "name")
    if sysfs_name:
        metadata["v4l2_name"] = sysfs_name

    usb_metadata = _read_v4l2_usb_metadata(sysfs_node)
    metadata.update({key: value for key, value in usb_metadata.items() if value})

    return GroupableDevice(
        device_ref=DeviceRef(
            role="camera",
            device_id=device.id,
            path=path,
            subsystem="v4l2",
        ),
        name=sysfs_name or device.name,
        metadata=metadata,
    )


def _alsa_groupable_device(
    device: Device,
    role: str,
    sysfs_sound_root: Path,
) -> GroupableDevice:
    metadata = _copy_grouping_metadata(device.metadata)
    alsa_device = (
        _metadata_string(device.metadata.get("alsa_device"))
        or _parse_alsa_device_string(device.id)
    )

    card: str | None = None
    device_number: str | None = None
    if alsa_device is not None:
        metadata.setdefault("alsa_device", alsa_device)
        card, device_number = _parse_alsa_card_and_device(alsa_device)
        if card is not None:
            metadata.setdefault("alsa_card", card)
        if device_number is not None:
            metadata.setdefault("alsa_device_number", device_number)

    card_name = _metadata_string(device.metadata.get("card_name"))
    if card_name:
        metadata.setdefault("alsa_card_name", card_name)

    usb_metadata = _read_alsa_usb_metadata(
        sysfs_sound_root=sysfs_sound_root,
        role=role,
        card=card,
        device_number=device_number,
    )
    metadata.update({key: value for key, value in usb_metadata.items() if value})

    return GroupableDevice(
        device_ref=DeviceRef(
            role=role,
            device_id=device.id,
            path=alsa_device,
            subsystem="alsa",
        ),
        name=device.name,
        metadata=metadata,
    )


def _read_v4l2_usb_metadata(sysfs_node: Path) -> dict[str, str]:
    device_path = sysfs_node / "device"
    if not device_path.exists():
        return {}

    return _read_usb_metadata_from_path(device_path)


def _read_alsa_usb_metadata(
    sysfs_sound_root: Path,
    role: str,
    card: str | None,
    device_number: str | None,
) -> dict[str, str]:
    if card is None or device_number is None:
        return {}

    direction = "c" if role == "audio-input" else "p"
    candidate_paths = [
        sysfs_sound_root / f"pcmC{card}D{device_number}{direction}",
        sysfs_sound_root / f"card{card}",
    ]

    for candidate_path in candidate_paths:
        usb_metadata = _read_usb_metadata_from_sysfs_node(candidate_path)
        if usb_metadata:
            return usb_metadata
    return {}


def _read_usb_metadata_from_sysfs_node(sysfs_node: Path) -> dict[str, str]:
    if not sysfs_node.exists():
        return {}

    device_path = sysfs_node / "device"
    if device_path.exists():
        usb_metadata = _read_usb_metadata_from_path(device_path)
        if usb_metadata:
            return usb_metadata

    return _read_usb_metadata_from_path(sysfs_node)


def _read_usb_metadata_from_path(path: Path) -> dict[str, str]:
    try:
        resolved_device_path = path.resolve(strict=False)
    except OSError:
        return {}

    usb_parent = _find_usb_parent_path(resolved_device_path)
    if usb_parent is None:
        return {}

    return {
        "usb_parent_path": usb_parent.name,
        "usb_vendor_id": _read_text_file(usb_parent / "idVendor"),
        "usb_product_id": _read_text_file(usb_parent / "idProduct"),
        "usb_product": _read_text_file(usb_parent / "product"),
        "usb_manufacturer": _read_text_file(usb_parent / "manufacturer"),
        "usb_serial": _read_text_file(usb_parent / "serial"),
    }


def _find_usb_parent_path(path: Path) -> Path | None:
    for current in [path, *path.parents]:
        if USB_TOPOLOGY_PATTERN.match(current.name):
            return current
    return None


def _copy_grouping_metadata(metadata: dict[str, Any]) -> dict[str, str]:
    copied: dict[str, str] = {}
    for key in GROUPING_METADATA_KEYS:
        value = _metadata_string(metadata.get(key))
        if value:
            copied[key] = value
    return copied


def _metadata_string(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float | str):
        text = str(value).strip()
        return text or None
    return None


def _parse_alsa_device_string(value: str) -> str | None:
    return value if ALSA_DEVICE_PATTERN.match(value) else None


def _parse_alsa_card_and_device(
    alsa_device: str,
) -> tuple[str | None, str | None]:
    match = ALSA_DEVICE_PATTERN.match(alsa_device)
    if match is None:
        return None, None
    return match.group(1), match.group(2)


def _read_text_file(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8").strip() or None
    except OSError:
        return None
