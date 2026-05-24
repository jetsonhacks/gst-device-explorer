"""CLI argument parser for gst-device-explorer."""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
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

    profile_parser = subparsers.add_parser(
        "profile",
        help="Build endpoint device profiles.",
    )
    profile_subparsers = profile_parser.add_subparsers(
        dest="profile_command",
        required=True,
    )
    profile_video_parser = profile_subparsers.add_parser(
        "video",
        help="Build a V4L2 video endpoint profile.",
    )
    profile_video_parser.add_argument(
        "device_path",
        help="Path to a video device.",
    )
    profile_video_parser.add_argument(
        "--json",
        action="store_true",
        help="Render the profile as JSON.",
    )
    profile_audio_input_parser = profile_subparsers.add_parser(
        "audio-input",
        help="Build an ALSA audio input endpoint profile.",
    )
    profile_audio_input_parser.add_argument(
        "alsa_device",
        help="ALSA device name such as hw:0,0.",
    )
    profile_audio_input_parser.add_argument(
        "--json",
        action="store_true",
        help="Render the profile as JSON.",
    )
    profile_audio_output_parser = profile_subparsers.add_parser(
        "audio-output",
        help="Build an ALSA audio output endpoint profile.",
    )
    profile_audio_output_parser.add_argument(
        "alsa_device",
        help="ALSA device name such as hw:0,0.",
    )
    profile_audio_output_parser.add_argument(
        "--json",
        action="store_true",
        help="Render the profile as JSON.",
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
    pipeline_video_parser.add_argument(
        "--diagnostics",
        action="store_true",
        help="Render structured diagnostics instead of pipeline candidates.",
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
    pipeline_audio_input_parser.add_argument(
        "--diagnostics",
        action="store_true",
        help="Render structured diagnostics instead of pipeline candidates.",
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
    pipeline_audio_output_parser.add_argument(
        "--diagnostics",
        action="store_true",
        help="Render structured diagnostics instead of pipeline candidates.",
    )

    report_parser = subparsers.add_parser(
        "report",
        help="Generate a structured system report.",
    )
    report_parser.add_argument(
        "--json",
        action="store_true",
        help="Render the report as JSON.",
    )

    recommend_parser = subparsers.add_parser(
        "recommend",
        help="Rank and recommend pipeline candidates for an endpoint.",
    )
    recommend_subparsers = recommend_parser.add_subparsers(
        dest="recommend_command",
        required=True,
    )
    recommend_video_parser = recommend_subparsers.add_parser(
        "video",
        help="Rank and recommend V4L2 video pipeline candidates.",
    )
    recommend_video_parser.add_argument(
        "device_path",
        help="Path to a video device.",
    )
    recommend_video_parser.add_argument(
        "--json",
        action="store_true",
        help="Render the ranking as JSON.",
    )
    recommend_audio_input_parser = recommend_subparsers.add_parser(
        "audio-input",
        help="Rank and recommend ALSA audio input pipeline candidates.",
    )
    recommend_audio_input_parser.add_argument(
        "alsa_device",
        help="ALSA device name such as hw:0,0.",
    )
    recommend_audio_input_parser.add_argument(
        "--json",
        action="store_true",
        help="Render the ranking as JSON.",
    )
    recommend_audio_output_parser = recommend_subparsers.add_parser(
        "audio-output",
        help="Rank and recommend ALSA audio output pipeline candidates.",
    )
    recommend_audio_output_parser.add_argument(
        "alsa_device",
        help="ALSA device name such as hw:0,0.",
    )
    recommend_audio_output_parser.add_argument(
        "--json",
        action="store_true",
        help="Render the ranking as JSON.",
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

    capture_parser = subparsers.add_parser(
        "capture",
        help="Create a short bounded media capture from one endpoint.",
    )
    capture_subparsers = capture_parser.add_subparsers(
        dest="capture_command",
        required=True,
    )
    capture_video_parser = capture_subparsers.add_parser(
        "video",
        help="Capture one generated V4L2 video candidate to a short file.",
    )
    capture_video_parser.add_argument(
        "device_path",
        help="Path to a video device.",
    )
    capture_video_parser.add_argument(
        "--duration",
        required=True,
        help="Positive capture duration in seconds.",
    )
    capture_video_parser.add_argument(
        "--output",
        required=True,
        help="Explicit output path for the captured file.",
    )
    capture_video_parser.add_argument(
        "--candidate",
        help="Candidate zero-based index or stable candidate ID.",
    )
    capture_video_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the selected capture command without starting GStreamer.",
    )
    capture_audio_input_parser = capture_subparsers.add_parser(
        "audio-input",
        help="Capture one generated ALSA audio input candidate to WAV.",
    )
    capture_audio_input_parser.add_argument(
        "alsa_device",
        help="ALSA device name such as hw:0,0.",
    )
    capture_audio_input_parser.add_argument(
        "--duration",
        required=True,
        help="Positive capture duration in seconds.",
    )
    capture_audio_input_parser.add_argument(
        "--output",
        required=True,
        help="Explicit output path for the captured file.",
    )
    capture_audio_input_parser.add_argument(
        "--candidate",
        help="Candidate zero-based index or stable candidate ID.",
    )
    capture_audio_input_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the selected capture command without starting GStreamer.",
    )

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate discovered composite devices.",
    )
    validate_subparsers = validate_parser.add_subparsers(
        dest="validate_command",
        required=True,
    )
    validate_group_parser = validate_subparsers.add_parser(
        "group",
        help="Summarize endpoint health for one composite device group.",
    )
    validate_group_parser.add_argument(
        "group_id",
        help="Composite device group ID.",
    )
    validate_group_parser.add_argument(
        "--json",
        action="store_true",
        help="Render the group validation as JSON.",
    )

    preset_parser = subparsers.add_parser(
        "preset",
        help="Inspect built-in named workflow presets.",
    )
    preset_subparsers = preset_parser.add_subparsers(
        dest="preset_command",
        required=True,
    )
    preset_list_parser = preset_subparsers.add_parser(
        "list",
        help="List built-in presets.",
    )
    preset_list_parser.add_argument(
        "--json",
        action="store_true",
        help="Render presets as JSON.",
    )
    preset_show_parser = preset_subparsers.add_parser(
        "show",
        help="Show one built-in preset.",
    )
    preset_show_parser.add_argument(
        "preset_id",
        help="Preset ID.",
    )
    preset_show_parser.add_argument(
        "--json",
        action="store_true",
        help="Render the preset as JSON.",
    )
    preset_command_parser = preset_subparsers.add_parser(
        "command",
        help="Suggest an existing safe command for one preset target.",
    )
    preset_command_parser.add_argument(
        "preset_id",
        help="Preset ID.",
    )
    preset_command_parser.add_argument(
        "target_kind",
        help="Target kind such as video, audio-input, audio-output, or group.",
    )
    preset_command_parser.add_argument(
        "target",
        help="Endpoint or group identifier.",
    )
    preset_command_parser.add_argument(
        "--duration",
        help="Capture duration in seconds for capture presets.",
    )
    preset_command_parser.add_argument(
        "--output",
        help="Output path for capture presets.",
    )
    preset_command_parser.add_argument(
        "--json",
        action="store_true",
        help="Render command suggestions as JSON.",
    )

    config_parser = subparsers.add_parser(
        "config",
        help="Inspect and validate bounded configuration preferences.",
    )
    config_subparsers = config_parser.add_subparsers(
        dest="config_command",
        required=True,
    )
    config_path_parser = config_subparsers.add_parser(
        "path",
        help="Show configuration search paths.",
    )
    config_path_parser.add_argument(
        "--json",
        action="store_true",
        help="Render configuration paths as JSON.",
    )
    config_show_parser = config_subparsers.add_parser(
        "show",
        help="Show the effective/default configuration.",
    )
    config_show_parser.add_argument(
        "--config",
        help="Explicit TOML configuration file to load.",
    )
    config_show_parser.add_argument(
        "--json",
        action="store_true",
        help="Render the configuration as JSON.",
    )
    config_validate_parser = config_subparsers.add_parser(
        "validate",
        help="Validate configuration without applying it to behavior.",
    )
    config_validate_parser.add_argument(
        "--config",
        help="Explicit TOML configuration file to validate.",
    )
    config_validate_parser.add_argument(
        "--json",
        action="store_true",
        help="Render validation results as JSON.",
    )

    return parser
