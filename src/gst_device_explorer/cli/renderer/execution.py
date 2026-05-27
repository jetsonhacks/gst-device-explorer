"""Renderers for pipeline execution and capture plans."""

from __future__ import annotations

from gst_device_explorer.core.models import ExecutionPlan


def print_execution_plan(plan: ExecutionPlan, dry_run: bool) -> None:
    print(f"Selected pipeline candidate: {plan.candidate_id}")
    print()
    print(plan.display_command)
    if plan.warnings:
        print()
        print("Warnings:")
        for warning in plan.warnings:
            print(f"- {warning}")
    print()
    if dry_run:
        print("Dry run only. Pipeline was not executed.")
    else:
        print("Running pipeline. Press Ctrl+C to stop.")


def print_capture_plan(
    plan: ExecutionPlan,
    endpoint: str,
    duration_seconds: float,
    output_path: str,
    dry_run: bool,
) -> None:
    if dry_run:
        print(f"Capture candidate: {plan.candidate_id}")
    else:
        print(f"Running capture candidate: {plan.candidate_id}")
    print(f"Endpoint: {endpoint}")
    print(f"Duration: {_format_duration(duration_seconds)} seconds")
    print(f"Output: {output_path}")
    print()
    if dry_run:
        print("Dry run: command not executed.")
        print()
    print(plan.display_command)
    if plan.warnings:
        print()
        print("Warnings:")
        for warning in plan.warnings:
            print(f"- {warning}")


def print_capture_completed() -> None:
    print()
    print("Capture completed.")


def print_capture_not_started_existing_output(output_path: str) -> None:
    print("Capture not started.")
    print()
    print("Output file already exists:")
    print(output_path)
    print()
    print("Choose a different output path.")


def _format_duration(duration_seconds: float) -> str:
    duration = float(duration_seconds)
    if duration.is_integer():
        return str(int(duration))
    return str(duration)
