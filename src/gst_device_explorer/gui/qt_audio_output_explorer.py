"""Audio-output Qt exploration widgets."""

from __future__ import annotations

import re
from collections.abc import Callable

from gst_device_explorer.core.audio_pipelines import AUDIO_SINE_FREQ, AUDIO_SINE_WAVE, build_audio_caps_text
from gst_device_explorer.gui.model import DetailPaneModel
from gst_device_explorer.gui.preview_runner import PreviewCommand
from gst_device_explorer.gui.qt_audio_output_file_playback import (
    DEFAULT_LEVEL as _DEFAULT_FILE_LEVEL,
    LEVEL_PRESETS as _FILE_LEVEL_PRESETS,
    create_audio_output_file_playback_widget,
    file_playback_argv,
)
from gst_device_explorer.gui.qt_audio_output_test import create_audio_output_test_widget
from gst_device_explorer.gui.qt_sections import copy_to_clipboard, create_text_label, target_from_summary, usb_path_from_group_item

_TONE_LEVEL_VOLUMES: dict[str, float] = {"Quiet": 0.2, "Normal": 0.5, "Loud": 0.8}
_DEFAULT_TONE_LEVEL = "Quiet"


def has_audio_output_explorer(detail: DetailPaneModel) -> bool:
    return detail.kind == "audio_output" and _endpoint_target(detail) is not None


def audio_output_explore_lines(detail: DetailPaneModel) -> tuple[str, ...]:
    target = _endpoint_target(detail)
    lines = ["Audio Output", _audio_header_text(detail)]
    lines.extend(_summary_lines(detail))
    lines.append("Audio Output Mode")
    for label, value in _mode_rows(detail):
        lines.extend((label, value))
    lines.append("Generated Output Pipeline")
    lines.append("Using default generated output candidate")
    if target is not None:
        lines.append(_generated_tone_pipeline(target, _audio_capability_values(detail), _DEFAULT_TONE_LEVEL))
    lines.append("Copy Pipeline")
    lines.append("Speaker Test")
    lines.extend(("Test Level", _DEFAULT_TONE_LEVEL))
    if _speaker_test_available(detail) and target is not None:
        lines.extend((
            "State: Ready",
            "Start Test",
            "Stop Test",
            "Plays a short generated tone through the selected output endpoint. "
            "Test Level adjusts only this generated pipeline and does not change "
            "system volume, mixer settings, or audio routing.",
        ))
    else:
        lines.extend((
            "State: Unavailable",
            "No safe generated speaker-test command is available for this endpoint.",
        ))
    lines.append("Local File Playback")
    if target is not None:
        lines.extend((
            "No file selected.",
            "Playback Level",
            _DEFAULT_FILE_LEVEL,
            "Start Playback",
            "Stop Playback",
            "Playback routes through the selected output endpoint. "
            "Playback Level adjusts only this playback pipeline and does not change "
            "system volume, mixer settings, or audio routing.",
        ))
    else:
        lines.append("No output endpoint is available.")
    return tuple(lines)


def create_audio_output_explorer_widget(
    detail: DetailPaneModel,
    *,
    status_callback: Callable[[str], None] | None = None,
    preview_runner: object | None = None,
    file_playback_runner: object | None = None,
) -> object:
    from PySide6.QtGui import QFont, QFontDatabase
    from PySide6.QtWidgets import QFormLayout, QGroupBox, QHBoxLayout, QLineEdit
    from PySide6.QtWidgets import QPushButton, QSizePolicy, QVBoxLayout, QWidget

    target = _endpoint_target(detail)
    values = _audio_capability_values(detail)
    pane = QWidget()
    layout = QVBoxLayout(pane)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)

    layout.addWidget(create_text_label(_audio_header_text(detail)))

    summary_box = QGroupBox("Audio Output")
    summary_layout = QVBoxLayout(summary_box)
    for line in _summary_lines(detail):
        summary_layout.addWidget(create_text_label(line))
    layout.addWidget(summary_box, 0)

    mode_box = QGroupBox("Audio Output Mode")
    mode_layout = QFormLayout(mode_box)
    for label, value in _mode_rows(detail):
        mode_layout.addRow(label, create_text_label(value))
    layout.addWidget(mode_box, 0)

    pipeline_box = QGroupBox("Generated Output Pipeline")
    pipeline_layout = QHBoxLayout(pipeline_box)
    pipeline_layout.setSpacing(6)
    _tone_level: list[str] = [_DEFAULT_TONE_LEVEL]
    pipeline_text = (
        _generated_tone_pipeline(target, values, _tone_level[0])
        if target is not None
        else "Pipeline unavailable."
    )
    pipeline_edit = QLineEdit(pipeline_text)
    pipeline_edit.setObjectName("audioOutputPipelineText")
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

    def _on_tone_level_change(level: str) -> None:
        _tone_level[0] = level
        if target is not None:
            pipeline_edit.setText(_generated_tone_pipeline(target, values, level))
            pipeline_edit.setCursorPosition(0)

    def current_test_command() -> PreviewCommand | None:
        if target is None or not _speaker_test_available(detail):
            return None
        return PreviewCommand(
            _generated_tone_argv(target, values, _tone_level[0]),
            target=target,
            description="Short generated speaker tone test",
        )

    speaker_test_widget, _refresh_speaker_test = create_audio_output_test_widget(
        current_test_command,
        preview_runner=preview_runner,
        on_level_change=_on_tone_level_change,
    )
    layout.addWidget(speaker_test_widget, 0)

    file_playback_widget, _refresh_file_playback = create_audio_output_file_playback_widget(
        target,
        preview_runner=file_playback_runner,
    )
    layout.addWidget(file_playback_widget, 0)

    layout.addStretch(1)
    return pane


def _summary_lines(detail: DetailPaneModel) -> tuple[str, ...]:
    lines = ["Kind: Audio Output"]
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


def _generated_tone_pipeline(target: str, values: dict[str, str], level: str) -> str:
    return " ".join(_generated_tone_argv(target, values, level))


def _generated_tone_argv(target: str, values: dict[str, str], level: str) -> tuple[str, ...]:
    volume = _TONE_LEVEL_VOLUMES.get(level, _TONE_LEVEL_VOLUMES[_DEFAULT_TONE_LEVEL])
    return (
        "gst-launch-1.0",
        "audiotestsrc",
        AUDIO_SINE_WAVE,
        AUDIO_SINE_FREQ,
        f"volume={volume}",
        "samplesperbuffer=2400",
        "num-buffers=20",
        "!",
        build_audio_caps_text(values),
        "!",
        "audioconvert",
        "!",
        "audioresample",
        "!",
        "alsasink",
        f"device={target}",
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
    button.setObjectName("audioOutputPipelineCopyButton")
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


def _speaker_test_available(detail: DetailPaneModel) -> bool:
    action = next((action for action in detail.actions if action.kind == "test_audio_output"), None)
    return bool(action and action.enabled)
