"""Small GUI-facing process runner for generated preview commands."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum
import subprocess


class PreviewState(str, Enum):
    IDLE = "Idle"
    READY = "Ready"
    STARTING = "Starting"
    RUNNING = "Running"
    STOPPING = "Stopping"
    EXITED = "Exited"
    FAILED = "Failed"
    UNAVAILABLE = "Unavailable"


@dataclass(frozen=True)
class PreviewCommand:
    """Structured generated preview command.

    The GUI must pass argv data through this object instead of shell text.
    """

    argv: tuple[str, ...]
    target: str
    description: str = "Generated camera preview command"

    def __init__(self, argv: Sequence[str], target: str, description: str = "Generated camera preview command") -> None:
        if isinstance(argv, str):
            raise TypeError("preview commands require structured argv, not shell text")
        argv_tuple = tuple(str(part) for part in argv)
        if not argv_tuple:
            raise ValueError("preview commands require at least one argv item")
        object.__setattr__(self, "argv", argv_tuple)
        object.__setattr__(self, "target", target)
        object.__setattr__(self, "description", description)


class PreviewRunner:
    """Own preview subprocess lifecycle for the Qt layer."""

    def __init__(
        self,
        *,
        popen_factory: Callable[[list[str]], object] | None = None,
        terminate_timeout_seconds: float = 2.0,
    ) -> None:
        self._popen_factory = popen_factory or subprocess.Popen
        self._terminate_timeout_seconds = terminate_timeout_seconds
        self._process: object | None = None
        self._command: PreviewCommand | None = None
        self.state = PreviewState.IDLE
        self.failure_text: str | None = None
        self.exit_code: int | None = None

    @property
    def command(self) -> PreviewCommand | None:
        return self._command

    def start(self, command: PreviewCommand) -> bool:
        """Start a structured generated preview command."""

        self.poll()
        if self.state in {PreviewState.STARTING, PreviewState.RUNNING, PreviewState.STOPPING}:
            self.failure_text = "Preview is already running."
            return False

        self.state = PreviewState.STARTING
        self.failure_text = None
        self.exit_code = None
        self._command = command
        try:
            self._process = self._popen_factory(list(command.argv))
        except (FileNotFoundError, OSError) as error:
            self._process = None
            self.state = PreviewState.FAILED
            self.failure_text = f"Preview failed to start: {error}"
            return False

        self.state = PreviewState.RUNNING
        return True

    def poll(self) -> PreviewState:
        """Refresh state from the child process, if one is active."""

        if self._process is None:
            return self.state
        poll = getattr(self._process, "poll", None)
        if poll is None:
            return self.state
        code = poll()
        if code is None:
            return self.state

        self.exit_code = int(code)
        self._process = None
        if code == 0:
            self.state = PreviewState.EXITED
            self.failure_text = None
        else:
            self.state = PreviewState.FAILED
            self.failure_text = f"Preview exited with code {code}."
        return self.state

    def stop(self) -> PreviewState:
        """Stop the running preview process and clean up."""

        self.poll()
        if self._process is None:
            if self.state == PreviewState.RUNNING:
                self.state = PreviewState.EXITED
            return self.state

        self.state = PreviewState.STOPPING
        process = self._process
        try:
            process.terminate()
            process.wait(timeout=self._terminate_timeout_seconds)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        except OSError as error:
            self.state = PreviewState.FAILED
            self.failure_text = f"Preview cleanup failed: {error}"
            self._process = None
            return self.state

        self._process = None
        self.state = PreviewState.EXITED
        self.failure_text = None
        return self.state

    def cleanup(self) -> PreviewState:
        return self.stop()
