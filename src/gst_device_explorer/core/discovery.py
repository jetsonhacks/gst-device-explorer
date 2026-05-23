"""Core device discovery orchestration."""

from __future__ import annotations

from gst_device_explorer.core.models import Device
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
