"""Camera-specific Qt exploration widgets."""

from __future__ import annotations

from collections.abc import Callable

from gst_device_explorer.gui.model import DetailPaneModel, DetailSection
from gst_device_explorer.gui.qt_camera_controls import create_camera_controls_widget
from gst_device_explorer.gui.qt_sections import (
    copy_to_clipboard,
    create_text_label,
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
    lines: list[str] = ["Camera Explorer", "Camera Summary"]
    lines.extend(_camera_summary_lines(detail))
    lines.append("Camera Settings")
    lines.extend(("Pixel Format", "Image Size", "Frame Duration / FPS"))
    for section in detail.sections:
        if section.title in {"Camera Modes", "Frame Rates"}:
            lines.extend(section.items)
    lines.append("Generated Pipeline")
    pipeline = _pipeline_text(detail)
    if pipeline is not None:
        lines.append(pipeline)
    lines.append("Copy Pipeline")
    lines.append("Camera Controls")
    control_section = _camera_section(detail, "V4L2 Controls")
    if control_section is not None:
        lines.extend(control_section.items)
    return tuple(lines)


def create_camera_explorer_widget(
    detail: DetailPaneModel,
    *,
    status_callback: Callable[[str], None] | None = None,
) -> object:
    from PySide6.QtWidgets import (
        QGroupBox,
        QHBoxLayout,
        QLineEdit,
        QListWidget,
        QPushButton,
        QSizePolicy,
        QVBoxLayout,
    )

    box = QGroupBox("Camera Explorer")
    layout = QVBoxLayout(box)
    layout.setSpacing(8)

    layout.addWidget(_camera_summary_widget(detail))

    mode_tree = _camera_mode_tree(detail)

    def _list_column(title: str) -> tuple[object, object]:
        col = QVBoxLayout()
        col.setSpacing(4)
        from PySide6.QtWidgets import QLabel

        label = QLabel(title)
        col.addWidget(label)
        lst = QListWidget()
        lst.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        lst.setMinimumHeight(100)
        col.addWidget(lst)
        return col, lst

    settings_box = QGroupBox("Camera Settings")
    settings_layout = QHBoxLayout(settings_box)
    settings_layout.setSpacing(8)

    fmt_col, fmt_list = _list_column("Pixel Format")
    res_col, res_list = _list_column("Image Size")
    rate_col, rate_list = _list_column("Frame Duration / FPS")

    for fmt in mode_tree:
        fmt_list.addItem(fmt)
    if not mode_tree:
        fmt_list.addItem("Unavailable")
        fmt_list.setEnabled(False)

    settings_layout.addLayout(fmt_col, 1)
    settings_layout.addLayout(res_col, 1)
    settings_layout.addLayout(rate_col, 1)
    layout.addWidget(settings_box)

    pipeline = _pipeline_text(detail)
    pipeline_box = QGroupBox("Generated Pipeline")
    pipeline_box_layout = QVBoxLayout(pipeline_box)
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
    pipeline_box_layout.addLayout(pipeline_row)
    layout.addWidget(pipeline_box)

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

    layout.addWidget(create_camera_controls_widget(detail))
    return box


def _camera_summary_widget(detail: DetailPaneModel) -> object:
    from PySide6.QtWidgets import QFormLayout, QGroupBox

    box = QGroupBox("Camera Summary")
    layout = QFormLayout(box)
    for line in _camera_summary_lines(detail):
        if ": " in line:
            label, value = line.split(": ", 1)
            layout.addRow(label, create_text_label(value))
        else:
            layout.addRow("", create_text_label(line))
    return box


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
    groups = _camera_section(detail, "Groups")
    if groups is not None and groups.items:
        rows.append(f"Group: {groups.items[0]}")
    return tuple(rows)


def _metadata_values(detail: DetailPaneModel) -> dict[str, str]:
    section = _camera_section(detail, "Metadata")
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


def _fps_fraction(label: str) -> str:
    value = label.removesuffix(" fps").strip()
    try:
        fps = float(value)
    except ValueError:
        return value
    if fps.is_integer():
        return f"{int(fps)}/1"
    return f"{round(fps * 1000)}/1000"
