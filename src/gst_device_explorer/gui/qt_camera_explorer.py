"""Camera-specific Qt exploration widgets."""

from __future__ import annotations

from collections.abc import Callable

from gst_device_explorer.gui.model import DetailPaneModel, DetailSection
from gst_device_explorer.gui.qt_camera_controls import (
    camera_control_accessible_lines,
    create_camera_controls_widget,
)
from gst_device_explorer.gui.qt_camera_modes import (
    camera_pipeline_argv_for_selection,
    camera_mode_tree,
    camera_pipeline_for_selection,
    camera_section,
    format_labels,
    initial_selected_mode,
    selected_mode_text,
)
from gst_device_explorer.gui.qt_camera_preview import create_camera_preview_widget
from gst_device_explorer.gui.qt_sections import (
    copy_to_clipboard,
    create_text_label,
    target_from_summary,
)
from gst_device_explorer.gui.preview_runner import PreviewCommand

CAMERA_MODE_SECTION_TITLE = "Camera Mode"
CAMERA_FRAME_RATE_LABEL = "Frame Rate"

CAMERA_EXPLORE_SECTION_TITLES = frozenset(
    {
        "Camera Explorer",
        "Camera Modes",
        "Frame Rates",
        "Generated Pipeline",
        "Raw Camera Capabilities",
        "V4L2 Controls",
    }
)


def has_camera_explorer(detail: DetailPaneModel) -> bool:
    return detail.kind == "video" and camera_section(detail, "Generated Pipeline") is not None


def is_camera_explore_section(detail: DetailPaneModel, section: DetailSection) -> bool:
    return detail.kind == "video" and section.title in CAMERA_EXPLORE_SECTION_TITLES


def camera_explore_lines(detail: DetailPaneModel) -> tuple[str, ...]:
    lines: list[str] = [_camera_header_text(detail)]
    subheader = _camera_subheader_text(detail)
    if subheader:
        lines.append(subheader)
    lines.append(CAMERA_MODE_SECTION_TITLE)
    lines.extend(("Pixel Format", "Image Size", CAMERA_FRAME_RATE_LABEL))
    labels = format_labels(detail)
    lines.extend(labels.get(pixel_format, pixel_format) for pixel_format in camera_mode_tree(detail))
    for section in detail.sections:
        if section.title in {"Camera Modes", "Frame Rates"}:
            lines.extend(section.items)
    selected = initial_selected_mode(detail)
    if selected is not None:
        lines.append("Selected")
        lines.append(f"Selected: {selected_mode_text(*selected)}")
    lines.append("Generated Pipeline")
    pipeline = _pipeline_text(detail)
    if pipeline is not None:
        lines.append(pipeline)
    lines.append("Copy Pipeline")
    lines.append("Preview")
    if _preview_available(detail) and initial_selected_mode(detail) is not None:
        lines.extend(("State: Ready", "Start Preview", "Stop Preview"))
    else:
        lines.extend(("State: Unavailable", "Preview unavailable: no eligible generated camera preview candidate."))
    lines.append("Camera Controls")
    lines.extend(camera_control_accessible_lines(detail))
    return tuple(lines)


