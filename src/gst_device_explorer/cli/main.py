"""Minimal command line renderer for gst-device-explorer."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from typing import Sequence

from gst_device_explorer.core.models import Capability, Device, EnvironmentFact
import gst_device_explorer.core.discovery as discovery
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

    return parser


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


def _to_json(items: list[Device] | list[EnvironmentFact] | list[Capability]) -> str:
    return json.dumps([asdict(item) for item in items], indent=2, sort_keys=True)


if __name__ == "__main__":
    raise SystemExit(main())
