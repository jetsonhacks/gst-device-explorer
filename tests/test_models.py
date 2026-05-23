from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from gst_device_explorer.core import (
    Capability,
    Device,
    EnvironmentFact,
    ExecutionPlan,
    PipelineCandidate,
    Profile,
    RendererOutput,
)


def test_device_can_represent_media_device_with_capabilities() -> None:
    capability = Capability(
        name="video_format",
        values={"format": "YUY2", "width": 1280, "height": 720, "fps": 30},
        source="v4l2",
    )
    device = Device(
        id="/dev/video0",
        kind="video_input",
        name="USB Camera",
        capabilities=[capability],
    )

    assert device.id == "/dev/video0"
    assert device.kind == "video_input"
    assert device.capabilities[0].values["format"] == "YUY2"


def test_device_kind_can_extend_beyond_initial_media_focus() -> None:
    device = Device(
        id="dxl-bus-0",
        kind="servo_bus",
        name="Dynamixel Bus",
    )

    assert device.kind == "servo_bus"


def test_environment_fact_records_host_stack_information() -> None:
    fact = EnvironmentFact(
        name="gstreamer_version",
        value="1.24.0",
        source="gst-inspect-1.0",
    )

    assert fact.name == "gstreamer_version"
    assert fact.value == "1.24.0"
    assert fact.source == "gst-inspect-1.0"


def test_profile_expresses_preferences_and_patterns() -> None:
    profile = Profile(
        name="jetson",
        description="Jetson-oriented GStreamer preferences",
        preferences=["prefer NVIDIA elements when available"],
        known_good_patterns=["nvarguscamerasrc for supported CSI cameras"],
    )

    assert profile.name == "jetson"
    assert "prefer NVIDIA elements when available" in profile.preferences
    assert profile.known_good_patterns == [
        "nvarguscamerasrc for supported CSI cameras"
    ]


def test_pipeline_candidate_contains_structured_recommendation() -> None:
    candidate = PipelineCandidate(
        candidate_id="generic-v4l2-yuyv-videoconvert-autovideosink",
        purpose="preview video input",
        command="gst-launch-1.0 v4l2src device=/dev/video0 ! autovideosink",
        confidence=0.75,
        argv=[
            "gst-launch-1.0",
            "v4l2src",
            "device=/dev/video0",
            "!",
            "autovideosink",
        ],
        reasons=["v4l2src is available", "device exposes video capabilities"],
        warnings=["pipeline has not been executed"],
        required_elements=["v4l2src", "autovideosink"],
        selected_profile="generic-linux",
    )

    assert candidate.purpose == "preview video input"
    assert candidate.candidate_id == "generic-v4l2-yuyv-videoconvert-autovideosink"
    assert candidate.confidence == 0.75
    assert candidate.argv == [
        "gst-launch-1.0",
        "v4l2src",
        "device=/dev/video0",
        "!",
        "autovideosink",
    ]
    assert candidate.required_elements == ["v4l2src", "autovideosink"]
    assert candidate.selected_profile == "generic-linux"


def test_pipeline_candidate_rejects_invalid_confidence() -> None:
    with pytest.raises(ValueError, match="confidence"):
        PipelineCandidate(
            purpose="invalid confidence",
            command="gst-launch-1.0 fakesrc ! fakesink",
            confidence=1.5,
        )


def test_execution_plan_contains_argv_and_display_command() -> None:
    plan = ExecutionPlan(
        candidate_id="generic-v4l2-yuyv-videoconvert-autovideosink",
        argv=["gst-launch-1.0", "fakesrc", "!", "fakesink"],
        display_command="gst-launch-1.0 fakesrc ! fakesink",
        warnings=["example warning"],
    )

    assert plan.candidate_id == "generic-v4l2-yuyv-videoconvert-autovideosink"
    assert plan.argv == ["gst-launch-1.0", "fakesrc", "!", "fakesink"]
    assert plan.display_command == "gst-launch-1.0 fakesrc ! fakesink"
    assert plan.warnings == ["example warning"]


def test_renderer_output_presents_structured_data() -> None:
    output = RendererOutput(
        kind="json",
        content={"devices": [{"id": "/dev/video0", "kind": "video_input"}]},
        warnings=["example output"],
    )

    assert output.kind == "json"
    assert output.content["devices"][0]["kind"] == "video_input"
    assert output.warnings == ["example output"]
