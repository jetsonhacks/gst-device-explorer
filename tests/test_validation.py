from pathlib import Path
import json
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.cli.main import main
from gst_device_explorer.cli.renderer import print_group_validation
from gst_device_explorer.cli.serializers import group_validation_to_json_dict
from gst_device_explorer.core.models import (
    Capability,
    CompositeDevice,
    Device,
    DeviceProfile,
    DeviceRef,
    EndpointValidationSummary,
    GroupingEvidence,
    GroupValidation,
    GroupValidationDiagnostics,
    GroupValidationEndpointCounts,
    ProfileCandidateSummary,
)
from gst_device_explorer.core.validation import build_group_validation
import gst_device_explorer.cli.commands as cli_commands


def test_group_validation_model_construction() -> None:
    validation = GroupValidation(
        kind="group_validation",
        group_id="usb-device-1-2-3",
        group_label="USB Device",
        grouping_method="unknown",
        status="ok",
        endpoint_counts=GroupValidationEndpointCounts(video=1),
        endpoint_summaries=[
            EndpointValidationSummary(
                endpoint_kind="video",
                endpoint="/dev/video0",
                status="ok",
                available_candidate_count=1,
            )
        ],
        diagnostics=GroupValidationDiagnostics(missing_elements=[]),
    )

    assert validation.kind == "group_validation"
    assert validation.group_id == "usb-device-1-2-3"
    assert validation.endpoint_counts.video == 1
    assert validation.endpoint_summaries[0].status == "ok"


def test_build_group_validation_with_video_and_audio_endpoints() -> None:
    validation = build_group_validation(
        _group(),
        [
            _profile("video", "/dev/video0", available=["video-preview"]),
            _profile("audio-input", "hw:2,0", available=["audio-input-test"]),
            _profile("audio-output", "hw:2,0", unavailable=["audio-output-test"]),
        ],
    )

    assert validation.group_id == "usb-device-1-2-3"
    assert validation.group_label == "USB Device"
    assert validation.grouping_method == "unknown"
    assert validation.status == "partial"
    assert validation.endpoint_counts.video == 1
    assert validation.endpoint_counts.audio_inputs == 1
    assert validation.endpoint_counts.audio_outputs == 1
    assert [summary.status for summary in validation.endpoint_summaries] == [
        "ok",
        "ok",
        "candidates_unavailable",
    ]


def test_build_group_validation_with_video_only_group() -> None:
    validation = build_group_validation(
        _video_group(),
        [_profile("video", "/dev/video0", available=["video-preview"])],
    )

    assert validation.status == "ok"
    assert validation.endpoint_counts.video == 1
    assert validation.endpoint_counts.audio_inputs == 0


def test_build_group_validation_with_audio_only_group() -> None:
    validation = build_group_validation(
        _audio_group(),
        [
            _profile("audio-input", "hw:2,0", available=["audio-input-test"]),
            _profile("audio-output", "hw:2,0", available=["audio-output-test"]),
        ],
    )

    assert validation.status == "ok"
    assert validation.endpoint_counts.audio_inputs == 1
    assert validation.endpoint_counts.audio_outputs == 1


def test_endpoint_no_candidates_status() -> None:
    validation = build_group_validation(
        _video_group(),
        [_profile("video", "/dev/video0")],
    )

    assert validation.endpoint_summaries[0].status == "no_candidates"
    assert validation.status == "unavailable"


def test_endpoint_candidates_unavailable_status() -> None:
    validation = build_group_validation(
        _video_group(),
        [_profile("video", "/dev/video0", unavailable=["video-preview"])],
    )

    assert validation.endpoint_summaries[0].status == "candidates_unavailable"
    assert validation.status == "unavailable"


def test_unknown_endpoint_status_when_profile_is_missing() -> None:
    validation = build_group_validation(_video_group(), [])

    assert validation.endpoint_summaries[0].status == "unknown"
    assert validation.status == "unknown"
    assert validation.endpoint_summaries[0].suggested_next_commands == [
        "gst-device-explorer profile video /dev/video0"
    ]


def test_group_status_partial_when_ok_and_non_ok_are_mixed() -> None:
    validation = build_group_validation(
        _group(),
        [
            _profile("video", "/dev/video0", available=["video-preview"]),
            _profile("audio-input", "hw:2,0", unavailable=["audio-input-test"]),
            _profile("audio-output", "hw:2,0"),
        ],
    )

    assert validation.status == "partial"


def test_missing_elements_are_aggregated_and_deduplicated() -> None:
    validation = build_group_validation(
        _group(),
        [
            _profile("video", "/dev/video0", unavailable=["video-preview"], missing=["x"]),
            _profile("audio-input", "hw:2,0", unavailable=["audio-input"], missing=["x", "y"]),
            _profile("audio-output", "hw:2,0", unavailable=["audio-output"], missing=["y"]),
        ],
    )

    assert validation.diagnostics.missing_elements == ["x", "y"]


