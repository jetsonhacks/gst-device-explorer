"""Camera-specific Qt exploration widgets."""

from __future__ import annotations

from collections.abc import Callable

from gst_device_explorer.gui.model import DetailPaneModel, DetailSection
from gst_device_explorer.gui.qt_sections import (
    copy_to_clipboard,
    create_text_label,
    split_display_row,
    target_from_summary,
)

CAMERA_EXPLORE_SECTION_TITLES = frozenset(
    {
        "Camera Explorer",
        "Camera Modes",
        "Frame Rates",
        "Generated Pipeline",
        "V4L2 Controls",
    }
)


def has_camera_explorer(detail: DetailPaneModel) -> bool:
    return detail.kind == "video" and _camera_section(detail, "Generated Pipeline") is not None


def is_camera_explore_section(detail: DetailPaneModel, section: DetailSection) -> bool:
    return detail.kind == "video" and section.title in CAMERA_EXPLORE_SECTION_TITLES


def camera_explore_lines(detail: DetailPaneModel) -> tuple[str, ...]:
    lines: list[str] = ["Camera Explorer"]
    for section in detail.sections:
        if is_camera_explore_section(detail, section):
            from gst_device_explorer.gui.qt_sections import section_display_title

            lines.append(section_display_title(section))
            lines.extend(section.items)
    return tuple(lines)


def create_camera_explorer_widget(
    detail: DetailPaneModel,
    *,
    status_callback: Callable[[str], None] | None = None,
) -> object:
    from PySide6.QtWidgets import (
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QPushButton,
        QSizePolicy,
        QVBoxLayout,
    )

    box = QGroupBox("Camera Explorer")
    layout = QVBoxLayout(box)
    layout.setSpacing(8)

    device_path = target_from_summary(detail)
    if device_path:
        identity_label = QLabel(f"Device: {device_path}")
        from PySide6.QtCore import Qt

        identity_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(identity_label)

    mode_tree = _camera_mode_tree(detail)

    def _list_column(title: str) -> tuple[object, object]:
        col = QVBoxLayout()
        col.setSpacing(4)
        label = QLabel(title)
        col.addWidget(label)
        lst = QListWidget()
        lst.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        lst.setMinimumHeight(100)
        col.addWidget(lst)
        return col, lst

    fmt_col, fmt_list = _list_column("Pixel Format")
    res_col, res_list = _list_column("Image Size")
    rate_col, rate_list = _list_column("Frame Duration")

    for fmt in mode_tree:
        fmt_list.addItem(fmt)
    if not mode_tree:
        fmt_list.addItem("Unavailable")
        fmt_list.setEnabled(False)

    mode_layout = QHBoxLayout()
    mode_layout.setSpacing(8)
    mode_layout.addLayout(fmt_col, 1)
    mode_layout.addLayout(res_col, 1)
    mode_layout.addLayout(rate_col, 1)
    layout.addLayout(mode_layout, 2)

    pipeline = _pipeline_text(detail)
    pipeline_row = QHBoxLayout()
    pipeline_edit = QLineEdit(pipeline or "Pipeline unavailable for this camera mode.")
    pipeline_edit.setReadOnly(True)
    pipeline_edit.setObjectName("cameraPipelineText")
    pipeline_row.addWidget(pipeline_edit)
    copy_btn = _copy_dynamic_button(
        "Copy Pipeline",
        pipeline_edit.text,
        status_callback=status_callback,
    )
    copy_btn.setEnabled(bool(pipeline))
    pipeline_row.addWidget(copy_btn)
    preview = QPushButton("Preview Deferred")
    preview.setEnabled(False)
    preview.setToolTip("Preview is deferred; this milestone does not execute pipelines.")
    pipeline_row.addWidget(preview)
    layout.addLayout(pipeline_row)

    def update_pipeline() -> None:
        rate_item = rate_list.currentItem()
        res_item = res_list.currentItem()
        fmt_item = fmt_list.currentItem()
        generated = _camera_pipeline_for_selection(
            detail,
            fmt_item.text() if fmt_item else "Unavailable",
            res_item.text() if res_item else "Unavailable",
            rate_item.text() if rate_item else "Unavailable",
        )
        pipeline_edit.setText(generated or "Pipeline unavailable for this camera mode.")
        copy_btn.setEnabled(bool(generated))

    def update_rates() -> None:
        res_item = res_list.currentItem()
        fmt_item = fmt_list.currentItem()
        resolution = res_item.text() if res_item else ""
        fmt = fmt_item.text() if fmt_item else ""
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
        fmt = fmt_item.text() if fmt_item else ""
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

    controls_box = QGroupBox("Dynamic V4L2 Controls (Read-Only)")
    controls_layout = QVBoxLayout(controls_box)
    control_lines = _control_lines(detail)
    if len(control_lines) == 1 and control_lines[0] == "No V4L2 controls advertised.":
        controls_layout.addWidget(create_text_label("No V4L2 controls advertised for this device."))
    else:
        for line in control_lines:
            controls_layout.addLayout(_control_row(line))
    layout.addWidget(controls_box)
    return box


