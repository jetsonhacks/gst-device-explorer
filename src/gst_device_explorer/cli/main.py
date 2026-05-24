"""Minimal command line dispatcher for gst-device-explorer."""

from __future__ import annotations

from typing import Sequence

from gst_device_explorer.core.models import CompositeDevice
import gst_device_explorer.core.capture as capture
import gst_device_explorer.core.discovery as discovery
import gst_device_explorer.probes.alsa as alsa_probe
import gst_device_explorer.probes.gst as gst_probe
import gst_device_explorer.probes.v4l2 as v4l2_probe
from gst_device_explorer.cli.parser import build_parser
import gst_device_explorer.cli.commands as commands
import gst_device_explorer.cli.renderer as renderer


def main(argv: Sequence[str] | None = None) -> int:
    """Run the gst-device-explorer CLI."""

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "devices":
        devices = discovery.discover_devices()
        renderer.print_devices(devices, as_json=args.json)
        return 0

    if args.command == "groups":
        if args.metadata:
            groupable_devices = discovery.discover_groupable_devices()
            renderer.print_grouping_metadata(groupable_devices, as_json=args.json)
            return 0
        groups = discovery.discover_composite_devices()
        renderer.print_composite_groups(groups, as_json=args.json)
        return 0

    if args.command == "group":
        groups = discovery.discover_composite_devices()
        group = _find_composite_group(groups, args.group_id)
        if group is None:
            print(f"Composite device group not found: {args.group_id}")
            return 1
        renderer.print_composite_group(group, as_json=args.json)
        return 0

    if args.command == "env":
        facts = gst_probe.inspect_gstreamer_environment()
        renderer.print_environment(facts, as_json=args.json)
        return 0

    if args.command == "audio-inputs":
        devices = alsa_probe.discover_alsa_audio_inputs()
        renderer.print_devices(
            devices,
            as_json=args.json,
            empty_message="No ALSA audio input devices found.",
            heading="Audio input devices:",
        )
        return 0

    if args.command == "audio-outputs":
        devices = alsa_probe.discover_alsa_audio_outputs()
        renderer.print_devices(
            devices,
            as_json=args.json,
            empty_message="No ALSA audio output devices found.",
            heading="Audio output devices:",
        )
        return 0

    if args.command == "video":
        capabilities = v4l2_probe.discover_v4l2_capabilities(args.device_path)
        renderer.print_video_capabilities(
            capabilities,
            device_path=args.device_path,
            as_json=args.json,
        )
        return 0

    if args.command == "profile" and args.profile_command == "audio-input":
        profile = commands.build_audio_input_profile(args.alsa_device)
        renderer.print_device_profile(profile, as_json=args.json)
        return 0

    if args.command == "profile" and args.profile_command == "audio-output":
        profile = commands.build_audio_output_profile(args.alsa_device)
        renderer.print_device_profile(profile, as_json=args.json)
        return 0

    if args.command == "profile" and args.profile_command == "video":
        profile = commands.build_video_profile(args.device_path)
        renderer.print_device_profile(profile, as_json=args.json)
        return 0

    if args.command == "pipeline" and args.pipeline_command == "video":
        if args.diagnostics:
            diagnostics = commands.build_video_preview_diagnostics(args.device_path)
            renderer.print_pipeline_diagnostics(
                diagnostics,
                device_kind="video",
                device_path=args.device_path,
                as_json=args.json,
            )
            return 0
        candidates = commands.build_video_preview_candidates(args.device_path)
        renderer.print_pipeline_candidates(
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
        if args.diagnostics:
            diagnostics = commands.build_audio_input_test_diagnostics(args.alsa_device)
            renderer.print_pipeline_diagnostics(
                diagnostics,
                device_kind="audio-input",
                device_path=args.alsa_device,
                as_json=args.json,
            )
            return 0
        candidates = commands.build_audio_input_test_candidates(args.alsa_device)
        renderer.print_pipeline_candidates(
            candidates,
            device_path=args.alsa_device,
            heading="Audio input pipeline candidates",
            empty_message="No audio input pipeline candidates found",
            as_json=args.json,
        )
        return 0

    if args.command == "pipeline" and args.pipeline_command == "audio-output":
        if args.diagnostics:
            diagnostics = commands.build_audio_output_test_diagnostics(args.alsa_device)
            renderer.print_pipeline_diagnostics(
                diagnostics,
                device_kind="audio-output",
                device_path=args.alsa_device,
                as_json=args.json,
            )
            return 0
        candidates = commands.build_audio_output_test_candidates(args.alsa_device)
        renderer.print_pipeline_candidates(
            candidates,
            device_path=args.alsa_device,
            heading="Audio output pipeline candidates",
            empty_message="No audio output pipeline candidates found",
            as_json=args.json,
        )
        return 0

    if args.command == "report":
        report = commands.build_system_report()
        renderer.print_system_report(report, as_json=args.json)
        return 0

    if args.command == "recommend" and args.recommend_command == "video":
        result = commands.build_video_recommendation(args.device_path)
        renderer.print_candidate_ranking(result, as_json=args.json)
        return 0

    if args.command == "recommend" and args.recommend_command == "audio-input":
        result = commands.build_audio_input_recommendation(args.alsa_device)
        renderer.print_candidate_ranking(result, as_json=args.json)
        return 0

    if args.command == "recommend" and args.recommend_command == "audio-output":
        result = commands.build_audio_output_recommendation(args.alsa_device)
        renderer.print_candidate_ranking(result, as_json=args.json)
        return 0

    if args.command == "run" and args.run_command == "video":
        candidates = commands.build_video_preview_candidates(args.device_path)
        return commands.run_selected_candidate(
            candidates,
            device_label=args.device_path,
            inspect_commands=[f"gst-device-explorer video {args.device_path}"],
            selection=args.candidate,
            dry_run=args.dry_run,
        )

    if args.command == "run" and args.run_command == "audio-input":
        candidates = commands.build_audio_input_test_candidates(args.alsa_device)
        return commands.run_selected_candidate(
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
        candidates = commands.build_audio_output_test_candidates(args.alsa_device)
        return commands.run_selected_candidate(
            candidates,
            device_label=args.alsa_device,
            inspect_commands=[
                "gst-device-explorer audio-outputs",
                f"gst-device-explorer pipeline audio-output {args.alsa_device}",
            ],
            selection=args.candidate,
            dry_run=args.dry_run,
        )

    if args.command == "capture" and args.capture_command == "video":
        duration = _validate_capture_duration(args.duration)
        if duration is None:
            return 1
        if not _validate_capture_output_path(args.output):
            return 1
        candidates = commands.build_video_capture_candidates(
            args.device_path,
            duration,
            args.output,
        )
        return commands.run_capture_candidate(
            candidates,
            endpoint=args.device_path,
            duration_seconds=duration,
            output_path=args.output,
            inspect_commands=[
                f"gst-device-explorer video {args.device_path}",
                f"gst-device-explorer pipeline video {args.device_path}",
            ],
            selection=args.candidate,
            dry_run=args.dry_run,
        )

    if args.command == "capture" and args.capture_command == "audio-input":
        duration = _validate_capture_duration(args.duration)
        if duration is None:
            return 1
        if not _validate_capture_output_path(args.output):
            return 1
        candidates = commands.build_audio_input_capture_candidates(
            args.alsa_device,
            duration,
            args.output,
        )
        return commands.run_capture_candidate(
            candidates,
            endpoint=args.alsa_device,
            duration_seconds=duration,
            output_path=args.output,
            inspect_commands=[
                "gst-device-explorer audio-inputs",
                f"gst-device-explorer pipeline audio-input {args.alsa_device}",
            ],
            selection=args.candidate,
            dry_run=args.dry_run,
        )

    if args.command == "validate" and args.validate_command == "group":
        result = commands.build_group_validation(args.group_id)
        if result is None:
            renderer.print_group_not_found(args.group_id, as_json=args.json)
            return 1
        renderer.print_group_validation(result, as_json=args.json)
        return 0

    parser.error("unknown command")
    return 2


def _find_composite_group(
    groups: list[CompositeDevice],
    group_id: str,
) -> CompositeDevice | None:
    return next((group for group in groups if group.id == group_id), None)


def _validate_capture_duration(value: str) -> float | None:
    try:
        return capture.validate_capture_duration(value)
    except ValueError as error:
        print(f"Error: {error}")
        return None


def _validate_capture_output_path(value: str) -> bool:
    try:
        capture.validate_capture_output_path(value)
    except FileExistsError:
        renderer.print_capture_not_started_existing_output(value)
        return False
    except ValueError as error:
        print(f"Error: {error}")
        return False
    return True


if __name__ == "__main__":
    raise SystemExit(main())
