from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.probes import discover_v4l2_video_devices


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
