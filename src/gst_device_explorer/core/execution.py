"""Safe pipeline execution planning helpers."""

from __future__ import annotations

import shlex
import subprocess
from typing import Callable

from gst_device_explorer.core.models import ExecutionPlan, PipelineCandidate


class CandidateSelectionError(ValueError):
    """Raised when a requested pipeline candidate cannot be selected."""


class ExecutionStartError(RuntimeError):
    """Raised when a selected pipeline cannot be started."""


def select_pipeline_candidate(
    candidates: list[PipelineCandidate],
    selection: str | None = None,
) -> PipelineCandidate:
    """Select a pipeline candidate by zero-based index or stable ID."""

    if not candidates:
        raise CandidateSelectionError("no pipeline candidates are available")

    if selection is None:
        return candidates[0]

    if selection.isdecimal():
        index = int(selection)
        if index < len(candidates):
            return candidates[index]
        raise CandidateSelectionError(
            f"candidate index {index} is out of range; "
            f"available range is 0-{len(candidates) - 1}"
        )

    for candidate in candidates:
        if candidate.candidate_id == selection:
            return candidate

    available_ids = ", ".join(
        candidate.candidate_id for candidate in candidates if candidate.candidate_id
    )
    if available_ids:
        raise CandidateSelectionError(
            f"candidate ID '{selection}' was not found; "
            f"available IDs: {available_ids}"
        )
    raise CandidateSelectionError(f"candidate ID '{selection}' was not found")


def create_execution_plan(candidate: PipelineCandidate) -> ExecutionPlan:
    """Create an argv-based execution plan from a structured candidate."""

    argv = candidate.argv if candidate.argv else shlex.split(candidate.command)
    return ExecutionPlan(
        candidate_id=candidate.candidate_id,
        argv=list(argv),
        display_command=candidate.command,
        warnings=list(candidate.warnings),
    )


def run_execution_plan(
    plan: ExecutionPlan,
    popen_factory: Callable[..., subprocess.Popen] | None = None,
    terminate_timeout_seconds: float = 2.0,
    timeout_seconds: float | None = None,
) -> int:
    """Run a selected pipeline using argv form and return its exit status."""

    if popen_factory is None:
        popen_factory = subprocess.Popen

    try:
        process = popen_factory(plan.argv)
    except (FileNotFoundError, OSError) as error:
        raise ExecutionStartError(str(error)) from error

    try:
        if timeout_seconds is None:
            return process.wait()
        return process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        _terminate_process(process, terminate_timeout_seconds)
        return 124
    except KeyboardInterrupt:
        _terminate_process(process, terminate_timeout_seconds)
        return 130


def _terminate_process(
    process: subprocess.Popen,
    terminate_timeout_seconds: float,
) -> None:
    process.terminate()
    try:
        process.wait(timeout=terminate_timeout_seconds)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
