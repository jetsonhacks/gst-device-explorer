from pathlib import Path
import json
import subprocess
import sys

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.cli.main import main
from gst_device_explorer.core.grouping import GroupableDevice
from gst_device_explorer.core.models import (
    Capability,
    CompositeDevice,
    Device,
    DeviceRef,
    EnvironmentFact,
    GroupingEvidence,
    PipelineCandidate,
    PipelineDiagnostic,
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


def test_groups_text_output_with_no_groups(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_main.discovery,
        "discover_composite_devices",
        lambda: [],
    )

    exit_code = main(["groups"])

    assert exit_code == 0
    assert capsys.readouterr().out == "No composite device groups found.\n"


def test_groups_metadata_text_output_with_no_records(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_main.discovery,
        "discover_groupable_devices",
        lambda: [],
    )

    exit_code = main(["groups", "--metadata"])

    assert exit_code == 0
    assert capsys.readouterr().out == "No grouping metadata records found.\n"


def test_groups_metadata_text_output(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_main.discovery,
        "discover_groupable_devices",
        lambda: [_groupable_camera()],
    )

    exit_code = main(["groups", "--metadata"])

    assert exit_code == 0
    assert capsys.readouterr().out == (
        "Grouping metadata:\n"
        "- Reachy Mini Camera\n"
        "  role: camera\n"
        "  device id: /dev/video0\n"
        "  path: /dev/video0\n"
        "  subsystem: v4l2\n"
        "  metadata:\n"
        "    usb_parent_path: 1-2.3\n"
        "    usb_product: Reachy Mini\n"
        "    v4l2_name: Reachy Mini Camera\n"
    )


def test_groups_metadata_json_output(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_main.discovery,
        "discover_groupable_devices",
        lambda: [_groupable_camera()],
    )

    exit_code = main(["groups", "--metadata", "--json"])
    data = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert data == [
        {
            "device_ref": {
                "device_id": "/dev/video0",
                "path": "/dev/video0",
                "role": "camera",
                "subsystem": "v4l2",
            },
            "metadata": {
                "usb_parent_path": "1-2.3",
                "usb_product": "Reachy Mini",
                "v4l2_name": "Reachy Mini Camera",
            },
            "name": "Reachy Mini Camera",
        }
    ]


def test_groups_text_output_with_one_group(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_main.discovery,
        "discover_composite_devices",
        lambda: [_composite_group()],
    )

    exit_code = main(["groups"])

    assert exit_code == 0
    assert capsys.readouterr().out == (
        "Composite devices:\n"
        "- Reachy Mini Audio\n"
        "  id: audio-device-alsa-card-0\n"
        "  kind: audio-device\n"
        "  confidence: 0.90\n"
        "  members:\n"
        "    - audio-input: hw:0,0\n"
        "    - audio-output: hw:0,0\n"
        "  evidence:\n"
        "    - alsa-card: audio devices share ALSA card 0\n"
    )


def test_groups_json_output(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_main.discovery,
        "discover_composite_devices",
        lambda: [_composite_group()],
    )

    exit_code = main(["groups", "--json"])
    data = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert data == [_composite_group_json()]


def test_group_text_output_selects_one_group(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_main.discovery,
        "discover_composite_devices",
        lambda: [_other_composite_group(), _composite_group()],
    )

    exit_code = main(["group", "audio-device-alsa-card-0"])

    assert exit_code == 0
    assert capsys.readouterr().out == (
        "- Reachy Mini Audio\n"
        "  id: audio-device-alsa-card-0\n"
        "  kind: audio-device\n"
        "  confidence: 0.90\n"
        "  members:\n"
        "    - audio-input: hw:0,0\n"
        "    - audio-output: hw:0,0\n"
        "  evidence:\n"
        "    - alsa-card: audio devices share ALSA card 0\n"
    )


def test_group_json_output_selects_one_group(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_main.discovery,
        "discover_composite_devices",
        lambda: [_other_composite_group(), _composite_group()],
    )

    exit_code = main(["group", "audio-device-alsa-card-0", "--json"])
    data = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert data == _composite_group_json()


def test_group_unknown_id_returns_error(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_main.discovery,
        "discover_composite_devices",
        lambda: [_composite_group()],
    )

    exit_code = main(["group", "missing-group"])

    assert exit_code == 1
    assert capsys.readouterr().out == (
        "Composite device group not found: missing-group\n"
    )


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
        "  element: v4l2src\n"
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
        candidate_id="generic-v4l2-mjpeg-jpegdec-autovideosink",
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
        "   id: generic-v4l2-mjpeg-jpegdec-autovideosink\n"
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
        candidate_id="generic-v4l2-video-preview",
        purpose="preview V4L2 video input",
        command="gst-launch-1.0 v4l2src device=/dev/video0 ! autovideosink",
        confidence=0.8,
        argv=["gst-launch-1.0", "v4l2src", "device=/dev/video0"],
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
            "argv": ["gst-launch-1.0", "v4l2src", "device=/dev/video0"],
            "candidate_id": "generic-v4l2-video-preview",
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


def test_pipeline_video_diagnostics_text_output(monkeypatch, capsys) -> None:
    _mock_pipeline_video_diagnostics(
        monkeypatch,
        [_video_diagnostic(status="available")],
    )

    exit_code = main(["pipeline", "video", "/dev/video0", "--diagnostics"])

    assert exit_code == 0
    assert capsys.readouterr().out == (
        "Pipeline diagnostics for video /dev/video0\n"
        "\n"
        "Candidate: generic-v4l2-mjpeg-jpegdec-autovideosink\n"
        "Status: available\n"
        "Reason: Required GStreamer elements are available and the device "
        "exposes a compatible video format.\n"
        "\n"
        "Required elements:\n"
        "  ok: v4l2src\n"
        "  ok: videoconvert\n"
        "  ok: autovideosink\n"
        "\n"
        "Suggested next step:\n"
        "  gst-device-explorer run video /dev/video0 --dry-run\n"
    )


def test_pipeline_video_diagnostics_text_output_with_missing_element(
    monkeypatch,
    capsys,
) -> None:
    _mock_pipeline_video_diagnostics(
        monkeypatch,
        [_video_diagnostic(status="unavailable")],
    )

    exit_code = main(["pipeline", "video", "/dev/video0", "--diagnostics"])

    assert exit_code == 0
    assert capsys.readouterr().out == (
        "Pipeline diagnostics for video /dev/video0\n"
        "\n"
        "Candidate: generic-v4l2-mjpeg-jpegdec-autovideosink\n"
        "Status: unavailable\n"
        "Reason: Required GStreamer elements are missing.\n"
        "\n"
        "Required elements:\n"
        "  ok: v4l2src\n"
        "  ok: videoconvert\n"
        "  missing: autovideosink\n"
        "\n"
        "Suggested checks:\n"
        "  gst-inspect-1.0 autovideosink\n"
    )


def test_pipeline_video_diagnostics_json_output(monkeypatch, capsys) -> None:
    _mock_pipeline_video_diagnostics(
        monkeypatch,
        [_video_diagnostic(status="available")],
    )

    exit_code = main(["pipeline", "video", "/dev/video0", "--diagnostics", "--json"])

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out) == {
        "device": "/dev/video0",
        "device_kind": "video",
        "diagnostics": [
            {
                "available_elements": [
                    "v4l2src",
                    "videoconvert",
                    "autovideosink",
                ],
                "candidate_id": "generic-v4l2-mjpeg-jpegdec-autovideosink",
                "missing_elements": [],
                "reason": (
                    "Required GStreamer elements are available and the device "
                    "exposes a compatible video format."
                ),
                "required_elements": [
                    "v4l2src",
                    "videoconvert",
                    "autovideosink",
                ],
                "status": "available",
                "suggested_next_checks": [],
            }
        ],
    }


