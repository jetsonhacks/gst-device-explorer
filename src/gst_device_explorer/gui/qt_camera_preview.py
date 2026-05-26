"""Camera preview Qt controls."""

from __future__ import annotations

from collections.abc import Callable

from gst_device_explorer.gui.preview_runner import PreviewCommand, PreviewRunner, PreviewState
from gst_device_explorer.gui.qt_sections import create_text_label


def create_camera_preview_widget(
    command_getter: Callable[[], PreviewCommand | None],
    *,
    preview_runner: object | None = None,
) -> tuple[object, Callable[[], None]]:
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QPushButton, QSizePolicy, QVBoxLayout

    runner = preview_runner or PreviewRunner()
    preview_box = QGroupBox("Preview")
    preview_layout = QVBoxLayout(preview_box)
    state_label = create_text_label("State: Unavailable")
    state_label.setObjectName("cameraPreviewStateText")
    message_label = create_text_label("")
    message_label.setObjectName("cameraPreviewMessageText")
    preview_layout.addWidget(state_label)
    preview_layout.addWidget(message_label)

    button_row = QHBoxLayout()
    button_row.setSpacing(6)
    start_button = QPushButton("Start Preview")
    start_button.setObjectName("cameraPreviewStartButton")
    start_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    stop_button = QPushButton("Stop Preview")
    stop_button.setObjectName("cameraPreviewStopButton")
    stop_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    button_row.addWidget(start_button)
    button_row.addWidget(stop_button)
    button_row.addStretch(1)
    preview_layout.addLayout(button_row)

    poll_timer = QTimer(preview_box)
    poll_timer.setInterval(250)

    def refresh() -> None:
        state = runner.poll()
        active = state in {PreviewState.STARTING, PreviewState.RUNNING, PreviewState.STOPPING}
        command = command_getter()
        if state == PreviewState.FAILED:
            state_label.setText("State: Failed")
            message_label.setText(getattr(runner, "failure_text", None) or "Preview failed.")
        elif state == PreviewState.EXITED:
            state_label.setText("State: Exited")
            message_label.setText("Preview stopped.")
        elif active:
            state_label.setText(f"State: {state.value}")
            message_label.setText("Preview is running for the generated camera command.")
        elif command is None:
            state_label.setText("State: Unavailable")
            message_label.setText("Preview unavailable: no eligible generated camera preview candidate.")
        else:
            state_label.setText("State: Ready")
            message_label.setText("Preview will run the generated command shown above.")

        start_button.setEnabled(command is not None and not active)
        stop_button.setEnabled(active)
        if active and not poll_timer.isActive():
            poll_timer.start()
        elif not active and poll_timer.isActive():
            poll_timer.stop()

    def start_preview() -> None:
        command = command_getter()
        if command is None:
            refresh()
            return
        runner.start(command)
        refresh()

    def stop_preview() -> None:
        runner.stop()
        refresh()

    start_button.clicked.connect(lambda _checked=False: start_preview())
    stop_button.clicked.connect(lambda _checked=False: stop_preview())
    poll_timer.timeout.connect(refresh)
    preview_box.destroyed.connect(lambda _obj=None: runner.cleanup())
    refresh()
    return preview_box, refresh
