"""Renderers for preset listing and command suggestions."""

from __future__ import annotations

import json
import shlex

from gst_device_explorer.cli.renderer._utils import _print_json
from gst_device_explorer.cli.serializers import (
    preset_command_suggestions_to_json_dict,
    preset_definition_to_json_dict,
)
from gst_device_explorer.core.presets import PresetCommandSuggestions, PresetDefinition
from gst_device_explorer.core.schema import wrap_json


def print_preset_list(presets: list[PresetDefinition], as_json: bool) -> None:
    if as_json:
        data = [preset_definition_to_json_dict(preset) for preset in presets]
        print(
            json.dumps(
                wrap_json("preset_list", data),
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
        print(
            json.dumps(
                wrap_json("preset_show", preset_definition_to_json_dict(preset)),
                indent=2,
                sort_keys=True,
            )
        )
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
                wrap_json(
                    "preset_command",
                    preset_command_suggestions_to_json_dict(result),
                ),
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
        print(f"  {shlex.join(suggestion.argv)}")
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
