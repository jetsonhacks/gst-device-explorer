"""Core device discovery orchestration."""

from __future__ import annotations

from pathlib import Path

from gst_device_explorer.core.grouping import GroupableDevice, build_composite_devices
from gst_device_explorer.core.grouping_metadata import build_groupable_devices
from gst_device_explorer.core.models import CompositeDevice, Device
from gst_device_explorer.probes.alsa import (
    discover_alsa_audio_inputs,
    discover_alsa_audio_outputs,
)
from gst_device_explorer.probes.v4l2 import discover_v4l2_video_devices


def discover_devices() -> list[Device]:
    """Discover known media devices using the current probe set."""

    devices: list[Device] = []
    devices.extend(discover_v4l2_video_devices())
    devices.extend(discover_alsa_audio_inputs())
    devices.extend(discover_alsa_audio_outputs())
    return devices


def discover_composite_devices(
    sysfs_video4linux_root: str | Path = "/sys/class/video4linux",
    sysfs_sound_root: str | Path = "/sys/class/sound",
) -> list[CompositeDevice]:
    """Discover composite devices using the current probe and grouping layers."""

    devices = discover_devices()
    groupable_devices = build_groupable_devices(
        devices,
        sysfs_video4linux_root=sysfs_video4linux_root,
        sysfs_sound_root=sysfs_sound_root,
    )
    return build_composite_devices(groupable_devices)


def discover_groupable_devices(
    sysfs_video4linux_root: str | Path = "/sys/class/video4linux",
    sysfs_sound_root: str | Path = "/sys/class/sound",
) -> list[GroupableDevice]:
    """Discover groupable device records using current probes and metadata."""

    devices = discover_devices()
    return build_groupable_devices(
        devices,
        sysfs_video4linux_root=sysfs_video4linux_root,
        sysfs_sound_root=sysfs_sound_root,
    )
