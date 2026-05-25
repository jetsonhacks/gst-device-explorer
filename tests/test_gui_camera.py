from pathlib import Path
import subprocess
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.core.models import (
    CameraControl,
    CameraControlChoice,
    CameraControlSet,
    Capability,
    Device,
)
from gst_device_explorer.gui.camera import (
    build_camera_explorer_state,
    build_camera_pipeline_text,
    camera_copy_actions,
    camera_explorer_sections,
)


def test_camera_explorer_state_shapes_modes_from_capabilities() -> None:
    state = build_camera_explorer_state(_camera())

    assert [option.pixel_format for option in state.formats] == ["MJPG", "YUYV"]
    assert state.selected_format == "MJPG"
    assert state.selected_resolution == "640x480"
    assert state.selected_frame_rate == "30 fps"
    assert state.pipeline_text is not None
    assert "v4l2src device=/dev/video0" in state.pipeline_text
    assert "image/jpeg,width=640,height=480,framerate=30/1" in state.pipeline_text


def test_camera_pipeline_text_is_display_only_gstreamer_text() -> None:
    text = build_camera_pipeline_text(
        device_path="/dev/video0",
        pixel_format="YUYV",
        resolution="1280x720",
        frame_rate="29.97 fps",
    )

    assert text == (
        "gst-launch-1.0 v4l2src device=/dev/video0 ! "
        "video/x-raw,width=1280,height=720,format=YUYV,framerate=29970/1000 ! "
        "autovideosink"
    )


def test_camera_explorer_sections_include_dynamic_controls() -> None:
    state = build_camera_explorer_state(_camera(), control_set=_control_set())

    sections = {section.title: section for section in camera_explorer_sections(state)}

    assert "Camera Explorer" in sections
    assert sections["Camera Modes"].items == (
        "MJPG: 640x480, 1280x720",
        "YUYV: 640x480",
    )
    assert sections["Frame Rates"].items == (
        "MJPG 640x480: 30 fps, 15 fps",
        "MJPG 1280x720: 30 fps",
        "YUYV 640x480: 20 fps",
    )
    assert "gst-launch-1.0 v4l2src device=/dev/video0" in sections["Generated Pipeline"].items[0]
    assert any("brightness: type=int" in item for item in sections["V4L2 Controls"].items)
    assert any("exposure_auto: type=menu" in item for item in sections["V4L2 Controls"].items)
    assert any("choices=1=Manual Mode|3=Aperture Priority Mode" in item for item in sections["V4L2 Controls"].items)


def test_camera_copy_actions_are_metadata_only(monkeypatch) -> None:
    def fail_popen(*args: object, **kwargs: object) -> None:
        raise AssertionError("camera copy metadata must not spawn subprocesses")

    monkeypatch.setattr(subprocess, "Popen", fail_popen)

    state = build_camera_explorer_state(_camera())
    actions = camera_copy_actions(state)

    assert [action.kind for action in actions] == ["copy_command", "copy_pipeline"]
    assert actions[0].target == "/dev/video0"
    assert actions[1].target == state.pipeline_text


def test_camera_without_capabilities_has_unavailable_pipeline_and_no_controls() -> None:
    state = build_camera_explorer_state(
        Device(id="/dev/video9", kind="video_input", name="No Modes", metadata={"path": "/dev/video9"}),
    )
    sections = {section.title: section for section in camera_explorer_sections(state)}

    assert state.pipeline_text is None
    assert state.unavailable_reason == "No supported camera mode is available."
    assert sections["Camera Modes"].items == ("No supported camera modes discovered.",)
    assert sections["V4L2 Controls"].items == ("No V4L2 controls advertised.",)


def _camera() -> Device:
    return Device(
        id="/dev/video0",
        kind="video_input",
        name="USB Camera",
        capabilities=[
            _capability("MJPG", 640, 480, [30.0, 15.0], "Motion-JPEG"),
            _capability("MJPG", 1280, 720, [30.0], "Motion-JPEG"),
            _capability("YUYV", 640, 480, [20.0], "YUYV 4:2:2"),
        ],
        metadata={"path": "/dev/video0", "backend": "v4l2"},
    )


