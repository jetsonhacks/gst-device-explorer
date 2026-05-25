"""Qt detail pane rendering for GUI models."""

from __future__ import annotations

from collections.abc import Callable

from gst_device_explorer.gui.model import DetailPaneModel, DetailSection, GuiAction

COPYABLE_ACTION_KINDS = frozenset(
    {
        "copy_command",
        "copy_pipeline",
        "dry_run",
        "show_diagnostics",
        "validate_group",
        "export_report",
        "refresh",
    }
)

COPYABLE_LINE_PREFIXES = (
    "Endpoint:",
    "Group id:",
    "command:",
    "target:",
)


class DetailPaneWidgetMixin:
    """Mixin containing renderer logic shared by the concrete QWidget."""

    def render_detail(self, detail: DetailPaneModel) -> None:
        raise NotImplementedError


def action_display_lines(action: GuiAction) -> tuple[str, ...]:
    """Return stable action metadata lines for rendering and tests."""

    lines = [
        f"kind: {action.kind}",
        f"safety: {action.safety}",
        f"enabled: {action.enabled}",
    ]
    if action.target_kind and action.target:
        lines.append(f"target: {action.target_kind} {action.target}")
    if action.suggested_command is not None:
        lines.append(f"command: {action.suggested_command.command}")
    if action.disabled_reason:
        lines.append(f"disabled: {action.disabled_reason}")
    return tuple(lines)


def detail_identity_items(detail: DetailPaneModel) -> tuple[tuple[str, str], ...]:
    """Return stable identity rows for the detail header."""

    rows = [
        ("Selection", detail.selected_id),
        ("Kind", detail.kind),
        ("Status", detail.status),
    ]
    target = _target_from_summary(detail)
    if target is not None:
        rows.append(("Target", target))
    return tuple(rows)


def section_display_title(section: DetailSection) -> str:
    """Normalize section titles into friendlier GUI headings."""

    title = section.title.strip()
    mapping = {
        "Metadata": "Identity and Metadata",
        "Capabilities": "Capabilities",
        "Candidate Summary": "Candidate Pipelines",
        "Recommendation": "Recommended Candidate",
        "Missing Elements": "Missing Elements",
        "Grouping Evidence": "Grouping Evidence",
        "Endpoints": "Constituent Endpoints",
        "Validation": "Endpoint Status",
        "Safe Actions": "Notes and Limitations",
        "Suggested Next Step": "Suggested Next Step",
        "Details": "Diagnostic Details",
        "Refresh": "Refresh",
        "Discovery": "Discovery",
        "Selection": "Selection",
        "V4L2 Controls": "Dynamic V4L2 Controls (Read-Only)",
    }
    return mapping.get(title, title)


def section_kind(section: DetailSection) -> str:
    """Classify a section for renderer decisions and tests."""

    title = section.title.lower()
    if "candidate" in title or "recommendation" in title:
        return "candidate"
    if "capabilit" in title:
        return "capability"
    if "missing" in title or "diagnostic" in title or "detail" in title:
        return "diagnostic"
    if "endpoint" in title or "evidence" in title or "validation" in title:
        return "group"
    if "metadata" in title or "summary" in title or "identity" in title:
        return "identity"
    return "notes"


def copyable_texts(detail: DetailPaneModel) -> tuple[tuple[str, str], ...]:
    """Return display-only strings that are safe to copy."""

    values: list[tuple[str, str]] = []
    for label, value in detail_identity_items(detail):
        if label in {"Selection", "Target"} and value:
            values.append((f"Copy {label}", value))
    for line in detail.summary:
        maybe = _copyable_line_value(line)
        if maybe is not None:
            values.append((f"Copy {_copy_label(line)}", maybe))
    for action in detail.actions:
        command = action_copy_text(action)
        if command is not None:
            label = action.label if action.label.startswith("Copy ") else f"Copy {action.label}"
            values.append((label, command))
    return tuple(dict(values).items())


def action_copy_text(action: GuiAction) -> str | None:
    """Return the safe copy text for an action, if one exists."""

    if action.suggested_command is not None:
        return action.suggested_command.command
    if action.kind in COPYABLE_ACTION_KINDS and action.target:
        return action.target
    return None


def copy_display_text(
    text: str,
    *,
    set_clipboard_text: Callable[[str], None],
    status_callback: Callable[[str], None] | None = None,
) -> None:
    """Copy display text through an injected clipboard setter."""

    set_clipboard_text(text)
    if status_callback is not None:
        status_callback("Copied to clipboard.")


