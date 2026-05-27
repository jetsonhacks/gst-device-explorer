"""Read-only camera control widgets for the Qt camera explorer."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from dataclasses import replace

from gst_device_explorer.core.models import CameraControlSet
from gst_device_explorer.gui.camera import camera_control_section
from gst_device_explorer.gui.model import DetailPaneModel
from gst_device_explorer.gui.qt_sections import create_text_label, split_display_row, target_from_summary

CONTROL_GROUP_ORDER = (
    "Image Adjustment",
    "Exposure & Gain",
    "White Balance",
    "Advanced",
)

IMAGE_ADJUSTMENT_CONTROLS = frozenset(
    {
        "brightness",
        "contrast",
        "saturation",
        "hue",
        "sharpness",
        "gamma",
    }
)
EXPOSURE_GAIN_CONTROLS = frozenset(
    {
        "auto_exposure",
        "exposure_auto",
        "exposure_absolute",
        "exposure_time_absolute",
        "gain",
        "backlight_compensation",
    }
)
WHITE_BALANCE_CONTROLS = frozenset(
    {
        "white_balance_automatic",
        "white_balance_temperature_auto",
        "white_balance_temperature",
    }
)
INACTIVE_TEXT_COLOR = "#6b7280"


@dataclass(frozen=True)
class CameraControlWidgetPlan:
    """Toolkit-neutral rendering plan for one read-only camera control."""

    name: str
    label: str
    control_id: str | None
    control_type: str
    device_path: str
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
    group: str

    @property
    def inactive(self) -> bool:
        return "inactive" in self.flags

    @property
    def read_only(self) -> bool:
        return any(flag in {"read-only", "readonly", "disabled"} for flag in self.normalized_flags)

    @property
    def writable(self) -> bool:
        return self.supported_for_writes and not self.inactive and not self.read_only

    @property
    def supported_for_writes(self) -> bool:
        if self.widget_kind == "slider_spin":
            return self.minimum is not None and self.maximum is not None
        if self.widget_kind == "checkbox":
            return True
        if self.widget_kind == "combo":
            return bool(self.choices)
        return False

    @property
    def normalized_flags(self) -> tuple[str, ...]:
        return tuple(flag.lower() for flag in self.flags)

    @property
    def default_label(self) -> str | None:
        if self.default_value is None:
            return None
        return _choice_label(self.choices, self.default_value) or self.default_value


def create_camera_controls_widget(
    detail: DetailPaneModel,
    *,
    camera_control_writer: object | None = None,
    camera_control_refresher: Callable[[str], CameraControlSet | None] | None = None,
    current_endpoint_getter: Callable[[], str | None] | None = None,
    status_callback: Callable[[str], None] | None = None,
) -> object:
    from PySide6.QtCore import QTimer, Qt
    from PySide6.QtWidgets import QFrame, QGroupBox, QLabel
    from PySide6.QtWidgets import QScrollArea, QSizePolicy, QVBoxLayout, QWidget

    current_detail = detail

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
    from gst_device_explorer.gui.qt_camera_control_widgets import control_row

    def refresh_controls() -> None:
        nonlocal current_detail
        endpoint = target_from_summary(current_detail)
        if endpoint is None or camera_control_refresher is None:
            return
        if current_endpoint_getter is not None and current_endpoint_getter() != endpoint:
            return
        refreshed = camera_control_refresher(endpoint)
        if refreshed is None:
            return
        current_detail = _detail_with_control_set(current_detail, refreshed)
        render_controls()

    def schedule_refresh() -> None:
        QTimer.singleShot(0, refresh_controls)

    def render_controls() -> None:
        scroll_x = scroll.horizontalScrollBar().value()
        scroll_y = scroll.verticalScrollBar().value()
        content = QWidget()
        content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(8)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        plans = camera_control_widget_plans(current_detail)
        endpoint = target_from_summary(current_detail)
        if not plans:
            content_layout.addWidget(create_text_label("No V4L2 controls advertised for this device."))
        else:
            first_group = True
            for group_name, group_plans in _grouped_control_plans(plans):
                if not first_group:
                    group_divider = QFrame()
                    group_divider.setFrameShape(QFrame.HLine)
                    group_divider.setFrameShadow(QFrame.Plain)
                    group_divider.setObjectName("cameraControlGroupDivider")
                    group_divider.setMaximumWidth(760)
                    content_layout.addWidget(group_divider)
                first_group = False
                heading = QLabel(group_name)
                heading.setObjectName("cameraControlGroupHeader")
                heading.setProperty("controlGroup", group_name)
                heading.setStyleSheet(
                    "QLabel#cameraControlGroupHeader {"
                    "font-weight: 600;"
                    "padding-top: 4px;"
                    "}"
                )
                content_layout.addWidget(heading)
                for plan in group_plans:
                    content_layout.addWidget(
                        control_row(
                            plan,
                            camera_control_writer=camera_control_writer,
                            selected_endpoint=endpoint,
                            current_endpoint_getter=current_endpoint_getter,
                            status_callback=status_callback,
                            refresh_callback=schedule_refresh,
                        )
                    )
        content_layout.addStretch(1)
        old = scroll.takeWidget()
        if old is not None:
            old.deleteLater()
        scroll.setWidget(content)
        QTimer.singleShot(0, lambda: _restore_scroll_position(scroll, scroll_x, scroll_y))

    render_controls()
    controls_layout.addWidget(scroll, 1)
    return controls_box


def _restore_scroll_position(scroll: object, horizontal: int, vertical: int) -> None:
    scroll.horizontalScrollBar().setValue(horizontal)
    scroll.verticalScrollBar().setValue(vertical)


def _detail_with_control_set(
    detail: DetailPaneModel,
    control_set: CameraControlSet,
) -> DetailPaneModel:
    replacement = camera_control_section(control_set)
    sections = tuple(
        replacement if section.title == "V4L2 Controls" else section
        for section in detail.sections
    )
    if all(section.title != "V4L2 Controls" for section in detail.sections):
        sections = (*sections, replacement)
    return replace(detail, sections=sections)


def camera_control_accessible_lines(detail: DetailPaneModel) -> tuple[str, ...]:
    lines: list[str] = []
    plans = camera_control_widget_plans(detail)
    if not plans:
        return ("No V4L2 controls advertised for this device.",)
    for group_name, group_plans in _grouped_control_plans(plans):
        lines.append(group_name)
        for plan in group_plans:
            lines.append(plan.label)
            lines.append(f"Current: {plan.current_label}")
            if plan.tooltip:
                lines.append(plan.tooltip)
            if plan.inactive:
                lines.append("Inactive for the current camera mode or auto setting.")
    return tuple(lines)


def camera_control_widget_plans(detail: DetailPaneModel) -> tuple[CameraControlWidgetPlan, ...]:
    return tuple(_control_plan(line) for line in _control_lines(detail) if line != "No V4L2 controls advertised.")


def camera_control_group_labels(detail: DetailPaneModel) -> tuple[str, ...]:
    return tuple(group_name for group_name, _plans in _grouped_control_plans(camera_control_widget_plans(detail)))


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
        control_id=fields.get("id"),
        control_type=fields.get("type", ""),
        device_path=fields.get("device", ""),
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
        group=_control_group(name),
    )


def _grouped_control_plans(
    plans: tuple[CameraControlWidgetPlan, ...],
) -> tuple[tuple[str, tuple[CameraControlWidgetPlan, ...]], ...]:
    by_group: dict[str, list[CameraControlWidgetPlan]] = {group: [] for group in CONTROL_GROUP_ORDER}
    for plan in plans:
        by_group.setdefault(plan.group, []).append(plan)
    return tuple(
        (group, tuple(group_plans))
        for group in CONTROL_GROUP_ORDER
        if (group_plans := by_group.get(group))
    )


def _control_group(name: str) -> str:
    normalized = name.lower().replace("-", "_")
    if normalized in IMAGE_ADJUSTMENT_CONTROLS:
        return "Image Adjustment"
    if normalized in EXPOSURE_GAIN_CONTROLS:
        return "Exposure & Gain"
    if normalized in WHITE_BALANCE_CONTROLS:
        return "White Balance"
    return "Advanced"


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