def test_pipeline_audio_input_text_output_with_one_candidate(
    monkeypatch,
    capsys,
) -> None:
    device = _audio_device(kind="audio_input")
    environment = [_element_fact("alsasrc")]
    candidate = PipelineCandidate(
        candidate_id="generic-alsa-audio-input-level-fakesink",
        purpose="test ALSA audio input levels",
        command=(
            "gst-launch-1.0 alsasrc device=hw:0,0 ! audioconvert ! "
            "audioresample ! level interval=1000000000 ! fakesink"
        ),
        confidence=0.8,
        argv=["gst-launch-1.0", "alsasrc", "device=hw:0,0"],
        reasons=["selected ALSA input device: hw:0,0"],
        warnings=[],
        required_elements=[
            "alsasrc",
            "audioconvert",
            "audioresample",
            "level",
            "fakesink",
        ],
        selected_profile="generic-alsa-audio-input-test",
    )

    monkeypatch.setattr(
        cli_main.alsa_probe,
        "discover_alsa_audio_inputs",
        lambda: [device],
    )
    monkeypatch.setattr(
        cli_main.gst_probe,
        "inspect_gstreamer_environment",
        lambda: environment,
    )

    def fake_build(found_device, facts):
        assert found_device == device
        assert facts == environment
        return [candidate]

    monkeypatch.setattr(
        cli_main.audio_pipelines,
        "build_audio_input_test_candidates",
        fake_build,
    )

    exit_code = main(["pipeline", "audio-input", "hw:0,0"])

    assert exit_code == 0
    assert capsys.readouterr().out == (
        "Audio input pipeline candidates for hw:0,0:\n"
        "1. test ALSA audio input levels\n"
        "   id: generic-alsa-audio-input-level-fakesink\n"
        "   command: gst-launch-1.0 alsasrc device=hw:0,0 ! "
        "audioconvert ! audioresample ! level interval=1000000000 ! fakesink\n"
        "   confidence: 0.8\n"
        "   profile: generic-alsa-audio-input-test\n"
        "   required elements: alsasrc, audioconvert, audioresample, level, "
        "fakesink\n"
        "   reasons:\n"
        "   - selected ALSA input device: hw:0,0\n"
    )


