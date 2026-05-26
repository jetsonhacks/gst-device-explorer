"""Audio-input activity test Qt controls."""

from __future__ import annotations

from collections.abc import Callable

from gst_device_explorer.gui.preview_runner import PreviewCommand, PreviewRunner, PreviewState
from gst_device_explorer.gui.qt_sections import create_text_label


def create_audio_input_test_widget(
    command_getter: Callable[[], PreviewCommand | None],
    *,
    preview_runner: object | None = None,
) -> tuple[object, Callable[[], None]]:
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QPushButton, QSizePolicy, QVBoxLayout

    _runner_owned = preview_runner is None
    runner = preview_runner or PreviewRunner()
    test_box = QGroupBox("Audio Input Activity Test")
    layout = QVBoxLayout(test_box)
    state_label = create_text_label("State: Unavailable")
    state_label.setObjectName("audioInputTestStateText")
    message_label = create_text_label("")
    message_label.setObjectName("audioInputTestMessageText")
    note_label = create_text_label(
        "Opens the selected microphone with a generated pipeline. Does not record, save, or retain microphone audio."
    )
    note_label.setObjectName("audioInputTestSafetyText")
    layout.addWidget(state_label)
    layout.addWidget(message_label)
    layout.addWidget(note_label)

    button_row = QHBoxLayout()
    button_row.setSpacing(6)
    start_button = QPushButton("Start Test")
    start_button.setObjectName("audioInputTestStartButton")
    start_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    stop_button = QPushButton("Stop Test")
    stop_button.setObjectName("audioInputTestStopButton")
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
            message_label.setText(getattr(runner, "failure_text", None) or "Audio input activity test failed.")
        elif state == PreviewState.EXITED:
            state_label.setText("State: Exited")
            message_label.setText("Audio input activity test stopped.")
        elif active:
            state_label.setText(f"State: {state.value}")
            message_label.setText("Audio input activity test is running for the generated input command.")
        elif command is None:
            state_label.setText("State: Unavailable")
            message_label.setText("No safe generated audio-input activity command is available for this endpoint.")
        else:
            state_label.setText("State: Ready")
            message_label.setText("Audio input activity test will run the generated command shown above.")

        start_button.setEnabled(command is not None and not active)
        stop_button.setEnabled(active)
        if active and not poll_timer.isActive():
            poll_timer.start()
        elif not active and poll_timer.isActive():
            poll_timer.stop()

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

    start_button.clicked.connect(lambda _checked=False: start_test())
    stop_button.clicked.connect(lambda _checked=False: stop_test())
    poll_timer.timeout.connect(refresh)
    if _runner_owned:
        test_box.destroyed.connect(lambda _obj=None: runner.cleanup())
    refresh()
    return test_box, refresh
