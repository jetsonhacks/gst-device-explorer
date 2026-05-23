from pathlib import Path
import json
import sys

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.cli.main import main
from gst_device_explorer.core.models import (
    Capability,
    Device,
    EnvironmentFact,
    PipelineCandidate,
)
import gst_device_explorer.cli.main as cli_main


def test_devices_text_output(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_main.discovery,
        "discover_devices",
        lambda: [
            Device(
                id="/dev/video0",
                kind="video_input",
                name="video0",
                metadata={"backend": "v4l2"},
            ),
            Device(
                id="hw:2,0",
                kind="audio_input",
                name="USB Camera: USB Audio",
                metadata={"backend": "alsa"},
            ),
        ],
    )

    exit_code = main(["devices"])

    assert exit_code == 0
    assert capsys.readouterr().out == (
        "Devices:\n"
        "- video_input: video0 (/dev/video0)\n"
        "  backend: v4l2\n"
        "- audio_input: USB Camera: USB Audio (hw:2,0)\n"
        "  backend: alsa\n"
    )


def test_devices_json_output(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_main.discovery,
        "discover_devices",
        lambda: [
            Device(
                id="hw:0,3",
                kind="audio_output",
                name="HDA Intel PCH: HDMI 0",
                metadata={"backend": "alsa"},
            )
        ],
    )

    exit_code = main(["devices", "--json"])

    assert exit_code == 0
    data = json.loads(capsys.readouterr().out)
    assert data == [
        {
            "capabilities": [],
            "id": "hw:0,3",
            "kind": "audio_output",
            "metadata": {"backend": "alsa"},
            "name": "HDA Intel PCH: HDMI 0",
        }
    ]


def test_env_text_output(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_main.gst_probe,
        "inspect_gstreamer_environment",
        lambda: [
            EnvironmentFact(
                name="gstreamer_version",
                value="1.22.8",
                source="gst-launch-1.0",
                metadata={"available": True},
            ),
            EnvironmentFact(
                name="gstreamer_element_available",
                value=True,
                source="gst-inspect-1.0",
                metadata={"element": "v4l2src"},
            ),
        ],
    )

    exit_code = main(["env"])

    assert exit_code == 0
    assert capsys.readouterr().out == (
        "Environment:\n"
        "- gstreamer_version: 1.22.8\n"
        "  source: gst-launch-1.0\n"
        "- gstreamer_element_available: True\n"
        "  source: gst-inspect-1.0\n"
    )


def test_env_json_output(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_main.gst_probe,
        "inspect_gstreamer_environment",
        lambda: [
            EnvironmentFact(
                name="gstreamer_tool_available",
                value=False,
                source="gst-launch-1.0",
                metadata={"tool": "gst-launch-1.0", "path": None},
            )
        ],
    )

    exit_code = main(["env", "--json"])

    assert exit_code == 0
    data = json.loads(capsys.readouterr().out)
    assert data == [
        {
            "metadata": {"path": None, "tool": "gst-launch-1.0"},
            "name": "gstreamer_tool_available",
            "source": "gst-launch-1.0",
            "value": False,
        }
    ]


def test_audio_inputs_text_output(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_main.alsa_probe,
        "discover_alsa_audio_inputs",
        lambda: [
            Device(
                id="hw:2,0",
                kind="audio_input",
                name="USB Camera: USB Audio",
                metadata={"backend": "alsa"},
            )
        ],
    )

    exit_code = main(["audio-inputs"])

    assert exit_code == 0
    assert capsys.readouterr().out == (
        "Audio input devices:\n"
        "- audio_input: USB Camera: USB Audio (hw:2,0)\n"
        "  backend: alsa\n"
    )


def test_audio_inputs_json_output(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_main.alsa_probe,
        "discover_alsa_audio_inputs",
        lambda: [
            Device(
                id="hw:2,0",
                kind="audio_input",
                name="USB Camera: USB Audio",
                metadata={"backend": "alsa", "alsa_device": "hw:2,0"},
            )
        ],
    )

    exit_code = main(["audio-inputs", "--json"])

    assert exit_code == 0
    data = json.loads(capsys.readouterr().out)
    assert data == [
        {
            "capabilities": [],
            "id": "hw:2,0",
            "kind": "audio_input",
            "metadata": {"alsa_device": "hw:2,0", "backend": "alsa"},
            "name": "USB Camera: USB Audio",
        }
    ]


def test_audio_outputs_text_output(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_main.alsa_probe,
        "discover_alsa_audio_outputs",
        lambda: [
            Device(
                id="hw:0,3",
                kind="audio_output",
                name="HDA Intel PCH: HDMI 0",
                metadata={"backend": "alsa"},
            )
        ],
    )

    exit_code = main(["audio-outputs"])

    assert exit_code == 0
    assert capsys.readouterr().out == (
        "Audio output devices:\n"
        "- audio_output: HDA Intel PCH: HDMI 0 (hw:0,3)\n"
        "  backend: alsa\n"
    )


