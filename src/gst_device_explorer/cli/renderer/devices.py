"""Renderers for devices, environment facts, groups, and capabilities."""

from __future__ import annotations

from dataclasses import asdict

from gst_device_explorer.cli.renderer._utils import _print_json
from gst_device_explorer.cli.serializers import to_json_data
from gst_device_explorer.core.grouping import GroupableDevice
from gst_device_explorer.core.models import Capability, CompositeDevice, Device, EnvironmentFact
from gst_device_explorer.core.schema import wrap_json
from gst_device_explorer.core.suggestions import SuggestedCommand
from gst_device_explorer.core.support import SupportBundleFile


def print_devices(
    devices: list[Device],
    as_json: bool,
    empty_message: str = "No devices found.",
    heading: str = "Devices:",
    json_kind: str = "devices",
) -> None:
    if as_json:
        _print_json(json_kind, to_json_data(devices))
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
        _print_json("environment", to_json_data(facts))
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
        _print_json("composite_groups", to_json_data(groups))
        return

    if not groups:
        print("No composite device groups found.")
        return

    print("Composite devices:")
    for group in groups:
        _print_composite_group_text(group)


def print_grouping_metadata(devices: list[GroupableDevice], as_json: bool) -> None:
    if as_json:
        _print_json("grouping_metadata", to_json_data(devices))
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
        _print_json("composite_group", asdict(group))
        return

    _print_composite_group_text(group)


def print_video_capabilities(
    capabilities: list[Capability],
    device_path: str,
    as_json: bool,
) -> None:
    if as_json:
        _print_json("video_capabilities", to_json_data(capabilities))
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


def print_suggestions_catalog(
    suggestions: list[SuggestedCommand],
    as_json: bool,
) -> None:
    if as_json:
        from gst_device_explorer.cli.serializers import suggested_command_to_json_dict

        _print_json(
            "suggestion_catalog",
            {"suggested_commands": [suggested_command_to_json_dict(s) for s in suggestions]},
        )
        return

    if not suggestions:
        print("No suggestions found.")
        return

    print("Suggested commands:")
    for suggestion in suggestions:
        print(f"  {suggestion.command}")
        if suggestion.purpose:
            print(f"    {suggestion.purpose}")


def print_support_bundle_written(
    output_path: str,
    files: list[SupportBundleFile],
) -> None:
    print(f"Support bundle written: {output_path}")
    print()
    print("Files:")
    print(f"  manifest.json")
    for f in files:
        print(f"  {f.path}")


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
