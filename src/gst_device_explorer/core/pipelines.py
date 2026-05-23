"""Pipeline candidate builders."""

from __future__ import annotations

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

    candidates: list[PipelineCandidate] = []
    for capability in capabilities:
        if capability.values.get("media_type") != "video":
            continue

        caps = _build_caps(capability.values)
        if caps is None:
            continue

        device_path = _device_path(device)
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

        candidates.append(
            PipelineCandidate(
                purpose="preview V4L2 video input",
                command=" ".join(command_parts),
                confidence=0.8,
                reasons=_candidate_reasons(
                    device_path=device_path,
                    values=capability.values,
                    required_elements=GENERIC_VIDEO_PREVIEW_ELEMENTS,
                ),
                warnings=[],
                required_elements=list(GENERIC_VIDEO_PREVIEW_ELEMENTS),
                selected_profile=GENERIC_VIDEO_PREVIEW_PROFILE,
            )
        )

    return candidates


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


def _build_caps(values: dict[str, Any]) -> str | None:
    pixel_format = values.get("pixel_format")
    width = values.get("width")
    height = values.get("height")

    if pixel_format == "MJPG":
        caps_parts = ["image/jpeg"]
    elif pixel_format == "YUYV":
        caps_parts = ["video/x-raw", "format=YUY2"]
    else:
        return None

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


def _candidate_reasons(
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
