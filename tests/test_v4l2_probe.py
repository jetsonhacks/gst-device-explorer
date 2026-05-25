from pathlib import Path
import subprocess
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.probes import discover_v4l2_video_devices
from gst_device_explorer.probes.v4l2 import (
    discover_v4l2_capabilities,
    discover_v4l2_controls,
)


def test_no_devices_found(tmp_path) -> None:
    devices = discover_v4l2_video_devices(tmp_path)

    assert devices == []


def test_one_video_device_found(tmp_path) -> None:
    video0 = tmp_path / "video0"
    video0.touch()

    devices = discover_v4l2_video_devices(tmp_path)

    assert len(devices) == 1
    assert devices[0].id == str(video0)
    assert devices[0].kind == "video_input"
    assert devices[0].name == "video0"
    assert devices[0].metadata["backend"] == "v4l2"
    assert devices[0].metadata["path"] == str(video0)
    assert devices[0].metadata["node_name"] == "video0"
    assert devices[0].metadata["exists"] is True
    assert devices[0].metadata["is_char_device"] is False


def test_multiple_video_devices_found_in_stable_order(tmp_path) -> None:
    (tmp_path / "video1").touch()
    (tmp_path / "video0").touch()

    devices = discover_v4l2_video_devices(tmp_path)

    assert [device.name for device in devices] == ["video0", "video1"]


def test_non_video_files_ignored(tmp_path) -> None:
    (tmp_path / "video0").touch()
    (tmp_path / "audio0").touch()
    (tmp_path / "not-video").touch()

    devices = discover_v4l2_video_devices(tmp_path)

    assert [device.name for device in devices] == ["video0"]


def test_missing_device_directory_handled_cleanly(tmp_path) -> None:
    missing_dir = tmp_path / "missing-dev"

    devices = discover_v4l2_video_devices(missing_dir)

    assert devices == []


def test_mjpg_capability_parsing(monkeypatch) -> None:
    output = """
ioctl: VIDIOC_ENUM_FMT
    Type: Video Capture

    [0]: 'MJPG' (Motion-JPEG, compressed)
        Size: Discrete 640x480
            Interval: Discrete 0.033s (30.000 fps)
"""
    _mock_v4l2_ctl(monkeypatch, output=output)

    capabilities = discover_v4l2_capabilities("/dev/video0")

    assert len(capabilities) == 1
    capability = capabilities[0]
    assert capability.name == "video_format"
    assert capability.source == "v4l2-ctl"
    assert capability.values["media_type"] == "video"
    assert capability.values["pixel_format"] == "MJPG"
    assert capability.values["raw_pixel_format"] == "MJPG"
    assert capability.values["description"] == "Motion-JPEG, compressed"
    assert capability.values["width"] == 640
    assert capability.values["height"] == 480
    assert capability.values["size"] == {"width": 640, "height": 480}
    assert capability.values["fps"] == [30.0]
    assert capability.values["device_path"] == "/dev/video0"


def test_yuyv_capability_parsing(monkeypatch) -> None:
    output = """
    [0]: 'YUYV' (YUYV 4:2:2)
        Size: Discrete 1280x720
            Interval: Discrete 0.050s (20.000 fps)
"""
    _mock_v4l2_ctl(monkeypatch, output=output)

    capabilities = discover_v4l2_capabilities("/dev/video2")

    assert len(capabilities) == 1
    assert capabilities[0].values["pixel_format"] == "YUYV"
    assert capabilities[0].values["description"] == "YUYV 4:2:2"
    assert capabilities[0].values["width"] == 1280
    assert capabilities[0].values["height"] == 720
    assert capabilities[0].values["fps"] == [20.0]


def test_multiple_sizes_and_frame_rates(monkeypatch) -> None:
    output = """
    [0]: 'MJPG' (Motion-JPEG, compressed)
        Size: Discrete 640x480
            Interval: Discrete 0.033s (30.000 fps)
            Interval: Discrete 0.067s (15.000 fps)
        Size: Discrete 1280x720
            Interval: Discrete 0.033s (30.000 fps)
    [1]: 'YUYV' (YUYV 4:2:2)
        Size: Discrete 640x480
            Interval: Discrete 0.100s (10.000 fps)
"""
    _mock_v4l2_ctl(monkeypatch, output=output)

    capabilities = discover_v4l2_capabilities("/dev/video0")

    assert [
        (
            capability.values["pixel_format"],
            capability.values["width"],
            capability.values["height"],
            capability.values["fps"],
        )
        for capability in capabilities
    ] == [
        ("MJPG", 640, 480, [30.0, 15.0]),
        ("MJPG", 1280, 720, [30.0]),
        ("YUYV", 640, 480, [10.0]),
    ]


