from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.core.audio_diagnostics import (
    build_audio_input_test_diagnostics,
    build_audio_output_test_diagnostics,
)
from gst_device_explorer.core.audio_pipelines import (
    build_audio_input_test_candidates,
    build_audio_output_test_candidates,
)
from gst_device_explorer.core.pipelines import build_video_preview_candidates
from gst_device_explorer.core.profiles import (
    build_audio_input_profile,
    build_audio_output_profile,
    build_video_profile,
)
from gst_device_explorer.core.video_diagnostics import build_video_preview_diagnostics
from gst_device_explorer.core.models import (
    Capability,
    CompositeDevice,
    Device,
    DeviceRef,
    EnvironmentFact,
    GroupingEvidence,
)


def test_audio_input_profile_summarizes_available_candidate() -> None:
    profile = build_audio_input_profile(
        _audio_input_device(),
        _environment_with_audio_input_elements(),
    )

    assert profile is not None
    assert profile.device_kind == "audio-input"
    assert profile.device == "hw:0,0"
    assert profile.display_name == "USB Audio: Capture"
    assert profile.metadata == {"backend": "alsa", "alsa_device": "hw:0,0"}
    assert profile.capabilities_summary == {}
    assert profile.groups == []
    assert profile.candidate_summary["available"][0].candidate_id == (
        "generic-alsa-audio-input-level-fakesink"
    )
    assert profile.candidate_summary["available"][0].status == "available"
    assert profile.candidate_summary["available"][0].missing_elements == []
    assert profile.candidate_summary["unavailable"] == []
    assert [cmd.command for cmd in profile.suggested_next_commands] == [
        "gst-device-explorer pipeline audio-input hw:0,0",
        "gst-device-explorer pipeline audio-input hw:0,0 --diagnostics",
        "gst-device-explorer run audio-input hw:0,0 --dry-run",
    ]


def test_audio_output_profile_summarizes_available_candidate() -> None:
    profile = build_audio_output_profile(
        _audio_output_device(),
        _environment_with_audio_output_elements(),
    )

    assert profile is not None
    assert profile.device_kind == "audio-output"
    assert profile.device == "hw:0,0"
    assert profile.display_name == "USB Audio: Playback"
    assert profile.metadata == {"backend": "alsa", "alsa_device": "hw:0,0"}
    assert profile.candidate_summary["available"][0].candidate_id == (
        "generic-alsa-audio-output-sine-alsasink"
    )
    assert profile.candidate_summary["available"][0].reason == (
        "ALSA playback device and required GStreamer elements are available."
    )
    assert profile.candidate_summary["unavailable"] == []
    assert [cmd.command for cmd in profile.suggested_next_commands] == [
        "gst-device-explorer pipeline audio-output hw:0,0",
        "gst-device-explorer pipeline audio-output hw:0,0 --diagnostics",
        "gst-device-explorer run audio-output hw:0,0 --dry-run",
    ]


def test_audio_output_profile_summarizes_unavailable_candidate() -> None:
    environment = [
        _element_fact("audiotestsrc", True),
        _element_fact("audioconvert", True),
        _element_fact("audioresample", True),
        _element_fact("alsasink", False),
    ]

    profile = build_audio_output_profile(_audio_output_device(), environment)

    assert profile is not None
    assert profile.candidate_summary["available"] == []
    unavailable = profile.candidate_summary["unavailable"][0]
    assert unavailable.candidate_id == "generic-alsa-audio-output-sine-alsasink"
    assert unavailable.status == "unavailable"
    assert unavailable.reason == "Required GStreamer elements are missing."
    assert unavailable.missing_elements == ["alsasink"]


def test_audio_profiles_ignore_wrong_device_kind() -> None:
    assert (
        build_audio_input_profile(
            _audio_output_device(),
            _environment_with_audio_input_elements(),
        )
        is None
    )
    assert (
        build_audio_output_profile(
            _audio_input_device(),
            _environment_with_audio_output_elements(),
        )
        is None
    )


def test_audio_profile_does_not_change_candidate_or_diagnostic_behavior() -> None:
    environment = [
        _element_fact("alsasrc", True),
        _element_fact("audioconvert", True),
        _element_fact("audioresample", True),
        _element_fact("level", False),
        _element_fact("fakesink", True),
    ]

    profile = build_audio_input_profile(_audio_input_device(), environment)
    diagnostics = build_audio_input_test_diagnostics(_audio_input_device(), environment)
    candidates = build_audio_input_test_candidates(_audio_input_device(), environment)

    assert profile is not None
    assert profile.candidate_summary["unavailable"][0].missing_elements == ["level"]
    assert diagnostics[0].missing_elements == ["level"]
    assert candidates == []