def test_suggested_commands_are_deduplicated() -> None:
    validation = build_group_validation(
        _audio_group(),
        [
            _profile(
                "audio-input",
                "hw:2,0",
                available=["audio-input"],
                suggested=["gst-device-explorer env"],
            ),
            _profile(
                "audio-output",
                "hw:2,0",
                available=["audio-output"],
                suggested=["gst-device-explorer env"],
            ),
        ],
    )

    assert validation.suggested_next_commands == ["gst-device-explorer env"]


def test_grouping_evidence_is_preserved() -> None:
    validation = build_group_validation(_group(), [])

    assert validation.evidence == _group().evidence


def test_group_validation_json_shape() -> None:
    validation = build_group_validation(
        _video_group(),
        [_profile("video", "/dev/video0", available=["video-preview"])],
    )

    data = group_validation_to_json_dict(validation)

    assert data["kind"] == "group_validation"
    assert data["group_id"] == "usb-device-1-2-3"
    assert data["endpoint_counts"] == {
        "audio_inputs": 0,
        "audio_outputs": 0,
        "unknown": 0,
        "video": 1,
    }
    assert data["endpoint_summaries"][0] == {
        "available_candidate_count": 1,
        "endpoint": "/dev/video0",
        "endpoint_kind": "video",
        "missing_elements": [],
        "recommended_candidate_id": "video-preview",
        "status": "ok",
        "suggested_next_commands": [
            "gst-device-explorer pipeline video /dev/video0",
            "gst-device-explorer pipeline video /dev/video0 --diagnostics",
            "gst-device-explorer run video /dev/video0 --dry-run",
        ],
        "unavailable_candidate_count": 0,
    }


def test_group_validation_text_output(capsys) -> None:
    validation = build_group_validation(
        _group(),
        [
            _profile("video", "/dev/video0", available=["video-preview"]),
            _profile("audio-input", "hw:2,0", unavailable=["audio-input"], missing=["alsasrc"]),
        ],
    )

    print_group_validation(validation, as_json=False)

    output = capsys.readouterr().out
    assert "Composite group validation: usb-device-1-2-3\n" in output
    assert "Status: partial\n" in output
    assert "- Video: /dev/video0\n" in output
    assert "Missing elements: alsasrc\n" in output
    assert "Suggested next commands:\n" in output


def test_group_validation_json_output(capsys) -> None:
    validation = build_group_validation(
        _video_group(),
        [_profile("video", "/dev/video0", available=["video-preview"])],
    )

    print_group_validation(validation, as_json=True)

    data = json.loads(capsys.readouterr().out)
    assert data["kind"] == "group_validation"
    assert data["data"]["endpoint_summaries"][0]["endpoint"] == "/dev/video0"


def test_cli_validate_group_text(monkeypatch, capsys) -> None:
    validation = build_group_validation(
        _video_group(),
        [_profile("video", "/dev/video0", available=["video-preview"])],
    )
    monkeypatch.setattr(cli_commands, "build_group_validation", lambda group_id: validation)

    exit_code = main(["validate", "group", "usb-device-1-2-3"])

    assert exit_code == 0
    assert "Composite group validation: usb-device-1-2-3\n" in capsys.readouterr().out


