"""Video pipeline diagnostic builders."""

from __future__ import annotations

from typing import Any

from gst_device_explorer.core.diagnostics import build_requirement_diagnostic
from gst_device_explorer.core.models import (
    Capability,
    Device,
    EnvironmentFact,
    PipelineDiagnostic,
)
from gst_device_explorer.core.pipelines import (
    GENERIC_MJPEG_VIDEO_PREVIEW_ELEMENTS,
    GENERIC_VIDEO_PREVIEW_ELEMENTS,
    JETSON_MJPEG_PREVIEW_ELEMENTS,
    _device_path,
)


GENERIC_V4L2_MJPEG_CANDIDATE_ID = "generic-v4l2-mjpeg-jpegdec-autovideosink"
GENERIC_V4L2_YUYV_CANDIDATE_ID = "generic-v4l2-yuyv-videoconvert-autovideosink"
JETSON_UVC_MJPEG_CANDIDATE_ID = "jetson-uvc-mjpeg-nvjpeg-nveglglessink"


def build_video_preview_diagnostics(
    device: Device,
    capabilities: list[Capability],
    environment: list[EnvironmentFact],
) -> list[PipelineDiagnostic]:
    """Build diagnostics for existing V4L2 video preview candidate families."""

    if device.kind != "video_input":
        return []

    device_path = _device_path(device)
    diagnostics: list[PipelineDiagnostic] = []
    emitted_candidate_ids: set[str] = set()

    for capability in capabilities:
        values = capability.values
        if values.get("media_type") != "video":
            continue

        generic_candidate_id = _generic_candidate_id(values)
        if (
            generic_candidate_id is not None
            and generic_candidate_id not in emitted_candidate_ids
        ):
            diagnostics.append(
                build_requirement_diagnostic(
                    candidate_id=generic_candidate_id,
                    device_kind="video",
                    device_id=device_path,
                    required_elements=(
                        GENERIC_MJPEG_VIDEO_PREVIEW_ELEMENTS
                        if values.get("pixel_format") == "MJPG"
                        else GENERIC_VIDEO_PREVIEW_ELEMENTS
                    ),
                    environment=environment,
                    available_reason=(
                        "Required GStreamer elements are available and the "
                        "device exposes a compatible video format."
                    ),
                )
            )
            emitted_candidate_ids.add(generic_candidate_id)

        if (
            values.get("pixel_format") == "MJPG"
            and JETSON_UVC_MJPEG_CANDIDATE_ID not in emitted_candidate_ids
        ):
            diagnostics.append(
                build_requirement_diagnostic(
                    candidate_id=JETSON_UVC_MJPEG_CANDIDATE_ID,
                    device_kind="video",
                    device_id=device_path,
                    required_elements=JETSON_MJPEG_PREVIEW_ELEMENTS,
                    environment=environment,
                    available_reason=(
                        "NVIDIA MJPEG preview elements are available and the "
                        "device exposes an MJPG video format."
                    ),
                )
            )
            emitted_candidate_ids.add(JETSON_UVC_MJPEG_CANDIDATE_ID)

    return diagnostics


def _generic_candidate_id(values: dict[str, Any]) -> str | None:
    pixel_format = values.get("pixel_format")
    if pixel_format == "MJPG":
        return GENERIC_V4L2_MJPEG_CANDIDATE_ID
    if pixel_format == "YUYV":
        return GENERIC_V4L2_YUYV_CANDIDATE_ID
    return None