def test_missing_v4l2_ctl_returns_empty_list(monkeypatch) -> None:
    monkeypatch.setattr("shutil.which", lambda command: None)

    capabilities = discover_v4l2_capabilities("/dev/video0")

    assert capabilities == []


def test_v4l2_ctl_command_failure_returns_empty_list(monkeypatch) -> None:
    _mock_v4l2_ctl(monkeypatch, output="", returncode=1)

    capabilities = discover_v4l2_capabilities("/dev/video0")

    assert capabilities == []


def test_empty_or_unrecognized_v4l2_output_returns_empty_list(monkeypatch) -> None:
    _mock_v4l2_ctl(monkeypatch, output="this is not v4l2 format output")

    capabilities = discover_v4l2_capabilities("/dev/video0")

    assert capabilities == []


def test_v4l2_integer_control_parsing(monkeypatch) -> None:
    output = """
User Controls

    brightness 0x00980900 (int)    : min=0 max=255 step=1 default=128 value=140
"""
    commands: list[list[str]] = []
    _mock_v4l2_controls(monkeypatch, output=output, commands=commands)

    controls = discover_v4l2_controls("/dev/video0")

    assert controls.device_path == "/dev/video0"
    assert controls.source == "v4l2-ctl"
    assert len(controls.controls) == 1
    control = controls.controls[0]
    assert control.name == "brightness"
    assert control.label == "Brightness"
    assert control.control_type == "int"
    assert control.control_id == "0x00980900"
    assert control.minimum == "0"
    assert control.maximum == "255"
    assert control.step == "1"
    assert control.default_value == "128"
    assert control.current_value == "140"
    assert "--list-ctrls-menus" in commands[0]
    assert "--set-ctrl" not in commands[0]


def test_v4l2_boolean_and_inactive_control_parsing(monkeypatch) -> None:
    output = """
User Controls

    led1_mode 0x0a046d05 (bool)   : default=0 value=1 flags=inactive
"""
    _mock_v4l2_controls(monkeypatch, output=output)

    controls = discover_v4l2_controls("/dev/video0")

    control = controls.controls[0]
    assert control.name == "led1_mode"
    assert control.control_type == "bool"
    assert control.default_value == "0"
    assert control.current_value == "1"
    assert control.flags == ("inactive",)


def test_v4l2_menu_control_parsing(monkeypatch) -> None:
    output = """
Camera Controls

    exposure_auto 0x009a0901 (menu) : min=0 max=3 default=3 value=1
        1: Manual Mode
        3: Aperture Priority Mode
"""
    _mock_v4l2_controls(monkeypatch, output=output)

    controls = discover_v4l2_controls("/dev/video2")

    control = controls.controls[0]
    assert control.name == "exposure_auto"
    assert control.control_type == "menu"
    assert control.current_value == "1"
    assert [(choice.value, choice.label) for choice in control.choices] == [
        ("1", "Manual Mode"),
        ("3", "Aperture Priority Mode"),
    ]


def test_v4l2_controls_handle_empty_or_malformed_output(monkeypatch) -> None:
    _mock_v4l2_controls(monkeypatch, output="this is not control output")

    controls = discover_v4l2_controls("/dev/video0")

    assert controls.device_path == "/dev/video0"
    assert controls.controls == ()


def test_missing_v4l2_ctl_returns_empty_control_set(monkeypatch) -> None:
    monkeypatch.setattr("shutil.which", lambda command: None)

    controls = discover_v4l2_controls("/dev/video0")

    assert controls.device_path == "/dev/video0"
    assert controls.controls == ()


def test_v4l2_control_command_failure_returns_empty_control_set(monkeypatch) -> None:
    _mock_v4l2_controls(monkeypatch, output="", returncode=1)

    controls = discover_v4l2_controls("/dev/video0")

    assert controls.device_path == "/dev/video0"
    assert controls.controls == ()


def _mock_v4l2_ctl(monkeypatch, output: str, returncode: int = 0) -> None:
    monkeypatch.setattr("shutil.which", lambda command: f"/usr/bin/{command}")

    def fake_run(command, check, capture_output, text, timeout):
        assert command[0] == "v4l2-ctl"
        assert command[1] == "--device"
        assert command[3] == "--list-formats-ext"
        assert check is False
        assert capture_output is True
        assert text is True
        assert timeout == 5
        return subprocess.CompletedProcess(
            command,
            returncode,
            stdout=output,
            stderr="",
        )

    monkeypatch.setattr("subprocess.run", fake_run)