def test_pipeline_audio_output_json_output_with_one_candidate(
    monkeypatch,
    capsys,
) -> None:
    candidate = PipelineCandidate(
        candidate_id="generic-alsa-audio-output-sine-alsasink",
        purpose="test ALSA audio output with sine wave",
        command=(
            "gst-launch-1.0 audiotestsrc wave=sine freq=440 ! "
            "audioconvert ! audioresample ! alsasink device=hw:0,0"
        ),
        confidence=0.8,
        argv=["gst-launch-1.0", "audiotestsrc", "wave=sine"],
        reasons=["selected ALSA output device: hw:0,0"],
        warnings=[],
        required_elements=[
            "audiotestsrc",
            "audioconvert",
            "audioresample",
            "alsasink",
        ],
        selected_profile="generic-alsa-audio-output-test",
    )

    monkeypatch.setattr(
        cli_main.alsa_probe,
        "discover_alsa_audio_outputs",
        lambda: [_audio_device(kind="audio_output")],
    )
    monkeypatch.setattr(
        cli_main.gst_probe,
        "inspect_gstreamer_environment",
        lambda: [],
    )
    monkeypatch.setattr(
        cli_main.audio_pipelines,
        "build_audio_output_test_candidates",
        lambda device, facts: [candidate],
    )

    exit_code = main(["pipeline", "audio-output", "hw:0,0", "--json"])

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out) == [
        {
            "argv": ["gst-launch-1.0", "audiotestsrc", "wave=sine"],
            "candidate_id": "generic-alsa-audio-output-sine-alsasink",
            "command": (
                "gst-launch-1.0 audiotestsrc wave=sine freq=440 ! "
                "audioconvert ! audioresample ! alsasink device=hw:0,0"
            ),
            "confidence": 0.8,
            "purpose": "test ALSA audio output with sine wave",
            "reasons": ["selected ALSA output device: hw:0,0"],
            "required_elements": [
                "audiotestsrc",
                "audioconvert",
                "audioresample",
                "alsasink",
            ],
            "selected_profile": "generic-alsa-audio-output-test",
            "warnings": [],
        }
    ]


def test_pipeline_audio_input_text_output_with_no_matching_device(
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(
        cli_main.alsa_probe,
        "discover_alsa_audio_inputs",
        lambda: [],
    )

    exit_code = main(["pipeline", "audio-input", "hw:0,0"])

    assert exit_code == 0
    assert capsys.readouterr().out == (
        "No audio input pipeline candidates found for hw:0,0.\n"
    )


def test_pipeline_audio_input_diagnostics_text_output(
    monkeypatch,
    capsys,
) -> None:
    device = _audio_device(kind="audio_input")
    environment = [_element_fact("alsasrc")]
    diagnostic = _audio_diagnostic("input", status="available")

    monkeypatch.setattr(
        cli_main.alsa_probe,
        "discover_alsa_audio_inputs",
        lambda: [device],
    )
    monkeypatch.setattr(
        cli_main.gst_probe,
        "inspect_gstreamer_environment",
        lambda: environment,
    )

    def fake_build(found_device, facts):
        assert found_device == device
        assert facts == environment
        return [diagnostic]

    monkeypatch.setattr(
        cli_main.audio_diagnostics,
        "build_audio_input_test_diagnostics",
        fake_build,
    )

    exit_code = main(["pipeline", "audio-input", "hw:0,0", "--diagnostics"])

    assert exit_code == 0
    assert capsys.readouterr().out == (
        "Pipeline diagnostics for audio-input hw:0,0\n"
        "\n"
        "Candidate: generic-alsa-audio-input-level-fakesink\n"
        "Status: available\n"
        "Reason: ALSA capture device and required GStreamer elements are "
        "available.\n"
        "\n"
        "Required elements:\n"
        "  ok: alsasrc\n"
        "  ok: audioconvert\n"
        "  ok: audioresample\n"
        "  ok: level\n"
        "  ok: fakesink\n"
        "\n"
        "Suggested next step:\n"
        "  gst-device-explorer run audio-input hw:0,0 --dry-run\n"
    )


def test_pipeline_audio_output_diagnostics_text_output_with_missing_element(
    monkeypatch,
    capsys,
) -> None:
    _mock_pipeline_audio_output_diagnostics(
        monkeypatch,
        [_audio_diagnostic("output", status="unavailable")],
    )

    exit_code = main(["pipeline", "audio-output", "hw:0,0", "--diagnostics"])

    assert exit_code == 0
    assert capsys.readouterr().out == (
        "Pipeline diagnostics for audio-output hw:0,0\n"
        "\n"
        "Candidate: generic-alsa-audio-output-sine-alsasink\n"
        "Status: unavailable\n"
        "Reason: Required GStreamer elements are missing.\n"
        "\n"
        "Required elements:\n"
        "  ok: audiotestsrc\n"
        "  ok: audioconvert\n"
        "  ok: audioresample\n"
        "  missing: alsasink\n"
        "\n"
        "Suggested checks:\n"
        "  gst-inspect-1.0 alsasink\n"
    )


def test_pipeline_audio_output_diagnostics_json_output(
    monkeypatch,
    capsys,
) -> None:
    _mock_pipeline_audio_output_diagnostics(
        monkeypatch,
        [_audio_diagnostic("output", status="available")],
    )

    exit_code = main(
        ["pipeline", "audio-output", "hw:0,0", "--diagnostics", "--json"]
    )

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out) == {
        "device": "hw:0,0",
        "device_kind": "audio-output",
        "diagnostics": [
            {
                "available_elements": [
                    "audiotestsrc",
                    "audioconvert",
                    "audioresample",
                    "alsasink",
                ],
                "candidate_id": "generic-alsa-audio-output-sine-alsasink",
                "missing_elements": [],
                "reason": (
                    "ALSA playback device and required GStreamer elements "
                    "are available."
                ),
                "required_elements": [
                    "audiotestsrc",
                    "audioconvert",
                    "audioresample",
                    "alsasink",
                ],
                "status": "available",
                "suggested_next_checks": [],
            }
        ],
    }


