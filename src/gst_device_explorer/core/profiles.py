"""Device profile builders."""

from __future__ import annotations

from fractions import Fraction
from typing import Any

from gst_device_explorer.core.audio_diagnostics import (
    build_audio_input_test_diagnostics,
    build_audio_output_test_diagnostics,
)
from gst_device_explorer.core.models import (
    Capability,
    CompositeDevice,
    Device,
    DeviceRef,
    DeviceProfile,
    EnvironmentFact,
    PipelineDiagnostic,
    ProfileCandidateSummary,
    ProfileGroupSummary,
)
from gst_device_explorer.core.video_diagnostics import build_video_preview_diagnostics


def build_audio_input_profile(
    device: Device,
    environment: list[EnvironmentFact],
    groups: list[CompositeDevice] | None = None,
) -> DeviceProfile | None:
    """Build an audio input endpoint profile from existing facts."""

    if device.kind != "audio_input":
        return None

    alsa_device = _alsa_device_name(device)
    diagnostics = build_audio_input_test_diagnostics(device, environment)
    return _build_audio_profile(
        device=device,
        device_kind="audio-input",
        alsa_device=alsa_device,
        diagnostics=diagnostics,
        groups=groups,
    )


def build_audio_output_profile(
    device: Device,
    environment: list[EnvironmentFact],
    groups: list[CompositeDevice] | None = None,
) -> DeviceProfile | None:
    """Build an audio output endpoint profile from existing facts."""

    if device.kind != "audio_output":
        return None

    alsa_device = _alsa_device_name(device)
    diagnostics = build_audio_output_test_diagnostics(device, environment)
    return _build_audio_profile(
        device=device,
        device_kind="audio-output",
        alsa_device=alsa_device,
        diagnostics=diagnostics,
        groups=groups,
    )


def build_video_profile(
    device: Device,
    capabilities: list[Capability],
    environment: list[EnvironmentFact],
    groups: list[CompositeDevice] | None = None,
) -> DeviceProfile | None:
    """Build a video endpoint profile from existing facts."""

    if device.kind != "video_input":
        return None

    device_path = _device_path(device)
    diagnostics = build_video_preview_diagnostics(device, capabilities, environment)
    return DeviceProfile(
        device_kind="video",
        device=device_path,
        display_name=device.name or None,
        metadata=dict(device.metadata),
        capabilities_summary=_video_capabilities_summary(capabilities),
        candidate_summary=_candidate_summary(diagnostics),
        groups=_profile_group_summaries(
            groups=groups,
            endpoint_role="camera",
            endpoint_id=device.id,
            endpoint_path=device_path,
        ),
        suggested_next_commands=[
            f"gst-device-explorer pipeline video {device_path}",
            f"gst-device-explorer pipeline video {device_path} --diagnostics",
            f"gst-device-explorer run video {device_path} --dry-run",
        ],
    )


def _build_audio_profile(
    device: Device,
    device_kind: str,
    alsa_device: str,
    diagnostics: list[PipelineDiagnostic],
    groups: list[CompositeDevice] | None,
) -> DeviceProfile:
    return DeviceProfile(
        device_kind=device_kind,
        device=alsa_device,
        display_name=device.name or None,
        metadata=dict(device.metadata),
        capabilities_summary={},
        candidate_summary=_candidate_summary(diagnostics),
        groups=_profile_group_summaries(
            groups=groups,
            endpoint_role=device_kind,
            endpoint_id=device.id,
            endpoint_path=alsa_device,
        ),
        suggested_next_commands=[
            f"gst-device-explorer pipeline {device_kind} {alsa_device}",
            f"gst-device-explorer pipeline {device_kind} {alsa_device} --diagnostics",
            f"gst-device-explorer run {device_kind} {alsa_device} --dry-run",
        ],
    )


def _candidate_summary(
    diagnostics: list[PipelineDiagnostic],
) -> dict[str, list[ProfileCandidateSummary]]:
    summary: dict[str, list[ProfileCandidateSummary]] = {
        "available": [],
        "unavailable": [],
    }
    for diagnostic in diagnostics:
        entry = ProfileCandidateSummary(
            candidate_id=diagnostic.candidate_id,
            status=diagnostic.status,
            reason=diagnostic.reason,
            missing_elements=list(diagnostic.missing_elements),
        )
        if diagnostic.status == "available":
            summary["available"].append(entry)
        else:
            summary["unavailable"].append(entry)
    return summary


def _profile_group_summaries(
    groups: list[CompositeDevice] | None,
    endpoint_role: str,
    endpoint_id: str,
    endpoint_path: str,
) -> list[ProfileGroupSummary]:
    if not groups:
        return []

    return [
        ProfileGroupSummary(
            group_id=group.id,
            label=group.name,
            confidence=group.confidence,
            kind=group.kind,
            member_count=len(group.members),
        )
        for group in groups
        if _group_contains_endpoint(
            group,
            endpoint_role=endpoint_role,
            endpoint_id=endpoint_id,
            endpoint_path=endpoint_path,
        )
    ]


def _group_contains_endpoint(
    group: CompositeDevice,
    endpoint_role: str,
    endpoint_id: str,
    endpoint_path: str,
) -> bool:
    return any(
        _member_matches_endpoint(
            member,
            endpoint_role=endpoint_role,
            endpoint_id=endpoint_id,
            endpoint_path=endpoint_path,
        )
        for member in group.members
    )


def _member_matches_endpoint(
    member: DeviceRef,
    endpoint_role: str,
    endpoint_id: str,
    endpoint_path: str,
) -> bool:
    if member.role != endpoint_role:
        return False
    return member.device_id == endpoint_id or member.path == endpoint_path


def _alsa_device_name(device: Device) -> str:
    value = device.metadata.get("alsa_device", device.id)
    return str(value)


def _device_path(device: Device) -> str:
    value = device.metadata.get("path", device.id)
    return str(value)


def _video_capabilities_summary(
    capabilities: list[Capability],
) -> dict[str, Any]:
    video_values = [
        capability.values
        for capability in capabilities
        if capability.values.get("media_type") == "video"
    ]
    formats = _unique_ordered(
        str(values["pixel_format"])
        for values in video_values
        if values.get("pixel_format") is not None
    )
    frame_rates = _unique_ordered(
        _fps_to_fraction(fps)
        for values in video_values
        for fps in _fps_values(values)
    )

    summary: dict[str, Any] = {"mode_count": len(video_values)}
    if formats:
        summary["formats"] = formats
    max_resolution = _max_resolution(video_values)
    if max_resolution is not None:
        summary["max_resolution"] = max_resolution
    if frame_rates:
        summary["frame_rates"] = frame_rates
    return summary


def _unique_ordered(values) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique.append(value)
    return unique


def _fps_values(values: dict[str, Any]) -> list[float | int]:
    fps_values = values.get("fps")
    if not isinstance(fps_values, list):
        return []
    return [fps for fps in fps_values if isinstance(fps, int | float)]


def _fps_to_fraction(fps: float | int) -> str:
    fraction = Fraction(str(fps)).limit_denominator(1001)
    return f"{fraction.numerator}/{fraction.denominator}"


def _max_resolution(values_list: list[dict[str, Any]]) -> str | None:
    best_width = None
    best_height = None
    best_pixels = -1
    for values in values_list:
        width = values.get("width")
        height = values.get("height")
        if not isinstance(width, int) or not isinstance(height, int):
            continue
        pixels = width * height
        if pixels > best_pixels:
            best_width = width
            best_height = height
            best_pixels = pixels
    if best_width is None or best_height is None:
        return None
    return f"{best_width}x{best_height}"
