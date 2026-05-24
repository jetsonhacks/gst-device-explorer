"""Synthetic tests for the SystemReport model, builder, serializer, and CLI."""

from pathlib import Path
import json
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.core.models import (
    Capability,
    CompositeDevice,
    Device,
    DeviceRef,
    EnvironmentFact,
    GroupingEvidence,
    ReportDevices,
    ReportDiagnostics,
    ReportProfiles,
    SystemReport,
)
from gst_device_explorer.core.report import build_system_report
from gst_device_explorer.cli.serializers import system_report_to_json_dict
from gst_device_explorer.cli.main import main
import gst_device_explorer.cli.commands as cli_commands


# ---------------------------------------------------------------------------
# Model construction
# ---------------------------------------------------------------------------


def test_system_report_can_be_constructed_from_defaults() -> None:
    report = SystemReport(kind="system_report", tool_version="0.7.0")

    assert report.kind == "system_report"
    assert report.tool_version == "0.7.0"
    assert report.environment == []
    assert report.devices.video == []
    assert report.devices.audio_inputs == []
    assert report.devices.audio_outputs == []
    assert report.groups == []
    assert report.profiles.video == []
    assert report.profiles.audio_inputs == []
    assert report.profiles.audio_outputs == []
    assert report.diagnostics.missing_elements == []
    assert report.suggested_next_commands == []


def test_system_report_stores_provided_values() -> None:
    video_device = _video_device()
    audio_in = _audio_input_device()
    audio_out = _audio_output_device()
    env = [_element_fact("v4l2src", True)]

    report = SystemReport(
        kind="system_report",
        tool_version="0.7.0",
        environment=env,
        devices=ReportDevices(
            video=[video_device],
            audio_inputs=[audio_in],
            audio_outputs=[audio_out],
        ),
    )

    assert report.devices.video == [video_device]
    assert report.devices.audio_inputs == [audio_in]
    assert report.devices.audio_outputs == [audio_out]
    assert report.environment == env


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


def test_build_system_report_uses_supplied_devices() -> None:
    report = build_system_report(
        video_devices=[_video_device()],
        audio_input_devices=[_audio_input_device()],
        audio_output_devices=[_audio_output_device()],
        groups=[],
        environment=_environment_with_all_elements(),
        video_capabilities={"/dev/video0": [_mjpeg_capability()]},
        tool_version="0.7.0",
    )

    assert report.kind == "system_report"
    assert report.tool_version == "0.7.0"
    assert len(report.devices.video) == 1
    assert len(report.devices.audio_inputs) == 1
    assert len(report.devices.audio_outputs) == 1


def test_build_system_report_builds_profiles_for_each_device() -> None:
    report = build_system_report(
        video_devices=[_video_device()],
        audio_input_devices=[_audio_input_device()],
        audio_output_devices=[_audio_output_device()],
        groups=[],
        environment=_environment_with_all_elements(),
        video_capabilities={"/dev/video0": [_mjpeg_capability()]},
        tool_version="0.7.0",
    )

    assert len(report.profiles.video) == 1
    assert len(report.profiles.audio_inputs) == 1
    assert len(report.profiles.audio_outputs) == 1
    assert report.profiles.video[0].device_kind == "video"
    assert report.profiles.audio_inputs[0].device_kind == "audio-input"
    assert report.profiles.audio_outputs[0].device_kind == "audio-output"


def test_build_system_report_with_no_devices() -> None:
    report = build_system_report(
        video_devices=[],
        audio_input_devices=[],
        audio_output_devices=[],
        groups=[],
        environment=[],
        video_capabilities={},
        tool_version="0.7.0",
    )

    assert report.devices.video == []
    assert report.devices.audio_inputs == []
    assert report.devices.audio_outputs == []
    assert report.profiles.video == []
    assert report.profiles.audio_inputs == []
    assert report.profiles.audio_outputs == []
    assert report.diagnostics.missing_elements == []
    assert report.suggested_next_commands == []


