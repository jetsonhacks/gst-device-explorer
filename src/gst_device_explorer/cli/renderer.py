"""Text and JSON rendering for gst-device-explorer CLI."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

from gst_device_explorer.core.grouping import GroupableDevice
from gst_device_explorer.core.config import ConfigValidationResult, ExplorerConfig
from gst_device_explorer.core.models import (
    CandidateRanking,
    Capability,
    CompositeDevice,
    Device,
    DeviceProfile,
    EnvironmentFact,
    ExecutionPlan,
    GroupValidation,
    PipelineCandidate,
    PipelineDiagnostic,
    SystemReport,
)
from gst_device_explorer.core.presets import PresetCommandSuggestions, PresetDefinition
from gst_device_explorer.cli.serializers import (
    candidate_ranking_to_json_dict,
    config_validation_result_to_json_dict,
    device_profile_to_json_dict,
    group_validation_to_json_dict,
    pipeline_diagnostic_to_json_dict,
    preset_command_suggestions_to_json_dict,
    preset_definition_to_json_dict,
    system_report_to_json_dict,
    to_json,
)


def print_devices(
    devices: list[Device],
    as_json: bool,
    empty_message: str = "No devices found.",
    heading: str = "Devices:",
) -> None:
    if as_json:
        print(to_json(devices))
        return

    if not devices:
        print(empty_message)
        return

    print(heading)
    for device in devices:
        backend = device.metadata.get("backend", "unknown")
        print(f"- {device.kind}: {device.name} ({device.id})")
        print(f"  backend: {backend}")


def print_environment(facts: list[EnvironmentFact], as_json: bool) -> None:
    if as_json:
        print(to_json(facts))
        return

    if not facts:
        print("No environment facts found.")
        return

    print("Environment:")
    for fact in facts:
        print(f"- {fact.name}: {fact.value}")
        if "element" in fact.metadata:
            print(f"  element: {fact.metadata['element']}")
        if fact.source is not None:
            print(f"  source: {fact.source}")


def print_composite_groups(groups: list[CompositeDevice], as_json: bool) -> None:
    if as_json:
        print(to_json(groups))
        return

    if not groups:
        print("No composite device groups found.")
        return

    print("Composite devices:")
    for group in groups:
        _print_composite_group_text(group)


def print_grouping_metadata(devices: list[GroupableDevice], as_json: bool) -> None:
    if as_json:
        print(to_json(devices))
        return

    if not devices:
        print("No grouping metadata records found.")
        return

    print("Grouping metadata:")
    for device in devices:
        print(f"- {device.name}")
        print(f"  role: {device.device_ref.role}")
        print(f"  device id: {device.device_ref.device_id}")
        if device.device_ref.path is not None:
            print(f"  path: {device.device_ref.path}")
        print(f"  subsystem: {device.device_ref.subsystem}")
        if device.metadata:
            print("  metadata:")
            for key in sorted(device.metadata):
                print(f"    {key}: {device.metadata[key]}")
        else:
            print("  metadata: none")


def print_composite_group(group: CompositeDevice, as_json: bool) -> None:
    if as_json:
        print(json.dumps(asdict(group), indent=2, sort_keys=True))
        return

    _print_composite_group_text(group)


def print_video_capabilities(
    capabilities: list[Capability],
    device_path: str,
    as_json: bool,
) -> None:
    if as_json:
        print(to_json(capabilities))
        return

    if not capabilities:
        print(f"No video capabilities found for {device_path}.")
        return

    print(f"Video capabilities for {device_path}:")
    for capability in capabilities:
        values = capability.values
        pixel_format = values.get("pixel_format", "unknown")
        description = values.get("description", "")
        width = values.get("width", "unknown")
        height = values.get("height", "unknown")
        fps_values = values.get("fps", [])
        fps = ", ".join(str(value) for value in fps_values) or "unknown"

        label = f"{pixel_format}"
        if description:
            label = f"{label} ({description})"

        print(f"- {label}: {width}x{height}")
        print(f"  fps: {fps}")
        if capability.source is not None:
            print(f"  source: {capability.source}")


def print_pipeline_candidates(
    candidates: list[PipelineCandidate],
    device_path: str,
    heading: str,
    empty_message: str,
    as_json: bool,
    show_all: bool = False,
    limit: int | None = None,
) -> None:
    rendered_candidates = _select_pipeline_candidates(
        candidates,
        as_json=as_json,
        show_all=show_all,
        limit=limit,
    )

    if as_json:
        print(to_json(rendered_candidates))
        return

    if not rendered_candidates:
        print(f"{empty_message} for {device_path}.")
        return

    print(f"{heading} for {device_path}:")
    for index, candidate in enumerate(rendered_candidates, start=1):
        print(f"{index}. {candidate.purpose}")
        if candidate.candidate_id:
            print(f"   id: {candidate.candidate_id}")
        print(f"   command: {candidate.command}")
        print(f"   confidence: {candidate.confidence}")
        if candidate.selected_profile is not None:
            print(f"   profile: {candidate.selected_profile}")
        if candidate.required_elements:
            print(
                "   required elements: "
                + ", ".join(candidate.required_elements)
            )
        if candidate.reasons:
            print("   reasons:")
            for reason in candidate.reasons:
                print(f"   - {reason}")
        if candidate.warnings:
            print("   warnings:")
            for warning in candidate.warnings:
                print(f"   - {warning}")


def print_device_profile(profile: DeviceProfile | None, as_json: bool) -> None:
    if profile is None:
        if as_json:
            print(json.dumps(None, indent=2, sort_keys=True))
            return
        print("No device profile found.")
        return

    if as_json:
        print(
            json.dumps(
                device_profile_to_json_dict(profile),
                indent=2,
                sort_keys=True,
            )
        )
        return

    print(f"Device profile for {profile.device_kind} {profile.device}")
    if profile.display_name is not None:
        print()
        print(f"Name: {profile.display_name}")
    if profile.metadata:
        print()
        print("Metadata:")
        for key in sorted(profile.metadata):
            print(f"  {key}: {profile.metadata[key]}")
    if profile.capabilities_summary:
        print()
        print("Capabilities:")
        _print_capabilities_summary(profile.capabilities_summary)
    print()
    print("Pipeline candidates:")
    for status in ("available", "unavailable"):
        for candidate in profile.candidate_summary.get(status, []):
            print(f"  {status:<11} {candidate.candidate_id}")
            if candidate.missing_elements:
                print("    missing: " + ", ".join(candidate.missing_elements))
    if profile.groups:
        print()
        print("Groups:")
        for group in profile.groups:
            print(f"  {group.label}    confidence {group.confidence:.2f}")
    print()
    print("Suggested next commands:")
    for command in profile.suggested_next_commands:
        print(f"  {command}")


def print_pipeline_diagnostics(
    diagnostics: list[PipelineDiagnostic],
    device_kind: str,
    device_path: str,
    as_json: bool,
) -> None:
    if as_json:
        print(
            json.dumps(
                {
                    "device_kind": device_kind,
                    "device": device_path,
                    "diagnostics": [
                        pipeline_diagnostic_to_json_dict(d)
                        for d in diagnostics
                    ],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return

    if not diagnostics:
        print(f"No pipeline diagnostics found for {device_kind} {device_path}.")
        return

    print(f"Pipeline diagnostics for {device_kind} {device_path}")
    for diagnostic in diagnostics:
        print()
        print(f"Candidate: {diagnostic.candidate_id}")
        print(f"Status: {diagnostic.status}")
        print(f"Reason: {diagnostic.reason}")
        print()
        print("Required elements:")
        for element in diagnostic.required_elements:
            marker = "ok" if element in diagnostic.available_elements else "missing"
            print(f"  {marker}: {element}")
        if diagnostic.suggested_next_checks:
            print()
            print("Suggested checks:")
            for check in diagnostic.suggested_next_checks:
                print(f"  {check}")
        elif diagnostic.status == "available":
            print()
            print("Suggested next step:")
            print(f"  gst-device-explorer run {device_kind} {device_path} --dry-run")


def print_candidate_ranking(ranking: CandidateRanking, as_json: bool) -> None:
    if as_json:
        print(
            json.dumps(candidate_ranking_to_json_dict(ranking), indent=2, sort_keys=True)
        )
        return

    print(f"Recommendations for {ranking.endpoint_kind} {ranking.endpoint}")
    print()

    if ranking.recommended_candidate_id is not None:
        print(f"Recommended: {ranking.recommended_candidate_id}")
    else:
        print("No available candidate.")

    if not ranking.ranked_candidates:
        return

    print()
    for item in ranking.ranked_candidates:
        status = "available" if item.available else "unavailable"
        print(f"{item.rank}. {item.candidate_id}  [{status}]")
        if item.selected_profile is not None:
            print(f"   Profile label: {item.selected_profile}")
        for reason in item.reasons:
            print(f"   Reason: {reason}")
        if item.warnings:
            for warning in item.warnings:
                print(f"   Warning: {warning}")
        if item.missing_elements:
            print(f"   Missing elements: {', '.join(item.missing_elements)}")
            print("   Suggested checks:")
            for element in item.missing_elements:
                print(f"     gst-inspect-1.0 {element}")


def print_system_report(report: SystemReport, as_json: bool) -> None:
    if as_json:
        print(json.dumps(system_report_to_json_dict(report), indent=2, sort_keys=True))
        return

    video_count = len(report.devices.video)
    audio_in_count = len(report.devices.audio_inputs)
    audio_out_count = len(report.devices.audio_outputs)
    group_count = len(report.groups)

    print(f"System report  tool version {report.tool_version}")
    print()
    print(f"Video devices:    {video_count}")
    print(f"Audio inputs:     {audio_in_count}")
    print(f"Audio outputs:    {audio_out_count}")
    print(f"Composite groups: {group_count}")

    if report.diagnostics.missing_elements:
        print()
        print("Missing GStreamer elements:")
        for element in report.diagnostics.missing_elements:
            print(f"  {element}")

    if report.suggested_next_commands:
        print()
        print("Suggested next commands:")
        for command in report.suggested_next_commands:
            print(f"  {command}")


def print_group_validation(validation: GroupValidation, as_json: bool) -> None:
    if as_json:
        print(json.dumps(group_validation_to_json_dict(validation), indent=2, sort_keys=True))
        return

    print(f"Composite group validation: {validation.group_id}")
    print(f"Status: {validation.status}")
    print(f"Grouping method: {validation.grouping_method}")
    if validation.group_label:
        print(f"Label: {validation.group_label}")

    if validation.evidence:
        print()
        print("Evidence:")
        for evidence in validation.evidence:
            print(f"- {evidence.source}: {evidence.description}")

    print()
    print("Endpoints:")
    if not validation.endpoint_summaries:
        print("- none")
    for summary in validation.endpoint_summaries:
        print(f"- {_endpoint_label(summary.endpoint_kind)}: {summary.endpoint}")
        print(f"  Status: {summary.status}")
        print(f"  Available candidates: {summary.available_candidate_count}")
        print(f"  Unavailable candidates: {summary.unavailable_candidate_count}")
        if summary.recommended_candidate_id is not None:
            print(f"  Recommended: {summary.recommended_candidate_id}")
        if summary.missing_elements:
            print(f"  Missing elements: {', '.join(summary.missing_elements)}")

    if validation.diagnostics.missing_elements:
        print()
        print("Missing elements:")
        for element in validation.diagnostics.missing_elements:
            print(f"- {element}")

    if validation.suggested_next_commands:
        print()
        print("Suggested next commands:")
        for command in validation.suggested_next_commands:
            print(f"- {command}")


def print_group_not_found(group_id: str, as_json: bool) -> None:
    if as_json:
        print(
            json.dumps(
                {
                    "error": "group_not_found",
                    "group_id": group_id,
                    "suggested_next_commands": ["gst-device-explorer groups"],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return

    print(f"Group not found: {group_id}")
    print()
    print("Run:")
    print("gst-device-explorer groups")


def print_preset_list(presets: list[PresetDefinition], as_json: bool) -> None:
    if as_json:
        print(
            json.dumps(
                [preset_definition_to_json_dict(preset) for preset in presets],
                indent=2,
                sort_keys=True,
            )
        )
        return

    print("Available presets:")
    for preset in presets:
        print(f"  {preset.preset_id:<32} {preset.description}")


def print_preset(preset: PresetDefinition, as_json: bool) -> None:
    if as_json:
        print(json.dumps(preset_definition_to_json_dict(preset), indent=2, sort_keys=True))
        return

    print(f"Preset: {preset.preset_id}")
    print(f"Title: {preset.title}")
    print(f"Target kind: {preset.target_kind}")
    if preset.related_command is not None:
        print(f"Related command: {preset.related_command}")
    print()
    print("Description:")
    print(f"  {preset.description}")
    if preset.arguments:
        print()
        print("Arguments:")
        for argument in preset.arguments:
            required = "required" if argument.required else "optional"
            print(f"  --{argument.name} ({required}): {argument.description}")
    if preset.safety_notes:
        print()
        print("Safety:")
        for note in preset.safety_notes:
            print(f"  - {note}")


def print_preset_command_suggestions(
    result: PresetCommandSuggestions,
    as_json: bool,
) -> None:
    if as_json:
        print(
            json.dumps(
                preset_command_suggestions_to_json_dict(result),
                indent=2,
                sort_keys=True,
            )
        )
        return

    print(f"Preset: {result.preset_id}")
    print(f"Target: {result.target_kind} {result.target}")
    print()
    heading = "Suggested command:" if len(result.suggestions) == 1 else "Suggested commands:"
    print(heading)
    for suggestion in result.suggestions:
        print(f"  {_render_argv(suggestion.argv)}")
        if suggestion.description:
            print(f"  {suggestion.description}")
    print()
    print("This command was not executed.")
    if any(suggestion.dry_run for suggestion in result.suggestions):
        print("Review the dry-run output before running a non-dry-run command.")


def print_preset_not_found(preset_id: str) -> None:
    print(f"Preset not found: {preset_id}")
    print()
    print("Try:")
    print("  gst-device-explorer preset list")


def print_preset_error(message: str) -> None:
    print(message)


def print_config_paths(paths: Sequence[Path], as_json: bool) -> None:
    if as_json:
        print(
            json.dumps(
                {
                    "paths": [str(path) for path in paths],
                    "required": False,
                    "applied": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return

    print("Configuration search paths:")
    for index, path in enumerate(paths, start=1):
        print(f"  {index}. {path}")
    print()
    print("No configuration file is required.")
    print("Milestone 12 only validates and displays configuration; it does not apply preferences yet.")


def print_config_show(result: ConfigValidationResult, as_json: bool) -> None:
    if as_json:
        print(
            json.dumps(
                config_validation_result_to_json_dict(result),
                indent=2,
                sort_keys=True,
            )
        )
        return

    if not result.valid:
        _print_config_invalid(result)
        return

    source = result.path if result.path is not None else "default"
    print(f"Configuration: {source}")
    print()
    if result.config is not None:
        _print_explorer_config(result.config)
    _print_config_issues("Warnings", result.warnings)
    print()
    print("Note: Configuration is currently display/validation only. It does not change command behavior yet.")


def print_config_validate(result: ConfigValidationResult, as_json: bool) -> None:
    if as_json:
        print(
            json.dumps(
                config_validation_result_to_json_dict(result),
                indent=2,
                sort_keys=True,
            )
        )
        return

    if not result.valid:
        _print_config_invalid(result)
        return

    if result.path is None:
        print("Configuration valid: default configuration")
        print("No configuration file found or required.")
    else:
        print(f"Configuration valid: {result.path}")
        if result.warnings:
            _print_config_issues("Warnings", result.warnings)
        else:
            print("Warnings: none")
    print("Preferences are not applied to command behavior in Milestone 12.")


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


def _print_composite_group_text(group: CompositeDevice) -> None:
    print(f"- {group.name}")
    print(f"  id: {group.id}")
    print(f"  kind: {group.kind}")
    print(f"  confidence: {group.confidence:.2f}")
    if group.members:
        print("  members:")
        for member in group.members:
            label = member.path or member.device_id
            print(f"    - {member.role}: {label}")
    if group.evidence:
        print("  evidence:")
        for evidence in group.evidence:
            print(f"    - {evidence.source}: {evidence.description}")


def _print_capabilities_summary(summary: dict) -> None:
    labels = {
        "formats": "Formats",
        "max_resolution": "Max resolution",
        "frame_rates": "Frame rates",
        "mode_count": "Mode count",
    }
    for key in ("formats", "max_resolution", "frame_rates", "mode_count"):
        if key not in summary:
            continue
        value = summary[key]
        if isinstance(value, list):
            rendered = ", ".join(str(item) for item in value)
        else:
            rendered = str(value)
        print(f"  {labels[key]}: {rendered}")


def _select_pipeline_candidates(
    candidates: list[PipelineCandidate],
    as_json: bool,
    show_all: bool,
    limit: int | None,
) -> list[PipelineCandidate]:
    if limit is not None:
        return candidates[: max(limit, 0)]
    if as_json or show_all:
        return candidates
    return candidates[:3]


def _format_duration(duration_seconds: float) -> str:
    duration = float(duration_seconds)
    if duration.is_integer():
        return str(int(duration))
    return str(duration)


def _endpoint_label(endpoint_kind: str) -> str:
    labels = {
        "video": "Video",
        "audio-input": "Audio input",
        "audio-output": "Audio output",
    }
    return labels.get(endpoint_kind, endpoint_kind.replace("-", " ").title())


def _render_argv(argv: tuple[str, ...]) -> str:
    return " ".join(argv)


def _print_explorer_config(config: ExplorerConfig) -> None:
    print("Video:")
    print(f"  preferred_sink: {_render_optional(config.video.preferred_sink)}")
    print(
        "  prefer_jetson_acceleration: "
        f"{_render_bool(config.video.prefer_jetson_acceleration)}"
    )
    print(f"  max_preview_width: {_render_optional(config.video.max_preview_width)}")
    print(f"  max_preview_height: {_render_optional(config.video.max_preview_height)}")
    print()
    print("Audio:")
    print(f"  output_test_frequency: {config.audio.output_test_frequency}")
    print(
        "  prefer_silent_input_tests: "
        f"{_render_bool(config.audio.prefer_silent_input_tests)}"
    )
    print()
    print("Report:")
    print(f"  include_metadata: {_render_bool(config.report.include_metadata)}")
    print(f"  include_diagnostics: {_render_bool(config.report.include_diagnostics)}")


def _print_config_invalid(result: ConfigValidationResult) -> None:
    source = result.path if result.path is not None else "default configuration"
    print(f"Configuration invalid: {source}")
    _print_config_issues("Errors", result.errors)
    _print_config_issues("Warnings", result.warnings)


def _print_config_issues(label: str, issues) -> None:
    if not issues:
        return
    print(f"{label}:")
    for issue in issues:
        print(f"  - {issue.path}: {issue.message}")


def _render_optional(value) -> str:
    return "none" if value is None else str(value)


def _render_bool(value: bool) -> str:
    return "true" if value else "false"
