"""Audio-input Qt exploration widgets."""

from __future__ import annotations

import re
from collections.abc import Callable

from gst_device_explorer.core.audio_pipelines import AUDIO_LEVEL_INTERVAL, build_audio_caps_text
from gst_device_explorer.gui.model import DetailPaneModel
from gst_device_explorer.gui.preview_runner import PreviewCommand
from gst_device_explorer.gui.qt_audio_input_test import create_audio_input_test_widget
from gst_device_explorer.gui.qt_sections import copy_to_clipboard, create_text_label, target_from_summary, usb_path_from_group_item


def has_audio_input_explorer(detail: DetailPaneModel) -> bool:
    return detail.kind == "audio_input" and _endpoint_target(detail) is not None


def audio_input_explore_lines(detail: DetailPaneModel) -> tuple[str, ...]:
    target = _endpoint_target(detail)
    lines = ["Audio Input", _audio_header_text(detail)]
    lines.extend(_summary_lines(detail))
    lines.append("Audio Input Mode")
    for label, value in _mode_rows(detail):
        lines.extend((label, value))
    lines.append("Generated Input Pipeline")
    if target is not None:
        lines.append(_generated_input_pipeline(target, _audio_capability_values(detail)))
    lines.append("Copy Pipeline")
    lines.append("Audio Input Activity Test")
    if _input_activity_test_available(detail) and target is not None:
        lines.extend(
            (
                "State: Ready",
                "Start Test",
                "Stop Test",
                "Opens the selected microphone with a generated pipeline. Does not record, save, or retain microphone audio.",
            )
        )
    else:
        lines.extend(
            (
                "State: Unavailable",
                "No safe generated audio-input activity command is available for this endpoint.",
            )
        )
    return tuple(lines)


def create_audio_input_explorer_widget(
    detail: DetailPaneModel,
    *,
    status_callback: Callable[[str], None] | None = None,
    preview_runner: object | None = None,
) -> object:
    from PySide6.QtGui import QFont, QFontDatabase
    from PySide6.QtWidgets import QFormLayout, QGroupBox, QHBoxLayout, QLineEdit
    from PySide6.QtWidgets import QPushButton, QSizePolicy, QVBoxLayout, QWidget

    target = _endpoint_target(detail)
    pane = QWidget()
    layout = QVBoxLayout(pane)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)

    layout.addWidget(create_text_label(_audio_header_text(detail)))

    summary_box = QGroupBox("Audio Input")
    summary_layout = QVBoxLayout(summary_box)
    for line in _summary_lines(detail):
        summary_layout.addWidget(create_text_label(line))
    layout.addWidget(summary_box, 0)

    mode_box = QGroupBox("Audio Input Mode")
    mode_layout = QFormLayout(mode_box)
    for label, value in _mode_rows(detail):
        mode_layout.addRow(label, create_text_label(value))
    layout.addWidget(mode_box, 0)

    pipeline_box = QGroupBox("Generated Input Pipeline")
    pipeline_layout = QHBoxLayout(pipeline_box)
    pipeline_layout.setSpacing(6)
    pipeline_text = (
        _generated_input_pipeline(target, _audio_capability_values(detail))
        if target is not None
        else "Pipeline unavailable."
    )
    pipeline_edit = QLineEdit(pipeline_text)
    pipeline_edit.setObjectName("audioInputPipelineText")
    pipeline_edit.setReadOnly(True)
    pipeline_edit.setProperty("presentation", "code")
    pipeline_font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
    pipeline_font.setStyleHint(QFont.Monospace)
    pipeline_font.setFixedPitch(True)
    pipeline_edit.setFont(pipeline_font)
    pipeline_edit.setMinimumWidth(0)
    pipeline_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    pipeline_edit.setCursorPosition(0)
    pipeline_layout.addWidget(pipeline_edit, 1)
    copy_button = _copy_button("Copy Pipeline", pipeline_edit.text, status_callback=status_callback)
    copy_button.setEnabled(target is not None)
    pipeline_layout.addWidget(copy_button)
    layout.addWidget(pipeline_box, 0)

    def current_test_command() -> PreviewCommand | None:
        if target is None or not _input_activity_test_available(detail):
            return None
        return PreviewCommand(
            _generated_input_pipeline_argv(target, _audio_capability_values(detail)),
            target=target,
            description="Non-recording audio input activity test",
        )

    activity_test_widget, _refresh_activity_test = create_audio_input_test_widget(
        current_test_command,
        preview_runner=preview_runner,
    )
    layout.addWidget(activity_test_widget, 0)
    layout.addStretch(1)
    return pane


