from pathlib import Path
import subprocess
import sys

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.gui.preview_runner import PreviewCommand, PreviewRunner, PreviewState


def test_preview_runner_starts_from_structured_argv() -> None:
    calls: list[list[str]] = []
    process = _FakeProcess()
    runner = PreviewRunner(popen_factory=lambda argv: calls.append(argv) or process)

    command = PreviewCommand(["gst-launch-1.0", "fakesrc", "!", "fakesink"], target="/dev/video0")

    assert runner.start(command) is True
    assert calls == [["gst-launch-1.0", "fakesrc", "!", "fakesink"]]
    assert runner.state == PreviewState.RUNNING
    assert runner.command == command


def test_preview_command_rejects_shell_string_input() -> None:
    with pytest.raises(TypeError):
        PreviewCommand("gst-launch-1.0 fakesrc ! fakesink", target="/dev/video0")  # type: ignore[arg-type]


def test_preview_runner_failed_start_sets_failed_state() -> None:
    def fail_start(_argv: list[str]) -> object:
        raise FileNotFoundError("missing gst-launch-1.0")

    runner = PreviewRunner(popen_factory=fail_start)

    assert runner.start(PreviewCommand(["missing"], target="/dev/video0")) is False
    assert runner.state == PreviewState.FAILED
    assert runner.failure_text == "Preview failed to start: missing gst-launch-1.0"


def test_preview_runner_poll_detects_normal_exit() -> None:
    process = _FakeProcess(returncode=0)
    runner = PreviewRunner(popen_factory=lambda _argv: process)
    runner.start(PreviewCommand(["python", "-c", "pass"], target="/dev/video0"))

    assert runner.poll() == PreviewState.EXITED
    assert runner.exit_code == 0
    assert runner.failure_text is None


def test_preview_runner_poll_detects_failed_exit() -> None:
    process = _FakeProcess(returncode=2)
    runner = PreviewRunner(popen_factory=lambda _argv: process)
    runner.start(PreviewCommand(["python", "-c", "raise SystemExit(2)"], target="/dev/video0"))

    assert runner.poll() == PreviewState.FAILED
    assert runner.exit_code == 2
    assert runner.failure_text == "Preview exited with code 2."


def test_preview_runner_exit_code_1_is_graceful_close() -> None:
    # gst-launch-1.0 exits with code 1 when the user closes the preview window.
    # That is not a failure — treat it the same as code 0.
    process = _FakeProcess(returncode=1)
    runner = PreviewRunner(popen_factory=lambda _argv: process)
    runner.start(PreviewCommand(["gst-launch-1.0", "fakesrc", "!", "fakesink"], target="/dev/video0"))

    assert runner.poll() == PreviewState.EXITED
    assert runner.exit_code == 1
    assert runner.failure_text is None


def test_preview_runner_stop_terminates_process() -> None:
    process = _FakeProcess()
    runner = PreviewRunner(popen_factory=lambda _argv: process)
    runner.start(PreviewCommand(["python", "-c", "import time; time.sleep(10)"], target="/dev/video0"))

    assert runner.stop() == PreviewState.EXITED
    assert process.terminated is True
    assert process.killed is False


def test_preview_runner_stop_kills_after_timeout() -> None:
    process = _FakeProcess(timeout_on_wait=True)
    runner = PreviewRunner(popen_factory=lambda _argv: process, terminate_timeout_seconds=0.01)
    runner.start(PreviewCommand(["python", "-c", "import time; time.sleep(10)"], target="/dev/video0"))

    assert runner.stop() == PreviewState.EXITED
    assert process.terminated is True
    assert process.killed is True


class _FakeProcess:
    def __init__(self, returncode: int | None = None, timeout_on_wait: bool = False) -> None:
        self.returncode = returncode
        self.timeout_on_wait = timeout_on_wait
        self.terminated = False
        self.killed = False

    def poll(self) -> int | None:
        return self.returncode

    def terminate(self) -> None:
        self.terminated = True

    def kill(self) -> None:
        self.killed = True
        self.returncode = -9

    def wait(self, timeout: float | None = None) -> int:
        if self.timeout_on_wait and not self.killed:
            raise subprocess.TimeoutExpired("preview", timeout)
        if self.returncode is None:
            self.returncode = 0
        return self.returncode