def create_camera_explorer_widget(
    detail: DetailPaneModel,
    *,
    status_callback: Callable[[str], None] | None = None,
    preview_runner: object | None = None,
) -> object:
    from PySide6.QtGui import QFont, QFontDatabase
    from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget
    from PySide6.QtWidgets import QListWidgetItem, QPushButton, QSizePolicy, QVBoxLayout, QWidget
    from PySide6.QtCore import Qt

    pane = QWidget()
    pane.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    layout = QVBoxLayout(pane)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)

    layout.addWidget(_camera_header_widget(detail))

    mode_tree = camera_mode_tree(detail)

    def _list_column(title: str) -> tuple[object, object]:
        col = QVBoxLayout()
        col.setSpacing(4)
        from PySide6.QtWidgets import QLabel

        label = QLabel(title)
        col.addWidget(label)
        lst = QListWidget()
        lst.setObjectName(
            {
                "Pixel Format": "cameraPixelFormatList",
                "Image Size": "cameraImageSizeList",
                CAMERA_FRAME_RATE_LABEL: "cameraFrameRateList",
            }[title]
        )
        lst.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        lst.setMinimumHeight(58)
        lst.setMaximumHeight(104)
        col.addWidget(lst)
        return col, lst

    settings_box = QGroupBox(CAMERA_MODE_SECTION_TITLE)
    settings_outer = QVBoxLayout(settings_box)
    settings_outer.setSpacing(6)
    settings_layout = QHBoxLayout()
    settings_layout.setSpacing(8)

    fmt_col, fmt_list = _list_column("Pixel Format")
    res_col, res_list = _list_column("Image Size")
    rate_col, rate_list = _list_column(CAMERA_FRAME_RATE_LABEL)

    labels = format_labels(detail)
    for fmt in mode_tree:
        item = QListWidgetItem(labels.get(fmt, fmt))
        item.setData(Qt.UserRole, fmt)
        fmt_list.addItem(item)
    if not mode_tree:
        fmt_list.addItem("Unavailable")
        fmt_list.setEnabled(False)

    settings_layout.addLayout(fmt_col, 1)
    settings_layout.addLayout(res_col, 1)
    settings_layout.addLayout(rate_col, 1)
    settings_outer.addLayout(settings_layout)
    initial_mode = initial_selected_mode(detail)
    selected_mode_label = create_text_label(
        "Selected: "
        + (selected_mode_text(*initial_mode) if initial_mode else "No supported camera mode selected.")
    )
    selected_mode_label.setObjectName("cameraSelectedModeText")
    settings_outer.addWidget(selected_mode_label)
    layout.addWidget(settings_box, 0)

    pipeline = _pipeline_text(detail)
    pipeline_box = QGroupBox("Generated Pipeline")
    pipeline_box_layout = QVBoxLayout(pipeline_box)
    pipeline_row = QHBoxLayout()
    pipeline_row.setSpacing(6)
    pipeline_edit = QLineEdit(pipeline or "Pipeline unavailable for this camera mode.")
    pipeline_edit.setReadOnly(True)
    pipeline_edit.setObjectName("cameraPipelineText")
    pipeline_edit.setProperty("presentation", "code")
    pipeline_font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
    pipeline_font.setStyleHint(QFont.Monospace)
    pipeline_font.setFixedPitch(True)
    pipeline_edit.setFont(pipeline_font)
    pipeline_edit.setMinimumWidth(0)
    pipeline_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    pipeline_edit.setStyleSheet(
        "QLineEdit#cameraPipelineText {"
        "font-family: monospace;"
        "padding: 3px 6px;"
        "}"
    )
    pipeline_edit.setCursorPosition(0)
    pipeline_row.addWidget(pipeline_edit, 1)
    copy_btn = _copy_dynamic_button(
        "Copy Pipeline",
        pipeline_edit.text,
        status_callback=status_callback,
    )
    copy_btn.setEnabled(bool(pipeline))
    pipeline_row.addWidget(copy_btn)
    pipeline_box_layout.addLayout(pipeline_row)
    layout.addWidget(pipeline_box, 0)

    def current_preview_command() -> PreviewCommand | None:
        if not _preview_available(detail):
            return None
        rate_item = rate_list.currentItem()
        res_item = res_list.currentItem()
        fmt_item = fmt_list.currentItem()
        fmt = fmt_item.data(Qt.UserRole) if fmt_item else "Unavailable"
        resolution = res_item.text() if res_item else "Unavailable"
        frame_rate = rate_item.text() if rate_item else "Unavailable"
        argv = camera_pipeline_argv_for_selection(detail, str(fmt), resolution, frame_rate)
        target = target_from_summary(detail)
        if argv is None or target is None:
            return None
        return PreviewCommand(
            argv,
            target=target,
            description=f"Preview {selected_mode_text(str(fmt), resolution, frame_rate)}",
        )

    preview_widget, update_preview_state = create_camera_preview_widget(
        current_preview_command,
        preview_runner=preview_runner,
    )
    layout.addWidget(preview_widget, 0)

    def update_pipeline() -> None:
        rate_item = rate_list.currentItem()
        res_item = res_list.currentItem()
        fmt_item = fmt_list.currentItem()
        fmt = fmt_item.data(Qt.UserRole) if fmt_item else "Unavailable"
        resolution = res_item.text() if res_item else "Unavailable"
        frame_rate = rate_item.text() if rate_item else "Unavailable"
        generated = camera_pipeline_for_selection(
            detail,
            str(fmt),
            resolution,
            frame_rate,
        )
        if generated:
            selected_mode_label.setText(f"Selected: {selected_mode_text(str(fmt), resolution, frame_rate)}")
        else:
            selected_mode_label.setText("Selected: No supported camera mode selected.")
        pipeline_edit.setText(generated or "Pipeline unavailable for this camera mode.")
        pipeline_edit.setCursorPosition(0)
        copy_btn.setEnabled(bool(generated))
        update_preview_state()

    def update_rates() -> None:
        res_item = res_list.currentItem()
        fmt_item = fmt_list.currentItem()
        resolution = res_item.text() if res_item else ""
        fmt = str(fmt_item.data(Qt.UserRole)) if fmt_item else ""
        rates = mode_tree.get(fmt, {}).get(resolution, ())
        rate_list.clear()
        for rate in rates:
            rate_list.addItem(rate)
        if not rates:
            rate_list.addItem("Unavailable")
            rate_list.setEnabled(False)
        else:
            rate_list.setEnabled(True)
            rate_list.setCurrentRow(0)
        update_pipeline()

    def update_resolutions() -> None:
        fmt_item = fmt_list.currentItem()
        fmt = str(fmt_item.data(Qt.UserRole)) if fmt_item else ""
        resolutions = tuple(mode_tree.get(fmt, {}))
        res_list.clear()
        for res in resolutions:
            res_list.addItem(res)
        if not resolutions:
            res_list.addItem("Unavailable")
            res_list.setEnabled(False)
        else:
            res_list.setEnabled(True)
            res_list.setCurrentRow(0)
        update_rates()

    fmt_list.currentItemChanged.connect(lambda _cur, _prev: update_resolutions())
    res_list.currentItemChanged.connect(lambda _cur, _prev: update_rates())
    rate_list.currentItemChanged.connect(lambda _cur, _prev: update_pipeline())

    if fmt_list.count() > 0 and fmt_list.isEnabled():
        fmt_list.setCurrentRow(0)
    update_preview_state()

    layout.addWidget(create_camera_controls_widget(detail), 1)
    return pane