def test_audio_input_profile_includes_matching_group_summaries() -> None:
    profile = build_audio_input_profile(
        _audio_input_device(),
        _environment_with_audio_input_elements(),
        [_audio_group(), _usb_family_group(), _other_video_group()],
    )

    assert profile is not None
    assert [
        {
            "group_id": group.group_id,
            "label": group.label,
            "confidence": group.confidence,
            "kind": group.kind,
            "member_count": group.member_count,
        }
        for group in profile.groups
    ] == [
        {
            "group_id": "audio-device-alsa-card-0",
            "label": "Reachy Mini Audio",
            "confidence": 0.9,
            "kind": "audio-device",
            "member_count": 2,
        },
        {
            "group_id": "usb-family-1-4",
            "label": "Reachy Mini",
            "confidence": 0.8,
            "kind": "unknown",
            "member_count": 3,
        },
    ]


def test_audio_output_profile_includes_matching_group_summaries() -> None:
    profile = build_audio_output_profile(
        _audio_output_device(),
        _environment_with_audio_output_elements(),
        [_audio_group(), _usb_family_group()],
    )

    assert profile is not None
    assert [group.group_id for group in profile.groups] == [
        "audio-device-alsa-card-0",
        "usb-family-1-4",
    ]


def test_video_profile_summarizes_capabilities_and_available_candidates() -> None:
    profile = build_video_profile(
        _video_device(),
        [
            _video_capability(pixel_format="MJPG", width=1920, height=1080, fps=[30.0]),
            _video_capability(pixel_format="YUYV", width=1280, height=720, fps=[15.0]),
        ],
        _environment_with_generic_and_jetson_elements(),
    )

    assert profile is not None
    assert profile.device_kind == "video"
    assert profile.device == "/dev/video0"
    assert profile.display_name == "video0"
    assert profile.metadata == {"backend": "v4l2", "path": "/dev/video0"}
    assert profile.capabilities_summary == {
        "formats": ["MJPG", "YUYV"],
        "frame_rates": ["30/1", "15/1"],
        "max_resolution": "1920x1080",
        "mode_count": 2,
    }
    assert [
        candidate.candidate_id
        for candidate in profile.candidate_summary["available"]
    ] == [
        "generic-v4l2-mjpeg-jpegdec-autovideosink",
        "jetson-uvc-mjpeg-nvjpeg-nveglglessink",
        "generic-v4l2-yuyv-videoconvert-autovideosink",
    ]
    assert profile.candidate_summary["unavailable"] == []
    assert profile.groups == []
    assert [cmd.command for cmd in profile.suggested_next_commands] == [
        "gst-device-explorer pipeline video /dev/video0",
        "gst-device-explorer pipeline video /dev/video0 --diagnostics",
        "gst-device-explorer run video /dev/video0 --dry-run",
    ]


def test_video_profile_summarizes_unavailable_candidate() -> None:
    environment = [
        _element_fact("v4l2src", True),
        _element_fact("videoconvert", True),
        _element_fact("autovideosink", False),
    ]

    profile = build_video_profile(
        _video_device(),
        [_video_capability(pixel_format="YUYV")],
        environment,
    )

    assert profile is not None
    assert profile.candidate_summary["available"] == []
    unavailable = profile.candidate_summary["unavailable"][0]
    assert unavailable.candidate_id == "generic-v4l2-yuyv-videoconvert-autovideosink"
    assert unavailable.status == "unavailable"
    assert unavailable.reason == "Required GStreamer elements are missing."
    assert unavailable.missing_elements == ["autovideosink"]


def test_video_profile_does_not_change_candidate_or_diagnostic_behavior() -> None:
    environment = [
        _element_fact("v4l2src", True),
        _element_fact("videoconvert", True),
        _element_fact("autovideosink", False),
    ]

    profile = build_video_profile(
        _video_device(),
        [_video_capability(pixel_format="MJPG")],
        environment,
    )
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

    assert profile is not None
    assert profile.candidate_summary["unavailable"][0].missing_elements == [
        "autovideosink"
    ]
    assert diagnostics[0].missing_elements == ["autovideosink"]
    assert candidates == []


def test_video_profile_includes_matching_group_summaries() -> None:
    profile = build_video_profile(
        _video_device(),
        [_video_capability(pixel_format="MJPG")],
        _environment_with_generic_and_jetson_elements(),
        [_video_group(), _usb_family_group(), _audio_group()],
    )

    assert profile is not None
    assert [
        {
            "group_id": group.group_id,
            "label": group.label,
            "confidence": group.confidence,
            "kind": group.kind,
            "member_count": group.member_count,
        }
        for group in profile.groups
    ] == [
        {
            "group_id": "usb-device-1-4-1",
            "label": "Reachy Mini Camera",
            "confidence": 0.9,
            "kind": "unknown",
            "member_count": 1,
        },
        {
            "group_id": "usb-family-1-4",
            "label": "Reachy Mini",
            "confidence": 0.8,
            "kind": "unknown",
            "member_count": 3,
        },
    ]


