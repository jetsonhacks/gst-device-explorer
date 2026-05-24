"""Text and JSON rendering for gst-device-explorer CLI."""

from __future__ import annotations

import json
from dataclasses import asdict

from gst_device_explorer.core.grouping import GroupableDevice
from gst_device_explorer.core.models import (
    Capability,
    CompositeDevice,
    Device,
    DeviceProfile,
    EnvironmentFact,
    ExecutionPlan,
    PipelineCandidate,
    PipelineDiagnostic,
    SystemReport,
)
from gst_device_explorer.cli.serializers import (
    device_profile_to_json_dict,
    pipeline_diagnostic_to_json_dict,
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
