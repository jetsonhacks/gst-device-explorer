"""Editable Qt widgets for individual camera controls."""

from __future__ import annotations

from collections.abc import Callable

from gst_device_explorer.gui.camera_control_writer import CameraControlWriteRequest
from gst_device_explorer.gui.qt_camera_controls import (
    INACTIVE_TEXT_COLOR,
    CameraControlWidgetPlan,
    _int_or,
)


def control_row(
    plan: CameraControlWidgetPlan,
    *,
    camera_control_writer: object | None,
    selected_endpoint: str | None,
    current_endpoint_getter: Callable[[], str | None] | None,
    status_callback: Callable[[str], None] | None,
    refresh_callback: Callable[[], None] | None,
) -> object:
    from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy, QWidget

    row = QWidget()
    row.setObjectName(f"cameraControlRow_{plan.name}")
    row.setProperty("controlName", plan.name)
    row.setProperty("controlGroup", plan.group)
    row.setProperty("inactive", plan.inactive)
    row.setMaximumWidth(760)
    row.setMinimumWidth(0)
    row.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    layout = QHBoxLayout(row)
    layout.setContentsMargins(4, 3, 4, 3)
    layout.setSpacing(8)
    row.setToolTip(plan.tooltip)
    row.setAccessibleName(plan.label)
    row.setAccessibleDescription(plan.tooltip)
    if plan.inactive:
        row.setStyleSheet("")

    title = QLabel(plan.label)
    title.setObjectName("cameraControlLabel")
    title.setProperty("inactive", plan.inactive)
    title.setMinimumWidth(150)
    title.setMaximumWidth(210)
    title.setToolTip(plan.tooltip)
    if plan.inactive:
        title.setStyleSheet(f"color: {INACTIVE_TEXT_COLOR};")
    layout.addWidget(title)

    status_label = QLabel("")
    status_label.setObjectName("cameraControlStatus")
    status_label.setProperty("controlName", plan.name)
    status_label.setMaximumWidth(180)

    def write_value(value: str) -> bool:
        return _write_control_value(
            plan,
            value,
            selected_endpoint=selected_endpoint,
            camera_control_writer=camera_control_writer,
            current_endpoint_getter=current_endpoint_getter,
            status_label=status_label,
            status_callback=status_callback,
            refresh_callback=refresh_callback,
        )

    editable = camera_control_writer is not None and selected_endpoint is not None and plan.writable
    control_widget = _control_widget(plan, editable=editable, write_value=write_value)
    control_widget.setProperty("inactive", plan.inactive)
    control_widget.setProperty("writable", editable)
    control_widget.setToolTip(plan.tooltip)
    control_widget.setAccessibleName(plan.label)
    control_widget.setAccessibleDescription(plan.tooltip)
    if plan.widget_kind == "checkbox":
        control_widget.setMinimumWidth(24)
        control_widget.setMaximumWidth(36)
        control_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        control_stretch = 0
    elif plan.widget_kind in {"combo", "button", "value"}:
        control_widget.setMinimumWidth(120)
        control_widget.setMaximumWidth(260)
        control_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        control_stretch = 0
    else:
        control_widget.setMaximumWidth(360)
        control_widget.setMinimumWidth(120)
        control_stretch = 1
    layout.addWidget(control_widget, control_stretch)

    if plan.default_value is not None:
        default_button = QPushButton("Default")
        default_button.setObjectName("cameraControlDefaultButton")
        default_button.setProperty("controlName", plan.name)
        default_button.setProperty("inactive", plan.inactive)
        default_button.setEnabled(editable)
        default_button.setToolTip(
            (
                "Reset this control to its reported device default."
                if editable
                else "Reset is available only for active writable controls."
            )
            + (f" Default: {plan.default_label}." if plan.default_label else "")
        )
        default_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        default_button.setMinimumWidth(76)
        if plan.inactive:
            default_button.setStyleSheet(
                "QPushButton:disabled {"
                f"color: {INACTIVE_TEXT_COLOR};"
                "}"
            )
        if editable:
            default_button.clicked.connect(
                lambda _checked=False, value=plan.default_value: write_value(str(value))
            )
        layout.addWidget(default_button)
    elif camera_control_writer is not None and plan.writable:
        status_label.setText("No default")
    if status_label.text() or camera_control_writer is not None:
        layout.addWidget(status_label)
    layout.addStretch(1)
    return row


def _control_widget(
    plan: CameraControlWidgetPlan,
    *,
    editable: bool,
    write_value: Callable[[str], bool],
) -> object:
    if plan.widget_kind == "slider_spin":
        return _slider_spin(plan, editable=editable, write_value=write_value)
    if plan.widget_kind == "checkbox":
        return _checkbox(plan, editable=editable, write_value=write_value)
    if plan.widget_kind == "combo":
        return _combo(plan, editable=editable, write_value=write_value)
    if plan.widget_kind == "button":
        return _readonly_button(plan)
    return _readonly_value_label(plan)


