"""Read-only camera control widgets for the Qt camera explorer."""

from __future__ import annotations

from dataclasses import dataclass

from gst_device_explorer.gui.model import DetailPaneModel
from gst_device_explorer.gui.qt_sections import create_text_label, split_display_row


@dataclass(frozen=True)
class CameraControlWidgetPlan:
    """Toolkit-neutral rendering plan for one read-only camera control."""

    name: str
    label: str
    widget_kind: str
    current_value: str
    current_label: str
    minimum: int | None
    maximum: int | None
    step: int | None
    default_value: str | None
    choices: tuple[tuple[str, str], ...]
    flags: tuple[str, ...]
    tooltip: str

    @property
    def inactive(self) -> bool:
        return "inactive" in self.flags

    @property
    def default_label(self) -> str | None:
        if self.default_value is None:
            return None
        return _choice_label(self.choices, self.default_value) or self.default_value


def create_camera_controls_widget(detail: DetailPaneModel) -> object:
    from PySide6.QtWidgets import QFrame, QGroupBox
    from PySide6.QtWidgets import QScrollArea, QSizePolicy, QVBoxLayout, QWidget

    controls_box = QGroupBox("Camera Controls")
    controls_box.setObjectName("cameraControlsSection")
    controls_layout = QVBoxLayout(controls_box)
    controls_layout.setContentsMargins(10, 10, 10, 10)
    controls_layout.setSpacing(8)
    controls_box.setMinimumHeight(180)
    controls_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    scroll = QScrollArea()
    scroll.setObjectName("cameraControlsScrollArea")
    scroll.setWidgetResizable(True)
    scroll.setMinimumHeight(180)
    scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    content = QWidget()
    content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
    content_layout = QVBoxLayout(content)
    content_layout.setContentsMargins(8, 8, 8, 8)
    content_layout.setSpacing(8)
    plans = camera_control_widget_plans(detail)
    if not plans:
        content_layout.addWidget(create_text_label("No V4L2 controls advertised for this device."))
    else:
        for plan in plans:
            content_layout.addWidget(_control_row(plan))
            divider = QFrame()
            divider.setFrameShape(QFrame.HLine)
            divider.setFrameShadow(QFrame.Sunken)
            content_layout.addWidget(divider)
    content_layout.addStretch(1)
    scroll.setWidget(content)
    controls_layout.addWidget(scroll, 1)
    return controls_box


def _control_row(plan: CameraControlWidgetPlan) -> object:
    from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy, QWidget

    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(2, 2, 2, 2)
    layout.setSpacing(10)
    row.setToolTip(plan.tooltip)
    row.setAccessibleName(plan.label)
    row.setAccessibleDescription(plan.tooltip)

    title = QLabel(plan.label)
    title.setMinimumWidth(180)
    title.setToolTip(plan.tooltip)
    if plan.inactive:
        title.setEnabled(False)
    layout.addWidget(title)

    control_widget = _readonly_control_widget(plan)
    control_widget.setToolTip(plan.tooltip)
    control_widget.setAccessibleName(plan.label)
    control_widget.setAccessibleDescription(plan.tooltip)
    layout.addWidget(control_widget, 1)

    if plan.inactive:
        inactive = QLabel("Inactive")
        inactive.setEnabled(False)
        inactive.setMinimumWidth(62)
        inactive.setToolTip("Inactive for the current camera mode or automatic setting.")
        layout.addWidget(inactive)

    if plan.default_value is not None:
        default_button = QPushButton("Default")
        default_button.setObjectName("cameraControlDefaultButton")
        default_button.setEnabled(False)
        default_button.setToolTip(
            "Reset-to-default is deferred; this view is read-only."
            + (f" Default: {plan.default_label}." if plan.default_label else "")
        )
        default_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(default_button)
    layout.addStretch(1)
    return row


def _readonly_control_widget(plan: CameraControlWidgetPlan) -> object:
    if plan.widget_kind == "slider_spin":
        return _readonly_slider_spin(plan)
    if plan.widget_kind == "checkbox":
        return _readonly_checkbox(plan)
    if plan.widget_kind == "combo":
        return _readonly_combo(plan)
    if plan.widget_kind == "button":
        return _readonly_button(plan)
    return _readonly_value_label(plan)


def _readonly_slider_spin(plan: CameraControlWidgetPlan) -> object:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QHBoxLayout, QSlider, QSpinBox, QWidget

    holder = QWidget()
    layout = QHBoxLayout(holder)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)
    slider = QSlider(Qt.Horizontal)
    spin = QSpinBox()
    spin.setObjectName("cameraControlIntegerValue")
    minimum = plan.minimum if plan.minimum is not None else _int_or(plan.current_value, 0)
    maximum = plan.maximum if plan.maximum is not None else _int_or(plan.current_value, minimum)
    step = plan.step or 1
    value = min(max(_int_or(plan.current_value, minimum), minimum), maximum)
    for widget in (slider, spin):
        widget.setMinimum(minimum)
        widget.setMaximum(maximum)
        widget.setSingleStep(step)
        widget.setValue(value)
        widget.setEnabled(False)
    spin.lineEdit().setAlignment(Qt.AlignmentFlag.AlignRight)
    spin.setMinimumWidth(72)
    layout.addWidget(slider, 1)
    layout.addWidget(spin, 0)
    return holder


