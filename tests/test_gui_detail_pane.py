from pathlib import Path
import subprocess
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.gui.builders import build_unknown_detail_pane
from gst_device_explorer.gui.demo import build_demo_gui_snapshot
from gst_device_explorer.gui.live import build_error_detail_pane, build_empty_snapshot
from gst_device_explorer.gui.qt_detail import (
    action_copy_text,
    copy_display_text,
    copyable_texts,
    detail_accessible_text,
    detail_identity_items,
    section_display_title,
    section_kind,
)


def test_group_detail_pane_has_polished_group_text() -> None:
    pane = build_demo_gui_snapshot().detail_panes["group:demo-usb-device"]
    text = detail_accessible_text(pane)

    assert "Demo Composite USB Device" in text
    assert "Group id: demo-usb-device" in text
    assert "Constituent Endpoints" in text
    assert "Grouping Evidence" in text
    assert "Endpoint Status" in text
    assert "Missing Elements" in text
    assert "Group-based execution and synchronized capture are not available." in text


def test_video_detail_pane_has_camera_specific_text() -> None:
    pane = build_demo_gui_snapshot().detail_panes["video:/dev/video0"]
    text = detail_accessible_text(pane)

    assert "Reachy-Style Camera" in text
    assert "Endpoint: /dev/video0" in text
    assert "Identity and Metadata" in text
    assert "Capabilities" in text
    assert "Candidate Pipelines" in text
    assert "Recommended Candidate" in text


def test_audio_input_output_panes_have_audio_specific_text() -> None:
    demo = build_demo_gui_snapshot()
    input_text = detail_accessible_text(demo.detail_panes["audio_input:hw:2,0"])
    output_text = detail_accessible_text(demo.detail_panes["audio_output:hw:2,0"])

    assert "Reachy-Style Microphone" in input_text
    assert "Endpoint: hw:2,0" in input_text
    assert "Candidate Pipelines" in input_text
    assert "Reachy-Style Speaker" in output_text
    assert "Endpoint: hw:2,0" in output_text
    assert "Recommended Candidate" in output_text


def test_copyable_texts_include_endpoint_and_suggested_commands() -> None:
    pane = build_demo_gui_snapshot().detail_panes["video:/dev/video0"]
    copyables = dict(copyable_texts(pane))

    assert "/dev/video0" in copyables.values()
    assert any("gst-device-explorer" in value for value in copyables.values())


def test_action_copy_text_uses_suggested_command_only() -> None:
    pane = build_demo_gui_snapshot().detail_panes["video:/dev/video0"]
    dry_run = next(action for action in pane.actions if action.kind == "dry_run")
    preview = next(action for action in pane.actions if action.kind == "preview")

    assert action_copy_text(dry_run) == "gst-device-explorer run video /dev/video0 --dry-run"
    assert action_copy_text(preview) is None


def test_copy_display_text_uses_clipboard_abstraction() -> None:
    copied: list[str] = []
    statuses: list[str] = []

    copy_display_text(
        "gst-device-explorer run video /dev/video0 --dry-run",
        set_clipboard_text=copied.append,
        status_callback=statuses.append,
    )

    assert copied == ["gst-device-explorer run video /dev/video0 --dry-run"]
    assert statuses == ["Copied to clipboard."]


def test_empty_error_unknown_states_render_user_facing_text() -> None:
    empty = build_empty_snapshot().detail_pane
    error = build_error_detail_pane("Unable to refresh media devices.", details="tool missing")
    unknown = build_unknown_detail_pane("video:/missing")

    assert "No Media Devices Discovered" in detail_accessible_text(empty)
    assert "Unable to refresh media devices." in detail_accessible_text(error)
    assert "tool missing" in detail_accessible_text(error)
    assert "Selection Unavailable" in detail_accessible_text(unknown)


def test_section_helpers_classify_polished_sections() -> None:
    pane = build_demo_gui_snapshot().detail_panes["video:/dev/video0"]
    sections = {section.title: section for section in pane.sections}

    assert section_display_title(sections["Metadata"]) == "Identity and Metadata"
    assert section_kind(sections["Capabilities"]) == "capability"
    assert section_kind(sections["Candidate Summary"]) == "candidate"
    assert section_kind(sections["Recommendation"]) == "candidate"


def test_identity_items_include_selection_kind_status_and_target() -> None:
    pane = build_demo_gui_snapshot().detail_panes["video:/dev/video0"]

    assert detail_identity_items(pane) == (
        ("Selection", "video:/dev/video0"),
        ("Kind", "video"),
        ("Status", "available"),
        ("Target", "/dev/video0"),
    )


def test_detail_helpers_do_not_execute_subprocesses(monkeypatch) -> None:
    def fail_popen(*args: object, **kwargs: object) -> None:
        raise AssertionError("detail pane helpers must not spawn subprocesses")

    monkeypatch.setattr(subprocess, "Popen", fail_popen)

    pane = build_demo_gui_snapshot().detail_panes["video:/dev/video0"]

    assert "Reachy-Style Camera" in detail_accessible_text(pane)
