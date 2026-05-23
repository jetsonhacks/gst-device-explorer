"""Minimal command line renderer for gst-device-explorer."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from typing import Sequence

from gst_device_explorer.core.models import (
    Capability,
    CompositeDevice,
    Device,
    EnvironmentFact,
    ExecutionPlan,
    PipelineCandidate,
)
from gst_device_explorer.core.grouping import GroupableDevice
import gst_device_explorer.core.discovery as discovery
import gst_device_explorer.core.execution as execution
import gst_device_explorer.core.audio_pipelines as audio_pipelines
import gst_device_explorer.core.pipelines as pipelines
import gst_device_explorer.probes.alsa as alsa_probe
import gst_device_explorer.probes.gst as gst_probe
import gst_device_explorer.probes.v4l2 as v4l2_probe


def main(argv: Sequence[str] | None = None) -> int:
    """Run the gst-device-explorer CLI."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "devices":
        devices = discovery.discover_devices()
        _print_devices(devices, as_json=args.json)
        return 0

    if args.command == "groups":
        if args.metadata:
            groupable_devices = discovery.discover_groupable_devices()
            _print_grouping_metadata(groupable_devices, as_json=args.json)
            return 0
        groups = discovery.discover_composite_devices()
        _print_composite_groups(groups, as_json=args.json)
        return 0

    if args.command == "group":
        groups = discovery.discover_composite_devices()
        group = _find_composite_group(groups, args.group_id)
        if group is None:
            print(f"Composite device group not found: {args.group_id}")
            return 1
        _print_composite_group(group, as_json=args.json)
        return 0

    if args.command == "env":
        facts = gst_probe.inspect_gstreamer_environment()
        _print_environment(facts, as_json=args.json)
        return 0

    if args.command == "audio-inputs":
        devices = alsa_probe.discover_alsa_audio_inputs()
        _print_devices(
            devices,
            as_json=args.json,
            empty_message="No ALSA audio input devices found.",
            heading="Audio input devices:",
        )
        return 0

    if args.command == "audio-outputs":
        devices = alsa_probe.discover_alsa_audio_outputs()
        _print_devices(
            devices,
            as_json=args.json,
            empty_message="No ALSA audio output devices found.",
            heading="Audio output devices:",
        )
        return 0

    if args.command == "video":
        capabilities = v4l2_probe.discover_v4l2_capabilities(args.device_path)
        _print_video_capabilities(
            capabilities,
            device_path=args.device_path,
            as_json=args.json,
        )
        return 0

    if args.command == "pipeline" and args.pipeline_command == "video":
        candidates = _build_video_preview_candidates(args.device_path)
        _print_pipeline_candidates(
            candidates,
            device_path=args.device_path,
            heading="Video preview pipeline candidates",
            empty_message="No video preview pipeline candidates found",
            as_json=args.json,
            show_all=args.all,
            limit=args.limit,
        )
        return 0

    if args.command == "pipeline" and args.pipeline_command == "audio-input":
        candidates = _build_audio_input_test_candidates(args.alsa_device)
        _print_pipeline_candidates(
            candidates,
            device_path=args.alsa_device,
            heading="Audio input pipeline candidates",
            empty_message="No audio input pipeline candidates found",
            as_json=args.json,
        )
        return 0

    if args.command == "pipeline" and args.pipeline_command == "audio-output":
        candidates = _build_audio_output_test_candidates(args.alsa_device)
        _print_pipeline_candidates(
            candidates,
            device_path=args.alsa_device,
            heading="Audio output pipeline candidates",
            empty_message="No audio output pipeline candidates found",
            as_json=args.json,
        )
        return 0

    if args.command == "run" and args.run_command == "video":
        candidates = _build_video_preview_candidates(args.device_path)
        return _run_selected_candidate(
            candidates,
            device_label=args.device_path,
            inspect_commands=[f"gst-device-explorer video {args.device_path}"],
            selection=args.candidate,
            dry_run=args.dry_run,
        )

    if args.command == "run" and args.run_command == "audio-input":
        candidates = _build_audio_input_test_candidates(args.alsa_device)
        return _run_selected_candidate(
            candidates,
            device_label=args.alsa_device,
            inspect_commands=[
                "gst-device-explorer audio-inputs",
                f"gst-device-explorer pipeline audio-input {args.alsa_device}",
            ],
            selection=args.candidate,
            dry_run=args.dry_run,
        )

    if args.command == "run" and args.run_command == "audio-output":
        candidates = _build_audio_output_test_candidates(args.alsa_device)
        return _run_selected_candidate(
            candidates,
            device_label=args.alsa_device,
            inspect_commands=[
                "gst-device-explorer audio-outputs",
                f"gst-device-explorer pipeline audio-output {args.alsa_device}",
            ],
            selection=args.candidate,
            dry_run=args.dry_run,
        )

    parser.error("unknown command")
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gst-device-explorer",
        description="Explore GStreamer-oriented media devices.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    devices_parser = subparsers.add_parser(
        "devices",
        help="Discover video and audio devices.",
    )
    devices_parser.add_argument(
        "--json",
        action="store_true",
        help="Render devices as JSON.",
    )

    groups_parser = subparsers.add_parser(
        "groups",
        help="Discover composite device groups.",
    )
    groups_parser.add_argument(
        "--json",
        action="store_true",
        help="Render composite device groups as JSON.",
    )
    groups_parser.add_argument(
        "--metadata",
        action="store_true",
        help="Render metadata records consumed by the grouping engine.",
    )

    group_parser = subparsers.add_parser(
        "group",
        help="Inspect one composite device group.",
    )
    group_parser.add_argument("group_id", help="Composite device group ID.")
    group_parser.add_argument(
        "--json",
        action="store_true",
        help="Render one composite device group as JSON.",
    )

    env_parser = subparsers.add_parser(
        "env",
        help="Inspect the GStreamer environment.",
    )
    env_parser.add_argument(
        "--json",
        action="store_true",
        help="Render environment facts as JSON.",
    )

    audio_inputs_parser = subparsers.add_parser(
        "audio-inputs",
        help="Discover ALSA audio input devices.",
    )
    audio_inputs_parser.add_argument(
        "--json",
        action="store_true",
        help="Render audio input devices as JSON.",
    )

    audio_outputs_parser = subparsers.add_parser(
        "audio-outputs",
        help="Discover ALSA audio output devices.",
    )
    audio_outputs_parser.add_argument(
        "--json",
        action="store_true",
        help="Render audio output devices as JSON.",
    )

    video_parser = subparsers.add_parser(
        "video",
        help="Inspect one V4L2 video device.",
    )
    video_parser.add_argument("device_path", help="Path to a video device.")
    video_parser.add_argument(
        "--json",
        action="store_true",
        help="Render video capabilities as JSON.",
    )

    pipeline_parser = subparsers.add_parser(
        "pipeline",
        help="Build pipeline candidates.",
    )
    pipeline_subparsers = pipeline_parser.add_subparsers(
        dest="pipeline_command",
        required=True,
    )
    pipeline_video_parser = pipeline_subparsers.add_parser(
        "video",
        help="Build V4L2 video preview pipeline candidates.",
    )
    pipeline_video_parser.add_argument(
        "device_path",
        help="Path to a video device.",
    )
    pipeline_video_parser.add_argument(
        "--json",
        action="store_true",
        help="Render pipeline candidates as JSON.",
    )
    pipeline_video_parser.add_argument(
        "--all",
        action="store_true",
        help="Render every pipeline candidate in text mode.",
    )
    pipeline_video_parser.add_argument(
        "--limit",
        type=int,
        help="Limit the number of rendered pipeline candidates.",
    )
    pipeline_audio_input_parser = pipeline_subparsers.add_parser(
        "audio-input",
        help="Build ALSA audio input test pipeline candidates.",
    )
    pipeline_audio_input_parser.add_argument(
        "alsa_device",
        help="ALSA device name such as hw:0,0.",
    )
    pipeline_audio_input_parser.add_argument(
        "--json",
        action="store_true",
        help="Render pipeline candidates as JSON.",
    )
    pipeline_audio_output_parser = pipeline_subparsers.add_parser(
        "audio-output",
        help="Build ALSA audio output test pipeline candidates.",
    )
    pipeline_audio_output_parser.add_argument(
        "alsa_device",
        help="ALSA device name such as hw:0,0.",
    )
    pipeline_audio_output_parser.add_argument(
        "--json",
        action="store_true",
        help="Render pipeline candidates as JSON.",
    )

    run_parser = subparsers.add_parser(
        "run",
        help="Select and run one pipeline candidate.",
    )
    run_subparsers = run_parser.add_subparsers(
        dest="run_command",
        required=True,
    )
    run_video_parser = run_subparsers.add_parser(
        "video",
        help="Run one generated V4L2 video preview pipeline candidate.",
    )
    run_video_parser.add_argument(
        "device_path",
        help="Path to a video device.",
    )
    run_video_parser.add_argument(
        "--candidate",
        help="Candidate zero-based index or stable candidate ID.",
    )
    run_video_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the selected command without starting GStreamer.",
    )
    run_audio_input_parser = run_subparsers.add_parser(
        "audio-input",
        help="Run one generated ALSA audio input test pipeline candidate.",
    )
    run_audio_input_parser.add_argument(
        "alsa_device",
        help="ALSA device name such as hw:0,0.",
    )
    run_audio_input_parser.add_argument(
        "--candidate",
        help="Candidate zero-based index or stable candidate ID.",
    )
    run_audio_input_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the selected command without starting GStreamer.",
    )
    run_audio_output_parser = run_subparsers.add_parser(
        "audio-output",
        help="Run one generated ALSA audio output test pipeline candidate.",
    )
    run_audio_output_parser.add_argument(
        "alsa_device",
        help="ALSA device name such as hw:0,0.",
    )
    run_audio_output_parser.add_argument(
        "--candidate",
        help="Candidate zero-based index or stable candidate ID.",
    )
    run_audio_output_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the selected command without starting GStreamer.",
    )

    return parser