def detail_accessible_text(detail: DetailPaneModel) -> str:
    """Return a compact text representation for headless tests."""

    lines = [detail.title]
    lines.extend(f"{label}: {value}" for label, value in detail_identity_items(detail))
    lines.extend(detail.summary)
    for section in detail.sections:
        lines.append(section_display_title(section))
        lines.extend(section.items)
    for action in detail.actions:
        lines.append(action.label)
        lines.extend(action_display_lines(action))
    return "\n".join(lines)


def create_detail_pane_widget(
    *,
    status_callback: Callable[[str], None] | None = None,
) -> object:
    """Create the concrete Qt detail widget.

    PySide6 imports stay inside this factory so non-GUI imports remain light.
    """

    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QAbstractItemView,
        QCheckBox,
        QComboBox,
        QFrame,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QPushButton,
        QScrollArea,
        QSizePolicy,
        QSlider,
        QSpinBox,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )

    class DetailPaneWidget(QWidget, DetailPaneWidgetMixin):
        def __init__(self) -> None:
            super().__init__()
            self._layout = QVBoxLayout(self)
            self._layout.setContentsMargins(16, 16, 16, 16)
            self._layout.setSpacing(12)

        def render_detail(self, detail: DetailPaneModel) -> None:
            _clear_layout(self._layout)
            self.setAccessibleName(detail.title)
            self.setAccessibleDescription(detail_accessible_text(detail))
            title = QLabel(detail.title)
            title.setObjectName("detailTitle")
            title.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self._layout.addWidget(title)

            identity_box = QGroupBox("Identity")
            identity_layout = QFormLayout(identity_box)
            for label, value in detail_identity_items(detail):
                identity_layout.addRow(label, _copyable_row(value))
            self._layout.addWidget(identity_box)

            if detail.summary:
                summary_box = QGroupBox("Summary")
                summary_layout = QVBoxLayout(summary_box)
                for line in detail.summary:
                    summary_layout.addWidget(_text_label(line))
                self._layout.addWidget(summary_box)

            if detail.kind == "video" and _camera_section(detail, "Generated Pipeline") is not None:
                self._layout.addWidget(_camera_explorer_widget(detail))

            for section in detail.sections:
                if detail.kind == "video" and section.title in {
                    "Camera Explorer",
                    "Camera Modes",
                    "Frame Rates",
                    "Generated Pipeline",
                    "V4L2 Controls",
                }:
                    continue
                section_box = QGroupBox(section_display_title(section))
                section_layout = QVBoxLayout(section_box)
                if section_kind(section) in {"candidate", "capability", "identity", "group"}:
                    section_layout.addWidget(_table_for_section(section))
                else:
                    for item in section.items:
                        section_layout.addWidget(_text_label(item))
                self._layout.addWidget(section_box)

            copyable = copyable_texts(detail)
            if copyable:
                copy_box = QGroupBox("Copy")
                copy_layout = QVBoxLayout(copy_box)
                for label, text in copyable:
                    copy_layout.addWidget(_copy_button(label, text))
                self._layout.addWidget(copy_box)

            actions_box = QGroupBox("Safe Actions")
            actions_layout = QVBoxLayout(actions_box)
            for action in detail.actions:
                row = QHBoxLayout()
                button = QPushButton(action.label)
                button.setEnabled(False)
                button.setToolTip(
                    "Display-only action metadata. This button does not execute commands."
                )
                button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                row.addWidget(button)
                copy_text = action_copy_text(action)
                if copy_text is not None:
                    row.addWidget(_copy_button("Copy", copy_text))
                row.addStretch(1)
                actions_layout.addLayout(row)
                for line in action_display_lines(action):
                    actions_layout.addWidget(_text_label(line))
                divider = QFrame()
                divider.setFrameShape(QFrame.HLine)
                divider.setFrameShadow(QFrame.Sunken)
                actions_layout.addWidget(divider)
            self._layout.addWidget(actions_box)
            self._layout.addStretch(1)

    class DetailScrollArea(QScrollArea):
        def __init__(self) -> None:
            super().__init__()
            self.setWidgetResizable(True)
            self._pane = DetailPaneWidget()
            self.setWidget(self._pane)

        def render_detail(self, detail: DetailPaneModel) -> None:
            self._pane.render_detail(detail)

    def _text_label(text: str) -> object:
        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        return label

    def _camera_explorer_widget(detail: DetailPaneModel) -> object:
        box = QGroupBox("Camera Explorer")
        layout = QVBoxLayout(box)
        layout.setSpacing(8)

        device_path = _target_from_summary(detail)
        if device_path:
            identity_label = QLabel(f"Device: {device_path}")
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
        copy_btn = _copy_dynamic_button("Copy Pipeline", pipeline_edit.text)
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
            controls_layout.addWidget(_text_label("No V4L2 controls advertised for this device."))
        else:
            for line in control_lines:
                controls_layout.addLayout(_control_row(line))
        layout.addWidget(controls_box)
        return box

    def _control_row(line: str) -> object:
        layout = QHBoxLayout()
        name, value = _split_display_row(line)
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
            layout.addWidget(_text_label(value))
        if disabled:
            label.setEnabled(False)
        layout.addStretch(1)
        return layout

    def _copyable_row(text: str) -> object:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(_text_label(text))
        layout.addWidget(_copy_button("Copy", text))
        layout.addStretch(1)
        return row

    def _copy_button(label: str, text: str) -> object:
        button = QPushButton(label)
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        button.clicked.connect(lambda _checked=False, value=text: _copy_to_clipboard(value))
        return button

    def _copy_dynamic_button(label: str, text_getter: Callable[[], str]) -> object:
        button = QPushButton(label)
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        button.clicked.connect(lambda _checked=False: _copy_to_clipboard(text_getter()))
        return button

    def _copy_to_clipboard(text: str) -> None:
        from PySide6.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        copy_display_text(
            text,
            set_clipboard_text=clipboard.setText,
            status_callback=status_callback,
        )

    def _table_for_section(section: DetailSection) -> object:
        rows = [_split_display_row(item) for item in section.items] or [("", "")]
        table = QTableWidget(len(rows), 2)
        table.setHorizontalHeaderLabels(["Item", "Value"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setAlternatingRowColors(True)
        table.setMinimumHeight(min(220, 48 + 28 * max(1, len(rows))))
        for row_index, (key, value) in enumerate(rows):
            table.setItem(row_index, 0, QTableWidgetItem(key))
            table.setItem(row_index, 1, QTableWidgetItem(value))
        table.resizeColumnsToContents()
        table.horizontalHeader().setStretchLastSection(True)
        return table

    def _clear_layout(layout: object) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    return DetailScrollArea()


def _camera_section(detail: DetailPaneModel, title: str) -> DetailSection | None:
    return next((section for section in detail.sections if section.title == title), None)


def _camera_formats(detail: DetailPaneModel) -> tuple[str, ...]:
    section = _camera_section(detail, "Camera Modes")
    if section is None:
        return ()
    return tuple(item.split(":", 1)[0] for item in section.items if ":" in item)


def _camera_resolutions(detail: DetailPaneModel) -> tuple[str, ...]:
    section = _camera_section(detail, "Camera Modes")
    if section is None:
        return ()
    result: list[str] = []
    for item in section.items:
        if ":" not in item:
            continue
        _fmt, values = item.split(":", 1)
        result.extend(value.strip() for value in values.split(",") if value.strip())
    return tuple(dict.fromkeys(result))


def _camera_frame_rates(detail: DetailPaneModel) -> tuple[str, ...]:
    section = _camera_section(detail, "Frame Rates")
    if section is None:
        return ()
    result: list[str] = []
    for item in section.items:
        if ":" not in item:
            continue
        _resolution, values = item.split(":", 1)
        result.extend(value.strip() for value in values.split(",") if value.strip())
    return tuple(dict.fromkeys(result))


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
    device_path = _target_from_summary(detail)
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


def _target_from_summary(detail: DetailPaneModel) -> str | None:
    for line in detail.summary:
        maybe = _copyable_line_value(line)
        if maybe is not None:
            return maybe
    return None


def _copyable_line_value(line: str) -> str | None:
    for prefix in COPYABLE_LINE_PREFIXES:
        if line.startswith(prefix):
            return line.removeprefix(prefix).strip()
    return None


def _copy_label(line: str) -> str:
    return line.split(":", 1)[0].strip().lower()


def _split_display_row(item: str) -> tuple[str, str]:
    for separator in (": ", " - "):
        if separator in item:
            left, right = item.split(separator, 1)
            return left, right
    return item, ""
