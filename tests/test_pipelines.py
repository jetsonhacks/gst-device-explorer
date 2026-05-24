from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.core.pipelines import build_video_preview_candidates
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
    assert candidate.candidate_id == "generic-v4l2-mjpeg-jpegdec-autovideosink"
    assert candidate.argv == [
        "gst-launch-1.0",
        "v4l2src",
        "device=/dev/video0",
        "!",
        "image/jpeg, width=1920, height=1080, framerate=60/1",
        "!",
        "videoconvert",
        "!",
        "autovideosink",
        "sync=false",
    ]
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
    assert (
        candidates[0].candidate_id
        == "generic-v4l2-yuyv-videoconvert-autovideosink"
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


def test_jetson_mjpg_candidate_is_generated_when_elements_are_present() -> None:
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
        _environment_with_generic_and_jetson_elements(),
    )

    jetson_candidate = _candidate_by_profile(candidates, "jetson-video-preview")
    assert jetson_candidate.command == (
        "gst-launch-1.0 v4l2src device=/dev/video0 io-mode=2 "
        "do-timestamp=true ! image/jpeg, width=1920, height=1080, "
        "framerate=60/1 ! jpegparse ! nvjpegdec ! "
        "'video/x-raw(memory:NVMM), format=Y42B' ! nvvidconv ! "
        "'video/x-raw(memory:NVMM), format=NV12' ! nveglglessink sync=false"
    )
    assert jetson_candidate.candidate_id == "jetson-uvc-mjpeg-nvjpeg-nveglglessink"
    assert jetson_candidate.argv == [
        "gst-launch-1.0",
        "v4l2src",
        "device=/dev/video0",
        "io-mode=2",
        "do-timestamp=true",
        "!",
        "image/jpeg, width=1920, height=1080, framerate=60/1",
        "!",
        "jpegparse",
        "!",
        "nvjpegdec",
        "!",
        "video/x-raw(memory:NVMM), format=Y42B",
        "!",
        "nvvidconv",
        "!",
        "video/x-raw(memory:NVMM), format=NV12",
        "!",
        "nveglglessink",
        "sync=false",
    ]
    assert jetson_candidate.required_elements == [
        "v4l2src",
        "jpegparse",
        "nvjpegdec",
        "nvvidconv",
        "nveglglessink",
    ]


def test_jetson_candidate_is_not_generated_for_yuyv() -> None:
    device = _video_device()
    capability = _video_capability(pixel_format="YUYV", description="YUYV 4:2:2")

    candidates = build_video_preview_candidates(
        device,
        [capability],
        _environment_with_generic_and_jetson_elements(),
    )

    assert all(
        candidate.selected_profile != "jetson-video-preview"
        for candidate in candidates
    )


def test_jetson_candidate_is_not_generated_when_required_elements_are_missing() -> None:
    device = _video_device()
    capability = _video_capability(pixel_format="MJPG")

    candidates = build_video_preview_candidates(
        device,
        [capability],
        _environment_with_required_elements(),
    )

    assert all(
        candidate.selected_profile != "jetson-video-preview"
        for candidate in candidates
    )


def test_generic_candidate_still_exists_when_jetson_candidate_is_generated() -> None:
    candidates = build_video_preview_candidates(
        _video_device(),
        [_video_capability(pixel_format="MJPG")],
        _environment_with_generic_and_jetson_elements(),
    )

    assert _candidate_by_profile(candidates, "generic-linux-video-preview")
    assert _candidate_by_profile(candidates, "jetson-video-preview")


def test_jetson_candidate_has_higher_confidence_than_generic() -> None:
    candidates = build_video_preview_candidates(
        _video_device(),
        [_video_capability(pixel_format="MJPG")],
        _environment_with_generic_and_jetson_elements(),
    )

    generic = _candidate_by_profile(candidates, "generic-linux-video-preview")
    jetson = _candidate_by_profile(candidates, "jetson-video-preview")

    assert jetson.confidence > generic.confidence


def test_jetson_candidate_reasons_include_profile_choices() -> None:
    candidates = build_video_preview_candidates(
        _video_device(),
        [_video_capability(pixel_format="MJPG", width=1920, height=1080, fps=[60.0])],
        _environment_with_generic_and_jetson_elements(),
    )

    jetson = _candidate_by_profile(candidates, "jetson-video-preview")

    assert jetson.reasons == [
        "selected device path: /dev/video0",
        "selected MJPG capability",
        "selected size: 1920x1080",
        "selected frame rate: 60/1",
        (
            "NVIDIA elements available: v4l2src, jpegparse, nvjpegdec, "
            "nvvidconv, nveglglessink"
        ),
        (
            "io-mode=2 and do-timestamp=true selected for low-latency "
            "UVC MJPEG preview"
        ),
        (
            "nveglglessink selected because it preserves aspect ratio better "
            "than nv3dsink for preview resizing"
        ),
    ]


def test_jetson_mjpg_1080p60_ranks_above_jetson_mjpg_high_resolution_30fps() -> None:
    candidates = build_video_preview_candidates(
        _video_device(),
        [
            _video_capability(
                pixel_format="MJPG",
                width=3840,
                height=2592,
                fps=[30.0],
            ),
            _video_capability(
                pixel_format="MJPG",
                width=1920,
                height=1080,
                fps=[60.0],
            ),
        ],
        _environment_with_generic_and_jetson_elements(),
    )

    jetson_candidates = [
        candidate
        for candidate in candidates
        if candidate.selected_profile == "jetson-video-preview"
    ]

    assert "width=1920, height=1080, framerate=60/1" in jetson_candidates[0].command
    assert "width=3840, height=2592, framerate=30/1" in jetson_candidates[1].command


def test_jetson_candidates_rank_above_matching_generic_candidates() -> None:
    candidates = build_video_preview_candidates(
        _video_device(),
        [_video_capability(pixel_format="MJPG", width=1920, height=1080, fps=[60.0])],
        _environment_with_generic_and_jetson_elements(),
    )

    assert candidates[0].selected_profile == "jetson-video-preview"
    assert candidates[1].selected_profile == "generic-linux-video-preview"


def test_low_frame_rate_yuyv_candidates_rank_below_mjpg_candidates() -> None:
    candidates = build_video_preview_candidates(
        _video_device(),
        [
            _video_capability(
                pixel_format="YUYV",
                description="YUYV 4:2:2",
                width=3840,
                height=2592,
                fps=[1.0],
            ),
            _video_capability(
                pixel_format="MJPG",
                description="Motion-JPEG, compressed",
                width=1920,
                height=1080,
                fps=[30.0],
            ),
        ],
        _environment_with_required_elements(),
    )

    assert candidates[0].command.startswith(
        "gst-launch-1.0 v4l2src device=/dev/video0 ! image/jpeg"
    )
    assert candidates[-1].command.startswith(
        "gst-launch-1.0 v4l2src device=/dev/video0 ! video/x-raw"
    )


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


def _environment_with_generic_and_jetson_elements() -> list[EnvironmentFact]:
    return [
        _element_fact("v4l2src", True),
        _element_fact("videoconvert", True),
        _element_fact("autovideosink", True),
        _element_fact("jpegparse", True),
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


def _candidate_by_profile(candidates, selected_profile):
    return next(
        candidate
        for candidate in candidates
        if candidate.selected_profile == selected_profile
    )
