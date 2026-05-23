from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.core import build_video_preview_candidates
from gst_device_explorer.core.models import Capability, Device, EnvironmentFact


def test_mjpg_generic_video_preview_candidate() -> None:
    device = _video_device()
    capability = _video_capability(
        pixel_format="MJPG",
        description="Motion-JPEG, compressed",
        width=1920,
        height=1080,
        fps=[60.0],
    )

    candidates = build_video_preview_candidates(
        device,
        [capability],
        _environment_with_required_elements(),
    )

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.command == (
        "gst-launch-1.0 v4l2src device=/dev/video0 ! "
        "image/jpeg, width=1920, height=1080, framerate=60/1 ! "
        "videoconvert ! autovideosink sync=false"
    )
    assert candidate.selected_profile == "generic-linux-video-preview"
    assert candidate.confidence == 0.8


def test_yuyv_generic_video_preview_candidate() -> None:
    device = _video_device()
    capability = _video_capability(
        pixel_format="YUYV",
        description="YUYV 4:2:2",
        width=1280,
        height=720,
        fps=[30.0],
    )

    candidates = build_video_preview_candidates(
        device,
        [capability],
        _environment_with_required_elements(),
    )

    assert len(candidates) == 1
    assert candidates[0].command == (
        "gst-launch-1.0 v4l2src device=/dev/video0 ! "
        "video/x-raw, format=YUY2, width=1280, height=720, framerate=30/1 ! "
        "videoconvert ! autovideosink sync=false"
    )


def test_non_video_device_produces_no_candidates() -> None:
    device = Device(id="hw:0,0", kind="audio_input", name="USB Audio")

    candidates = build_video_preview_candidates(
        device,
        [_video_capability()],
        _environment_with_required_elements(),
    )

    assert candidates == []


def test_missing_required_elements_produces_no_candidates() -> None:
    device = _video_device()
    environment = [
        _element_fact("v4l2src", True),
        _element_fact("videoconvert", True),
        _element_fact("autovideosink", False),
    ]

    candidates = build_video_preview_candidates(
        device,
        [_video_capability()],
        environment,
    )

    assert candidates == []


def test_reasons_and_required_elements_are_populated() -> None:
    device = _video_device()
    capability = _video_capability(pixel_format="MJPG", width=640, height=480)

    candidates = build_video_preview_candidates(
        device,
        [capability],
        _environment_with_required_elements(),
    )

    candidate = candidates[0]
    assert candidate.required_elements == [
        "v4l2src",
        "videoconvert",
        "autovideosink",
    ]
    assert candidate.reasons == [
        "selected device path: /dev/video0",
        "selected pixel format: MJPG",
        "selected size: 640x480",
        "selected frame rate: 30/1",
        "required elements available: v4l2src, videoconvert, autovideosink",
    ]
    assert candidate.warnings == []


def _video_device() -> Device:
    return Device(
        id="/dev/video0",
        kind="video_input",
        name="video0",
        metadata={"backend": "v4l2", "path": "/dev/video0"},
    )


def _video_capability(
    pixel_format: str = "MJPG",
    description: str = "Motion-JPEG, compressed",
    width: int = 640,
    height: int = 480,
    fps: list[float] | None = None,
) -> Capability:
    return Capability(
        name="video_format",
        values={
            "media_type": "video",
            "pixel_format": pixel_format,
            "description": description,
            "width": width,
            "height": height,
            "fps": fps if fps is not None else [30.0],
        },
        source="v4l2-ctl",
    )


def _environment_with_required_elements() -> list[EnvironmentFact]:
    return [
        _element_fact("v4l2src", True),
        _element_fact("videoconvert", True),
        _element_fact("autovideosink", True),
    ]


def _element_fact(element: str, available: bool) -> EnvironmentFact:
    return EnvironmentFact(
        name="gstreamer_element_available",
        value=available,
        source="gst-inspect-1.0",
        metadata={"element": element},
    )
