"""Structured suggested command model and builders.

Suggested commands are advisory metadata. They are never executed automatically.
Consumers should treat them as display-only guidance for what a user can run next.
"""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass

SAFETY_INSPECTION = "inspection"
SAFETY_DRY_RUN = "dry_run"
SAFETY_BOUNDED_CAPTURE = "bounded_capture"
SAFETY_SAFE_EXECUTION = "safe_execution"
SAFETY_EXTERNAL_CHECK = "external_check"

_SAFETY_VALUES = frozenset(
    {
        SAFETY_INSPECTION,
        SAFETY_DRY_RUN,
        SAFETY_BOUNDED_CAPTURE,
        SAFETY_SAFE_EXECUTION,
        SAFETY_EXTERNAL_CHECK,
    }
)


@dataclass(frozen=True)
class SuggestedCommand:
    """A structured, advisory suggested command.

    Suggested commands are metadata only. They must not be executed automatically.
    The argv field preserves the structured command; command is the rendered display string.
    """

    id: str
    title: str
    argv: tuple[str, ...]
    purpose: str
    source: str
    safety: str
    target_kind: str | None = None
    target: str | None = None
    notes: tuple[str, ...] = ()

    @property
    def command(self) -> str:
        """Shell-safe display string rendered from argv."""
        return shlex.join(self.argv)


def _make_id(argv: tuple[str, ...]) -> str:
    """Generate a deterministic slug from argv, skipping the tool name."""
    parts = []
    for part in argv:
        if part == "gst-device-explorer":
            continue
        if part.startswith("--"):
            slug = re.sub(r"[^a-z0-9]+", "-", part[2:].lower()).strip("-")
        else:
            slug = re.sub(r"[^a-z0-9]+", "-", part.lower()).strip("-")
        if slug:
            parts.append(slug)
    return "-".join(parts) if parts else "cmd"


# ---------------------------------------------------------------------------
# Generic catalog builders
# ---------------------------------------------------------------------------


def suggest_env_command() -> SuggestedCommand:
    argv = ("gst-device-explorer", "env")
    return SuggestedCommand(
        id=_make_id(argv),
        title="Inspect GStreamer environment",
        argv=argv,
        purpose="Check GStreamer tool availability and element presence.",
        source="environment",
        safety=SAFETY_INSPECTION,
    )


def suggest_devices_command() -> SuggestedCommand:
    argv = ("gst-device-explorer", "devices")
    return SuggestedCommand(
        id=_make_id(argv),
        title="Discover all devices",
        argv=argv,
        purpose="Discover all video and audio devices on the system.",
        source="discovery",
        safety=SAFETY_INSPECTION,
    )


def suggest_audio_inputs_command() -> SuggestedCommand:
    argv = ("gst-device-explorer", "audio-inputs")
    return SuggestedCommand(
        id=_make_id(argv),
        title="Discover audio input devices",
        argv=argv,
        purpose="List all ALSA audio input devices.",
        source="discovery",
        safety=SAFETY_INSPECTION,
    )


def suggest_audio_outputs_command() -> SuggestedCommand:
    argv = ("gst-device-explorer", "audio-outputs")
    return SuggestedCommand(
        id=_make_id(argv),
        title="Discover audio output devices",
        argv=argv,
        purpose="List all ALSA audio output devices.",
        source="discovery",
        safety=SAFETY_INSPECTION,
    )


def suggest_group_list() -> SuggestedCommand:
    argv = ("gst-device-explorer", "groups")
    return SuggestedCommand(
        id=_make_id(argv),
        title="List composite device groups",
        argv=argv,
        purpose="List discovered composite device groups.",
        source="grouping",
        safety=SAFETY_INSPECTION,
    )


def suggest_group_validation(group_id: str) -> SuggestedCommand:
    argv = ("gst-device-explorer", "validate", "group", group_id)
    return SuggestedCommand(
        id=_make_id(argv),
        title=f"Validate composite group {group_id}",
        argv=argv,
        purpose=f"Summarize endpoint health for composite group {group_id}.",
        source="group_validation",
        safety=SAFETY_INSPECTION,
        target_kind="group",
        target=group_id,
    )


def suggest_report() -> SuggestedCommand:
    argv = ("gst-device-explorer", "report")
    return SuggestedCommand(
        id=_make_id(argv),
        title="Generate system report",
        argv=argv,
        purpose="Generate a structured report of all discovered devices and diagnostics.",
        source="report",
        safety=SAFETY_INSPECTION,
    )