def test_build_system_report_aggregates_missing_elements() -> None:
    environment = [
        _element_fact("v4l2src", True),
        _element_fact("videoconvert", True),
        _element_fact("autovideosink", False),
        _element_fact("alsasrc", False),
        _element_fact("audioconvert", True),
        _element_fact("audioresample", True),
        _element_fact("level", True),
        _element_fact("fakesink", True),
        _element_fact("audiotestsrc", True),
        _element_fact("alsasink", False),
    ]

    report = build_system_report(
        video_devices=[_video_device()],
        audio_input_devices=[_audio_input_device()],
        audio_output_devices=[_audio_output_device()],
        groups=[],
        environment=environment,
        video_capabilities={"/dev/video0": [_yuyv_capability()]},
        tool_version="0.7.0",
    )

    assert "autovideosink" in report.diagnostics.missing_elements
    assert "alsasrc" in report.diagnostics.missing_elements
    assert "alsasink" in report.diagnostics.missing_elements


def test_build_system_report_deduplicates_missing_elements() -> None:
    environment = [
        _element_fact("v4l2src", True),
        _element_fact("videoconvert", True),
        _element_fact("autovideosink", False),
    ]

    report = build_system_report(
        video_devices=[_video_device(), _video_device2()],
        audio_input_devices=[],
        audio_output_devices=[],
        groups=[],
        environment=environment,
        video_capabilities={
            "/dev/video0": [_yuyv_capability()],
            "/dev/video1": [_yuyv_capability()],
        },
        tool_version="0.7.0",
    )

    assert report.diagnostics.missing_elements.count("autovideosink") == 1


def test_build_system_report_collects_suggested_commands_from_profiles() -> None:
    report = build_system_report(
        video_devices=[_video_device()],
        audio_input_devices=[],
        audio_output_devices=[],
        groups=[],
        environment=_environment_with_all_elements(),
        video_capabilities={"/dev/video0": [_mjpeg_capability()]},
        tool_version="0.7.0",
    )

    assert "gst-device-explorer pipeline video /dev/video0" in [
        cmd.command for cmd in report.suggested_next_commands
    ]


def test_build_system_report_deduplicates_suggested_commands() -> None:
    report = build_system_report(
        video_devices=[_video_device()],
        audio_input_devices=[_audio_input_device()],
        audio_output_devices=[],
        groups=[],
        environment=_environment_with_all_elements(),
        video_capabilities={"/dev/video0": [_mjpeg_capability()]},
        tool_version="0.7.0",
    )

    commands = report.suggested_next_commands
    assert len(commands) == len(set(commands))


def test_build_system_report_includes_groups() -> None:
    group = _composite_group()
    report = build_system_report(
        video_devices=[],
        audio_input_devices=[],
        audio_output_devices=[],
        groups=[group],
        environment=[],
        video_capabilities={},
        tool_version="0.7.0",
    )

    assert len(report.groups) == 1
    assert report.groups[0].id == group.id


def test_build_system_report_includes_environment() -> None:
    env = [_element_fact("v4l2src", True)]
    report = build_system_report(
        video_devices=[],
        audio_input_devices=[],
        audio_output_devices=[],
        groups=[],
        environment=env,
        video_capabilities={},
        tool_version="0.7.0",
    )

    assert report.environment == env


def test_build_system_report_uses_empty_capabilities_when_device_not_in_map() -> None:
    report = build_system_report(
        video_devices=[_video_device()],
        audio_input_devices=[],
        audio_output_devices=[],
        groups=[],
        environment=_environment_with_all_elements(),
        video_capabilities={},  # no capabilities for /dev/video0
        tool_version="0.7.0",
    )

    assert len(report.profiles.video) == 1
    assert report.profiles.video[0].capabilities_summary.get("mode_count") == 0


# ---------------------------------------------------------------------------
# JSON serialization shape
# ---------------------------------------------------------------------------


def test_system_report_json_has_expected_top_level_keys() -> None:
    report = _minimal_report()
    data = system_report_to_json_dict(report)

    assert set(data.keys()) == {
        "kind",
        "tool_version",
        "environment",
        "devices",
        "groups",
        "profiles",
        "diagnostics",
        "suggested_next_commands",
    }


def test_system_report_json_devices_has_expected_keys() -> None:
    report = _minimal_report()
    data = system_report_to_json_dict(report)

    assert set(data["devices"].keys()) == {"video", "audio_inputs", "audio_outputs"}


