"""Audio-output speaker test Qt controls."""

from __future__ import annotations

from collections.abc import Callable

from gst_device_explorer.gui.preview_runner import PreviewCommand, PreviewRunner, PreviewState
from gst_device_explorer.gui.qt_sections import create_text_label

_LEVEL_PRESETS: tuple[str, ...] = ("Quiet", "Normal", "Loud")
_DEFAULT_LEVEL = "Quiet"


def create_audio_output_test_widget(
    command_getter: Callable[[], PreviewCommand | None],
    *,
    preview_runner: object | None = None,
    on_level_change: Callable[[str], None] | None = None,
) -> tuple[object, Callable[[], None]]:
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import (
        QComboBox,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QPushButton,
        QSizePolicy,
        QVBoxLayout,
    )

    _runner_owned = preview_runner is None
    runner = preview_runner or PreviewRunner()
    test_box = QGroupBox("Speaker Test")
    layout = QVBoxLayout(test_box)

    level_form = QFormLayout()
    level_combo = QComboBox()
    level_combo.setObjectName("audioOutputTestLevelCombo")
    for preset in _LEVEL_PRESETS:
        level_combo.addItem(preset)
    level_combo.setCurrentText(_DEFAULT_LEVEL)
    level_form.addRow("Test Level:", level_combo)
    layout.addLayout(level_form)

    state_label = create_text_label("State: Unavailable")
    state_label.setObjectName("audioOutputTestStateText")
    message_label = create_text_label("")
    message_label.setObjectName("audioOutputTestMessageText")
    note_label = create_text_label(
        "Plays a short generated tone through the selected output endpoint. "
        "Test Level adjusts only this generated pipeline and does not change "
        "system volume, mixer settings, or audio routing."
    )
    note_label.setObjectName("audioOutputTestSafetyText")
    layout.addWidget(state_label)
    layout.addWidget(message_label)
    layout.addWidget(note_label)

    button_row = QHBoxLayout()
    button_row.setSpacing(6)
    start_button = QPushButton("Start Test")
    start_button.setObjectName("audioOutputTestStartButton")
    start_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    stop_button = QPushButton("Stop Test")
    stop_button.setObjectName("audioOutputTestStopButton")
    stop_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    button_row.addWidget(start_button)
    button_row.addWidget(stop_button)
    button_row.addStretch(1)
    layout.addLayout(button_row)

    poll_timer = QTimer(test_box)
    poll_timer.setInterval(250)

    def refresh() -> None:
        state = runner.poll()
        active = state in {PreviewState.STARTING, PreviewState.RUNNING, PreviewState.STOPPING}
        command = command_getter()
        if state == PreviewState.FAILED:
            state_label.setText("State: Failed")
            message_label.setText(getattr(runner, "failure_text", None) or "Speaker test failed.")
        elif state == PreviewState.EXITED:
            state_label.setText("State: Exited")
            message_label.setText("Speaker test stopped.")
        elif active:
            state_label.setText(f"State: {state.value}")
            message_label.setText("Speaker test is running for the generated audio output command.")
        elif command is None:
            state_label.setText("State: Unavailable")
            message_label.setText("No safe generated speaker-test command is available for this endpoint.")
        else:
            state_label.setText("State: Ready")
            message_label.setText("Speaker test will run the generated command shown above.")

        start_button.setEnabled(command is not None and not active)
        stop_button.setEnabled(active)
        if active and not poll_timer.isActive():
            poll_timer.start()
        elif not active and poll_timer.isActive():
            poll_timer.stop()

    def _on_level_changed(text: str) -> None:
        if on_level_change is not None:
            on_level_change(text)
        refresh()

    def start_test() -> None:
        command = command_getter()
        if command is None:
            refresh()
            return
        runner.start(command)
        refresh()

    def stop_test() -> None:
        runner.stop()
        refresh()

    level_combo.currentTextChanged.connect(_on_level_changed)
    start_button.clicked.connect(lambda _checked=False: start_test())
    stop_button.clicked.connect(lambda _checked=False: stop_test())
    poll_timer.timeout.connect(refresh)
    if _runner_owned:
        test_box.destroyed.connect(lambda _obj=None: runner.cleanup())
    refresh()
    return test_box, refresh
