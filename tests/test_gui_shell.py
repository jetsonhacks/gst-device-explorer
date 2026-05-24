from pathlib import Path
import subprocess
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.cli.main import main
from gst_device_explorer.cli.parser import build_parser
from gst_device_explorer.gui.demo import DEMO_GENERATED_AT, build_demo_gui_snapshot
from gst_device_explorer.gui.qt_detail import action_display_lines
import gst_device_explorer.gui.qt_app as qt_app


def test_parser_accepts_gui_command_and_demo_flag() -> None:
    args = build_parser().parse_args(["gui", "--demo"])

    assert args.command == "gui"
    assert args.demo is True


def test_gui_command_dispatches_to_lazy_launcher(monkeypatch) -> None:
    calls: list[bool] = []

    def fake_launch_gui(*, demo: bool = False) -> int:
        calls.append(demo)
        return 0

    monkeypatch.setattr(qt_app, "launch_gui", fake_launch_gui)

    assert main(["gui", "--demo"]) == 0
    assert calls == [True]


def test_demo_snapshot_is_deterministic() -> None:
    first = build_demo_gui_snapshot()
    second = build_demo_gui_snapshot()

    assert first.snapshot == second.snapshot
    assert first.detail_panes == second.detail_panes
    assert first.snapshot.generated_at == DEMO_GENERATED_AT


def test_demo_snapshot_contains_grouped_and_standalone_sidebar_nodes() -> None:
    demo = build_demo_gui_snapshot()
    ids = _flatten_sidebar_ids(demo.snapshot.sidebar_roots)

    assert "group:demo-usb-device" in ids
    assert "group:demo-usb-device:video:/dev/video0" in ids
    assert "group:demo-usb-device:audio_input:hw:2,0" in ids
    assert "group:demo-usb-device:audio_output:hw:2,0" in ids
    assert "video:/dev/video2" in ids


def test_demo_detail_pane_mapping_updates_for_group_child_selection() -> None:
    demo = build_demo_gui_snapshot()

    assert demo.detail_panes["group:demo-usb-device"].kind == "group"
    assert demo.detail_panes["group:demo-usb-device:video:/dev/video0"].kind == "video"
    assert demo.detail_panes["group:demo-usb-device:audio_input:hw:2,0"].kind == "audio_input"
    assert demo.detail_panes["group:demo-usb-device:audio_output:hw:2,0"].kind == "audio_output"


def test_action_display_lines_are_metadata_only() -> None:
    demo = build_demo_gui_snapshot()
    pane = demo.detail_panes["video:/dev/video2"]
    preview = next(action for action in pane.actions if action.kind == "preview")
    lines = action_display_lines(preview)

    assert "safety: safe_execution" in lines
    assert "enabled: False" in lines
    assert "disabled: No available generated candidate is known yet." in lines


def test_gui_demo_building_does_not_execute_subprocesses(monkeypatch) -> None:
    def fail_popen(*args: object, **kwargs: object) -> None:
        raise AssertionError("GUI demo snapshot must not spawn subprocesses")

    monkeypatch.setattr(subprocess, "Popen", fail_popen)

    demo = build_demo_gui_snapshot()

    assert demo.snapshot.detail_pane.kind == "group"


def test_non_qt_gui_imports_do_not_import_pyside6() -> None:
    assert "PySide6" not in sys.modules


def _flatten_sidebar_ids(nodes) -> list[str]:
    result: list[str] = []
    for node in nodes:
        result.append(node.id)
        result.extend(_flatten_sidebar_ids(node.children))
    return result