def _capability(pixel_format: str, width: int, height: int, fps: list[float], description: str) -> Capability:
    return Capability(
        name="video_format",
        values={
            "media_type": "video",
            "pixel_format": pixel_format,
            "description": description,
            "width": width,
            "height": height,
            "fps": fps,
        },
        source="v4l2-ctl",
    )


def _control_set() -> CameraControlSet:
    return CameraControlSet(
        device_path="/dev/video0",
        source="v4l2-ctl",
        controls=(
            CameraControl(
                name="brightness",
                label="Brightness",
                control_type="int",
                device_path="/dev/video0",
                current_value="140",
                default_value="128",
                minimum="0",
                maximum="255",
                step="1",
            ),
            CameraControl(
                name="exposure_auto",
                label="Exposure Auto",
                control_type="menu",
                device_path="/dev/video0",
                current_value="1",
                choices=(
                    CameraControlChoice(value="1", label="Manual Mode"),
                    CameraControlChoice(value="3", label="Aperture Priority Mode"),
                ),
            ),
        ),
    )


def test_pipeline_text_updates_when_format_changes() -> None:
    """Pipeline text must reflect the selected pixel format and media type."""
    mjpg_pipeline = build_camera_pipeline_text(
        device_path="/dev/video0",
        pixel_format="MJPG",
        resolution="1920x1080",
        frame_rate="60 fps",
        media_type="image/jpeg",
    )
    yuyv_pipeline = build_camera_pipeline_text(
        device_path="/dev/video0",
        pixel_format="YUYV",
        resolution="640x480",
        frame_rate="20 fps",
    )

    assert mjpg_pipeline is not None
    assert "image/jpeg" in mjpg_pipeline
    assert "width=1920" in mjpg_pipeline
    assert "height=1080" in mjpg_pipeline
    assert "framerate=60/1" in mjpg_pipeline
    assert "format=" not in mjpg_pipeline

    assert yuyv_pipeline is not None
    assert "video/x-raw" in yuyv_pipeline
    assert "format=YUYV" in yuyv_pipeline
    assert "width=640" in yuyv_pipeline
    assert "framerate=20/1" in yuyv_pipeline


def test_pipeline_text_fractional_frame_rate() -> None:
    text = build_camera_pipeline_text(
        device_path="/dev/video0",
        pixel_format="YUYV",
        resolution="1280x720",
        frame_rate="29.97 fps",
    )

    assert text is not None
    assert "framerate=29970/1000" in text


def test_no_controls_section_shows_unavailable_message() -> None:
    state = build_camera_explorer_state(
        Device(id="/dev/video9", kind="video_input", name="No Controls", metadata={"path": "/dev/video9"}),
        control_set=CameraControlSet(device_path="/dev/video9", source="v4l2-ctl", controls=()),
    )
    sections = {section.title: section for section in camera_explorer_sections(state)}

    assert sections["V4L2 Controls"].items == ("No V4L2 controls advertised.",)


def test_camera_explorer_state_with_real_camera_format() -> None:
    """Camera with high-resolution MJPG modes like the Reachy Mini Camera."""
    device = Device(
        id="/dev/video0",
        kind="video_input",
        name="Reachy Mini Camera",
        capabilities=[
            _capability("MJPG", 3840, 2592, [30.0], "Motion-JPEG, compressed"),
            _capability("MJPG", 1920, 1080, [60.0], "Motion-JPEG, compressed"),
            _capability("YUYV", 1920, 1080, [5.0], "YUYV 4:2:2"),
        ],
        metadata={"path": "/dev/video0", "backend": "v4l2"},
    )
    state = build_camera_explorer_state(device)

    assert [f.pixel_format for f in state.formats] == ["MJPG", "YUYV"]
    assert state.selected_format == "MJPG"
    assert state.selected_resolution == "1920x1080"
    assert state.pipeline_text is not None
    assert "image/jpeg" in state.pipeline_text
    assert "width=1920" in state.pipeline_text


def test_pipeline_text_without_frame_rate_is_valid() -> None:
    text = build_camera_pipeline_text(
        device_path="/dev/video0",
        pixel_format="MJPG",
        resolution="640x480",
        frame_rate=None,
        media_type="image/jpeg",
    )

    assert text is not None
    assert "framerate=" not in text
    assert "image/jpeg" in text