def _build_video_preview_candidates(device_path: str) -> list[PipelineCandidate]:
    device = Device(
        id=device_path,
        kind="video_input",
        name=device_path,
        metadata={"backend": "v4l2", "path": device_path},
    )
    capabilities = v4l2_probe.discover_v4l2_capabilities(device_path)
    environment = gst_probe.inspect_gstreamer_environment()
    return pipelines.build_video_preview_candidates(
        device,
        capabilities,
        environment,
    )


def _build_audio_input_test_candidates(alsa_device: str) -> list[PipelineCandidate]:
    device = _find_alsa_device(
        alsa_probe.discover_alsa_audio_inputs(),
        alsa_device,
        kind="audio_input",
    )
    if device is None:
        return []

    environment = gst_probe.inspect_gstreamer_environment()
    return audio_pipelines.build_audio_input_test_candidates(device, environment)


def _build_audio_output_test_candidates(alsa_device: str) -> list[PipelineCandidate]:
    device = _find_alsa_device(
        alsa_probe.discover_alsa_audio_outputs(),
        alsa_device,
        kind="audio_output",
    )
    if device is None:
        return []

    environment = gst_probe.inspect_gstreamer_environment()
    return audio_pipelines.build_audio_output_test_candidates(device, environment)


def _find_alsa_device(
    devices: list[Device],
    alsa_device: str,
    kind: str,
) -> Device | None:
    return next(
        (
            device
            for device in devices
            if device.kind == kind
            and (
                device.id == alsa_device
                or device.metadata.get("alsa_device") == alsa_device
            )
        ),
        None,
    )


