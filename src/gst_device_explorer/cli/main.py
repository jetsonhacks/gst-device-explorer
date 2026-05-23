"""Minimal command line renderer for gst-device-explorer."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from typing import Sequence

from gst_device_explorer.core.models import Device, EnvironmentFact
import gst_device_explorer.core.discovery as discovery
import gst_device_explorer.probes.gst as gst_probe


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

    return parser


def _print_devices(devices: list[Device], as_json: bool) -> None:
    if as_json:
        print(_to_json(devices))
        return

    if not devices:
        print("No devices found.")
        return

    print("Devices:")
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


def _to_json(items: list[Device] | list[EnvironmentFact]) -> str:
    return json.dumps([asdict(item) for item in items], indent=2, sort_keys=True)


if __name__ == "__main__":
    raise SystemExit(main())
