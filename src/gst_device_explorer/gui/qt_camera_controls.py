"""Read-only camera control widgets for the Qt camera explorer."""

from __future__ import annotations

from gst_device_explorer.gui.model import DetailPaneModel
from gst_device_explorer.gui.qt_sections import create_text_label, split_display_row


def create_camera_controls_widget(detail: DetailPaneModel) -> object:
    from PySide6.QtWidgets import QGroupBox, QVBoxLayout

    controls_box = QGroupBox("Camera Controls")
    controls_layout = QVBoxLayout(controls_box)
    control_lines = _control_lines(detail)
    if len(control_lines) == 1 and control_lines[0] == "No V4L2 controls advertised.":
        controls_layout.addWidget(create_text_label("No V4L2 controls advertised for this device."))
    else:
        for line in control_lines:
            controls_layout.addLayout(_control_row(line))
    return controls_box


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


def _control_lines(detail: DetailPaneModel) -> tuple[str, ...]:
    section = next((section for section in detail.sections if section.title == "V4L2 Controls"), None)
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
