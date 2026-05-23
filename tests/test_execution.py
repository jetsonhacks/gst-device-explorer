from pathlib import Path
import subprocess
import sys

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.core.execution import (
    CandidateSelectionError,
    create_execution_plan,
    run_execution_plan,
    select_pipeline_candidate,
)
from gst_device_explorer.core.models import ExecutionPlan, PipelineCandidate


def test_select_pipeline_candidate_defaults_to_first_candidate() -> None:
    candidates = [_candidate(1), _candidate(2)]

    assert select_pipeline_candidate(candidates) == candidates[0]


def test_select_pipeline_candidate_by_zero_based_index() -> None:
    candidates = [_candidate(1), _candidate(2)]

    assert select_pipeline_candidate(candidates, "1") == candidates[1]


def test_select_pipeline_candidate_by_id() -> None:
    candidates = [_candidate(1), _candidate(2)]

    assert select_pipeline_candidate(candidates, "test-candidate-2") == candidates[1]


def test_select_pipeline_candidate_rejects_invalid_index() -> None:
    with pytest.raises(CandidateSelectionError, match="out of range"):
        select_pipeline_candidate([_candidate(1)], "2")


def test_select_pipeline_candidate_rejects_invalid_id() -> None:
    with pytest.raises(CandidateSelectionError, match="was not found"):
        select_pipeline_candidate([_candidate(1)], "missing")


def test_create_execution_plan_uses_candidate_argv() -> None:
    candidate = _candidate(1)

    plan = create_execution_plan(candidate)

    assert plan.candidate_id == "test-candidate-1"
    assert plan.argv == ["gst-launch-1.0", "candidate-1"]
    assert plan.display_command == "gst-launch-1.0 candidate-1"


def test_run_execution_plan_invokes_popen_with_argv_form() -> None:
    calls = []
    process = _FakeProcess(return_code=0)
    plan = _execution_plan(["gst-launch-1.0", "candidate-1"])

    def fake_popen(*args, **kwargs):
        calls.append((args, kwargs))
        return process

    exit_code = run_execution_plan(plan, popen_factory=fake_popen)

    assert exit_code == 0
    assert calls == [((["gst-launch-1.0", "candidate-1"],), {})]


def test_run_execution_plan_propagates_child_return_code() -> None:
    process = _FakeProcess(return_code=37)
    plan = _execution_plan(["gst-launch-1.0", "candidate-1"])

    exit_code = run_execution_plan(plan, popen_factory=lambda argv: process)

    assert exit_code == 37


def test_run_execution_plan_terminates_child_on_keyboard_interrupt() -> None:
    process = _FakeProcess(
        return_code=0,
        interrupt_on_first_wait=True,
    )
    plan = _execution_plan(["gst-launch-1.0", "candidate-1"])

    exit_code = run_execution_plan(
        plan,
        popen_factory=lambda argv: process,
        terminate_timeout_seconds=0.01,
    )

    assert exit_code == 130
    assert process.terminated is True
    assert process.killed is False


def test_run_execution_plan_kills_child_if_terminate_times_out() -> None:
    process = _FakeProcess(
        return_code=0,
        interrupt_on_first_wait=True,
        timeout_after_terminate=True,
    )
    plan = _execution_plan(["gst-launch-1.0", "candidate-1"])

    exit_code = run_execution_plan(
        plan,
        popen_factory=lambda argv: process,
        terminate_timeout_seconds=0.01,
    )

    assert exit_code == 130
    assert process.terminated is True
    assert process.killed is True


def _candidate(index: int) -> PipelineCandidate:
    return PipelineCandidate(
        candidate_id=f"test-candidate-{index}",
        purpose=f"candidate {index}",
        command=f"gst-launch-1.0 candidate-{index}",
        confidence=1.0,
        argv=["gst-launch-1.0", f"candidate-{index}"],
    )


def _execution_plan(argv: list[str]) -> ExecutionPlan:
    return ExecutionPlan(
        candidate_id="test-candidate",
        argv=argv,
        display_command=" ".join(argv),
        warnings=[],
    )


class _FakeProcess:
    def __init__(
        self,
        return_code: int,
        interrupt_on_first_wait: bool = False,
        timeout_after_terminate: bool = False,
    ) -> None:
        self.return_code = return_code
        self.interrupt_on_first_wait = interrupt_on_first_wait
        self.timeout_after_terminate = timeout_after_terminate
        self.wait_calls = 0
        self.terminated = False
        self.killed = False

    def wait(self, timeout=None):
        self.wait_calls += 1
        if self.interrupt_on_first_wait and self.wait_calls == 1:
            raise KeyboardInterrupt
        if (
            timeout is not None
            and self.timeout_after_terminate
            and self.terminated
            and not self.killed
        ):
            raise subprocess.TimeoutExpired("gst-launch-1.0", timeout)
        return self.return_code

    def terminate(self) -> None:
        self.terminated = True

    def kill(self) -> None:
        self.killed = True