def _print_devices(
    devices: list[Device],
    as_json: bool,
    empty_message: str = "No devices found.",
    heading: str = "Devices:",
) -> None:
    if as_json:
        print(_to_json(devices))
        return

    if not devices:
        print(empty_message)
        return

    print(heading)
    for device in devices:
        backend = device.metadata.get("backend", "unknown")
        print(f"- {device.kind}: {device.name} ({device.id})")
        print(f"  backend: {backend}")


def _print_environment(facts: list[EnvironmentFact], as_json: bool) -> None:
    if as_json:
        print(_to_json(facts))
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


def _print_composite_groups(
    groups: list[CompositeDevice],
    as_json: bool,
) -> None:
    if as_json:
        print(_to_json(groups))
        return

    if not groups:
        print("No composite device groups found.")
        return

    print("Composite devices:")
    for group in groups:
        _print_composite_group_text(group)


def _print_grouping_metadata(
    devices: list[GroupableDevice],
    as_json: bool,
) -> None:
    if as_json:
        print(_to_json(devices))
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


def _print_composite_group(
    group: CompositeDevice,
    as_json: bool,
) -> None:
    if as_json:
        print(json.dumps(asdict(group), indent=2, sort_keys=True))
        return

    _print_composite_group_text(group)


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


def _find_composite_group(
    groups: list[CompositeDevice],
    group_id: str,
) -> CompositeDevice | None:
    return next((group for group in groups if group.id == group_id), None)