def test_profile_groups_are_empty_when_no_groups_match() -> None:
    audio_profile = build_audio_input_profile(
        _audio_input_device(),
        _environment_with_audio_input_elements(),
        [_other_video_group()],
    )
    video_profile = build_video_profile(
        _video_device(),
        [_video_capability(pixel_format="MJPG")],
        _environment_with_generic_and_jetson_elements(),
        [_audio_group()],
    )

    assert audio_profile is not None
    assert video_profile is not None
    assert audio_profile.groups == []
    assert video_profile.groups == []


def test_video_profile_ignores_wrong_device_kind() -> None:
    assert (
        build_video_profile(
            _audio_input_device(),
            [_video_capability(pixel_format="MJPG")],
            _environment_with_generic_and_jetson_elements(),
        )
        is None
    )


def _audio_input_device() -> Device:
    return Device(
        id="hw:0,0",
        kind="audio_input",
        name="USB Audio: Capture",
        metadata={"backend": "alsa", "alsa_device": "hw:0,0"},
    )


def _audio_output_device() -> Device:
    return Device(
        id="hw:0,0",
        kind="audio_output",
        name="USB Audio: Playback",
        metadata={"backend": "alsa", "alsa_device": "hw:0,0"},
    )


def _video_device() -> Device:
    return Device(
        id="/dev/video0",
        kind="video_input",
        name="video0",
        metadata={"backend": "v4l2", "path": "/dev/video0"},
    )


def _video_capability(
    pixel_format: str,
    width: int = 640,
    height: int = 480,
    fps: list[float] | None = None,
) -> Capability:
    return Capability(
        name="video_format",
        values={
            "media_type": "video",
            "pixel_format": pixel_format,
            "description": pixel_format,
            "width": width,
            "height": height,
            "fps": fps if fps is not None else [30.0],
        },
        source="v4l2-ctl",
    )


def _audio_group() -> CompositeDevice:
    return CompositeDevice(
        id="audio-device-alsa-card-0",
        name="Reachy Mini Audio",
        kind="audio-device",
        confidence=0.9,
        members=[
            DeviceRef(
                role="audio-input",
                device_id="hw:0,0",
                path="hw:0,0",
                subsystem="alsa",
            ),
            DeviceRef(
                role="audio-output",
                device_id="hw:0,0",
                path="hw:0,0",
                subsystem="alsa",
            ),
        ],
        evidence=[
            GroupingEvidence(
                source="alsa-card",
                description="audio devices share ALSA card 0",
                strength=0.9,
            )
        ],
    )


def _video_group() -> CompositeDevice:
    return CompositeDevice(
        id="usb-device-1-4-1",
        name="Reachy Mini Camera",
        kind="unknown",
        confidence=0.9,
        members=[
            DeviceRef(
                role="camera",
                device_id="/dev/video0",
                path="/dev/video0",
                subsystem="v4l2",
            )
        ],
        evidence=[
            GroupingEvidence(
                source="usb-topology",
                description="devices share USB parent path 1-4.1",
                strength=0.9,
            )
        ],
    )


def _usb_family_group() -> CompositeDevice:
    return CompositeDevice(
        id="usb-family-1-4",
        name="Reachy Mini",
        kind="unknown",
        confidence=0.8,
        members=[
            DeviceRef(
                role="camera",
                device_id="/dev/video0",
                path="/dev/video0",
                subsystem="v4l2",
            ),
            DeviceRef(
                role="audio-input",
                device_id="hw:0,0",
                path="hw:0,0",
                subsystem="alsa",
            ),
            DeviceRef(
                role="audio-output",
                device_id="hw:0,0",
                path="hw:0,0",
                subsystem="alsa",
            ),
        ],
        evidence=[
            GroupingEvidence(
                source="usb-topology",
                description="composite groups share USB ancestor 1-4",
                strength=0.8,
            )
        ],
    )


def _other_video_group() -> CompositeDevice:
    return CompositeDevice(
        id="usb-device-2-1",
        name="Other Camera",
        kind="unknown",
        confidence=0.9,
        members=[
            DeviceRef(
                role="camera",
                device_id="/dev/video9",
                path="/dev/video9",
                subsystem="v4l2",
            )
        ],
    )


def _environment_with_audio_input_elements() -> list[EnvironmentFact]:
    return [
        _element_fact("alsasrc", True),
        _element_fact("audioconvert", True),
        _element_fact("audioresample", True),
        _element_fact("level", True),
        _element_fact("fakesink", True),
    ]


def _environment_with_audio_output_elements() -> list[EnvironmentFact]:
    return [
        _element_fact("audiotestsrc", True),
        _element_fact("audioconvert", True),
        _element_fact("audioresample", True),
        _element_fact("alsasink", True),
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
