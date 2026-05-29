"""PySide6 application launch helpers."""

from __future__ import annotations

from gst_device_explorer.gui.demo import build_demo_gui_snapshot
from gst_device_explorer.gui.live import build_live_gui_snapshot, refresh_gui_snapshot
import gst_device_explorer.probes.v4l2 as v4l2_probe


def gui_main() -> None:
    """Console script entry point: launch the GUI, optionally in demo mode."""

    import argparse
    import sys

    parser = argparse.ArgumentParser(
        prog="gst-device-explorer",
        description="GStreamer device explorer.",
    )
    parser.add_argument("--demo", action="store_true", help="Launch with synthetic demo devices.")
    args = parser.parse_args()
    sys.exit(launch_gui(demo=args.demo))


def launch_gui(*, demo: bool = False) -> int:
    """Launch the minimal PySide6 GUI shell."""

    from PySide6.QtWidgets import QApplication

    from gst_device_explorer.gui.camera_control_writer import CameraControlWriter
    from gst_device_explorer.gui.qt_main_window import create_main_window

    app = QApplication.instance() or QApplication([])
    gui_state = build_initial_gui_state(demo=demo)
    window = create_main_window(
        gui_state.snapshot,
        gui_state.detail_panes,
        refresh_builder=_refresh_builder(demo=demo),
        camera_control_writer=None if demo else CameraControlWriter(),
        camera_control_refresher=None if demo else v4l2_probe.discover_v4l2_controls,
    )
    window.show()
    return int(app.exec())


def build_initial_gui_state(*, demo: bool = False):
    """Build the initial GUI state without importing Qt."""

    if demo:
        return build_demo_gui_snapshot()
    return refresh_gui_snapshot(builder=build_live_gui_snapshot)


def _refresh_builder(*, demo: bool = False):
    if demo:
        return lambda previous_selected_id=None: build_demo_gui_snapshot()
    return lambda previous_selected_id=None: refresh_gui_snapshot(
        builder=build_live_gui_snapshot,
        previous_selected_id=previous_selected_id,
    )
