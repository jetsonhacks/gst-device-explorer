from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.cli.main import main
import gst_device_explorer.cli.tui as cli_tui
from gst_device_explorer.cli.parser import build_parser
from gst_device_explorer.core.config import ConfigValidationResult, default_config
from gst_device_explorer.core.models import (
    CompositeDevice,
    Device,
    DeviceRef,
    EnvironmentFact,
    GroupingEvidence,
    ReportDevices,
    SystemReport,
)
from gst_device_explorer.core.presets import PresetDefinition
from gst_device_explorer.core.suggestions import suggest_video_pipeline
from gst_device_explorer.core.schema import list_schema_documents
from gst_device_explorer.core.tui import (
    TuiNavigationState,
    build_tui_review_model,
    build_tui_sections,
    handle_tui_key,
    render_current_screen,
    render_overview_lines,
)


def test_parser_recognizes_tui() -> None:
    args = build_parser().parse_args(["tui"])

    assert args.command == "tui"
    assert args.snapshot is False


def test_parser_recognizes_tui_snapshot() -> None:
    args = build_parser().parse_args(["tui", "--snapshot"])

    assert args.command == "tui"
    assert args.snapshot is True


def test_review_model_renders_overview_counts() -> None:
    model = _review_model()

    lines = render_overview_lines(model)

    assert "gst-device-explorer TUI" in lines
    assert "  Environment: available" in lines
    assert "  Video devices: 1" in lines
    assert "  Audio inputs: 1" in lines
    assert "  Audio outputs: 1" in lines
    assert "  Composite groups: 1" in lines
    assert "  Presets: 1" in lines
    assert "  Config: defaults" in lines
    assert "Read-only: suggested commands are displayed, not executed." in lines


def test_review_model_handles_no_devices() -> None:
    model = build_tui_review_model(
        report=SystemReport(kind="system_report", tool_version="0.15.0"),
        presets=[],
        config=ConfigValidationResult(path=None, valid=True, config=default_config()),
        schema_documents=[],
    )

    sections = build_tui_sections(model)
    devices = next(section for section in sections if section.section_id == "devices")

    assert "  none" in devices.lines
    assert "No composite groups discovered." in next(
        section for section in sections if section.section_id == "groups"
    ).lines


def test_sections_include_suggested_commands_not_execution() -> None:
    model = _review_model()

    section = next(
        section
        for section in build_tui_sections(model)
        if section.section_id == "suggested_commands"
    )

    assert "gst-device-explorer report --json" in section.lines
    assert "gst-device-explorer pipeline video /dev/video0" in section.lines
    assert all("gst-launch-1.0" not in line for line in section.lines)


def test_navigation_moves_and_opens_sections() -> None:
    state = TuiNavigationState()

    state = handle_tui_key(state, "down")
    assert state.selected_index == 1
    assert state.active_section_id is None

    state = handle_tui_key(state, "enter")
    assert state.selected_index == 1
    assert state.active_section_id == "devices"

    state = handle_tui_key(state, "escape")
    assert state.selected_index == 1
    assert state.active_section_id is None


def test_navigation_number_key_and_quit() -> None:
    state = handle_tui_key(TuiNavigationState(), "4")

    assert state.selected_index == 3
    assert state.active_section_id == "presets"

    state = handle_tui_key(state, "q")
    assert state.quit_requested is True


def test_render_current_screen_section_view() -> None:
    model = _review_model()
    state = TuiNavigationState(selected_index=0, active_section_id="devices")

    lines = render_current_screen(model, state)

    assert lines[0] == "Devices"
    assert "  /dev/video0  Camera" in lines
    assert "Esc: back   q: quit" in lines


def test_tui_snapshot_command(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli_tui, "build_review_model", lambda: _review_model())

    exit_code = main(["tui", "--snapshot"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert output.startswith("gst-device-explorer TUI\n")
    assert "Sections\n" in output
    assert "Read-only: suggested commands are displayed, not executed.\n" in output


def test_tui_snapshot_does_not_call_execution_or_capture(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli_tui.commands, "build_system_report", lambda: _report())

    def fail(*args, **kwargs):
        raise AssertionError("execution helper should not be called")

    monkeypatch.setattr(cli_tui.commands, "run_selected_candidate", fail)
    monkeypatch.setattr(cli_tui.commands, "run_capture_candidate", fail)

    exit_code = main(["tui", "--snapshot"])

    assert exit_code == 0
    assert "gst-device-explorer TUI" in capsys.readouterr().out


def _review_model():
    return build_tui_review_model(
        report=_report(),
        presets=[
            PresetDefinition(
                preset_id="camera-preview",
                title="Camera Preview",
                description="Preview a video endpoint.",
                target_kind="video",
                safety_notes=(),
            )
        ],
        config=ConfigValidationResult(path=None, valid=True, config=default_config()),
        schema_documents=list_schema_documents()[:2],
    )


def _report() -> SystemReport:
    return SystemReport(
        kind="system_report",
        tool_version="0.15.0",
        environment=[
            EnvironmentFact(
                name="gstreamer_tool_available",
                value=True,
                source="gst-launch-1.0",
                metadata={"tool": "gst-launch-1.0"},
            ),
            EnvironmentFact(
                name="gstreamer_tool_available",
                value=True,
                source="gst-inspect-1.0",
                metadata={"tool": "gst-inspect-1.0"},
            ),
        ],
        devices=ReportDevices(
            video=[Device(id="/dev/video0", kind="video_input", name="Camera")],
            audio_inputs=[Device(id="hw:0,0", kind="audio_input", name="Mic")],
            audio_outputs=[Device(id="hw:1,0", kind="audio_output", name="Speaker")],
        ),
        groups=[
            CompositeDevice(
                id="usb-device-1",
                name="USB Device",
                kind="unknown",
                members=[
                    DeviceRef(
                        role="camera",
                        device_id="/dev/video0",
                        path="/dev/video0",
                        subsystem="v4l2",
                    ),
                ],
                evidence=[
                    GroupingEvidence(
                        source="synthetic",
                        description="test evidence",
                        strength=0.9,
                    ),
                ],
                confidence=0.9,
            )
        ],
        suggested_next_commands=[suggest_video_pipeline("/dev/video0")],
    )
