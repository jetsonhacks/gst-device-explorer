"""Core data structures for gst-device-explorer."""

from gst_device_explorer.core.models import (
    Capability,
    Device,
    EnvironmentFact,
    ExecutionPlan,
    PipelineCandidate,
    Profile,
    RendererOutput,
)


def discover_devices() -> list[Device]:
    """Discover known media devices using the current probe set."""

    from gst_device_explorer.core.discovery import discover_devices as _discover_devices

    return _discover_devices()


def build_video_preview_candidates(
    device: Device,
    capabilities: list[Capability],
    environment: list[EnvironmentFact],
) -> list[PipelineCandidate]:
    """Build video preview pipeline candidates."""

    from gst_device_explorer.core.pipelines import (
        build_video_preview_candidates as _build_video_preview_candidates,
    )

    return _build_video_preview_candidates(device, capabilities, environment)


__all__ = [
    "Capability",
    "Device",
    "EnvironmentFact",
    "ExecutionPlan",
    "PipelineCandidate",
    "Profile",
    "RendererOutput",
    "build_video_preview_candidates",
    "discover_devices",
]