def _readonly_checkbox(plan: CameraControlWidgetPlan) -> object:
    from PySide6.QtWidgets import QCheckBox

    checkbox = QCheckBox()
    checkbox.setChecked(plan.current_value.lower() in {"1", "true", "yes", "on"})
    checkbox.setEnabled(False)
    return checkbox


def _readonly_combo(plan: CameraControlWidgetPlan) -> object:
    from PySide6.QtWidgets import QComboBox

    combo = QComboBox()
    choices = plan.choices or ((plan.current_value, plan.current_label),)
    for value, label in choices:
        combo.addItem(label, value)
    selected = next((index for index, (value, _label) in enumerate(choices) if value == plan.current_value), 0)
    combo.setCurrentIndex(selected)
    combo.setEnabled(False)
    return combo


def _readonly_button(plan: CameraControlWidgetPlan) -> object:
    from PySide6.QtWidgets import QPushButton

    button = QPushButton(plan.label)
    button.setEnabled(False)
    return button


def _readonly_value_label(plan: CameraControlWidgetPlan) -> object:
    from PySide6.QtWidgets import QLabel

    label = QLabel(plan.current_label)
    label.setEnabled(not plan.inactive)
    return label


def camera_control_accessible_lines(detail: DetailPaneModel) -> tuple[str, ...]:
    lines: list[str] = []
    plans = camera_control_widget_plans(detail)
    if not plans:
        return ("No V4L2 controls advertised for this device.",)
    for plan in plans:
        lines.append(plan.label)
        lines.append(f"Current: {plan.current_label}")
        if plan.tooltip:
            lines.append(plan.tooltip)
        if plan.inactive:
            lines.append("Inactive for the current camera mode or auto setting.")
    return tuple(lines)


def camera_control_widget_plans(detail: DetailPaneModel) -> tuple[CameraControlWidgetPlan, ...]:
    return tuple(_control_plan(line) for line in _control_lines(detail) if line != "No V4L2 controls advertised.")


def _control_lines(detail: DetailPaneModel) -> tuple[str, ...]:
    section = next((section for section in detail.sections if section.title == "V4L2 Controls"), None)
    if section is None:
        return ("No V4L2 controls advertised.",)
    return section.items


def _control_plan(line: str) -> CameraControlWidgetPlan:
    name, value = split_display_row(line)
    fields = _control_fields(value)
    choices = _control_choices(fields.get("choices", ""))
    current_value = fields.get("value", "")
    widget_kind = _control_widget_kind(fields)
    return CameraControlWidgetPlan(
        name=name,
        label=_control_label(name),
        widget_kind=widget_kind,
        current_value=current_value,
        current_label=_current_value_label(widget_kind, choices, current_value),
        minimum=_int_or_none(fields.get("range_min")),
        maximum=_int_or_none(fields.get("range_max")),
        step=_int_or_none(fields.get("step")),
        default_value=fields.get("default"),
        choices=choices,
        flags=_control_flags(fields),
        tooltip=_control_tooltip(fields, choices),
    )


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


def _control_flags(fields: dict[str, str]) -> tuple[str, ...]:
    return tuple(flag for flag in fields.get("flags", "").split(",") if flag)


def _control_widget_kind(fields: dict[str, str]) -> str:
    control_type = fields.get("type", "").lower()
    if control_type in {"int", "integer", "int64"}:
        return "slider_spin"
    if control_type in {"bool", "boolean"}:
        return "checkbox"
    if control_type in {"menu", "intmenu"}:
        return "combo"
    if control_type == "button":
        return "button"
    return "value"


def _control_choices(value: str) -> tuple[tuple[str, str], ...]:
    result = []
    for part in value.split("|"):
        if "=" in part:
            choice_value, label = part.split("=", 1)
            result.append((choice_value, label))
    return tuple(result)


def _control_tooltip(fields: dict[str, str], choices: tuple[tuple[str, str], ...]) -> str:
    parts = []
    if fields.get("range_min") and fields.get("range_max"):
        range_text = f"Range: {fields['range_min']} to {fields['range_max']}"
        if fields.get("step"):
            range_text += f", step {fields['step']}"
        parts.append(range_text)
    elif fields.get("step"):
        parts.append(f"Step: {fields['step']}")
    if fields.get("default"):
        parts.append(f"Default: {_value_with_choice_label(choices, fields['default'])}")
    if choices:
        parts.append("Choices: " + ", ".join(label for _value, label in choices))
    flags = fields.get("flags")
    if flags:
        parts.append("Flags: " + flags.replace(",", ", "))
    control_type = fields.get("type")
    if control_type:
        parts.append(f"Type: {control_type}")
    return " - ".join(parts)


def _value_with_choice_label(choices: tuple[tuple[str, str], ...], value: str) -> str:
    return _choice_label(choices, value) or value


def _current_value_label(widget_kind: str, choices: tuple[tuple[str, str], ...], value: str) -> str:
    if not value:
        return "Unavailable"
    if widget_kind == "checkbox":
        return "On" if value.lower() in {"1", "true", "yes", "on"} else "Off"
    return _value_with_choice_label(choices, value)


def _choice_label(choices: tuple[tuple[str, str], ...], value: str) -> str | None:
    for choice_value, choice_label in choices:
        if choice_value == value:
            return choice_label
    return None


def _control_label(name: str) -> str:
    return name.replace("_", " ").replace("-", " ").title()


def _int_or_none(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _int_or(value: str, fallback: int) -> int:
    try:
        return int(value)
    except ValueError:
        return fallback