def test_system_report_json_profiles_has_expected_keys() -> None:
    report = _minimal_report()
    data = system_report_to_json_dict(report)

    assert set(data["profiles"].keys()) == {"video", "audio_inputs", "audio_outputs"}


def test_system_report_json_diagnostics_has_expected_keys() -> None:
    report = _minimal_report()
    data = system_report_to_json_dict(report)

    assert "missing_elements" in data["diagnostics"]


def test_system_report_json_kind_and_version() -> None:
    report = _minimal_report()
    data = system_report_to_json_dict(report)

    assert data["kind"] == "system_report"
    assert data["tool_version"] == "0.7.0"


def test_system_report_json_serializes_devices() -> None:
    report = build_system_report(
        video_devices=[_video_device()],
        audio_input_devices=[_audio_input_device()],
        audio_output_devices=[_audio_output_device()],
        groups=[],
        environment=[],
        video_capabilities={},
        tool_version="0.7.0",
    )
    data = system_report_to_json_dict(report)

    assert len(data["devices"]["video"]) == 1
    assert data["devices"]["video"][0]["id"] == "/dev/video0"
    assert len(data["devices"]["audio_inputs"]) == 1
    assert data["devices"]["audio_inputs"][0]["id"] == "hw:0,0"
    assert len(data["devices"]["audio_outputs"]) == 1
    assert data["devices"]["audio_outputs"][0]["id"] == "hw:0,0"


def test_system_report_json_serializes_profiles() -> None:
    report = build_system_report(
        video_devices=[_video_device()],
        audio_input_devices=[_audio_input_device()],
        audio_output_devices=[_audio_output_device()],
        groups=[],
        environment=_environment_with_all_elements(),
        video_capabilities={"/dev/video0": [_mjpeg_capability()]},
        tool_version="0.7.0",
    )
    data = system_report_to_json_dict(report)

    assert len(data["profiles"]["video"]) == 1
    assert data["profiles"]["video"][0]["device_kind"] == "video"
    assert len(data["profiles"]["audio_inputs"]) == 1
    assert data["profiles"]["audio_inputs"][0]["device_kind"] == "audio-input"
    assert len(data["profiles"]["audio_outputs"]) == 1
    assert data["profiles"]["audio_outputs"][0]["device_kind"] == "audio-output"


def test_system_report_json_serializes_missing_elements() -> None:
    environment = [
        _element_fact("v4l2src", True),
        _element_fact("videoconvert", True),
        _element_fact("autovideosink", False),
    ]
    report = build_system_report(
        video_devices=[_video_device()],
        audio_input_devices=[],
        audio_output_devices=[],
        groups=[],
        environment=environment,
        video_capabilities={"/dev/video0": [_yuyv_capability()]},
        tool_version="0.7.0",
    )
    data = system_report_to_json_dict(report)

    assert "autovideosink" in data["diagnostics"]["missing_elements"]


def test_system_report_json_is_valid_json_string() -> None:
    report = _minimal_report()
    data = system_report_to_json_dict(report)
    serialized = json.dumps(data, indent=2, sort_keys=True)
    parsed = json.loads(serialized)

    assert parsed["kind"] == "system_report"


# ---------------------------------------------------------------------------
# CLI — report --json
# ---------------------------------------------------------------------------


def test_report_json_command_exits_zero(monkeypatch, capsys) -> None:
    _patch_probes_empty(monkeypatch)

    exit_code = main(["report", "--json"])

    assert exit_code == 0


def test_report_json_command_emits_valid_json(monkeypatch, capsys) -> None:
    _patch_probes_empty(monkeypatch)

    main(["report", "--json"])

    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, dict)


