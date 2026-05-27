"""Tests for camera_pipeline_argv_for_selection — the function the Qt explorer actually calls."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.gui.model import DetailPaneModel, DetailSection
from gst_device_explorer.gui.qt_camera_modes import (
    camera_pipeline_argv_for_selection,
    camera_pipeline_for_selection,
)


def _detail(device_path: str) -> DetailPaneModel:
    return DetailPaneModel(
        selected_id=device_path,
        title="Camera",
        kind="video_input",
        status="ok",
        summary=(f"Endpoint: {device_path}",),
    )


def test_pipeline_argv_yuyv_uses_raw_caps_and_videoconvert() -> None:
    argv = camera_pipeline_argv_for_selection(_detail("/dev/video0"), "YUYV", "1280x720", "30 fps")

    assert argv is not None
    joined = " ".join(argv)
    assert "video/x-raw" in joined
    assert "format=YUY2" in joined
    assert "videoconvert" in joined
    assert "autovideosink sync=false" in joined


def test_pipeline_argv_h264_uses_x_h264_caps_and_hardware_decoder() -> None:
    argv = camera_pipeline_argv_for_selection(_detail("/dev/video2"), "H264", "1920x1080", "30 fps")

    assert argv is not None
    joined = " ".join(argv)
    assert "video/x-h264" in joined
    assert "format=" not in joined
    assert "h264parse" in joined
    assert "nvv4l2decoder" in joined
    assert "nvvidconv" in joined
    assert "autovideosink sync=false" in joined


def test_pipeline_argv_hevc_uses_x_h265_caps_and_hardware_decoder() -> None:
    argv = camera_pipeline_argv_for_selection(_detail("/dev/video2"), "HEVC", "1920x1080", "30 fps")

    assert argv is not None
    joined = " ".join(argv)
    assert "video/x-h265" in joined
    assert "format=" not in joined
    assert "h265parse" in joined
    assert "nvv4l2decoder" in joined
    assert "nvvidconv" in joined
    assert "autovideosink sync=false" in joined


def test_pipeline_argv_h264_argv_structure_is_valid_gst_launch() -> None:
    argv = camera_pipeline_argv_for_selection(_detail("/dev/video2"), "H264", "1920x1080", "30 fps")

    assert argv is not None
    assert argv[0] == "gst-launch-1.0"
    assert argv[1] == "v4l2src"
    assert "device=/dev/video2" in argv
    assert argv.count("!") >= 4


def test_pipeline_for_selection_h264_display_text_matches_argv() -> None:
    detail = _detail("/dev/video2")
    text = camera_pipeline_for_selection(detail, "H264", "1920x1080", "30 fps")
    argv = camera_pipeline_argv_for_selection(detail, "H264", "1920x1080", "30 fps")

    assert text is not None
    assert argv is not None
    assert "video/x-h264,width=1920,height=1080,framerate=30/1" in text
    assert "h264parse ! nvv4l2decoder ! nvvidconv ! autovideosink sync=false" in text