def test_audio_outputs_json_output(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_main.alsa_probe,
        "discover_alsa_audio_outputs",
        lambda: [
            Device(
                id="hw:0,3",
                kind="audio_output",
                name="HDA Intel PCH: HDMI 0",
                metadata={"backend": "alsa", "alsa_device": "hw:0,3"},
            )
        ],
    )

    exit_code = main(["audio-outputs", "--json"])

    assert exit_code == 0
    data = json.loads(capsys.readouterr().out)
    assert data == [
        {
            "capabilities": [],
            "id": "hw:0,3",
            "kind": "audio_output",
            "metadata": {"alsa_device": "hw:0,3", "backend": "alsa"},
            "name": "HDA Intel PCH: HDMI 0",
        }
    ]


def test_audio_inputs_no_device_behavior(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_main.alsa_probe,
        "discover_alsa_audio_inputs",
        lambda: [],
    )

    text_exit_code = main(["audio-inputs"])
    text_output = capsys.readouterr().out

    json_exit_code = main(["audio-inputs", "--json"])
    json_output = capsys.readouterr().out

    assert text_exit_code == 0
    assert text_output == "No ALSA audio input devices found.\n"
    assert json_exit_code == 0
    assert json.loads(json_output) == []


def test_audio_outputs_no_device_behavior(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_main.alsa_probe,
        "discover_alsa_audio_outputs",
        lambda: [],
    )

    text_exit_code = main(["audio-outputs"])
    text_output = capsys.readouterr().out

    json_exit_code = main(["audio-outputs", "--json"])
    json_output = capsys.readouterr().out

    assert text_exit_code == 0
    assert text_output == "No ALSA audio output devices found.\n"
    assert json_exit_code == 0
    assert json.loads(json_output) == []


def test_video_text_output_with_capabilities(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_main.v4l2_probe,
        "discover_v4l2_capabilities",
        lambda device_path: [
            Capability(
                name="video_format",
                values={
                    "media_type": "video",
                    "pixel_format": "MJPG",
                    "description": "Motion-JPEG, compressed",
                    "width": 640,
                    "height": 480,
                    "fps": [30.0, 15.0],
                },
                source="v4l2-ctl",
            )
        ],
    )

    exit_code = main(["video", "/dev/video0"])

    assert exit_code == 0
    assert capsys.readouterr().out == (
        "Video capabilities for /dev/video0:\n"
        "- MJPG (Motion-JPEG, compressed): 640x480\n"
        "  fps: 30.0, 15.0\n"
        "  source: v4l2-ctl\n"
    )


def test_video_json_output_with_capabilities(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_main.v4l2_probe,
        "discover_v4l2_capabilities",
        lambda device_path: [
            Capability(
                name="video_format",
                values={
                    "media_type": "video",
                    "pixel_format": "YUYV",
                    "description": "YUYV 4:2:2",
                    "width": 1280,
                    "height": 720,
                    "fps": [20.0],
                },
                source="v4l2-ctl",
            )
        ],
    )

    exit_code = main(["video", "/dev/video2", "--json"])

    assert exit_code == 0
    data = json.loads(capsys.readouterr().out)
    assert data == [
        {
            "name": "video_format",
            "source": "v4l2-ctl",
            "values": {
                "description": "YUYV 4:2:2",
                "fps": [20.0],
                "height": 720,
                "media_type": "video",
                "pixel_format": "YUYV",
                "width": 1280,
            },
        }
    ]


def test_video_text_output_with_no_capabilities(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_main.v4l2_probe,
        "discover_v4l2_capabilities",
        lambda device_path: [],
    )

    exit_code = main(["video", "/dev/video0"])

    assert exit_code == 0
    assert capsys.readouterr().out == (
        "No video capabilities found for /dev/video0.\n"
    )


def test_video_json_output_with_no_capabilities(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_main.v4l2_probe,
        "discover_v4l2_capabilities",
        lambda device_path: [],
    )

    exit_code = main(["video", "/dev/video0", "--json"])

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out) == []