def suggest_schema_list() -> SuggestedCommand:
    argv = ("gst-device-explorer", "schema", "list")
    return SuggestedCommand(
        id=_make_id(argv),
        title="List schema documents",
        argv=argv,
        purpose="List available schema discovery documents.",
        source="schema",
        safety=SAFETY_INSPECTION,
    )


def suggest_config_show() -> SuggestedCommand:
    argv = ("gst-device-explorer", "config", "show")
    return SuggestedCommand(
        id=_make_id(argv),
        title="Show configuration",
        argv=argv,
        purpose="Display the effective configuration settings.",
        source="config",
        safety=SAFETY_INSPECTION,
    )


def suggest_preset_list() -> SuggestedCommand:
    argv = ("gst-device-explorer", "preset", "list")
    return SuggestedCommand(
        id=_make_id(argv),
        title="List built-in presets",
        argv=argv,
        purpose="List the built-in named workflow presets.",
        source="presets",
        safety=SAFETY_INSPECTION,
    )


def suggest_preset_show(preset_id: str) -> SuggestedCommand:
    argv = ("gst-device-explorer", "preset", "show", preset_id)
    return SuggestedCommand(
        id=_make_id(argv),
        title=f"Show preset {preset_id}",
        argv=argv,
        purpose=f"Display details and required arguments for preset {preset_id}.",
        source="presets",
        safety=SAFETY_INSPECTION,
        target_kind="preset",
        target=preset_id,
    )


# ---------------------------------------------------------------------------
# Profile and pipeline builders
# ---------------------------------------------------------------------------


def suggest_profile(device_kind: str, device: str) -> SuggestedCommand:
    """Generic profile suggestion for any supported device kind."""
    argv = ("gst-device-explorer", "profile", device_kind, device)
    return SuggestedCommand(
        id=_make_id(argv),
        title=f"Inspect {device_kind} profile for {device}",
        argv=argv,
        purpose=f"Summarize {device_kind} endpoint capabilities for {device}.",
        source="device_profile",
        safety=SAFETY_INSPECTION,
        target_kind=device_kind,
        target=device,
    )


def suggest_video_profile(device: str) -> SuggestedCommand:
    argv = ("gst-device-explorer", "profile", "video", device)
    return SuggestedCommand(
        id=_make_id(argv),
        title=f"Inspect video profile for {device}",
        argv=argv,
        purpose=f"Summarize video endpoint capabilities and candidate availability for {device}.",
        source="device_profile",
        safety=SAFETY_INSPECTION,
        target_kind="video",
        target=device,
    )


def suggest_video_pipeline(device: str) -> SuggestedCommand:
    argv = ("gst-device-explorer", "pipeline", "video", device)
    return SuggestedCommand(
        id=_make_id(argv),
        title=f"List video pipeline candidates for {device}",
        argv=argv,
        purpose=f"List available video preview pipeline candidates for {device}.",
        source="device_profile",
        safety=SAFETY_INSPECTION,
        target_kind="video",
        target=device,
    )


def suggest_video_pipeline_diagnostics(device: str) -> SuggestedCommand:
    argv = ("gst-device-explorer", "pipeline", "video", device, "--diagnostics")
    return SuggestedCommand(
        id=_make_id(argv),
        title=f"Diagnose video pipeline candidates for {device}",
        argv=argv,
        purpose=f"Explain video candidate availability for {device}.",
        source="device_profile",
        safety=SAFETY_INSPECTION,
        target_kind="video",
        target=device,
    )


def suggest_video_run_dry_run(device: str) -> SuggestedCommand:
    argv = ("gst-device-explorer", "run", "video", device, "--dry-run")
    return SuggestedCommand(
        id=_make_id(argv),
        title=f"Preview video run command for {device}",
        argv=argv,
        purpose=f"Display the video preview command for {device} without executing it.",
        source="device_profile",
        safety=SAFETY_DRY_RUN,
        target_kind="video",
        target=device,
    )


def suggest_audio_input_profile(device: str) -> SuggestedCommand:
    argv = ("gst-device-explorer", "profile", "audio-input", device)
    return SuggestedCommand(
        id=_make_id(argv),
        title=f"Inspect audio input profile for {device}",
        argv=argv,
        purpose=f"Summarize audio input endpoint capabilities for {device}.",
        source="device_profile",
        safety=SAFETY_INSPECTION,
        target_kind="audio-input",
        target=device,
    )


def suggest_audio_input_pipeline(device: str) -> SuggestedCommand:
    argv = ("gst-device-explorer", "pipeline", "audio-input", device)
    return SuggestedCommand(
        id=_make_id(argv),
        title=f"List audio input pipeline candidates for {device}",
        argv=argv,
        purpose=f"List available audio input test pipeline candidates for {device}.",
        source="device_profile",
        safety=SAFETY_INSPECTION,
        target_kind="audio-input",
        target=device,
    )


