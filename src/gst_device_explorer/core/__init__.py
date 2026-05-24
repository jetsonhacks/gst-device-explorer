"""Core data structures for gst-device-explorer."""

from gst_device_explorer.core.models import (
    Capability,
    CompositeDevice,
    Device,
    DeviceRef,
    DeviceProfile,
    EnvironmentFact,
    ExecutionPlan,
    GroupingEvidence,
    PipelineDiagnostic,
    PipelineCandidate,
    Profile,
    ProfileCandidateSummary,
    ProfileGroupSummary,
    RendererOutput,
)
from gst_device_explorer.core.grouping import (
    GroupableDevice,
    build_composite_devices,
)
from gst_device_explorer.core.grouping_metadata import build_groupable_devices


def discover_devices() -> list[Device]:
    """Discover known media devices using the current probe set."""

    from gst_device_explorer.core.discovery import discover_devices as _discover_devices

    return _discover_devices()


def discover_composite_devices() -> list[CompositeDevice]:
    """Discover composite devices using the current probe and grouping layers."""

    from gst_device_explorer.core.discovery import (
        discover_composite_devices as _discover_composite_devices,
    )

    return _discover_composite_devices()


def discover_groupable_devices() -> list[GroupableDevice]:
    """Discover groupable device records using current probes and metadata."""

    from gst_device_explorer.core.discovery import (
        discover_groupable_devices as _discover_groupable_devices,
    )

    return _discover_groupable_devices()


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


def build_video_preview_diagnostics(
    device: Device,
    capabilities: list[Capability],
    environment: list[EnvironmentFact],
) -> list[PipelineDiagnostic]:
    """Build diagnostics for video preview pipeline candidates."""

    from gst_device_explorer.core.video_diagnostics import (
        build_video_preview_diagnostics as _build_video_preview_diagnostics,
    )

    return _build_video_preview_diagnostics(device, capabilities, environment)


def build_audio_input_test_candidates(
    device: Device,
    environment: list[EnvironmentFact],
) -> list[PipelineCandidate]:
    """Build audio input test pipeline candidates."""

    from gst_device_explorer.core.audio_pipelines import (
        build_audio_input_test_candidates as _build_audio_input_test_candidates,
    )

    return _build_audio_input_test_candidates(device, environment)


def build_audio_output_test_candidates(
    device: Device,
    environment: list[EnvironmentFact],
) -> list[PipelineCandidate]:
    """Build audio output test pipeline candidates."""

    from gst_device_explorer.core.audio_pipelines import (
        build_audio_output_test_candidates as _build_audio_output_test_candidates,
    )

    return _build_audio_output_test_candidates(device, environment)


def build_audio_input_test_diagnostics(
    device: Device,
    environment: list[EnvironmentFact],
) -> list[PipelineDiagnostic]:
    """Build diagnostics for audio input test pipeline candidates."""

    from gst_device_explorer.core.audio_diagnostics import (
        build_audio_input_test_diagnostics as _build_audio_input_test_diagnostics,
    )

    return _build_audio_input_test_diagnostics(device, environment)


def build_audio_output_test_diagnostics(
    device: Device,
    environment: list[EnvironmentFact],
) -> list[PipelineDiagnostic]:
    """Build diagnostics for audio output test pipeline candidates."""

    from gst_device_explorer.core.audio_diagnostics import (
        build_audio_output_test_diagnostics as _build_audio_output_test_diagnostics,
    )

    return _build_audio_output_test_diagnostics(device, environment)


def build_audio_input_profile(
    device: Device,
    environment: list[EnvironmentFact],
    groups: list[CompositeDevice] | None = None,
) -> DeviceProfile | None:
    """Build an audio input endpoint profile."""

    from gst_device_explorer.core.profiles import (
        build_audio_input_profile as _build_audio_input_profile,
    )

    return _build_audio_input_profile(device, environment, groups)


def build_audio_output_profile(
    device: Device,
    environment: list[EnvironmentFact],
    groups: list[CompositeDevice] | None = None,
) -> DeviceProfile | None:
    """Build an audio output endpoint profile."""

    from gst_device_explorer.core.profiles import (
        build_audio_output_profile as _build_audio_output_profile,
    )

    return _build_audio_output_profile(device, environment, groups)


def build_video_profile(
    device: Device,
    capabilities: list[Capability],
    environment: list[EnvironmentFact],
    groups: list[CompositeDevice] | None = None,
) -> DeviceProfile | None:
    """Build a video endpoint profile."""

    from gst_device_explorer.core.profiles import (
        build_video_profile as _build_video_profile,
    )

    return _build_video_profile(device, capabilities, environment, groups)


__all__ = [
    "Capability",
    "CompositeDevice",
    "Device",
    "DeviceRef",
    "DeviceProfile",
    "EnvironmentFact",
    "ExecutionPlan",
    "GroupingEvidence",
    "GroupableDevice",
    "PipelineDiagnostic",
    "PipelineCandidate",
    "Profile",
    "ProfileCandidateSummary",
    "ProfileGroupSummary",
    "RendererOutput",
    "build_audio_input_profile",
    "build_audio_input_test_candidates",
    "build_audio_input_test_diagnostics",
    "build_audio_output_profile",
    "build_audio_output_test_candidates",
    "build_audio_output_test_diagnostics",
    "build_composite_devices",
    "build_groupable_devices",
    "build_video_profile",
    "build_video_preview_candidates",
    "build_video_preview_diagnostics",
    "discover_composite_devices",
    "discover_devices",
    "discover_groupable_devices",
]
