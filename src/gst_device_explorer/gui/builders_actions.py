"""GuiAction factory functions for device detail panes."""

from __future__ import annotations

from gst_device_explorer.core.suggestions import (
    SAFETY_BOUNDED_CAPTURE,
    SAFETY_DRY_RUN,
    SAFETY_INSPECTION,
    SAFETY_SAFE_EXECUTION,
    suggest_audio_input_pipeline_diagnostics,
    suggest_audio_input_run_dry_run,
    suggest_audio_output_pipeline_diagnostics,
    suggest_audio_output_run_dry_run,
    suggest_devices_command,
    suggest_report,
    suggest_video_pipeline_diagnostics,
    suggest_video_run_dry_run,
)
from gst_device_explorer.gui.model import GuiAction


def _refresh_action() -> GuiAction:
    return GuiAction(
        id="refresh:devices",
        label="Refresh",
        kind="refresh",
        enabled=True,
        safety=SAFETY_INSPECTION,
        suggested_command=suggest_devices_command(),
    )


def _export_report_action() -> GuiAction:
    return GuiAction(
        id="export:report",
        label="Export Report",
        kind="export_report",
        enabled=True,
        safety=SAFETY_INSPECTION,
        suggested_command=suggest_report(),
    )


def _diagnostics_action(target_kind: str, target: str) -> GuiAction:
    suggestion = {
        "video": suggest_video_pipeline_diagnostics,
        "audio-input": suggest_audio_input_pipeline_diagnostics,
        "audio-output": suggest_audio_output_pipeline_diagnostics,
    }[target_kind](target)
    return GuiAction(
        id=f"diagnostics:{target_kind}:{target}",
        label="Show Diagnostics",
        kind="show_diagnostics",
        enabled=True,
        safety=SAFETY_INSPECTION,
        target_kind=target_kind,
        target=target,
        suggested_command=suggestion,
    )


def _dry_run_action(target_kind: str, target: str) -> GuiAction:
    suggestion = {
        "video": suggest_video_run_dry_run,
        "audio-input": suggest_audio_input_run_dry_run,
        "audio-output": suggest_audio_output_run_dry_run,
    }[target_kind](target)
    return GuiAction(
        id=f"dry-run:{target_kind}:{target}",
        label="Dry Run",
        kind="dry_run",
        enabled=True,
        safety=SAFETY_DRY_RUN,
        target_kind=target_kind,
        target=target,
        suggested_command=suggestion,
    )


def _run_action(
    *,
    action_id: str,
    label: str,
    kind: str,
    target_kind: str,
    target: str,
    enabled: bool,
) -> GuiAction:
    return GuiAction(
        id=action_id,
        label=label,
        kind=kind,
        enabled=enabled,
        safety=SAFETY_SAFE_EXECUTION,
        target_kind=target_kind,
        target=target,
        suggested_command=None,
        disabled_reason=None if enabled else "No available generated candidate is known yet.",
    )


def _capture_action(target_kind: str, target: str) -> GuiAction:
    return GuiAction(
        id=f"capture:{target_kind}:{target}",
        label="Capture",
        kind="capture",
        enabled=False,
        safety=SAFETY_BOUNDED_CAPTURE,
        target_kind=target_kind,
        target=target,
        suggested_command=None,
        disabled_reason="Choose an explicit output path before capture.",
    )