def _mock_v4l2_controls(
    monkeypatch,
    output: str,
    returncode: int = 0,
    commands: list[list[str]] | None = None,
) -> None:
    monkeypatch.setattr("shutil.which", lambda command: f"/usr/bin/{command}")

    def fake_run(command, check, capture_output, text, timeout):
        if commands is not None:
            commands.append(command)
        assert command[0] == "v4l2-ctl"
        assert command[1] == "--device"
        assert command[3] == "--list-ctrls-menus"
        assert check is False
        assert capture_output is True
        assert text is True
        assert timeout == 5
        return subprocess.CompletedProcess(
            command,
            returncode,
            stdout=output,
            stderr="",
        )

    monkeypatch.setattr("subprocess.run", fake_run)


def test_menu_control_with_current_value_annotation(monkeypatch) -> None:
    """Real v4l2-ctl annotates current menu value as 'value=2 (60 Hz)'. Parser must ignore the annotation."""
    output = """
User Controls

           power_line_frequency 0x00980918 (menu)   : min=0 max=2 default=1 value=2 (60 Hz)
				0: Disabled
				1: 50 Hz
				2: 60 Hz
"""
    _mock_v4l2_controls(monkeypatch, output=output)

    controls = discover_v4l2_controls("/dev/video0")

    assert len(controls.controls) == 1
    control = controls.controls[0]
    assert control.name == "power_line_frequency"
    assert control.control_type == "menu"
    assert control.current_value == "2"
    assert control.default_value == "1"
    assert [(c.value, c.label) for c in control.choices] == [
        ("0", "Disabled"),
        ("1", "50 Hz"),
        ("2", "60 Hz"),
    ]


def test_inactive_int_control_flags_from_real_format(monkeypatch) -> None:
    """white_balance_temperature appears inactive when auto WB is on."""
    output = """
User Controls

      white_balance_temperature 0x0098091a (int)    : min=2800 max=6500 step=1 default=4600 value=4600 flags=inactive
"""
    _mock_v4l2_controls(monkeypatch, output=output)

    controls = discover_v4l2_controls("/dev/video0")

    control = controls.controls[0]
    assert control.name == "white_balance_temperature"
    assert control.control_type == "int"
    assert control.current_value == "4600"
    assert "inactive" in control.flags


def test_real_camera_style_full_control_block(monkeypatch) -> None:
    """Smoke test matching the Reachy Mini Camera v4l2-ctl output format."""
    output = """
User Controls

                     brightness 0x00980900 (int)    : min=-64 max=64 step=1 default=0 value=4
        white_balance_automatic 0x0098090c (bool)   : default=1 value=1
           power_line_frequency 0x00980918 (menu)   : min=0 max=2 default=1 value=2 (60 Hz)
				0: Disabled
				1: 50 Hz
				2: 60 Hz
      white_balance_temperature 0x0098091a (int)    : min=2800 max=6500 step=1 default=4600 value=4600 flags=inactive

Camera Controls

                  auto_exposure 0x009a0901 (menu)   : min=0 max=3 default=3 value=3 (Aperture Priority Mode)
				1: Manual Mode
				3: Aperture Priority Mode
         exposure_time_absolute 0x009a0902 (int)    : min=3 max=2047 step=1 default=166 value=127 flags=inactive
     exposure_dynamic_framerate 0x009a0903 (bool)   : default=0 value=0
"""
    _mock_v4l2_controls(monkeypatch, output=output)

    controls = discover_v4l2_controls("/dev/video0")

    names = [c.name for c in controls.controls]
    assert "brightness" in names
    assert "white_balance_automatic" in names
    assert "power_line_frequency" in names
    assert "white_balance_temperature" in names
    assert "auto_exposure" in names
    assert "exposure_time_absolute" in names
    assert "exposure_dynamic_framerate" in names

    wb_temp = next(c for c in controls.controls if c.name == "white_balance_temperature")
    assert "inactive" in wb_temp.flags

    exposure_abs = next(c for c in controls.controls if c.name == "exposure_time_absolute")
    assert "inactive" in exposure_abs.flags

    plf = next(c for c in controls.controls if c.name == "power_line_frequency")
    assert plf.current_value == "2"
    assert len(plf.choices) == 3
