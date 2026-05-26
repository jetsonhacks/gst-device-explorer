"""Audio-output local file playback Qt controls."""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

from gst_device_explorer.gui.preview_runner import PreviewCommand, PreviewRunner, PreviewState
from gst_device_explorer.gui.qt_sections import create_text_label

LEVEL_PRESETS: tuple[str, ...] = ("Quiet", "Normal", "Loud")
DEFAULT_LEVEL = "Quiet"
_LEVEL_VOLUMES: dict[str, float] = {"Quiet": 0.2, "Normal": 0.5, "Loud": 0.8}


def file_playback_argv(target: str, file_path: str, level: str) -> tuple[str, ...]:
    """Build structured argv for local file playback through the selected output endpoint."""
    volume = _LEVEL_VOLUMES.get(level, _LEVEL_VOLUMES[DEFAULT_LEVEL])
    return (
        "gst-launch-1.0",
        "filesrc",
        f"location={file_path}",
        "!",
        "decodebin",
        "!",
        "audioconvert",
        "!",
        "audioresample",
        "!",
        "volume",
        f"volume={volume}",
        "!",
        "alsasink",
        f"device={target}",
    )


def is_safe_local_file(path: str) -> bool:
    """Return True if path is an acceptable local file (not a URL, directory, or playlist)."""
    if not path:
        return False
    for scheme in ("http://", "https://", "ftp://", "rtsp://", "file://"):
        if path.lower().startswith(scheme):
            return False
    if os.path.isdir(path):
        return False
    return True


def create_audio_output_file_playback_widget(
    target: str | None,
    *,
    preview_runner: object | None = None,
    _select_file: Callable[[], str | None] | None = None,
) -> tuple[object, Callable[[], None]]:
    """Create the Local File Playback group box widget.

    _select_file is injectable for tests; in production it opens a QFileDialog.
    Returns (widget, refresh_callback).
    """
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import (
        QComboBox,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QSizePolicy,
        QVBoxLayout,
    )

    _runner_owned = preview_runner is None
    runner = preview_runner or PreviewRunner()
    _file_path: list[str | None] = [None]
    _level: list[str] = [DEFAULT_LEVEL]

    playback_box = QGroupBox("Local File Playback")
    layout = QVBoxLayout(playback_box)

    file_row = QHBoxLayout()
    select_button = QPushButton("Select Audio File")
    select_button.setObjectName("audioOutputPlaybackSelectButton")
    select_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    file_label = QLabel("No file selected.")
    file_label.setObjectName("audioOutputPlaybackFileLabel")
    file_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    file_row.addWidget(select_button)
    file_row.addWidget(file_label, 1)
    layout.addLayout(file_row)

    level_form = QFormLayout()
    level_combo = QComboBox()
    level_combo.setObjectName("audioOutputPlaybackLevelCombo")
    for preset in LEVEL_PRESETS:
        level_combo.addItem(preset)
    level_combo.setCurrentText(DEFAULT_LEVEL)
    level_form.addRow("Playback Level:", level_combo)
    layout.addLayout(level_form)

    state_label = create_text_label("State: Unavailable")
    state_label.setObjectName("audioOutputPlaybackStateText")
    message_label = create_text_label("")
    message_label.setObjectName("audioOutputPlaybackMessageText")
    note_label = create_text_label(
        "Playback routes through the selected output endpoint. "
        "Playback Level adjusts only this playback pipeline and does not change "
        "system volume, mixer settings, or audio routing."
    )
    note_label.setObjectName("audioOutputPlaybackSafetyText")
    layout.addWidget(state_label)
    layout.addWidget(message_label)
    layout.addWidget(note_label)

    button_row = QHBoxLayout()
    button_row.setSpacing(6)
    start_button = QPushButton("Start Playback")
    start_button.setObjectName("audioOutputPlaybackStartButton")
    start_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    stop_button = QPushButton("Stop Playback")
    stop_button.setObjectName("audioOutputPlaybackStopButton")
    stop_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    button_row.addWidget(start_button)
    button_row.addWidget(stop_button)
    button_row.addStretch(1)
    layout.addLayout(button_row)

    poll_timer = QTimer(playback_box)
    poll_timer.setInterval(250)

    def _current_command() -> PreviewCommand | None:
        if target is None or _file_path[0] is None:
            return None
        if not is_safe_local_file(_file_path[0]):
            return None
        return PreviewCommand(
            file_playback_argv(target, _file_path[0], _level[0]),
            target=target,
            description="Local file playback quality test",
        )

    def refresh() -> None:
        state = runner.poll()
        active = state in {PreviewState.STARTING, PreviewState.RUNNING, PreviewState.STOPPING}
        command = _current_command()
        if state == PreviewState.FAILED:
            state_label.setText("State: Failed")
            message_label.setText(
                getattr(runner, "failure_text", None)
                or "Playback failed. The file may not be supported or the endpoint may be unavailable."
            )
        elif state == PreviewState.EXITED:
            state_label.setText("State: Exited")
            message_label.setText("Playback stopped.")
        elif active:
            state_label.setText(f"State: {state.value}")
            message_label.setText("Playback is running.")
        elif target is None:
            state_label.setText("State: Unavailable")
            message_label.setText("No output endpoint is available.")
        elif _file_path[0] is None:
            state_label.setText("State: Unavailable")
            message_label.setText("Select a local audio file to enable playback.")
        else:
            state_label.setText("State: Ready")
            message_label.setText("Playback will route through the selected output endpoint.")

        start_button.setEnabled(command is not None and not active)
        stop_button.setEnabled(active)
        if active and not poll_timer.isActive():
            poll_timer.start()
        elif not active and poll_timer.isActive():
            poll_timer.stop()

    def _on_file_selected() -> None:
        if _select_file is not None:
            path = _select_file()
        else:
            path = _open_file_dialog(playback_box)
        if path and is_safe_local_file(path):
            _file_path[0] = path
            file_label.setText(Path(path).name)
            file_label.setToolTip(path)
        refresh()

    def _on_level_changed(text: str) -> None:
        _level[0] = text
        refresh()

    def start_playback() -> None:
        command = _current_command()
        if command is None:
            refresh()
            return
        runner.start(command)
        refresh()

    def stop_playback() -> None:
        runner.stop()
        refresh()

    select_button.clicked.connect(lambda _checked=False: _on_file_selected())
    level_combo.currentTextChanged.connect(_on_level_changed)
    start_button.clicked.connect(lambda _checked=False: start_playback())
    stop_button.clicked.connect(lambda _checked=False: stop_playback())
    poll_timer.timeout.connect(refresh)
    if _runner_owned:
        playback_box.destroyed.connect(lambda _obj=None: runner.cleanup())
    refresh()
    return playback_box, refresh


def _open_file_dialog(parent: object) -> str | None:
    from PySide6.QtWidgets import QFileDialog

    path, _ = QFileDialog.getOpenFileName(
        parent,
        "Select Audio File",
        "",
        "Audio Files (*.wav *.flac *.ogg *.mp3 *.m4a *.aac);;All Files (*)",
    )
    return path or None
