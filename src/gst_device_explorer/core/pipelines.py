"""Pipeline candidate builders."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from gst_device_explorer.core.models import (
    Capability,
    Device,
    EnvironmentFact,
    PipelineCandidate,
)


GENERIC_VIDEO_PREVIEW_PROFILE = "generic-linux-video-preview"
GENERIC_VIDEO_PREVIEW_ELEMENTS = ["v4l2src", "videoconvert", "autovideosink"]
JETSON_VIDEO_PREVIEW_PROFILE = "jetson-video-preview"
JETSON_MJPEG_PREVIEW_ELEMENTS = [
    "v4l2src",
    "jpegparse",
    "nvjpegdec",
    "nvvidconv",
    "nveglglessink",
]


@dataclass(frozen=True)
class _RankedCandidate:
    candidate: PipelineCandidate
    values: dict[str, Any]


def build_video_preview_candidates(
    device: Device,
    capabilities: list[Capability],
    environment: list[EnvironmentFact],
) -> list[PipelineCandidate]:
    """Build generic Linux V4L2 video preview pipeline candidates."""

    if device.kind != "video_input":
        return []

    missing_elements = _missing_elements(environment, GENERIC_VIDEO_PREVIEW_ELEMENTS)
    if missing_elements:
        return []

    candidates: list[_RankedCandidate] = []
    for capability in capabilities:
        if capability.values.get("media_type") != "video":
            continue

        caps = _build_caps(capability.values)
        if caps is None:
            continue

        device_path = _device_path(device)
        candidates.append(
            _RankedCandidate(
                candidate=_generic_video_preview_candidate(device_path, capability),
                values=capability.values,
            )
        )

        jetson_candidate = _jetson_mjpeg_preview_candidate(
            device_path=device_path,
            capability=capability,
            environment=environment,
        )
        if jetson_candidate is not None:
            candidates.append(
                _RankedCandidate(
                    candidate=jetson_candidate,
                    values=capability.values,
                )
            )

    return _sort_candidates(candidates)


def _generic_video_preview_candidate(
    device_path: str,
    capability: Capability,
) -> PipelineCandidate:
    caps = _build_caps(capability.values)
    if caps is None:
        raise ValueError("generic video preview candidate requires supported caps")

    command_parts = [
        "gst-launch-1.0",
        "v4l2src",
        f"device={device_path}",
        "!",
        caps,
        "!",
        "videoconvert",
        "!",
        "autovideosink",
        "sync=false",
    ]

    return PipelineCandidate(
        purpose="preview V4L2 video input",
        command=" ".join(command_parts),
        confidence=0.8,
        reasons=_generic_candidate_reasons(
            device_path=device_path,
            values=capability.values,
            required_elements=GENERIC_VIDEO_PREVIEW_ELEMENTS,
        ),
        warnings=[],
        required_elements=list(GENERIC_VIDEO_PREVIEW_ELEMENTS),
        selected_profile=GENERIC_VIDEO_PREVIEW_PROFILE,
    )


def _jetson_mjpeg_preview_candidate(
    device_path: str,
    capability: Capability,
    environment: list[EnvironmentFact],
) -> PipelineCandidate | None:
    values = capability.values
    if values.get("media_type") != "video" or values.get("pixel_format") != "MJPG":
        return None

    if _missing_elements(environment, JETSON_MJPEG_PREVIEW_ELEMENTS):
        return None

    caps = _build_mjpg_caps(values)
    command_parts = [
        "gst-launch-1.0",
        "v4l2src",
        f"device={device_path}",
        "io-mode=2",
        "do-timestamp=true",
        "!",
        caps,
        "!",
        "jpegparse",
        "!",
        "nvjpegdec",
        "!",
        "'video/x-raw(memory:NVMM), format=Y42B'",
        "!",
        "nvvidconv",
        "!",
        "'video/x-raw(memory:NVMM), format=NV12'",
        "!",
        "nveglglessink",
        "sync=false",
    ]

    return PipelineCandidate(
        purpose="preview V4L2 MJPEG video input with Jetson NVIDIA elements",
        command=" ".join(command_parts),
        confidence=0.9,
        reasons=_jetson_candidate_reasons(
            device_path=device_path,
            values=values,
            required_elements=JETSON_MJPEG_PREVIEW_ELEMENTS,
        ),
        warnings=[],
        required_elements=list(JETSON_MJPEG_PREVIEW_ELEMENTS),
        selected_profile=JETSON_VIDEO_PREVIEW_PROFILE,
    )


def _missing_elements(
    environment: list[EnvironmentFact],
    required_elements: list[str],
) -> list[str]:
    available = {
        fact.metadata.get("element")
        for fact in environment
        if fact.name == "gstreamer_element_available" and fact.value is True
    }
    return [element for element in required_elements if element not in available]


def _sort_candidates(candidates: list[_RankedCandidate]) -> list[PipelineCandidate]:
    return [
        ranked.candidate
        for ranked in sorted(candidates, key=_candidate_sort_key, reverse=True)
    ]


def _candidate_sort_key(ranked: _RankedCandidate) -> tuple[float, int, float, int]:
    values = ranked.values
    fps = _first_fps(values) or 0.0
    width = values.get("width")
    height = values.get("height")
    pixels = width * height if isinstance(width, int) and isinstance(height, int) else 0

    return (
        ranked.candidate.confidence,
        _format_score(values),
        float(fps),
        pixels,
    )


def _format_score(values: dict[str, Any]) -> int:
    if values.get("pixel_format") == "MJPG":
        return 2
    if values.get("pixel_format") == "YUYV":
        return 1
    return 0


def _build_caps(values: dict[str, Any]) -> str | None:
    pixel_format = values.get("pixel_format")

    if pixel_format == "MJPG":
        return _build_mjpg_caps(values)
    elif pixel_format == "YUYV":
        caps_parts = ["video/x-raw", "format=YUY2"]
    else:
        return None

    width = values.get("width")
    height = values.get("height")
    if width is not None:
        caps_parts.append(f"width={width}")
    if height is not None:
        caps_parts.append(f"height={height}")

    fps = _first_fps(values)
    if fps is not None:
        caps_parts.append(f"framerate={_fps_to_fraction(fps)}")

    return ", ".join(caps_parts)


def _build_mjpg_caps(values: dict[str, Any]) -> str:
    caps_parts = ["image/jpeg"]
    width = values.get("width")
    height = values.get("height")

    if width is not None:
        caps_parts.append(f"width={width}")
    if height is not None:
        caps_parts.append(f"height={height}")

    fps = _first_fps(values)
    if fps is not None:
        caps_parts.append(f"framerate={_fps_to_fraction(fps)}")

    return ", ".join(caps_parts)


def _first_fps(values: dict[str, Any]) -> float | int | None:
    fps_values = values.get("fps")
    if not isinstance(fps_values, list) or not fps_values:
        return None

    first = fps_values[0]
    if isinstance(first, int | float):
        return first
    return None


def _fps_to_fraction(fps: float | int) -> str:
    fraction = Fraction(str(fps)).limit_denominator(1001)
    return f"{fraction.numerator}/{fraction.denominator}"


def _device_path(device: Device) -> str:
    path = device.metadata.get("path")
    if isinstance(path, str) and path:
        return path
    return device.id


def _generic_candidate_reasons(
    device_path: str,
    values: dict[str, Any],
    required_elements: list[str],
) -> list[str]:
    reasons = [
        f"selected device path: {device_path}",
        f"selected pixel format: {values.get('pixel_format')}",
        f"selected size: {values.get('width')}x{values.get('height')}",
        "required elements available: " + ", ".join(required_elements),
    ]

    fps = _first_fps(values)
    if fps is not None:
        reasons.insert(3, f"selected frame rate: {_fps_to_fraction(fps)}")

    return reasons


def _jetson_candidate_reasons(
    device_path: str,
    values: dict[str, Any],
    required_elements: list[str],
) -> list[str]:
    reasons = [
        f"selected device path: {device_path}",
        "selected MJPG capability",
        f"selected size: {values.get('width')}x{values.get('height')}",
        "NVIDIA elements available: " + ", ".join(required_elements),
        (
            "io-mode=2 and do-timestamp=true selected for low-latency "
            "UVC MJPEG preview"
        ),
        (
            "nveglglessink selected because it preserves aspect ratio better "
            "than nv3dsink for preview resizing"
        ),
    ]

    fps = _first_fps(values)
    if fps is not None:
        reasons.insert(3, f"selected frame rate: {_fps_to_fraction(fps)}")

    return reasons