def test_cli_validate_group_with_mocked_discovery_and_profiles(
    monkeypatch,
    capsys,
) -> None:
    group = _group()
    monkeypatch.setattr(
        cli_commands.discovery,
        "discover_composite_devices",
        lambda: [group],
    )
    monkeypatch.setattr(
        cli_commands.gst_probe,
        "inspect_gstreamer_environment",
        lambda: [],
    )
    monkeypatch.setattr(
        cli_commands.v4l2_probe,
        "discover_v4l2_video_devices",
        lambda: [_video_device()],
    )
    monkeypatch.setattr(
        cli_commands.v4l2_probe,
        "discover_v4l2_capabilities",
        lambda device_id: [_video_capability()],
    )
    monkeypatch.setattr(
        cli_commands.alsa_probe,
        "discover_alsa_audio_inputs",
        lambda: [_audio_device("audio_input")],
    )
    monkeypatch.setattr(
        cli_commands.alsa_probe,
        "discover_alsa_audio_outputs",
        lambda: [_audio_device("audio_output")],
    )
    monkeypatch.setattr(
        cli_commands.profiles,
        "build_video_profile",
        lambda device, capabilities, environment, groups: _profile(
            "video", "/dev/video0", available=["video-preview"]
        ),
    )
    monkeypatch.setattr(
        cli_commands.profiles,
        "build_audio_input_profile",
        lambda device, environment, groups: _profile(
            "audio-input", "hw:2,0", available=["audio-input"]
        ),
    )
    monkeypatch.setattr(
        cli_commands.profiles,
        "build_audio_output_profile",
        lambda device, environment, groups: _profile(
            "audio-output", "hw:2,0", unavailable=["audio-output"], missing=["alsasink"]
        ),
    )

    exit_code = main(["validate", "group", "usb-device-1-2-3"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Status: partial\n" in output
    assert "- Audio output: hw:2,0\n" in output


def test_cli_validate_group_json(monkeypatch, capsys) -> None:
    validation = build_group_validation(
        _video_group(),
        [_profile("video", "/dev/video0", available=["video-preview"])],
    )
    monkeypatch.setattr(cli_commands, "build_group_validation", lambda group_id: validation)

    exit_code = main(["validate", "group", "usb-device-1-2-3", "--json"])

    assert exit_code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["kind"] == "group_validation"
    assert data["data"]["group_id"] == "usb-device-1-2-3"


def test_cli_validate_group_not_found(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli_commands, "build_group_validation", lambda group_id: None)

    exit_code = main(["validate", "group", "missing"])

    assert exit_code == 1
    assert capsys.readouterr().out == (
        "Group not found: missing\n"
        "\n"
        "Run:\n"
        "gst-device-explorer groups\n"
    )


def test_cli_validate_group_not_found_json(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli_commands, "build_group_validation", lambda group_id: None)

    exit_code = main(["validate", "group", "missing", "--json"])

    assert exit_code == 1
    data = json.loads(capsys.readouterr().out)
    assert data == {
        "error": "group_not_found",
        "group_id": "missing",
        "suggested_next_commands": ["gst-device-explorer groups"],
    }


def test_cli_validate_group_does_not_invoke_execution(monkeypatch) -> None:
    validation = build_group_validation(_video_group(), [])
    monkeypatch.setattr(cli_commands, "build_group_validation", lambda group_id: validation)
    monkeypatch.setattr(
        cli_commands.execution,
        "run_execution_plan",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("execution invoked")),
    )

    assert main(["validate", "group", "usb-device-1-2-3"]) == 0


def _group() -> CompositeDevice:
    return CompositeDevice(
        id="usb-device-1-2-3",
        name="USB Device",
        kind="unknown",
        confidence=0.9,
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
                path="hw:2,0",
                subsystem="alsa",
            ),
            DeviceRef(
                role="audio-output",
                device_id="hw:2,0",
                path="hw:2,0",
                subsystem="alsa",
            ),
        ],
        evidence=[
            GroupingEvidence(
                source="usb-topology",
                description="devices share USB parent path 1-2.3",
                strength=0.9,
            )
        ],
    )


def _video_group() -> CompositeDevice:
    group = _group()
    return CompositeDevice(
        id=group.id,
        name=group.name,
        kind=group.kind,
        confidence=group.confidence,
        members=[group.members[0]],
        evidence=group.evidence,
    )


def _audio_group() -> CompositeDevice:
    group = _group()
    return CompositeDevice(
        id="audio-device-alsa-card-2",
        name="USB Audio",
        kind="audio-device",
        confidence=0.9,
        members=group.members[1:],
        evidence=group.evidence,
    )


def _profile(
    device_kind: str,
    device: str,
    available: list[str] | None = None,
    unavailable: list[str] | None = None,
    missing: list[str] | None = None,
    suggested: list[str] | None = None,
) -> DeviceProfile:
    return DeviceProfile(
        device_kind=device_kind,
        device=device,
        candidate_summary={
            "available": [
                ProfileCandidateSummary(
                    candidate_id=candidate_id,
                    status="available",
                    reason="available",
                    missing_elements=[],
                )
                for candidate_id in (available or [])
            ],
            "unavailable": [
                ProfileCandidateSummary(
                    candidate_id=candidate_id,
                    status="unavailable",
                    reason="missing elements",
                    missing_elements=list(missing or []),
                )
                for candidate_id in (unavailable or [])
            ],
        },
        suggested_next_commands=suggested
        or [
            f"gst-device-explorer pipeline {device_kind} {device}",
            f"gst-device-explorer pipeline {device_kind} {device} --diagnostics",
            f"gst-device-explorer run {device_kind} {device} --dry-run",
        ],
    )


def _video_device() -> Device:
    return Device(
        id="/dev/video0",
        kind="video_input",
        name="video0",
        metadata={"backend": "v4l2", "path": "/dev/video0"},
    )


def _audio_device(kind: str) -> Device:
    return Device(
        id="hw:2,0",
        kind=kind,
        name="USB Audio",
        metadata={"backend": "alsa", "alsa_device": "hw:2,0"},
    )


def _video_capability() -> Capability:
    return Capability(
        name="video_format",
        values={"media_type": "video", "pixel_format": "MJPG"},
        source="v4l2-ctl",
    )
