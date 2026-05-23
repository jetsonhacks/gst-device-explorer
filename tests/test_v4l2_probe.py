from pathlib import Path
import subprocess
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.probes import discover_v4l2_video_devices
from gst_device_explorer.probes.v4l2 import discover_v4l2_capabilities


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