def suggest_audio_input_pipeline_diagnostics(device: str) -> SuggestedCommand:
    argv = ("gst-device-explorer", "pipeline", "audio-input", device, "--diagnostics")
    return SuggestedCommand(
        id=_make_id(argv),
        title=f"Diagnose audio input pipeline candidates for {device}",
        argv=argv,
        purpose=f"Explain audio input candidate availability for {device}.",
        source="device_profile",
        safety=SAFETY_INSPECTION,
        target_kind="audio-input",
        target=device,
    )


def suggest_audio_input_run_dry_run(device: str) -> SuggestedCommand:
    argv = ("gst-device-explorer", "run", "audio-input", device, "--dry-run")
    return SuggestedCommand(
        id=_make_id(argv),
        title=f"Preview audio input run command for {device}",
        argv=argv,
        purpose=f"Display the audio input test command for {device} without executing it.",
        source="device_profile",
        safety=SAFETY_DRY_RUN,
        target_kind="audio-input",
        target=device,
    )


def suggest_audio_output_profile(device: str) -> SuggestedCommand:
    argv = ("gst-device-explorer", "profile", "audio-output", device)
    return SuggestedCommand(
        id=_make_id(argv),
        title=f"Inspect audio output profile for {device}",
        argv=argv,
        purpose=f"Summarize audio output endpoint capabilities for {device}.",
        source="device_profile",
        safety=SAFETY_INSPECTION,
        target_kind="audio-output",
        target=device,
    )


def suggest_audio_output_pipeline(device: str) -> SuggestedCommand:
    argv = ("gst-device-explorer", "pipeline", "audio-output", device)
    return SuggestedCommand(
        id=_make_id(argv),
        title=f"List audio output pipeline candidates for {device}",
        argv=argv,
        purpose=f"List available audio output test pipeline candidates for {device}.",
        source="device_profile",
        safety=SAFETY_INSPECTION,
        target_kind="audio-output",
        target=device,
    )


def suggest_audio_output_pipeline_diagnostics(device: str) -> SuggestedCommand:
    argv = ("gst-device-explorer", "pipeline", "audio-output", device, "--diagnostics")
    return SuggestedCommand(
        id=_make_id(argv),
        title=f"Diagnose audio output pipeline candidates for {device}",
        argv=argv,
        purpose=f"Explain audio output candidate availability for {device}.",
        source="device_profile",
        safety=SAFETY_INSPECTION,
        target_kind="audio-output",
        target=device,
    )


def suggest_audio_output_run_dry_run(device: str) -> SuggestedCommand:
    argv = ("gst-device-explorer", "run", "audio-output", device, "--dry-run")
    return SuggestedCommand(
        id=_make_id(argv),
        title=f"Preview audio output run command for {device}",
        argv=argv,
        purpose=f"Display the audio output test command for {device} without executing it.",
        source="device_profile",
        safety=SAFETY_DRY_RUN,
        target_kind="audio-output",
        target=device,
    )


def suggest_preset_command(
    preset_id: str,
    target_kind: str,
    target: str,
) -> SuggestedCommand:
    argv = ("gst-device-explorer", "preset", "command", preset_id, target_kind, target)
    return SuggestedCommand(
        id=_make_id(argv),
        title=f"Run preset {preset_id} for {target_kind} {target}",
        argv=argv,
        purpose=(
            f"Generate command suggestions for preset {preset_id} "
            f"applied to {target_kind} {target}."
        ),
        source="presets",
        safety=SAFETY_INSPECTION,
        target_kind=target_kind,
        target=target,
    )


def suggest_gst_inspect(element: str) -> SuggestedCommand:
    argv = ("gst-inspect-1.0", element)
    return SuggestedCommand(
        id=_make_id(argv),
        title=f"Inspect GStreamer element {element}",
        argv=argv,
        purpose=f"Check whether the GStreamer element {element} is installed.",
        source="diagnostics",
        safety=SAFETY_EXTERNAL_CHECK,
    )


# ---------------------------------------------------------------------------
# Generic catalog
# ---------------------------------------------------------------------------


def list_generic_suggestions() -> list[SuggestedCommand]:
    """Return the catalog of generic suggested commands in deterministic order."""
    return [
        suggest_env_command(),
        suggest_devices_command(),
        suggest_audio_inputs_command(),
        suggest_audio_outputs_command(),
        suggest_group_list(),
        suggest_report(),
        suggest_schema_list(),
        suggest_config_show(),
        suggest_preset_list(),
    ]