def test_pipeline_video_text_output_with_one_candidate(monkeypatch, capsys) -> None:
    capability = Capability(
        name="video_format",
        values={"media_type": "video", "pixel_format": "MJPG"},
        source="v4l2-ctl",
    )
    environment = [
        EnvironmentFact(
            name="gstreamer_element_available",
            value=True,
            source="gst-inspect-1.0",
            metadata={"element": "v4l2src"},
        )
    ]
    candidate = PipelineCandidate(
        purpose="preview V4L2 video input",
        command=(
            "gst-launch-1.0 v4l2src device=/dev/video0 ! "
            "image/jpeg, width=640, height=480, framerate=30/1 ! "
            "videoconvert ! autovideosink sync=false"
        ),
        confidence=0.8,
        reasons=[
            "selected device path: /dev/video0",
            "selected pixel format: MJPG",
        ],
        warnings=[],
        required_elements=["v4l2src", "videoconvert", "autovideosink"],
        selected_profile="generic-linux-video-preview",
    )

    monkeypatch.setattr(
        cli_main.v4l2_probe,
        "discover_v4l2_capabilities",
        lambda device_path: [capability],
    )
    monkeypatch.setattr(
        cli_main.gst_probe,
        "inspect_gstreamer_environment",
        lambda: environment,
    )

    def fake_build(device, capabilities, facts):
        assert device.id == "/dev/video0"
        assert device.kind == "video_input"
        assert device.metadata["path"] == "/dev/video0"
        assert capabilities == [capability]
        assert facts == environment
        return [candidate]

    monkeypatch.setattr(
        cli_main.pipelines,
        "build_video_preview_candidates",
        fake_build,
    )

    exit_code = main(["pipeline", "video", "/dev/video0"])

    assert exit_code == 0
    assert capsys.readouterr().out == (
        "Video preview pipeline candidates for /dev/video0:\n"
        "1. preview V4L2 video input\n"
        "   command: gst-launch-1.0 v4l2src device=/dev/video0 ! "
        "image/jpeg, width=640, height=480, framerate=30/1 ! "
        "videoconvert ! autovideosink sync=false\n"
        "   confidence: 0.8\n"
        "   profile: generic-linux-video-preview\n"
        "   required elements: v4l2src, videoconvert, autovideosink\n"
        "   reasons:\n"
        "   - selected device path: /dev/video0\n"
        "   - selected pixel format: MJPG\n"
    )


def test_pipeline_video_json_output_with_one_candidate(monkeypatch, capsys) -> None:
    candidate = PipelineCandidate(
        purpose="preview V4L2 video input",
        command="gst-launch-1.0 v4l2src device=/dev/video0 ! autovideosink",
        confidence=0.8,
        reasons=["selected device path: /dev/video0"],
        warnings=[],
        required_elements=["v4l2src", "autovideosink"],
        selected_profile="generic-linux-video-preview",
    )

    monkeypatch.setattr(
        cli_main.v4l2_probe,
        "discover_v4l2_capabilities",
        lambda device_path: [],
    )
    monkeypatch.setattr(
        cli_main.gst_probe,
        "inspect_gstreamer_environment",
        lambda: [],
    )
    monkeypatch.setattr(
        cli_main.pipelines,
        "build_video_preview_candidates",
        lambda device, capabilities, facts: [candidate],
    )

    exit_code = main(["pipeline", "video", "/dev/video0", "--json"])

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out) == [
        {
            "command": (
                "gst-launch-1.0 v4l2src device=/dev/video0 ! autovideosink"
            ),
            "confidence": 0.8,
            "purpose": "preview V4L2 video input",
            "reasons": ["selected device path: /dev/video0"],
            "required_elements": ["v4l2src", "autovideosink"],
            "selected_profile": "generic-linux-video-preview",
            "warnings": [],
        }
    ]


def test_pipeline_video_text_output_with_no_candidates(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_main.v4l2_probe,
        "discover_v4l2_capabilities",
        lambda device_path: [],
    )
    monkeypatch.setattr(
        cli_main.gst_probe,
        "inspect_gstreamer_environment",
        lambda: [],
    )
    monkeypatch.setattr(
        cli_main.pipelines,
        "build_video_preview_candidates",
        lambda device, capabilities, facts: [],
    )

    exit_code = main(["pipeline", "video", "/dev/video0"])

    assert exit_code == 0
    assert capsys.readouterr().out == (
        "No video preview pipeline candidates found for /dev/video0.\n"
    )


def test_pipeline_video_json_output_with_no_candidates(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_main.v4l2_probe,
        "discover_v4l2_capabilities",
        lambda device_path: [],
    )
    monkeypatch.setattr(
        cli_main.gst_probe,
        "inspect_gstreamer_environment",
        lambda: [],
    )
    monkeypatch.setattr(
        cli_main.pipelines,
        "build_video_preview_candidates",
        lambda device, capabilities, facts: [],
    )

    exit_code = main(["pipeline", "video", "/dev/video0", "--json"])

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out) == []


def test_unknown_command_exits_with_error(capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["unknown"])

    assert exc_info.value.code == 2
    assert "invalid choice" in capsys.readouterr().err
