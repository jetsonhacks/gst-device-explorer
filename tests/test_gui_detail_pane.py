from dataclasses import replace
import os
from pathlib import Path
import subprocess
import sys

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.gui.builders import build_unknown_detail_pane
from gst_device_explorer.gui.builders import build_detail_pane_for_video
from gst_device_explorer.core.models import (
    CameraControl,
    CameraControlChoice,
    CameraControlSet,
    Capability,
    Device,
    DeviceProfile,
    ProfileGroupSummary,
)
from gst_device_explorer.gui.demo import build_demo_gui_snapshot
from gst_device_explorer.gui.live import build_error_detail_pane, build_empty_snapshot
from gst_device_explorer.gui.model import DetailSection
from gst_device_explorer.gui.qt_camera_controls import camera_control_group_labels, camera_control_widget_plans
from gst_device_explorer.gui.qt_camera_modes import camera_mode_tree
from gst_device_explorer.gui.qt_detail import (
    action_copy_text,
    copy_display_text,
    copyable_texts,
    detail_accessible_text,
    detail_identity_items,
    detail_tab_titles,
    device_information_accessible_text,
    explore_accessible_text,
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
    assert "Camera Explorer" in text
    assert "Selected format: MJPG" in text
    assert "Camera Modes" in text
    assert "Frame Rates" in text
    assert "Generated Pipeline" in text
    assert "gst-launch-1.0 v4l2src device=/dev/video0" in text
    assert "Dynamic V4L2 Controls" in text
    assert "brightness: type=int" in text
    assert "exposure_auto: type=menu" in text
    assert "Manual Mode" in text
    assert "Identity and Metadata" in text
    assert "Capabilities" in text
    assert "Candidate Pipelines" in text
    assert "Recommended Candidate" in text


def test_selected_detail_pane_has_explore_and_device_information_tabs() -> None:
    pane = build_demo_gui_snapshot().detail_panes["video:/dev/video0"]

    assert detail_tab_titles(pane) == ("Explore", "Device Information")


def test_camera_explore_tab_contains_camera_explorer_not_report_sections() -> None:
    pane = build_demo_gui_snapshot().detail_panes["video:/dev/video0"]
    text = explore_accessible_text(pane)

    assert text.startswith("Explore\n")
    assert "Reachy-Style Camera - /dev/video0" in text
    assert "Driver: uvcvideo" in text
    assert "Camera Mode" in text
    assert "Pixel Format" in text
    assert "Image Size" in text
    assert "Frame Rate" in text
    assert "Selected" in text
    assert "Selected: MJPG, 640x480, 30 fps" in text
    assert "Generated Pipeline" in text
    assert "gst-launch-1.0 v4l2src device=/dev/video0" in text
    assert "Copy Pipeline" in text
    assert "Camera Controls" in text
    assert "Brightness" in text
    assert "Current: 140" in text
    assert text.index("Camera Mode") < text.index("Generated Pipeline")
    assert text.index("Selected: MJPG, 640x480, 30 fps") < text.index("Generated Pipeline")
    assert text.index("Generated Pipeline") < text.index("Camera Controls")
    assert "Camera Explorer" not in text
    assert "Camera Summary" not in text
    assert "Identity and Metadata" not in text
    assert "Candidate Pipelines" not in text
    assert "Safe Actions" not in text
    assert "Preview Deferred" not in text


def test_camera_explorer_widget_uses_mode_and_frame_rate_labels() -> None:
    widget, QtWidgets = _camera_explorer_widget()

    try:
        group_titles = {group.title() for group in widget.findChildren(QtWidgets.QGroupBox)}
        labels = {label.text() for label in widget.findChildren(QtWidgets.QLabel)}

        assert "Camera Mode" in group_titles
        assert "Camera Settings" not in group_titles
        assert "Frame Rate" in labels
        assert "Frame Duration / FPS" not in labels
    finally:
        widget.deleteLater()
        _forget_pyside_modules()


def test_camera_pipeline_widget_is_read_only_code_and_copyable() -> None:
    statuses: list[str] = []
    widget, QtWidgets = _camera_explorer_widget(status_callback=statuses.append)

    try:
        pipeline = widget.findChild(QtWidgets.QLineEdit, "cameraPipelineText")
        copy_button = widget.findChild(QtWidgets.QPushButton, "cameraPipelineCopyButton")

        assert pipeline is not None
        assert copy_button is not None
        assert pipeline.isReadOnly()
        assert pipeline.property("presentation") == "code"
        assert pipeline.font().fixedPitch()

        copy_button.click()

        assert statuses == ["Copied to clipboard."]
        assert copy_button.text() == "Copied"
    finally:
        widget.deleteLater()
        _forget_pyside_modules()


def test_long_camera_pipeline_keeps_copy_button_visible() -> None:
    widget, QtWidgets = _camera_explorer_widget(pane=_detail_with_long_pipeline())
    widget.resize(420, 320)
    widget.show()
    QtWidgets.QApplication.processEvents()

    try:
        pipeline = widget.findChild(QtWidgets.QLineEdit, "cameraPipelineText")
        copy_button = widget.findChild(QtWidgets.QPushButton, "cameraPipelineCopyButton")

        assert pipeline is not None
        assert copy_button is not None
        assert pipeline.width() > 0
        assert copy_button.width() > 0
        assert copy_button.geometry().right() <= widget.width()
        assert copy_button.isVisible()
    finally:
        widget.deleteLater()
        _forget_pyside_modules()


def test_camera_explore_header_uses_group_derived_display_name() -> None:
    pane = build_detail_pane_for_video(
        Device(
            id="/dev/video0",
            kind="video_input",
            name="video0",
            metadata={"path": "/dev/video0"},
            capabilities=[_video_capability("MJPG", "Motion-JPEG", 640, 480, [30.0])],
        ),
        profile=DeviceProfile(
            device_kind="video",
            device="/dev/video0",
            display_name="video0",
            groups=(
                ProfileGroupSummary(
                    group_id="usb-device",
                    label="Reachy Mini",
                    confidence=0.95,
                    kind="usb",
                    member_count=3,
                ),
            ),
        ),
    )

    assert pane.title == "Reachy Mini Camera"
    assert "Reachy Mini Camera - /dev/video0" in explore_accessible_text(pane)


def test_camera_mode_tree_contains_all_demo_modes_by_format_and_size() -> None:
    pane = build_demo_gui_snapshot().detail_panes["video:/dev/video0"]

    assert camera_mode_tree(pane) == {
        "MJPG": {
            "640x480": ("30 fps", "15 fps"),
        },
        "YUYV": {
            "1280x720": ("30 fps",),
        },
    }


def test_camera_mode_tree_prefers_raw_reachy_camera_capabilities() -> None:
    pane = build_detail_pane_for_video(
        _reachy_camera(),
        control_set=_reachy_controls(),
    )
    text = explore_accessible_text(pane)

    assert camera_mode_tree(pane) == {
        "MJPG": {
            "3840x2592": ("30 fps",),
            "1920x1080": ("60 fps",),
            "3840x2160": ("30 fps",),
            "3264x2448": ("30 fps",),
        },
        "YUYV": {
            "3840x2592": ("1 fps",),
            "1920x1080": ("5 fps",),
            "3840x2160": ("1 fps",),
            "3264x2448": ("1 fps",),
        },
    }
    assert "MJPG (Motion-JPEG, compressed)" in text
    assert "YUYV (YUYV 4:2:2)" in text
    assert "MJPG, 3840x2592, 30 fps" in text
    assert "640x480" not in text


def test_camera_controls_use_raw_reachy_control_set() -> None:
    pane = build_detail_pane_for_video(
        _reachy_camera(),
        control_set=_reachy_controls(),
    )
    text = explore_accessible_text(pane)
    plans = {plan.name: plan for plan in camera_control_widget_plans(pane)}

    assert "Power Line Frequency" in text
    assert "Current: 60 Hz" in text
    assert "Choices: Disabled, 50 Hz, 60 Hz" in text
    assert "White Balance Temperature" in text
    assert "Range: 2800 to 6500, step 1" in text
    assert "Default: 4600" in text
    assert "Flags: inactive" in text
    assert "Inactive for the current camera mode or auto setting." in text
    assert "power_line_frequency: type=menu" not in text
    assert "synthetic_control" not in text
    assert plans["power_line_frequency"].widget_kind == "combo"
    assert plans["power_line_frequency"].choices == (
        ("0", "Disabled"),
        ("1", "50 Hz"),
        ("2", "60 Hz"),
    )
    assert plans["power_line_frequency"].current_label == "60 Hz"
    assert plans["white_balance_temperature"].widget_kind == "slider_spin"
    assert plans["white_balance_temperature"].minimum == 2800
    assert plans["white_balance_temperature"].maximum == 6500
    assert plans["white_balance_temperature"].step == 1
    assert plans["white_balance_temperature"].inactive
    assert plans["white_balance_temperature_auto"].widget_kind == "checkbox"
    assert plans["white_balance_temperature_auto"].current_value == "1"
    assert plans["white_balance_temperature_auto"].current_label == "On"
    assert camera_control_group_labels(pane) == ("White Balance", "Advanced")


def test_camera_controls_group_common_controls_in_expected_order() -> None:
    pane = build_detail_pane_for_video(
        _camera_with_grouped_controls(),
        control_set=_grouped_controls(),
    )
    plans = {plan.name: plan for plan in camera_control_widget_plans(pane)}

    assert camera_control_group_labels(pane) == (
        "Image Adjustment",
        "Exposure & Gain",
        "White Balance",
        "Advanced",
    )
    assert plans["brightness"].group == "Image Adjustment"
    assert plans["exposure_time_absolute"].group == "Exposure & Gain"
    assert plans["white_balance_temperature"].group == "White Balance"
    assert plans["power_line_frequency"].group == "Advanced"


def test_camera_control_widget_renders_group_headers_and_keeps_controls() -> None:
    pane = build_detail_pane_for_video(
        _camera_with_grouped_controls(),
        control_set=_grouped_controls(),
    )
    widget, QtWidgets = _camera_explorer_widget(pane=pane)

    try:
        headers = [
            label.text()
            for label in widget.findChildren(QtWidgets.QLabel, "cameraControlGroupHeader")
        ]
        rows = {
            row.property("controlName"): row
            for row in widget.findChildren(QtWidgets.QWidget)
            if row.property("controlName")
        }

        assert headers == [
            "Image Adjustment",
            "Exposure & Gain",
            "White Balance",
            "Advanced",
        ]
        assert {
            "brightness",
            "exposure_time_absolute",
            "white_balance_temperature",
            "power_line_frequency",
        } <= set(rows)
    finally:
        widget.deleteLater()
        _forget_pyside_modules()


def test_inactive_camera_control_row_is_muted_and_non_interactive() -> None:
    pane = build_detail_pane_for_video(
        _reachy_camera(),
        control_set=_reachy_controls(),
    )
    widget, QtWidgets = _camera_explorer_widget(pane=pane)

    try:
        inactive_row = widget.findChild(QtWidgets.QWidget, "cameraControlRow_white_balance_temperature")
        active_row = widget.findChild(QtWidgets.QWidget, "cameraControlRow_power_line_frequency")

        assert inactive_row is not None
        assert active_row is not None
        assert inactive_row.property("inactive") is True
        assert active_row.property("inactive") is False

        inactive_label = inactive_row.findChild(QtWidgets.QLabel, "cameraControlLabel")
        inactive_default = inactive_row.findChild(QtWidgets.QPushButton, "cameraControlDefaultButton")
        inactive_spin = inactive_row.findChild(QtWidgets.QSpinBox, "cameraControlIntegerValue")
        active_label = active_row.findChild(QtWidgets.QLabel, "cameraControlLabel")

        assert inactive_label is not None
        assert inactive_default is not None
        assert inactive_spin is not None
        assert active_label is not None
        assert inactive_label.text() == "White Balance Temperature"
        assert inactive_label.isEnabled()
        assert inactive_label.property("inactive") is True
        assert "#6b7280" in inactive_label.styleSheet()
        assert inactive_row.findChild(QtWidgets.QLabel, "cameraControlInactiveStatus") is None
        assert not inactive_default.isEnabled()
        assert inactive_default.text() == "Default"
        assert inactive_default.minimumWidth() >= 76
        assert inactive_default.property("inactive") is True
        assert "#6b7280" in inactive_default.styleSheet()
        assert not inactive_spin.isEnabled()
        assert active_label.isEnabled()
    finally:
        widget.deleteLater()
        _forget_pyside_modules()


def test_camera_control_rows_are_bounded_at_reduced_width() -> None:
    pane = build_detail_pane_for_video(
        _camera_with_grouped_controls(),
        control_set=_grouped_controls(),
    )
    widget, QtWidgets = _camera_explorer_widget(pane=pane)
    widget.resize(520, 520)
    widget.show()
    QtWidgets.QApplication.processEvents()

    try:
        rows = [
            row
            for row in widget.findChildren(QtWidgets.QWidget)
            if row.objectName().startswith("cameraControlRow_")
        ]

        assert rows
        assert all(row.maximumWidth() == 760 for row in rows)
        assert all(row.width() <= widget.width() for row in rows)
    finally:
        widget.deleteLater()
        _forget_pyside_modules()


def test_checkbox_camera_control_keeps_default_button_attached() -> None:
    pane = build_detail_pane_for_video(
        _reachy_camera(),
        control_set=_reachy_controls(),
    )
    widget, QtWidgets = _camera_explorer_widget(pane=pane)
    widget.resize(760, 520)
    widget.show()
    QtWidgets.QApplication.processEvents()

    try:
        row = widget.findChild(QtWidgets.QWidget, "cameraControlRow_white_balance_temperature_auto")

        assert row is not None
        checkbox = row.findChild(QtWidgets.QCheckBox, "cameraControlCheckbox")
        default_button = row.findChild(QtWidgets.QPushButton, "cameraControlDefaultButton")

        assert checkbox is not None
        assert default_button is not None
        assert checkbox.maximumWidth() == 36
        assert default_button.geometry().left() - checkbox.geometry().right() <= 18
    finally:
        widget.deleteLater()
        _forget_pyside_modules()


def test_device_information_tab_contains_report_sections_not_camera_explorer() -> None:
    pane = build_demo_gui_snapshot().detail_panes["video:/dev/video0"]
    text = device_information_accessible_text(pane)

    assert text.startswith("Device Information\n")
    assert "Identity" in text
    assert "Summary" in text
    assert "Identity and Metadata" in text
    assert "Capabilities" in text
    assert "Candidate Pipelines" in text
    assert "Recommended Candidate" in text
    assert "Copy" in text
    assert "Safe Actions" in text
    assert "Camera Explorer" not in text
    assert "Dynamic V4L2 Controls" not in text


def test_non_camera_explore_tabs_are_lightweight_placeholders() -> None:
    demo = build_demo_gui_snapshot()
    group_text = explore_accessible_text(demo.detail_panes["group:demo-usb-device"])
    input_text = explore_accessible_text(demo.detail_panes["audio_input:hw:2,0"])
    output_text = explore_accessible_text(demo.detail_panes["audio_output:hw:2,0"])

    assert "Group exploration dashboard is deferred." in group_text
    assert "Select an endpoint in the sidebar to explore it directly." in group_text
    assert "Audio input exploration controls are deferred." in input_text
    assert "Audio output exploration controls are deferred." in output_text
    assert "Candidate Pipelines" not in input_text
    assert "Recommended Candidate" not in output_text


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
    assert any("gst-launch-1.0 v4l2src device=/dev/video0" in value for value in copyables.values())
    assert any("gst-device-explorer" in value for value in copyables.values())


def test_action_copy_text_uses_suggested_command_only() -> None:
    pane = build_demo_gui_snapshot().detail_panes["video:/dev/video0"]
    dry_run = next(action for action in pane.actions if action.kind == "dry_run")
    preview = next(action for action in pane.actions if action.kind == "preview")
    copy_pipeline = next(action for action in pane.actions if action.kind == "copy_pipeline")

    assert action_copy_text(dry_run) == "gst-device-explorer run video /dev/video0 --dry-run"
    assert action_copy_text(preview) is None
    assert action_copy_text(copy_pipeline).startswith("gst-launch-1.0 v4l2src device=/dev/video0")


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


def _camera_explorer_widget(*, pane=None, status_callback=None):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    QtWidgets = pytest.importorskip("PySide6.QtWidgets")
    QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    from gst_device_explorer.gui.qt_camera_explorer import create_camera_explorer_widget

    detail = pane or build_demo_gui_snapshot().detail_panes["video:/dev/video0"]
    return create_camera_explorer_widget(detail, status_callback=status_callback), QtWidgets


def _detail_with_long_pipeline():
    pane = build_demo_gui_snapshot().detail_panes["video:/dev/video0"]
    long_pipeline = (
        "gst-launch-1.0 v4l2src device=/dev/video0 ! "
        "image/jpeg,width=3840,height=2160,framerate=60/1 ! "
        "jpegdec ! videoconvert ! videoscale ! "
        "queue max-size-buffers=2 leaky=downstream ! "
        "autovideosink sync=false"
    )
    return replace(
        pane,
        sections=tuple(
            DetailSection(section.title, (long_pipeline,))
            if section.title == "Generated Pipeline"
            else section
            for section in pane.sections
        ),
    )


def _camera_with_grouped_controls() -> Device:
    return Device(
        id="/dev/video0",
        kind="video_input",
        name="Grouped Control Camera",
        metadata={"path": "/dev/video0"},
        capabilities=[_video_capability("MJPG", "Motion-JPEG", 640, 480, [30.0])],
    )


def _grouped_controls() -> CameraControlSet:
    return CameraControlSet(
        device_path="/dev/video0",
        source="v4l2-ctl",
        controls=(
            CameraControl(
                name="brightness",
                label="Brightness",
                control_type="int",
                device_path="/dev/video0",
                current_value="140",
                default_value="128",
                minimum="0",
                maximum="255",
                step="1",
            ),
            CameraControl(
                name="exposure_time_absolute",
                label="Exposure Time Absolute",
                control_type="int",
                device_path="/dev/video0",
                current_value="156",
                default_value="156",
                minimum="1",
                maximum="5000",
                step="1",
            ),
            CameraControl(
                name="white_balance_temperature",
                label="White Balance Temperature",
                control_type="int",
                device_path="/dev/video0",
                current_value="4600",
                default_value="4600",
                minimum="2800",
                maximum="6500",
                step="1",
            ),
            CameraControl(
                name="power_line_frequency",
                label="Power Line Frequency",
                control_type="menu",
                device_path="/dev/video0",
                current_value="2",
                default_value="1",
                choices=(
                    CameraControlChoice(value="0", label="Disabled"),
                    CameraControlChoice(value="1", label="50 Hz"),
                    CameraControlChoice(value="2", label="60 Hz"),
                ),
            ),
        ),
    )


def _forget_pyside_modules() -> None:
    for name in tuple(sys.modules):
        if name == "PySide6" or name.startswith("PySide6."):
            sys.modules.pop(name, None)


def _reachy_camera() -> Device:
    return Device(
        id="/dev/video0",
        kind="video_input",
        name="Reachy Mini Camera",
        metadata={"path": "/dev/video0", "driver": "uvcvideo", "bus": "usb-a80aa10000.usb-4.1.4"},
        capabilities=[
            _video_capability("MJPG", "Motion-JPEG, compressed", 3840, 2592, [30.0]),
            _video_capability("MJPG", "Motion-JPEG, compressed", 1920, 1080, [60.0]),
            _video_capability("MJPG", "Motion-JPEG, compressed", 3840, 2160, [30.0]),
            _video_capability("MJPG", "Motion-JPEG, compressed", 3264, 2448, [30.0]),
            _video_capability("YUYV", "YUYV 4:2:2", 3840, 2592, [1.0]),
            _video_capability("YUYV", "YUYV 4:2:2", 1920, 1080, [5.0]),
            _video_capability("YUYV", "YUYV 4:2:2", 3840, 2160, [1.0]),
            _video_capability("YUYV", "YUYV 4:2:2", 3264, 2448, [1.0]),
        ],
    )


def _video_capability(
    pixel_format: str,
    description: str,
    width: int,
    height: int,
    fps: list[float],
) -> Capability:
    return Capability(
        name="video_format",
        values={
            "device_path": "/dev/video0",
            "media_type": "video",
            "pixel_format": pixel_format,
            "description": description,
            "width": width,
            "height": height,
            "fps": fps,
        },
        source="v4l2-ctl",
    )


def _reachy_controls() -> CameraControlSet:
    return CameraControlSet(
        device_path="/dev/video0",
        source="v4l2-ctl",
        controls=(
            CameraControl(
                name="power_line_frequency",
                label="Power Line Frequency",
                control_type="menu",
                device_path="/dev/video0",
                current_value="2",
                default_value="1",
                minimum="0",
                maximum="2",
                choices=(
                    CameraControlChoice(value="0", label="Disabled"),
                    CameraControlChoice(value="1", label="50 Hz"),
                    CameraControlChoice(value="2", label="60 Hz"),
                ),
            ),
            CameraControl(
                name="white_balance_temperature",
                label="White Balance Temperature",
                control_type="int",
                device_path="/dev/video0",
                current_value="4600",
                default_value="4600",
                minimum="2800",
                maximum="6500",
                step="1",
                flags=("inactive",),
            ),
            CameraControl(
                name="white_balance_temperature_auto",
                label="White Balance Temperature Auto",
                control_type="bool",
                device_path="/dev/video0",
                current_value="1",
                default_value="1",
            ),
        ),
    )
