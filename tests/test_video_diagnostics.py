from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.core.pipelines import build_video_preview_candidates
from gst_device_explorer.core.video_diagnostics import build_video_preview_diagnostics
from gst_device_explorer.core.models import Capability, Device, EnvironmentFact


def test_generic_mjpg_video_diagnostic_available() -> None:
    diagnostics = build_video_preview_diagnostics(
        _video_device(),
        [_video_capability(pixel_format="MJPG")],
        _environment_with_generic_elements(),
    )

    diagnostic = _diagnostic_by_id(
        diagnostics,
        "generic-v4l2-mjpeg-jpegdec-autovideosink",
    )
    assert diagnostic.device_kind == "video"
    assert diagnostic.device == "/dev/video0"
    assert diagnostic.status == "available"
    assert diagnostic.reason == (
        "Required GStreamer elements are available and the device exposes "
        "a compatible video format."
    )
    assert diagnostic.required_elements == [
        "v4l2src",
        "jpegparse",
        "jpegdec",
        "videoconvert",
        "autovideosink",
    ]
    assert diagnostic.available_elements == diagnostic.required_elements
    assert diagnostic.missing_elements == []
    assert diagnostic.suggested_next_checks == []


def test_generic_video_diagnostic_with_missing_required_element() -> None:
    diagnostics = build_video_preview_diagnostics(
        _video_device(),
        [_video_capability(pixel_format="YUYV")],
        [
            _element_fact("v4l2src", True),
            _element_fact("videoconvert", True),
            _element_fact("autovideosink", False),
        ],
    )

    diagnostic = _diagnostic_by_id(
        diagnostics,
        "generic-v4l2-yuyv-videoconvert-autovideosink",
    )
    assert diagnostic.status == "unavailable"
    assert diagnostic.reason == "Required GStreamer elements are missing."
    assert diagnostic.required_elements == [
        "v4l2src",
        "videoconvert",
        "autovideosink",
    ]
    assert diagnostic.available_elements == ["v4l2src", "videoconvert"]
    assert diagnostic.missing_elements == ["autovideosink"]
    assert diagnostic.suggested_next_checks == ["gst-inspect-1.0 autovideosink"]


def test_jetson_mjpg_video_diagnostic_available() -> None:
    diagnostics = build_video_preview_diagnostics(
        _video_device(),
        [_video_capability(pixel_format="MJPG")],
        _environment_with_generic_and_jetson_elements(),
    )

    diagnostic = _diagnostic_by_id(
        diagnostics,
        "jetson-uvc-mjpeg-nvjpeg-nveglglessink",
    )
    assert diagnostic.status == "available"
    assert diagnostic.reason == (
        "NVIDIA MJPEG preview elements are available and the device exposes "
        "an MJPG video format."
    )
    assert diagnostic.required_elements == [
        "v4l2src",
        "jpegparse",
        "nvjpegdec",
        "nvvidconv",
        "nveglglessink",
    ]
    assert diagnostic.available_elements == diagnostic.required_elements
    assert diagnostic.missing_elements == []


def test_jetson_mjpg_video_diagnostic_with_missing_required_element() -> None:
    diagnostics = build_video_preview_diagnostics(
        _video_device(),
        [_video_capability(pixel_format="MJPG")],
        [
            _element_fact("v4l2src", True),
            _element_fact("videoconvert", True),
            _element_fact("autovideosink", True),
            _element_fact("jpegparse", True),
            _element_fact("nvjpegdec", True),
            _element_fact("nvvidconv", False),
            _element_fact("nveglglessink", True),
        ],
    )

    diagnostic = _diagnostic_by_id(
        diagnostics,
        "jetson-uvc-mjpeg-nvjpeg-nveglglessink",
    )
    assert diagnostic.status == "unavailable"
    assert diagnostic.available_elements == [
        "v4l2src",
        "jpegparse",
        "nvjpegdec",
        "nveglglessink",
    ]
    assert diagnostic.missing_elements == ["nvvidconv"]
    assert diagnostic.suggested_next_checks == ["gst-inspect-1.0 nvvidconv"]


def test_video_diagnostics_omit_unsupported_video_formats() -> None:
    diagnostics = build_video_preview_diagnostics(
        _video_device(),
        [_video_capability(pixel_format="H264")],
        _environment_with_generic_and_jetson_elements(),
    )

    assert diagnostics == []


def test_video_diagnostics_do_not_change_candidate_generation_behavior() -> None:
    environment = [
        _element_fact("v4l2src", True),
        _element_fact("videoconvert", True),
        _element_fact("autovideosink", False),
    ]

    diagnostics = build_video_preview_diagnostics(
        _video_device(),
        [_video_capability(pixel_format="MJPG")],
        environment,
    )
    candidates = build_video_preview_candidates(
        _video_device(),
        [_video_capability(pixel_format="MJPG")],
        environment,
    )

    assert _diagnostic_by_id(
        diagnostics,
        "generic-v4l2-mjpeg-jpegdec-autovideosink",
    ).status == "unavailable"
    assert candidates == []


def _video_device() -> Device:
    return Device(
        id="/dev/video0",
        kind="video_input",
        name="video0",
        metadata={"backend": "v4l2", "path": "/dev/video0"},
    )


def _video_capability(pixel_format: str) -> Capability:
    return Capability(
        name="video_format",
        values={
            "media_type": "video",
            "pixel_format": pixel_format,
            "description": pixel_format,
            "width": 640,
            "height": 480,
            "fps": [30.0],
        },
        source="v4l2-ctl",
    )


def _environment_with_generic_elements() -> list[EnvironmentFact]:
    return [
        _element_fact("v4l2src", True),
        _element_fact("jpegparse", True),
        _element_fact("jpegdec", True),
        _element_fact("videoconvert", True),
        _element_fact("autovideosink", True),
    ]


def _environment_with_generic_and_jetson_elements() -> list[EnvironmentFact]:
    return [
        _element_fact("v4l2src", True),
        _element_fact("videoconvert", True),
        _element_fact("autovideosink", True),
        _element_fact("jpegparse", True),
        _element_fact("jpegdec", True),
        _element_fact("nvjpegdec", True),
        _element_fact("nvvidconv", True),
        _element_fact("nveglglessink", True),
    ]


def _element_fact(element: str, available: bool) -> EnvironmentFact:
    return EnvironmentFact(
        name="gstreamer_element_available",
        value=available,
        source="gst-inspect-1.0",
        metadata={"element": element},
    )


def _diagnostic_by_id(diagnostics, candidate_id):
    return next(
        diagnostic
        for diagnostic in diagnostics
        if diagnostic.candidate_id == candidate_id
    )
