"""PySide6 application launch helpers."""

from __future__ import annotations


def launch_gui(*, demo: bool = False) -> int:
    """Launch the minimal PySide6 GUI shell."""

    from PySide6.QtWidgets import QApplication

    from gst_device_explorer.gui.builders import build_media_explorer_snapshot
    from gst_device_explorer.gui.demo import build_demo_gui_snapshot
    from gst_device_explorer.gui.qt_main_window import create_main_window

    app = QApplication.instance() or QApplication([])
    if demo:
        gui_state = build_demo_gui_snapshot()
        window = create_main_window(gui_state.snapshot, gui_state.detail_panes)
    else:
        snapshot = build_media_explorer_snapshot()
        window = create_main_window(snapshot, {snapshot.detail_pane.selected_id: snapshot.detail_pane})
    window.show()
    return int(app.exec())