def _control_row(line: str) -> object:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QLabel, QSlider, QSpinBox

    layout = QHBoxLayout()
    name, value = split_display_row(line)
    label = QLabel(name)
    label.setMinimumWidth(160)
    layout.addWidget(label)
    fields = _control_fields(value)
    control_type = fields.get("type", "unknown")
    disabled = "inactive" in fields.get("flags", "").split(",")
    if control_type in {"int", "int64"}:
        slider = QSlider(Qt.Horizontal)
        spin = QSpinBox()
        minimum = _int_or_default(fields.get("range_min"), 0)
        maximum = _int_or_default(fields.get("range_max"), 100)
        current = _int_or_default(fields.get("value"), minimum)
        step = max(1, _int_or_default(fields.get("step"), 1))
        slider.setRange(minimum, maximum)
        slider.setSingleStep(step)
        slider.setValue(max(minimum, min(maximum, current)))
        spin.setRange(minimum, maximum)
        spin.setSingleStep(step)
        spin.setValue(max(minimum, min(maximum, current)))
        slider.setEnabled(False)
        spin.setEnabled(False)
        layout.addWidget(slider)
        layout.addWidget(spin)
    elif control_type == "bool":
        checkbox = QCheckBox()
        checkbox.setChecked(fields.get("value") == "1")
        checkbox.setEnabled(False)
        layout.addWidget(checkbox)
    elif control_type in {"menu", "intmenu"}:
        combo = QComboBox()
        choices = _control_choices(fields.get("choices", ""))
        for choice_value, choice_label in choices:
            combo.addItem(choice_label, choice_value)
        current = fields.get("value")
        if current:
            for index, (choice_value, _choice_label) in enumerate(choices):
                if choice_value == current:
                    combo.setCurrentIndex(index)
                    break
        combo.setEnabled(False)
        layout.addWidget(combo)
    else:
        layout.addWidget(create_text_label(value))
    if disabled:
        label.setEnabled(False)
    layout.addStretch(1)
    return layout


def _copy_dynamic_button(
    label: str,
    text_getter: Callable[[], str],
    *,
    status_callback: Callable[[str], None] | None = None,
) -> object:
    from PySide6.QtWidgets import QPushButton, QSizePolicy

    button = QPushButton(label)
    button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    button.clicked.connect(
        lambda _checked=False: copy_to_clipboard(
            text_getter(),
            status_callback=status_callback,
        )
    )
    return button


def _camera_section(detail: DetailPaneModel, title: str) -> DetailSection | None:
    return next((section for section in detail.sections if section.title == title), None)


def _camera_mode_tree(detail: DetailPaneModel) -> dict[str, dict[str, tuple[str, ...]]]:
    modes = _camera_section(detail, "Camera Modes")
    rates = _camera_section(detail, "Frame Rates")
    result: dict[str, dict[str, tuple[str, ...]]] = {}
    if modes is None:
        return result

    rate_by_resolution: dict[str, tuple[str, ...]] = {}
    if rates is not None:
        for item in rates.items:
            if ":" not in item:
                continue
            key, values = item.split(":", 1)
            rate_by_resolution[key.strip()] = tuple(
                value.strip() for value in values.split(",") if value.strip()
            )

    for item in modes.items:
        if ":" not in item:
            continue
        pixel_format, values = item.split(":", 1)
        resolutions = tuple(value.strip() for value in values.split(",") if value.strip())
        if not resolutions:
            continue
        fmt = pixel_format.strip()
        result[fmt] = {
            resolution: rate_by_resolution.get(
                f"{fmt} {resolution}",
                rate_by_resolution.get(resolution, ()),
            )
            for resolution in resolutions
        }
    return result


def _camera_pipeline_for_selection(
    detail: DetailPaneModel,
    pixel_format: str,
    resolution: str,
    frame_rate: str,
) -> str | None:
    device_path = target_from_summary(detail)
    if (
        device_path is None
        or not pixel_format
        or pixel_format == "Unavailable"
        or not resolution
        or resolution == "Unavailable"
        or "x" not in resolution
    ):
        return None
    width, height = resolution.split("x", 1)
    caps_type = "image/jpeg" if pixel_format == "MJPG" else "video/x-raw"
    caps_parts = [caps_type, f"width={width}", f"height={height}"]
    if caps_type == "video/x-raw":
        caps_parts.append(f"format={pixel_format}")
    if frame_rate and frame_rate != "Unavailable":
        caps_parts.append(f"framerate={_fps_fraction(frame_rate)}")
    return f"gst-launch-1.0 v4l2src device={device_path} ! {','.join(caps_parts)} ! autovideosink"


def _pipeline_text(detail: DetailPaneModel) -> str | None:
    section = _camera_section(detail, "Generated Pipeline")
    if section is None or not section.items:
        return None
    value = section.items[0]
    return value if value.startswith("gst-launch-1.0 ") else None


def _control_lines(detail: DetailPaneModel) -> tuple[str, ...]:
    section = _camera_section(detail, "V4L2 Controls")
    if section is None:
        return ("No V4L2 controls advertised.",)
    return section.items


def _control_fields(value: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for part in value.split(";"):
        if "=" not in part:
            continue
        key, item_value = part.strip().split("=", 1)
        if key == "range" and ".." in item_value:
            minimum, maximum = item_value.split("..", 1)
            result["range_min"] = minimum
            result["range_max"] = maximum
        else:
            result[key] = item_value
    return result


def _control_choices(value: str) -> tuple[tuple[str, str], ...]:
    result = []
    for part in value.split("|"):
        if "=" in part:
            choice_value, label = part.split("=", 1)
            result.append((choice_value, label))
    return tuple(result)


def _int_or_default(value: str | None, default: int) -> int:
    try:
        return int(value) if value is not None else default
    except ValueError:
        return default


def _fps_fraction(label: str) -> str:
    value = label.removesuffix(" fps").strip()
    try:
        fps = float(value)
    except ValueError:
        return value
    if fps.is_integer():
        return f"{int(fps)}/1"
    return f"{round(fps * 1000)}/1000"
