from pathlib import Path
from dataclasses import asdict
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from gst_device_explorer.core.models import (
    Capability,
    CompositeDevice,
    Device,
    DeviceRef,
    EnvironmentFact,
    ExecutionPlan,
    GroupingEvidence,
    PipelineCandidate,
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


def test_device_ref_can_reference_v4l2_camera() -> None:
    ref = DeviceRef(
        role="camera",
        device_id="/dev/video0",
        path="/dev/video0",
        subsystem="v4l2",
    )

    assert ref.role == "camera"
    assert ref.device_id == "/dev/video0"
    assert ref.path == "/dev/video0"
    assert ref.subsystem == "v4l2"


def test_device_ref_can_reference_alsa_audio_input() -> None:
    ref = DeviceRef(
        role="audio-input",
        device_id="hw:2,0",
        path=None,
        subsystem="alsa",
    )

    assert ref.role == "audio-input"
    assert ref.device_id == "hw:2,0"
    assert ref.path is None
    assert ref.subsystem == "alsa"


def test_grouping_evidence_records_source_description_and_strength() -> None:
    evidence = GroupingEvidence(
        source="usb-topology",
        description="camera and audio devices share the same USB parent path",
        strength=0.9,
    )

    assert evidence.source == "usb-topology"
    assert evidence.description == (
        "camera and audio devices share the same USB parent path"
    )
    assert evidence.strength == 0.9


def test_grouping_evidence_rejects_invalid_strength() -> None:
    with pytest.raises(ValueError, match="strength"):
        GroupingEvidence(
            source="usb-topology",
            description="invalid evidence strength",
            strength=1.5,
        )


def test_composite_device_groups_camera_audio_input_and_audio_output() -> None:
    camera = DeviceRef(
        role="camera",
        device_id="/dev/video0",
        path="/dev/video0",
        subsystem="v4l2",
    )
    audio_input = DeviceRef(
        role="audio-input",
        device_id="hw:2,0",
        path=None,
        subsystem="alsa",
    )
    audio_output = DeviceRef(
        role="audio-output",
        device_id="hw:2,0",
        path=None,
        subsystem="alsa",
    )
    evidence = [
        GroupingEvidence(
            source="synthetic-test",
            description="camera and audio devices are expected to be grouped",
            strength=0.8,
        )
    ]

    composite = CompositeDevice(
        id="synthetic-composite-device",
        name="Synthetic Composite Device",
        kind="robot",
        confidence=0.85,
        members=[camera, audio_input, audio_output],
        evidence=evidence,
    )

    assert composite.confidence == 0.85
    assert composite.members == [camera, audio_input, audio_output]
    assert composite.evidence == evidence


def test_composite_device_rejects_invalid_confidence() -> None:
    with pytest.raises(ValueError, match="confidence"):
        CompositeDevice(
            id="invalid-composite-device",
            name="Invalid Composite Device",
            kind="unknown",
            confidence=-0.1,
        )


def test_composite_device_asdict_serializes_nested_members_and_evidence() -> None:
    composite = CompositeDevice(
        id="synthetic-composite-device",
        name="Synthetic Composite Device",
        kind="camera-system",
        confidence=0.75,
        members=[
            DeviceRef(
                role="camera",
                device_id="/dev/video0",
                path="/dev/video0",
                subsystem="v4l2",
            ),
            DeviceRef(
                role="audio-input",
                device_id="hw:2,0",
                path=None,
                subsystem="alsa",
            ),
        ],
        evidence=[
            GroupingEvidence(
                source="usb-topology",
                description="members share the same USB parent path",
                strength=0.9,
            )
        ],
    )

    assert asdict(composite) == {
        "id": "synthetic-composite-device",
        "name": "Synthetic Composite Device",
        "kind": "camera-system",
        "confidence": 0.75,
        "members": [
            {
                "role": "camera",
                "device_id": "/dev/video0",
                "path": "/dev/video0",
                "subsystem": "v4l2",
            },
            {
                "role": "audio-input",
                "device_id": "hw:2,0",
                "path": None,
                "subsystem": "alsa",
            },
        ],
        "evidence": [
            {
                "source": "usb-topology",
                "description": "members share the same USB parent path",
                "strength": 0.9,
            }
        ],
    }