def _print_video_capabilities(
    capabilities: list[Capability],
    device_path: str,
    as_json: bool,
) -> None:
    if as_json:
        print(_to_json(capabilities))
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


def _print_pipeline_candidates(
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
        print(_to_json(rendered_candidates))
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


def _run_selected_candidate(
    candidates: list[PipelineCandidate],
    device_label: str,
    inspect_commands: list[str],
    selection: str | None,
    dry_run: bool,
) -> int:
    if not candidates:
        print(f"No pipeline candidates were generated for {device_label}.")
        print()
        print("Try:")
        for command in inspect_commands:
            print(f"  {command}")
        print("  gst-device-explorer env")
        return 1

    try:
        candidate = execution.select_pipeline_candidate(
            candidates,
            selection=selection,
        )
    except execution.CandidateSelectionError as error:
        print(f"Error: {error}")
        return 1

    plan = execution.create_execution_plan(candidate)
    _print_execution_plan(plan, dry_run=dry_run)

    if dry_run:
        return 0

    try:
        return execution.run_execution_plan(plan)
    except execution.ExecutionStartError as error:
        print(f"Error: could not start pipeline: {error}")
        return 1


def _print_execution_plan(plan: ExecutionPlan, dry_run: bool) -> None:
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


def _to_json(
    items: list[Device]
    | list[EnvironmentFact]
    | list[Capability]
    | list[PipelineCandidate]
    | list[CompositeDevice]
    | list[GroupableDevice],
) -> str:
    if items and isinstance(items[0], PipelineCandidate):
        return json.dumps(
            [_pipeline_candidate_to_json_dict(item) for item in items],
            indent=2,
            sort_keys=True,
        )
    return json.dumps([asdict(item) for item in items], indent=2, sort_keys=True)


def _pipeline_candidate_to_json_dict(candidate: PipelineCandidate) -> dict:
    return {
        "argv": candidate.argv,
        "candidate_id": candidate.candidate_id,
        "command": candidate.command,
        "confidence": candidate.confidence,
        "purpose": candidate.purpose,
        "reasons": candidate.reasons,
        "required_elements": candidate.required_elements,
        "selected_profile": candidate.selected_profile,
        "warnings": candidate.warnings,
    }


if __name__ == "__main__":
    raise SystemExit(main())
