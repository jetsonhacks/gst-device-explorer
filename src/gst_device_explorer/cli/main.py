"""Minimal command line renderer for gst-device-explorer."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from typing import Sequence

from gst_device_explorer.core.models import (
    Capability,
    Device,
    EnvironmentFact,
    ExecutionPlan,
    PipelineCandidate,
)
import gst_device_explorer.core.discovery as discovery
import gst_device_explorer.core.execution as execution
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
            as_json=args.json,
            show_all=args.all,
            limit=args.limit,
        )
        return 0

    if args.command == "run" and args.run_command == "video":
        candidates = _build_video_preview_candidates(args.device_path)
        if not candidates:
            print(
                f"No pipeline candidates were generated for {args.device_path}."
            )
            print()
            print("Try:")
            print(f"  gst-device-explorer video {args.device_path}")
            print("  gst-device-explorer env")
            return 1

        try:
            candidate = execution.select_pipeline_candidate(
                candidates,
                selection=args.candidate,
            )
        except execution.CandidateSelectionError as error:
            print(f"Error: {error}")
            return 1

        plan = execution.create_execution_plan(candidate)
        _print_execution_plan(plan, dry_run=args.dry_run)

        if args.dry_run:
            return 0

        try:
            return execution.run_execution_plan(plan)
        except execution.ExecutionStartError as error:
            print(f"Error: could not start pipeline: {error}")
            return 1

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
        print(f"No video preview pipeline candidates found for {device_path}.")
        return

    print(f"Video preview pipeline candidates for {device_path}:")
    for index, candidate in enumerate(rendered_candidates, start=1):
        print(f"{index}. {candidate.purpose}")
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
    | list[PipelineCandidate],
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