def test_pipeline_video_text_output_shows_top_three_by_default(
    monkeypatch,
    capsys,
) -> None:
    _mock_pipeline_video_candidates(
        monkeypatch,
        [_pipeline_candidate(index) for index in range(1, 5)],
    )

    exit_code = main(["pipeline", "video", "/dev/video0"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "candidate 1" in output
    assert "candidate 2" in output
    assert "candidate 3" in output
    assert "candidate 4" not in output


def test_pipeline_video_text_output_all_shows_every_candidate(
    monkeypatch,
    capsys,
) -> None:
    _mock_pipeline_video_candidates(
        monkeypatch,
        [_pipeline_candidate(index) for index in range(1, 5)],
    )

    exit_code = main(["pipeline", "video", "/dev/video0", "--all"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "candidate 1" in output
    assert "candidate 2" in output
    assert "candidate 3" in output
    assert "candidate 4" in output


def test_pipeline_video_text_output_limit_one_shows_one_candidate(
    monkeypatch,
    capsys,
) -> None:
    _mock_pipeline_video_candidates(
        monkeypatch,
        [_pipeline_candidate(index) for index in range(1, 4)],
    )

    exit_code = main(["pipeline", "video", "/dev/video0", "--limit", "1"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "candidate 1" in output
    assert "candidate 2" not in output
    assert "candidate 3" not in output


def test_pipeline_video_json_output_returns_all_candidates_by_default(
    monkeypatch,
    capsys,
) -> None:
    _mock_pipeline_video_candidates(
        monkeypatch,
        [_pipeline_candidate(index) for index in range(1, 4)],
    )

    exit_code = main(["pipeline", "video", "/dev/video0", "--json"])
    data = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert [item["purpose"] for item in data] == [
        "candidate 1",
        "candidate 2",
        "candidate 3",
    ]


def test_pipeline_video_json_output_limit_one_returns_one_candidate(
    monkeypatch,
    capsys,
) -> None:
    _mock_pipeline_video_candidates(
        monkeypatch,
        [_pipeline_candidate(index) for index in range(1, 4)],
    )

    exit_code = main(
        ["pipeline", "video", "/dev/video0", "--json", "--limit", "1"]
    )
    data = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert [item["purpose"] for item in data] == ["candidate 1"]


def test_run_video_dry_run_selects_top_candidate(monkeypatch, capsys) -> None:
    _mock_pipeline_video_candidates(
        monkeypatch,
        [_pipeline_candidate(1), _pipeline_candidate(2)],
    )

    exit_code = main(["run", "video", "/dev/video0", "--dry-run"])

    assert exit_code == 0
    assert capsys.readouterr().out == (
        "Selected pipeline candidate: test-candidate-1\n"
        "\n"
        "gst-launch-1.0 candidate-1\n"
        "\n"
        "Dry run only. Pipeline was not executed.\n"
    )


def test_run_video_dry_run_does_not_invoke_subprocess(
    monkeypatch,
    capsys,
) -> None:
    _mock_pipeline_video_candidates(monkeypatch, [_pipeline_candidate(1)])

    def fail_popen(*args, **kwargs):
        raise AssertionError("subprocess.Popen should not be called")

    monkeypatch.setattr(subprocess, "Popen", fail_popen)

    exit_code = main(["run", "video", "/dev/video0", "--dry-run"])

    assert exit_code == 0
    assert "Dry run only. Pipeline was not executed." in capsys.readouterr().out


def test_run_video_dry_run_selects_candidate_by_index(monkeypatch, capsys) -> None:
    _mock_pipeline_video_candidates(
        monkeypatch,
        [_pipeline_candidate(1), _pipeline_candidate(2)],
    )

    exit_code = main(
        ["run", "video", "/dev/video0", "--candidate", "1", "--dry-run"]
    )

    assert exit_code == 0
    assert "Selected pipeline candidate: test-candidate-2\n" in capsys.readouterr().out


def test_run_video_dry_run_accepts_zero_candidate_index(monkeypatch, capsys) -> None:
    _mock_pipeline_video_candidates(
        monkeypatch,
        [_pipeline_candidate(1), _pipeline_candidate(2)],
    )

    exit_code = main(
        ["run", "video", "/dev/video0", "--candidate", "0", "--dry-run"]
    )

    assert exit_code == 0
    assert "Selected pipeline candidate: test-candidate-1\n" in capsys.readouterr().out


def test_run_video_dry_run_selects_candidate_by_id(monkeypatch, capsys) -> None:
    _mock_pipeline_video_candidates(
        monkeypatch,
        [_pipeline_candidate(1), _pipeline_candidate(2)],
    )

    exit_code = main(
        [
            "run",
            "video",
            "/dev/video0",
            "--candidate",
            "test-candidate-2",
            "--dry-run",
        ]
    )

    assert exit_code == 0
    assert "Selected pipeline candidate: test-candidate-2\n" in capsys.readouterr().out


def test_run_video_invalid_candidate_index_returns_error(
    monkeypatch,
    capsys,
) -> None:
    _mock_pipeline_video_candidates(monkeypatch, [_pipeline_candidate(1)])

    exit_code = main(
        ["run", "video", "/dev/video0", "--candidate", "2", "--dry-run"]
    )

    assert exit_code == 1
    assert "candidate index 2 is out of range" in capsys.readouterr().out


def test_run_video_invalid_candidate_id_returns_error(monkeypatch, capsys) -> None:
    _mock_pipeline_video_candidates(monkeypatch, [_pipeline_candidate(1)])

    exit_code = main(
        [
            "run",
            "video",
            "/dev/video0",
            "--candidate",
            "missing-candidate",
            "--dry-run",
        ]
    )

    assert exit_code == 1
    assert "candidate ID 'missing-candidate' was not found" in capsys.readouterr().out


def test_run_video_no_candidates_returns_diagnostic(monkeypatch, capsys) -> None:
    _mock_pipeline_video_candidates(monkeypatch, [])

    exit_code = main(["run", "video", "/dev/video0", "--dry-run"])

    assert exit_code == 1
    assert capsys.readouterr().out == (
        "No pipeline candidates were generated for /dev/video0.\n"
        "\n"
        "Try:\n"
        "  gst-device-explorer video /dev/video0\n"
        "  gst-device-explorer env\n"
    )


def test_run_video_invokes_subprocess_with_selected_candidate_argv(
    monkeypatch,
    capsys,
) -> None:
    _mock_pipeline_video_candidates(
        monkeypatch,
        [_pipeline_candidate(1), _pipeline_candidate(2)],
    )
    calls = []

    class FakeProcess:
        def wait(self):
            return 0

    def fake_popen(*args, **kwargs):
        calls.append((args, kwargs))
        return FakeProcess()

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    exit_code = main(
        ["run", "video", "/dev/video0", "--candidate", "test-candidate-2"]
    )

    assert exit_code == 0
    assert calls == [((["gst-launch-1.0", "candidate-2"],), {})]
    assert capsys.readouterr().out == (
        "Selected pipeline candidate: test-candidate-2\n"
        "\n"
        "gst-launch-1.0 candidate-2\n"
        "\n"
        "Running pipeline. Press Ctrl+C to stop.\n"
    )


def test_run_video_propagates_child_return_code(monkeypatch, capsys) -> None:
    _mock_pipeline_video_candidates(monkeypatch, [_pipeline_candidate(1)])

    class FakeProcess:
        def wait(self):
            return 23

    monkeypatch.setattr(subprocess, "Popen", lambda argv: FakeProcess())

    exit_code = main(["run", "video", "/dev/video0"])

    assert exit_code == 23
    assert "Running pipeline. Press Ctrl+C to stop." in capsys.readouterr().out


def test_run_video_reports_subprocess_start_error(monkeypatch, capsys) -> None:
    _mock_pipeline_video_candidates(monkeypatch, [_pipeline_candidate(1)])

    def fake_popen(argv):
        raise FileNotFoundError("gst-launch-1.0")

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    exit_code = main(["run", "video", "/dev/video0"])

    assert exit_code == 1
    assert "Error: could not start pipeline: gst-launch-1.0" in capsys.readouterr().out


def test_run_audio_input_dry_run_selects_structured_candidate(
    monkeypatch,
    capsys,
) -> None:
    _mock_pipeline_audio_input_candidates(
        monkeypatch,
        [_audio_pipeline_candidate("input")],
    )

    exit_code = main(["run", "audio-input", "hw:0,0", "--dry-run"])

    assert exit_code == 0
    assert capsys.readouterr().out == (
        "Selected pipeline candidate: generic-alsa-audio-input-level-fakesink\n"
        "\n"
        "gst-launch-1.0 alsasrc device=hw:0,0 ! audioconvert ! "
        "audioresample ! level interval=1000000000 ! fakesink\n"
        "\n"
        "Dry run only. Pipeline was not executed.\n"
    )


def test_run_audio_output_dry_run_selects_structured_candidate(
    monkeypatch,
    capsys,
) -> None:
    _mock_pipeline_audio_output_candidates(
        monkeypatch,
        [_audio_pipeline_candidate("output")],
    )

    exit_code = main(["run", "audio-output", "hw:0,0", "--dry-run"])

    assert exit_code == 0
    assert capsys.readouterr().out == (
        "Selected pipeline candidate: generic-alsa-audio-output-sine-alsasink\n"
        "\n"
        "gst-launch-1.0 audiotestsrc wave=sine freq=440 ! audioconvert ! "
        "audioresample ! alsasink device=hw:0,0\n"
        "\n"
        "Dry run only. Pipeline was not executed.\n"
    )


def test_run_audio_output_dry_run_selects_candidate_by_id(
    monkeypatch,
    capsys,
) -> None:
    candidates = [
        _pipeline_candidate(1),
        _audio_pipeline_candidate("output"),
    ]
    _mock_pipeline_audio_output_candidates(monkeypatch, candidates)

    exit_code = main(
        [
            "run",
            "audio-output",
            "hw:0,0",
            "--candidate",
            "generic-alsa-audio-output-sine-alsasink",
            "--dry-run",
        ]
    )

    assert exit_code == 0
    assert (
        "Selected pipeline candidate: generic-alsa-audio-output-sine-alsasink\n"
        in capsys.readouterr().out
    )


def test_run_audio_input_invokes_subprocess_with_selected_candidate_argv(
    monkeypatch,
    capsys,
) -> None:
    _mock_pipeline_audio_input_candidates(
        monkeypatch,
        [_audio_pipeline_candidate("input")],
    )
    calls = []

    class FakeProcess:
        def wait(self):
            return 0

    def fake_popen(*args, **kwargs):
        calls.append((args, kwargs))
        return FakeProcess()

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    exit_code = main(["run", "audio-input", "hw:0,0"])

    assert exit_code == 0
    assert calls == [
        (
            (
                [
                    "gst-launch-1.0",
                    "alsasrc",
                    "device=hw:0,0",
                    "!",
                    "audioconvert",
                    "!",
                    "audioresample",
                    "!",
                    "level",
                    "interval=1000000000",
                    "!",
                    "fakesink",
                ],
            ),
            {},
        )
    ]
    assert "Running pipeline. Press Ctrl+C to stop." in capsys.readouterr().out


def test_run_audio_output_invokes_subprocess_without_shell(
    monkeypatch,
    capsys,
) -> None:
    _mock_pipeline_audio_output_candidates(
        monkeypatch,
        [_audio_pipeline_candidate("output")],
    )
    calls = []

    class FakeProcess:
        def wait(self):
            return 0

    def fake_popen(*args, **kwargs):
        calls.append((args, kwargs))
        return FakeProcess()

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    exit_code = main(["run", "audio-output", "hw:0,0"])

    assert exit_code == 0
    assert calls[0][0] == (
        [
            "gst-launch-1.0",
            "audiotestsrc",
            "wave=sine",
            "freq=440",
            "!",
            "audioconvert",
            "!",
            "audioresample",
            "!",
            "alsasink",
            "device=hw:0,0",
        ],
    )
    assert "shell" not in calls[0][1]
    assert "Running pipeline. Press Ctrl+C to stop." in capsys.readouterr().out


def test_run_audio_input_no_candidates_returns_diagnostic(
    monkeypatch,
    capsys,
) -> None:
    _mock_pipeline_audio_input_candidates(monkeypatch, [])

    exit_code = main(["run", "audio-input", "hw:0,0", "--dry-run"])

    assert exit_code == 1
    assert capsys.readouterr().out == (
        "No pipeline candidates were generated for hw:0,0.\n"
        "\n"
        "Try:\n"
        "  gst-device-explorer audio-inputs\n"
        "  gst-device-explorer pipeline audio-input hw:0,0\n"
        "  gst-device-explorer env\n"
    )


def test_run_audio_output_invalid_candidate_id_returns_error(
    monkeypatch,
    capsys,
) -> None:
    _mock_pipeline_audio_output_candidates(
        monkeypatch,
        [_audio_pipeline_candidate("output")],
    )

    exit_code = main(
        [
            "run",
            "audio-output",
            "hw:0,0",
            "--candidate",
            "missing-candidate",
            "--dry-run",
        ]
    )

    assert exit_code == 1
    assert "candidate ID 'missing-candidate' was not found" in capsys.readouterr().out


def test_unknown_command_exits_with_error(capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["unknown"])

    assert exc_info.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def _mock_pipeline_video_candidates(monkeypatch, candidates) -> None:
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
        lambda device, capabilities, facts: candidates,
    )


def _mock_pipeline_video_diagnostics(monkeypatch, diagnostics) -> None:
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
        cli_main.video_diagnostics,
        "build_video_preview_diagnostics",
        lambda device, capabilities, facts: diagnostics,
    )


def _mock_pipeline_audio_input_candidates(monkeypatch, candidates) -> None:
    monkeypatch.setattr(
        cli_main.alsa_probe,
        "discover_alsa_audio_inputs",
        lambda: [_audio_device(kind="audio_input")],
    )
    monkeypatch.setattr(
        cli_main.gst_probe,
        "inspect_gstreamer_environment",
        lambda: [],
    )
    monkeypatch.setattr(
        cli_main.audio_pipelines,
        "build_audio_input_test_candidates",
        lambda device, facts: candidates,
    )


def _mock_pipeline_audio_output_candidates(monkeypatch, candidates) -> None:
    monkeypatch.setattr(
        cli_main.alsa_probe,
        "discover_alsa_audio_outputs",
        lambda: [_audio_device(kind="audio_output")],
    )
    monkeypatch.setattr(
        cli_main.gst_probe,
        "inspect_gstreamer_environment",
        lambda: [],
    )
    monkeypatch.setattr(
        cli_main.audio_pipelines,
        "build_audio_output_test_candidates",
        lambda device, facts: candidates,
    )


def _mock_pipeline_audio_output_diagnostics(monkeypatch, diagnostics) -> None:
    monkeypatch.setattr(
        cli_main.alsa_probe,
        "discover_alsa_audio_outputs",
        lambda: [_audio_device(kind="audio_output")],
    )
    monkeypatch.setattr(
        cli_main.gst_probe,
        "inspect_gstreamer_environment",
        lambda: [],
    )
    monkeypatch.setattr(
        cli_main.audio_diagnostics,
        "build_audio_output_test_diagnostics",
        lambda device, facts: diagnostics,
    )


def _pipeline_candidate(index: int) -> PipelineCandidate:
    return PipelineCandidate(
        candidate_id=f"test-candidate-{index}",
        purpose=f"candidate {index}",
        command=f"gst-launch-1.0 candidate-{index}",
        confidence=1.0 - (index / 10),
        argv=["gst-launch-1.0", f"candidate-{index}"],
        reasons=[],
        warnings=[],
        required_elements=["v4l2src"],
        selected_profile="generic-linux-video-preview",
    )


def _video_diagnostic(status: str) -> PipelineDiagnostic:
    if status == "unavailable":
        return PipelineDiagnostic(
            candidate_id="generic-v4l2-mjpeg-jpegdec-autovideosink",
            device_kind="video",
            device="/dev/video0",
            status="unavailable",
            reason="Required GStreamer elements are missing.",
            required_elements=["v4l2src", "videoconvert", "autovideosink"],
            available_elements=["v4l2src", "videoconvert"],
            missing_elements=["autovideosink"],
            suggested_next_checks=["gst-inspect-1.0 autovideosink"],
        )

    return PipelineDiagnostic(
        candidate_id="generic-v4l2-mjpeg-jpegdec-autovideosink",
        device_kind="video",
        device="/dev/video0",
        status="available",
        reason=(
            "Required GStreamer elements are available and the device exposes "
            "a compatible video format."
        ),
        required_elements=["v4l2src", "videoconvert", "autovideosink"],
        available_elements=["v4l2src", "videoconvert", "autovideosink"],
        missing_elements=[],
        suggested_next_checks=[],
    )


def _audio_diagnostic(kind: str, status: str) -> PipelineDiagnostic:
    if kind == "input":
        return PipelineDiagnostic(
            candidate_id="generic-alsa-audio-input-level-fakesink",
            device_kind="audio-input",
            device="hw:0,0",
            status=status,
            reason=(
                "ALSA capture device and required GStreamer elements are available."
            ),
            required_elements=[
                "alsasrc",
                "audioconvert",
                "audioresample",
                "level",
                "fakesink",
            ],
            available_elements=[
                "alsasrc",
                "audioconvert",
                "audioresample",
                "level",
                "fakesink",
            ],
            missing_elements=[],
            suggested_next_checks=[],
        )

    if status == "unavailable":
        return PipelineDiagnostic(
            candidate_id="generic-alsa-audio-output-sine-alsasink",
            device_kind="audio-output",
            device="hw:0,0",
            status="unavailable",
            reason="Required GStreamer elements are missing.",
            required_elements=[
                "audiotestsrc",
                "audioconvert",
                "audioresample",
                "alsasink",
            ],
            available_elements=[
                "audiotestsrc",
                "audioconvert",
                "audioresample",
            ],
            missing_elements=["alsasink"],
            suggested_next_checks=["gst-inspect-1.0 alsasink"],
        )

    return PipelineDiagnostic(
        candidate_id="generic-alsa-audio-output-sine-alsasink",
        device_kind="audio-output",
        device="hw:0,0",
        status="available",
        reason="ALSA playback device and required GStreamer elements are available.",
        required_elements=[
            "audiotestsrc",
            "audioconvert",
            "audioresample",
            "alsasink",
        ],
        available_elements=[
            "audiotestsrc",
            "audioconvert",
            "audioresample",
            "alsasink",
        ],
        missing_elements=[],
        suggested_next_checks=[],
    )


def _audio_pipeline_candidate(kind: str) -> PipelineCandidate:
    if kind == "input":
        return PipelineCandidate(
            candidate_id="generic-alsa-audio-input-level-fakesink",
            purpose="test ALSA audio input levels",
            command=(
                "gst-launch-1.0 alsasrc device=hw:0,0 ! audioconvert ! "
                "audioresample ! level interval=1000000000 ! fakesink"
            ),
            confidence=0.8,
            argv=[
                "gst-launch-1.0",
                "alsasrc",
                "device=hw:0,0",
                "!",
                "audioconvert",
                "!",
                "audioresample",
                "!",
                "level",
                "interval=1000000000",
                "!",
                "fakesink",
            ],
            reasons=[],
            warnings=[],
            required_elements=[
                "alsasrc",
                "audioconvert",
                "audioresample",
                "level",
                "fakesink",
            ],
            selected_profile="generic-alsa-audio-input-test",
        )

    return PipelineCandidate(
        candidate_id="generic-alsa-audio-output-sine-alsasink",
        purpose="test ALSA audio output with sine wave",
        command=(
            "gst-launch-1.0 audiotestsrc wave=sine freq=440 ! "
            "audioconvert ! audioresample ! alsasink device=hw:0,0"
        ),
        confidence=0.8,
        argv=[
            "gst-launch-1.0",
            "audiotestsrc",
            "wave=sine",
            "freq=440",
            "!",
            "audioconvert",
            "!",
            "audioresample",
            "!",
            "alsasink",
            "device=hw:0,0",
        ],
        reasons=[],
        warnings=[],
        required_elements=[
            "audiotestsrc",
            "audioconvert",
            "audioresample",
            "alsasink",
        ],
        selected_profile="generic-alsa-audio-output-test",
    )


def _audio_device(kind: str) -> Device:
    return Device(
        id="hw:0,0",
        kind=kind,
        name="USB Audio",
        metadata={"backend": "alsa", "alsa_device": "hw:0,0"},
    )


def _element_fact(element: str, available: bool = True) -> EnvironmentFact:
    return EnvironmentFact(
        name="gstreamer_element_available",
        value=available,
        source="gst-inspect-1.0",
        metadata={"element": element},
    )


def _composite_group() -> CompositeDevice:
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


def _other_composite_group() -> CompositeDevice:
    return CompositeDevice(
        id="usb-device-1-2-3",
        name="USB Device 1-2.3",
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
                description="devices share USB parent path 1-2.3",
                strength=0.9,
            )
        ],
    )


def _composite_group_json() -> dict:
    return {
        "confidence": 0.9,
        "evidence": [
            {
                "description": "audio devices share ALSA card 0",
                "source": "alsa-card",
                "strength": 0.9,
            }
        ],
        "id": "audio-device-alsa-card-0",
        "kind": "audio-device",
        "members": [
            {
                "device_id": "hw:0,0",
                "path": "hw:0,0",
                "role": "audio-input",
                "subsystem": "alsa",
            },
            {
                "device_id": "hw:0,0",
                "path": "hw:0,0",
                "role": "audio-output",
                "subsystem": "alsa",
            },
        ],
        "name": "Reachy Mini Audio",
    }


def _groupable_camera() -> GroupableDevice:
    return GroupableDevice(
        device_ref=DeviceRef(
            role="camera",
            device_id="/dev/video0",
            path="/dev/video0",
            subsystem="v4l2",
        ),
        name="Reachy Mini Camera",
        metadata={
            "v4l2_name": "Reachy Mini Camera",
            "usb_parent_path": "1-2.3",
            "usb_product": "Reachy Mini",
        },
    )
