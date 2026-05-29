import os
from pathlib import Path
import subprocess
import sys
import tomllib

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.cli.main import main
from gst_device_explorer.cli.parser import build_parser
from gst_device_explorer.gui.demo import DEMO_GENERATED_AT, build_demo_gui_snapshot
from gst_device_explorer.gui.qt_detail import action_display_lines
from gst_device_explorer.gui.preview_runner import PreviewState
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


def test_initial_gui_state_demo_does_not_call_live_refresh(monkeypatch) -> None:
    def fail_live_refresh(*args: object, **kwargs: object) -> None:
        raise AssertionError("demo mode must not build a live snapshot")

    monkeypatch.setattr(qt_app, "refresh_gui_snapshot", fail_live_refresh)

    state = qt_app.build_initial_gui_state(demo=True)

    assert state.snapshot.generated_at == DEMO_GENERATED_AT


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


def test_group_endpoint_action_navigates_to_endpoint_detail() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    QtWidgets = pytest.importorskip("PySide6.QtWidgets")
    QtCore = pytest.importorskip("PySide6.QtCore")
    QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    from gst_device_explorer.gui.qt_main_window import create_main_window

    demo = build_demo_gui_snapshot()
    window = create_main_window(demo.snapshot, demo.detail_panes)
    window.show()
    QtWidgets.QApplication.processEvents()

    try:
        buttons = window.findChildren(QtWidgets.QPushButton, "groupEndpointExploreButton")
        camera_button = next(button for button in buttons if button.text() == "Explore Camera")

        camera_button.click()
        QtWidgets.QApplication.processEvents()

        tree = window.findChild(QtWidgets.QTreeWidget, "sidebarTree")
        assert tree is not None
        item = tree.currentItem()
        assert item is not None
        assert item.data(0, QtCore.Qt.UserRole) == "group:demo-usb-device:video:/dev/video0"
    finally:
        window.close()
        window.deleteLater()
        _forget_pyside_modules()


def test_main_window_close_cleans_up_preview_runner() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    QtWidgets = pytest.importorskip("PySide6.QtWidgets")
    QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    from gst_device_explorer.gui.qt_main_window import create_main_window

    runner = _FakePreviewRunner()
    runner.state = PreviewState.RUNNING
    demo = build_demo_gui_snapshot()
    window = create_main_window(demo.snapshot, demo.detail_panes, preview_runner=runner)
    window.show()
    QtWidgets.QApplication.processEvents()

    try:
        window.close()
        QtWidgets.QApplication.processEvents()

        assert runner.cleanup_calls >= 1
        assert runner.state == PreviewState.EXITED
    finally:
        window.deleteLater()
        _forget_pyside_modules()


def test_main_window_refresh_cleans_up_audio_output_test_runner() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    QtWidgets = pytest.importorskip("PySide6.QtWidgets")
    QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    from gst_device_explorer.gui.qt_main_window import create_main_window

    runner = _FakePreviewRunner()
    runner.state = PreviewState.RUNNING
    demo = build_demo_gui_snapshot()

    class _Bundle:
        snapshot = demo.snapshot
        detail_panes = demo.detail_panes

    window = create_main_window(
        demo.snapshot,
        demo.detail_panes,
        refresh_builder=lambda previous_selected_id=None: _Bundle(),
        preview_runner=runner,
    )
    window.show()
    QtWidgets.QApplication.processEvents()

    try:
        window.refresh_snapshot()
        QtWidgets.QApplication.processEvents()

        assert runner.cleanup_calls >= 1
        assert runner.state == PreviewState.EXITED
    finally:
        window.close()
        window.deleteLater()
        _forget_pyside_modules()


def test_main_window_title() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    QtWidgets = pytest.importorskip("PySide6.QtWidgets")
    QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    from gst_device_explorer.gui.qt_main_window import create_main_window

    demo = build_demo_gui_snapshot()
    window = create_main_window(demo.snapshot, demo.detail_panes)

    try:
        assert window.windowTitle() == "GStreamer Device Explorer"
    finally:
        window.close()
        window.deleteLater()
        _forget_pyside_modules()


def test_non_qt_gui_imports_do_not_import_pyside6() -> None:
    assert "PySide6" not in sys.modules


def _flatten_sidebar_ids(nodes) -> list[str]:
    result: list[str] = []
    for node in nodes:
        result.append(node.id)
        result.extend(_flatten_sidebar_ids(node.children))
    return result


def test_pyside6_is_a_default_project_dependency() -> None:
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)
    deps = config["project"]["dependencies"]
    assert any("PySide6" in dep for dep in deps), "PySide6 must be in default project dependencies"
    optional_gui = config.get("project", {}).get("optional-dependencies", {}).get("gui", [])
    assert not any("PySide6" in dep for dep in optional_gui), "PySide6 should not remain in a gui optional extra"


def test_gst_device_explorer_script_points_to_gui_main() -> None:
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)
    scripts = config["project"]["scripts"]
    assert scripts.get("gst-device-explorer") == "gst_device_explorer.gui.qt_app:gui_main"


def test_gst_device_explorer_cli_script_points_to_cli_main() -> None:
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)
    scripts = config["project"]["scripts"]
    assert scripts.get("gst-device-explorer-cli") == "gst_device_explorer.cli.main:main"


def test_gui_main_launches_gui_with_no_args(monkeypatch) -> None:
    calls: list[bool] = []

    def fake_launch_gui(*, demo: bool = False) -> int:
        calls.append(demo)
        return 0

    monkeypatch.setattr(qt_app, "launch_gui", fake_launch_gui)
    monkeypatch.setattr(sys, "argv", ["gst-device-explorer"])
    with pytest.raises(SystemExit) as exc_info:
        qt_app.gui_main()
    assert exc_info.value.code == 0
    assert calls == [False]


def test_gui_main_passes_demo_flag_to_launch_gui(monkeypatch) -> None:
    calls: list[bool] = []

    def fake_launch_gui(*, demo: bool = False) -> int:
        calls.append(demo)
        return 0

    monkeypatch.setattr(qt_app, "launch_gui", fake_launch_gui)
    monkeypatch.setattr(sys, "argv", ["gst-device-explorer", "--demo"])
    with pytest.raises(SystemExit) as exc_info:
        qt_app.gui_main()
    assert exc_info.value.code == 0
    assert calls == [True]


def test_cli_main_still_dispatches_subcommands(monkeypatch) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])
    assert exc_info.value.code == 0


def _forget_pyside_modules() -> None:
    for name in tuple(sys.modules):
        if name == "PySide6" or name.startswith("PySide6."):
            sys.modules.pop(name, None)


class _FakePreviewRunner:
    def __init__(self) -> None:
        self.state = PreviewState.IDLE
        self.failure_text = None
        self.cleanup_calls = 0

    def poll(self):
        return self.state

    def cleanup(self):
        self.cleanup_calls += 1
        self.state = PreviewState.EXITED
        return self.state
