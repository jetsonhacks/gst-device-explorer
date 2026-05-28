"""Camera preview Qt controls."""

from __future__ import annotations

from collections.abc import Callable

from gst_device_explorer.gui.preview_runner import PreviewCommand, PreviewRunner, PreviewState


def create_camera_preview_widget(
    command_getter: Callable[[], PreviewCommand | None],
    *,
    preview_runner: object | None = None,
) -> tuple[object, object, Callable[[], None]]:
    """Return (preview_button, status_label, refresh).

    preview_button toggles between start and stop: clicking starts the preview
    when idle and stops it when running.  status_label shows one-line feedback.
    refresh polls the runner and synchronises both widgets; call it whenever the
    available command may have changed.
    """
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QSizePolicy, QStyle

    _runner_owned = preview_runner is None
    runner = preview_runner or PreviewRunner()

    preview_btn = QPushButton()
    preview_btn.setObjectName("cameraPreviewButton")
    preview_btn.setFixedSize(28, 28)
    preview_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    status_label = QLabel()
    status_label.setObjectName("cameraPreviewStatusLabel")
    status_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    poll_timer = QTimer(preview_btn)
    poll_timer.setInterval(250)

    def _status_text() -> str:
        state = runner.state
        if state == PreviewState.FAILED:
            reason = (getattr(runner, "failure_text", None) or "").strip()
            short = reason[:60] if reason else "unknown error"
            return f"Preview failed: {short}"
        if state == PreviewState.EXITED:
            return "Preview closed"
        if state in {PreviewState.RUNNING, PreviewState.STOPPING}:
            return "Preview running"
        if state == PreviewState.STARTING:
            return "Starting preview..."
        return "Ready" if command_getter() is not None else "Unavailable"

    def refresh() -> None:
        state = runner.poll()
        active = state in {PreviewState.STARTING, PreviewState.RUNNING, PreviewState.STOPPING}
        command = command_getter()

        style = QApplication.style()
        status_label.setText(_status_text())

        if active:
            preview_btn.setIcon(style.standardIcon(QStyle.SP_MediaStop))
            preview_btn.setToolTip("Stop preview")
            preview_btn.setEnabled(True)
        else:
            preview_btn.setIcon(style.standardIcon(QStyle.SP_MediaPlay))
            preview_btn.setToolTip("Open preview window")
            preview_btn.setEnabled(command is not None)

        if active and not poll_timer.isActive():
            poll_timer.start()
        elif not active and poll_timer.isActive():
            poll_timer.stop()

    def on_toggle(_checked: bool = False) -> None:
        state = runner.poll()
        active = state in {PreviewState.STARTING, PreviewState.RUNNING, PreviewState.STOPPING}
        if active:
            runner.stop()
        else:
            command = command_getter()
            if command is not None:
                runner.start(command)
        refresh()

    preview_btn.clicked.connect(on_toggle)
    poll_timer.timeout.connect(refresh)
    if _runner_owned:
        preview_btn.destroyed.connect(lambda _obj=None: runner.cleanup())
    refresh()
    return preview_btn, status_label, refresh
