"""Core data structures for gst-device-explorer."""

from gst_device_explorer.core.models import (
    Capability,
    Device,
    EnvironmentFact,
    PipelineCandidate,
    Profile,
    RendererOutput,
)


def discover_devices() -> list[Device]:
    """Discover known media devices using the current probe set."""

    from gst_device_explorer.core.discovery import discover_devices as _discover_devices

    return _discover_devices()


__all__ = [
    "Capability",
    "Device",
    "EnvironmentFact",
    "PipelineCandidate",
    "Profile",
    "RendererOutput",
    "discover_devices",
]
