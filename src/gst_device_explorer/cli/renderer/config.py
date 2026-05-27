"""Renderers for configuration and schema commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from gst_device_explorer.cli.renderer._utils import _print_json
from gst_device_explorer.cli.serializers import (
    config_validation_result_to_json_dict,
    schema_document_summary_to_json_dict,
    schema_document_to_json_dict,
)
from gst_device_explorer.core.config import ConfigValidationResult, ExplorerConfig
from gst_device_explorer.core.schema import SchemaDocument, wrap_json


def print_config_paths(paths: Sequence[Path], as_json: bool) -> None:
    if as_json:
        data = {
            "paths": [str(path) for path in paths],
            "required": False,
            "applied": False,
        }
        print(
            json.dumps(
                wrap_json("config_path", data),
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
                wrap_json("config_show", config_validation_result_to_json_dict(result)),
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
                wrap_json(
                    "config_validate",
                    config_validation_result_to_json_dict(result),
                ),
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


def print_schema_list(documents: list[SchemaDocument], as_json: bool) -> None:
    if as_json:
        print(
            json.dumps(
                wrap_json(
                    "schema_list",
                    {
                        "schemas": [
                            schema_document_summary_to_json_dict(document)
                            for document in documents
                        ],
                    },
                ),
                indent=2,
                sort_keys=True,
            )
        )
        return

    print("Available schema documents:")
    print()
    for document in documents:
        print(f"  {document.schema_id}")
        print(f"    {document.purpose}")
    print()
    print("Use:")
    print("  gst-device-explorer schema show <schema-id>")


def print_schema_document(document: SchemaDocument, as_json: bool) -> None:
    if as_json:
        print(
            json.dumps(
                wrap_json("schema_show", schema_document_to_json_dict(document)),
                indent=2,
                sort_keys=True,
            )
        )
        return

    print(f"Schema: {document.schema_id}")
    print(f"Purpose: {document.purpose}")
    print()
    print("Fields:")
    for field in document.fields:
        print(f"  {field.name:<15} {field.value_type:<7} {field.description}")
    if document.current_schema_version is not None:
        print()
        print(f"Current schema_version: {document.current_schema_version}")


def print_schema_not_found(schema_id: str) -> None:
    print(f"Schema not found: {schema_id}")
    print()
    print("Try:")
    print("  gst-device-explorer schema list")


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