def test_report_json_command_has_expected_keys(monkeypatch, capsys) -> None:
    _patch_probes_empty(monkeypatch)

    main(["report", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert "kind" in data
    assert "tool_version" in data
    assert "schema_version" in data
    assert "data" in data
    assert "devices" in data["data"]
    assert "groups" in data["data"]
    assert "profiles" in data["data"]
    assert "diagnostics" in data["data"]
    assert "suggested_next_commands" in data["data"]


def test_report_json_command_kind_is_system_report(monkeypatch, capsys) -> None:
    _patch_probes_empty(monkeypatch)

    main(["report", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert data["kind"] == "system_report"


def test_report_json_command_version_is_current(monkeypatch, capsys) -> None:
    _patch_probes_empty(monkeypatch)

    main(["report", "--json"])

    data = json.loads(capsys.readouterr().out)
    from gst_device_explorer import __version__
    assert data["tool_version"] == __version__


def test_report_json_command_includes_discovered_devices(monkeypatch, capsys) -> None:
    _patch_probes_with_one_device_each(monkeypatch)

    main(["report", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert len(data["data"]["devices"]["video"]) == 1
    assert len(data["data"]["devices"]["audio_inputs"]) == 1
    assert len(data["data"]["devices"]["audio_outputs"]) == 1


def test_report_json_command_includes_profiles(monkeypatch, capsys) -> None:
    _patch_probes_with_one_device_each(monkeypatch)

    main(["report", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert len(data["data"]["profiles"]["video"]) == 1
    assert len(data["data"]["profiles"]["audio_inputs"]) == 1
    assert len(data["data"]["profiles"]["audio_outputs"]) == 1


# ---------------------------------------------------------------------------
# CLI — report (text)
# ---------------------------------------------------------------------------


def test_report_text_command_exits_zero(monkeypatch, capsys) -> None:
    _patch_probes_empty(monkeypatch)

    exit_code = main(["report"])

    assert exit_code == 0


def test_report_text_command_shows_device_counts(monkeypatch, capsys) -> None:
    _patch_probes_with_one_device_each(monkeypatch)

    main(["report"])

    out = capsys.readouterr().out
    assert "Video devices" in out
    assert "Audio inputs" in out
    assert "Audio outputs" in out


def test_report_text_command_shows_version(monkeypatch, capsys) -> None:
    _patch_probes_empty(monkeypatch)

    main(["report"])

    from gst_device_explorer import __version__
    out = capsys.readouterr().out
    assert __version__ in out


# ---------------------------------------------------------------------------
# No pipeline execution
# ---------------------------------------------------------------------------


def test_build_system_report_does_not_call_execution(monkeypatch) -> None:
    import gst_device_explorer.core.execution as execution_mod

    calls: list[str] = []

    def _guard(*args, **kwargs):
        calls.append("execution called")
        raise AssertionError("report builder must not execute pipelines")

    monkeypatch.setattr(execution_mod, "run_execution_plan", _guard)
    monkeypatch.setattr(execution_mod, "select_pipeline_candidate", _guard)

    build_system_report(
        video_devices=[_video_device()],
        audio_input_devices=[_audio_input_device()],
        audio_output_devices=[_audio_output_device()],
        groups=[],
        environment=_environment_with_all_elements(),
        video_capabilities={"/dev/video0": [_mjpeg_capability()]},
        tool_version="0.7.0",
    )

    assert calls == []


# ---------------------------------------------------------------------------
# Existing behavior guard
# ---------------------------------------------------------------------------


def test_existing_devices_command_still_works(monkeypatch, capsys) -> None:
    import gst_device_explorer.core.discovery as discovery_mod

    monkeypatch.setattr(
        discovery_mod,
        "discover_devices",
        lambda: [_video_device()],
    )

    exit_code = main(["devices"])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "video_input" in out


def test_existing_env_command_still_works(monkeypatch, capsys) -> None:
    import gst_device_explorer.probes.gst as gst_probe_mod

    monkeypatch.setattr(
        gst_probe_mod,
        "inspect_gstreamer_environment",
        lambda: [],
    )

    exit_code = main(["env"])

    assert exit_code == 0


# ---------------------------------------------------------------------------
# Helpers and fixtures
# ---------------------------------------------------------------------------


def _minimal_report() -> SystemReport:
    return SystemReport(kind="system_report", tool_version="0.7.0")


def _video_device() -> Device:
    return Device(
        id="/dev/video0",
        kind="video_input",
        name="video0",
        metadata={"backend": "v4l2", "path": "/dev/video0"},
    )


def _video_device2() -> Device:
    return Device(
        id="/dev/video1",
        kind="video_input",
        name="video1",
        metadata={"backend": "v4l2", "path": "/dev/video1"},
    )


def _audio_input_device() -> Device:
    return Device(
        id="hw:0,0",
        kind="audio_input",
        name="USB Audio: Capture",
        metadata={"backend": "alsa", "alsa_device": "hw:0,0"},
    )


def _audio_output_device() -> Device:
    return Device(
        id="hw:0,0",
        kind="audio_output",
        name="USB Audio: Playback",
        metadata={"backend": "alsa", "alsa_device": "hw:0,0"},
    )


def _element_fact(element: str, available: bool) -> EnvironmentFact:
    return EnvironmentFact(
        name="gstreamer_element_available",
        value=available,
        source="gst-inspect-1.0",
        metadata={"element": element},
    )


def _mjpeg_capability() -> Capability:
    return Capability(
        name="video/x-raw",
        values={
            "media_type": "video",
            "pixel_format": "MJPG",
            "width": 1920,
            "height": 1080,
            "fps": [30.0],
        },
        source="v4l2-ctl",
    )


def _yuyv_capability() -> Capability:
    return Capability(
        name="video/x-raw",
        values={
            "media_type": "video",
            "pixel_format": "YUYV",
            "width": 1280,
            "height": 720,
            "fps": [30.0],
        },
        source="v4l2-ctl",
    )


def _environment_with_all_elements() -> list[EnvironmentFact]:
    return [
        _element_fact("v4l2src", True),
        _element_fact("videoconvert", True),
        _element_fact("autovideosink", True),
        _element_fact("jpegparse", True),
        _element_fact("nvjpegdec", True),
        _element_fact("nvvidconv", True),
        _element_fact("nveglglessink", True),
        _element_fact("alsasrc", True),
        _element_fact("audioconvert", True),
        _element_fact("audioresample", True),
        _element_fact("level", True),
        _element_fact("fakesink", True),
        _element_fact("audiotestsrc", True),
        _element_fact("alsasink", True),
    ]


def _composite_group() -> CompositeDevice:
    return CompositeDevice(
        id="usb-device-1-4-1",
        name="Test Camera Group",
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
                source="usb_parent_path",
                description="shared USB parent",
                strength=0.9,
            )
        ],
    )


def _patch_probes_empty(monkeypatch) -> None:
    monkeypatch.setattr(
        cli_commands.v4l2_probe, "discover_v4l2_video_devices", lambda: []
    )
    monkeypatch.setattr(
        cli_commands.alsa_probe, "discover_alsa_audio_inputs", lambda: []
    )
    monkeypatch.setattr(
        cli_commands.alsa_probe, "discover_alsa_audio_outputs", lambda: []
    )
    monkeypatch.setattr(
        cli_commands.gst_probe, "inspect_gstreamer_environment", lambda: []
    )
    monkeypatch.setattr(
        cli_commands.discovery, "discover_composite_devices", lambda: []
    )
    monkeypatch.setattr(
        cli_commands.v4l2_probe, "discover_v4l2_capabilities", lambda path: []
    )


def _patch_probes_with_one_device_each(monkeypatch) -> None:
    monkeypatch.setattr(
        cli_commands.v4l2_probe,
        "discover_v4l2_video_devices",
        lambda: [_video_device()],
    )
    monkeypatch.setattr(
        cli_commands.alsa_probe,
        "discover_alsa_audio_inputs",
        lambda: [_audio_input_device()],
    )
    monkeypatch.setattr(
        cli_commands.alsa_probe,
        "discover_alsa_audio_outputs",
        lambda: [_audio_output_device()],
    )
    monkeypatch.setattr(
        cli_commands.gst_probe,
        "inspect_gstreamer_environment",
        lambda: _environment_with_all_elements(),
    )
    monkeypatch.setattr(
        cli_commands.discovery, "discover_composite_devices", lambda: []
    )
    monkeypatch.setattr(
        cli_commands.v4l2_probe,
        "discover_v4l2_capabilities",
        lambda path: [_mjpeg_capability()],
    )