def _camera_header_widget(detail: DetailPaneModel) -> object:
    from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

    header = QWidget()
    layout = QVBoxLayout(header)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(2)
    title = QLabel(_camera_header_text(detail))
    title.setObjectName("cameraHeaderTitle")
    layout.addWidget(title)
    subheader = _camera_subheader_text(detail)
    if subheader:
        layout.addWidget(create_text_label(subheader))
    return header


def _camera_header_text(detail: DetailPaneModel) -> str:
    device_path = target_from_summary(detail)
    if device_path:
        return f"{detail.title} - {device_path}"
    return detail.title


def _camera_subheader_text(detail: DetailPaneModel) -> str:
    parts = []
    metadata = _metadata_values(detail)
    driver = metadata.get("driver")
    if driver:
        parts.append(f"Driver: {driver}")
    groups = camera_section(detail, "Groups")
    if groups is not None and groups.items:
        group_label = groups.items[0].split(" (", 1)[0]
        parts.append(f"Group: {group_label}")
    return " - ".join(parts)


def _camera_summary_lines(detail: DetailPaneModel) -> tuple[str, ...]:
    rows = [f"Name: {detail.title}"]
    device_path = target_from_summary(detail)
    if device_path:
        rows.append(f"Device path: {device_path}")
    metadata = _metadata_values(detail)
    driver = metadata.get("driver")
    if driver:
        rows.append(f"Driver: {driver}")
    bus = metadata.get("bus")
    if bus:
        rows.append(f"Bus: {bus}")
    groups = camera_section(detail, "Groups")
    if groups is not None and groups.items:
        rows.append(f"Group: {groups.items[0]}")
    return tuple(rows)


def _metadata_values(detail: DetailPaneModel) -> dict[str, str]:
    section = camera_section(detail, "Metadata")
    if section is None:
        return {}
    result: dict[str, str] = {}
    for item in section.items:
        if ": " in item:
            key, value = item.split(": ", 1)
            result[key] = value
    return result


def _copy_dynamic_button(
    label: str,
    text_getter: Callable[[], str],
    *,
    status_callback: Callable[[str], None] | None = None,
) -> object:
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QPushButton, QSizePolicy

    button = QPushButton(label)
    button.setObjectName("cameraPipelineCopyButton")
    button.setToolTip(label)
    button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    original_label = label

    def _copy(_checked: bool = False) -> None:
        copy_to_clipboard(
            text_getter(),
            status_callback=status_callback,
        )
        button.setText("Copied")
        button.setToolTip("Copied")
        QTimer.singleShot(1200, lambda: _reset_copy_button(button, original_label))

    button.clicked.connect(_copy)
    return button


def _reset_copy_button(button: object, label: str) -> None:
    try:
        button.setText(label)
        button.setToolTip(label)
    except RuntimeError:
        pass


def _pipeline_text(detail: DetailPaneModel) -> str | None:
    section = camera_section(detail, "Generated Pipeline")
    if section is None or not section.items:
        return None
    value = section.items[0]
    return value if value.startswith("gst-launch-1.0 ") else None


def _preview_available(detail: DetailPaneModel) -> bool:
    action = next((action for action in detail.actions if action.kind == "preview"), None)
    return bool(action and action.enabled)