def _slider_spin(
    plan: CameraControlWidgetPlan,
    *,
    editable: bool,
    write_value: Callable[[str], bool],
) -> object:
    from PySide6.QtCore import QSignalBlocker, Qt
    from PySide6.QtWidgets import QHBoxLayout, QSlider, QSpinBox, QWidget

    holder = QWidget()
    holder.setObjectName("cameraControlSliderSpin")
    layout = QHBoxLayout(holder)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)
    slider = QSlider(Qt.Horizontal)
    slider.setObjectName("cameraControlSlider")
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
        widget.setEnabled(editable)
    slider.valueChanged.connect(spin.setValue)

    def spin_changed(new_value: int) -> None:
        with QSignalBlocker(slider):
            slider.setValue(new_value)
        if not write_value(str(new_value)):
            with QSignalBlocker(slider), QSignalBlocker(spin):
                slider.setValue(value)
                spin.setValue(value)

    spin.valueChanged.connect(spin_changed)
    spin.lineEdit().setAlignment(Qt.AlignmentFlag.AlignRight)
    spin.setMinimumWidth(72)
    spin.setMaximumWidth(88)
    layout.addWidget(slider, 1)
    layout.addWidget(spin, 0)
    return holder


def _checkbox(
    plan: CameraControlWidgetPlan,
    *,
    editable: bool,
    write_value: Callable[[str], bool],
) -> object:
    from PySide6.QtCore import QSignalBlocker
    from PySide6.QtWidgets import QCheckBox

    checkbox = QCheckBox()
    checkbox.setObjectName("cameraControlCheckbox")
    checked = plan.current_value.lower() in {"1", "true", "yes", "on"}
    checkbox.setChecked(checked)
    checkbox.setEnabled(editable)

    def toggled(is_checked: bool) -> None:
        if not write_value("1" if is_checked else "0"):
            with QSignalBlocker(checkbox):
                checkbox.setChecked(checked)

    checkbox.toggled.connect(toggled)
    return checkbox


def _combo(
    plan: CameraControlWidgetPlan,
    *,
    editable: bool,
    write_value: Callable[[str], bool],
) -> object:
    from PySide6.QtCore import QSignalBlocker
    from PySide6.QtWidgets import QComboBox

    combo = QComboBox()
    combo.setObjectName("cameraControlCombo")
    choices = plan.choices or ((plan.current_value, plan.current_label),)
    for value, label in choices:
        combo.addItem(label, value)
    selected = next((index for index, (value, _label) in enumerate(choices) if value == plan.current_value), 0)
    combo.setCurrentIndex(selected)
    combo.setEnabled(editable)
    combo.setMinimumWidth(160)
    combo.setMaximumWidth(260)

    def changed(index: int) -> None:
        value = combo.itemData(index)
        if value is None:
            return
        if not write_value(str(value)):
            with QSignalBlocker(combo):
                combo.setCurrentIndex(selected)

    combo.currentIndexChanged.connect(changed)
    return combo


def _readonly_button(plan: CameraControlWidgetPlan) -> object:
    from PySide6.QtWidgets import QPushButton

    button = QPushButton(plan.label)
    button.setObjectName("cameraControlButton")
    button.setEnabled(False)
    return button


def _readonly_value_label(plan: CameraControlWidgetPlan) -> object:
    from PySide6.QtWidgets import QLabel

    label = QLabel(plan.current_label)
    label.setObjectName("cameraControlValueLabel")
    label.setEnabled(False)
    return label


def _write_control_value(
    plan: CameraControlWidgetPlan,
    value: str,
    *,
    selected_endpoint: str | None,
    camera_control_writer: object | None,
    current_endpoint_getter: Callable[[], str | None] | None,
    status_label: object,
    status_callback: Callable[[str], None] | None,
    refresh_callback: Callable[[], None] | None,
) -> bool:
    if camera_control_writer is None or selected_endpoint is None:
        _set_status(status_label, "Unavailable", status_callback)
        return False
    current_endpoint = current_endpoint_getter() if current_endpoint_getter is not None else selected_endpoint
    if current_endpoint != selected_endpoint:
        _set_status(status_label, "Stale endpoint", status_callback)
        return False
    request = CameraControlWriteRequest(
        endpoint=selected_endpoint,
        control_name=plan.name,
        control_id=plan.control_id,
        control_type=plan.control_type,
        value=value,
    )
    try:
        write = getattr(camera_control_writer, "write", None)
        result = write(request) if write is not None else camera_control_writer(request)
    except Exception as error:  # pragma: no cover - defensive GUI boundary
        _set_status(status_label, f"Failed: {error}", status_callback)
        return False
    success = bool(getattr(result, "success", result))
    if success:
        _set_status(status_label, "Updated", status_callback)
        if refresh_callback is not None and plan.widget_kind in {"checkbox", "combo"}:
            refresh_callback()
        return True
    message = str(getattr(result, "message", "") or "Failed")
    _set_status(status_label, message, status_callback)
    return False


def _set_status(label: object, message: str, status_callback: Callable[[str], None] | None) -> None:
    set_text = getattr(label, "setText", None)
    if set_text is not None:
        set_text(message)
    if status_callback is not None:
        status_callback(message)