def _summary_lines(detail: DetailPaneModel) -> tuple[str, ...]:
    lines = ["Kind: Audio Input"]
    target = _endpoint_target(detail)
    if target is not None:
        lines.append(f"Endpoint: {target}")
    groups = _section_items(detail, "Groups")
    if groups:
        lines.append("Group: " + groups[0].split(" (", 1)[0])
        usb_path = usb_path_from_group_item(groups[0])
        if usb_path:
            lines.append(f"USB path: {usb_path}")
    return tuple(lines)


def _mode_rows(detail: DetailPaneModel) -> tuple[tuple[str, str], ...]:
    values = _audio_capability_values(detail)
    return (
        ("Sample Format", values.get("sample_format") or values.get("format") or "No detailed format list available"),
        ("Sample Rate", values.get("sample_rate") or values.get("rate") or "No detailed sample rate list available"),
        ("Channels", values.get("channels") or "No detailed channel count available"),
        ("GStreamer Caps", build_audio_caps_text(values)),
    )


def _audio_capability_values(detail: DetailPaneModel) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in _section_items(detail, "Capabilities"):
        if ": " not in item:
            continue
        _name, raw_values = item.split(": ", 1)
        result.update(_parse_capability_value_mapping(raw_values))
    return result


def _parse_capability_value_mapping(raw_values: str) -> dict[str, str]:
    result: dict[str, str] = {}
    matches = list(re.finditer(r"(?:^|, )([A-Za-z_]+)=", raw_values))
    for index, match in enumerate(matches):
        value_start = match.end()
        value_end = matches[index + 1].start() if index + 1 < len(matches) else len(raw_values)
        result[match.group(1)] = raw_values[value_start:value_end].strip().removesuffix(",")
    return result


def _audio_header_text(detail: DetailPaneModel) -> str:
    target = _endpoint_target(detail)
    if target:
        return f"{detail.title} - {target}"
    return detail.title


def _endpoint_target(detail: DetailPaneModel) -> str | None:
    return target_from_summary(detail)


def _section_items(detail: DetailPaneModel, title: str) -> tuple[str, ...]:
    section = next((section for section in detail.sections if section.title == title), None)
    return () if section is None else section.items


def _generated_input_pipeline(target: str, values: dict[str, str]) -> str:
    return " ".join(_generated_input_pipeline_argv(target, values))


def _generated_input_pipeline_argv(target: str, values: dict[str, str]) -> tuple[str, ...]:
    return (
        "gst-launch-1.0",
        "alsasrc",
        f"device={target}",
        "num-buffers=20",
        "!",
        build_audio_caps_text(values),
        "!",
        "audioconvert",
        "!",
        "audioresample",
        "!",
        "level",
        AUDIO_LEVEL_INTERVAL,
        "!",
        "fakesink",
        "sync=false",
    )


def _copy_button(
    label: str,
    text_getter: Callable[[], str],
    *,
    status_callback: Callable[[str], None] | None = None,
) -> object:
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QPushButton, QSizePolicy

    button = QPushButton(label)
    button.setObjectName("audioInputPipelineCopyButton")
    button.setToolTip(label)
    button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def _copy(_checked: bool = False) -> None:
        copy_to_clipboard(text_getter(), status_callback=status_callback)
        button.setText("Copied")
        button.setToolTip("Copied")
        QTimer.singleShot(1200, lambda: _reset_copy_button(button, label))

    button.clicked.connect(_copy)
    return button


def _reset_copy_button(button: object, label: str) -> None:
    try:
        button.setText(label)
        button.setToolTip(label)
    except RuntimeError:
        pass


def _input_activity_test_available(detail: DetailPaneModel) -> bool:
    action = next((action for action in detail.actions if action.kind == "test_audio_input"), None)
    return bool(action and action.enabled)
