"""Support bundle command handler."""

from __future__ import annotations

import datetime
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

from gst_device_explorer import __version__
from gst_device_explorer.cli.commands import build_system_report
from gst_device_explorer.cli.renderer import print_support_bundle_written, print_system_report
from gst_device_explorer.cli.serializers import (
    config_validation_result_to_json_dict,
    schema_document_summary_to_json_dict,
    suggested_command_to_json_dict,
    support_bundle_manifest_to_json_dict,
    system_report_to_json_dict,
    to_json_data,
)
from gst_device_explorer.core.schema import JSON_SCHEMA_VERSION, wrap_json
from gst_device_explorer.core.support import (
    SupportBundleFile,
    SupportBundleManifest,
    validate_bundle_output_path,
)
from gst_device_explorer.core.tui import build_tui_review_model, render_overview_lines
import gst_device_explorer.core.config as config
import gst_device_explorer.core.discovery as discovery
import gst_device_explorer.core.presets as presets
import gst_device_explorer.core.schema as schema_mod
import gst_device_explorer.core.suggestions as suggestions_mod


def run_support_bundle(output_path_str: str) -> int:
    """Create a support bundle directory at the given output path."""
    output_path = Path(output_path_str)

    try:
        validate_bundle_output_path(output_path)
    except FileExistsError as error:
        print(f"Error: {error}")
        return 1
    except ValueError as error:
        print(f"Error: {error}")
        return 1

    written_files: list[SupportBundleFile] = []
    bundle_warnings: list[str] = []

    report = build_system_report()
    config_result = config.effective_config()
    config_paths = config.config_search_paths()
    schema_documents = schema_mod.list_schema_documents()
    suggestions = suggestions_mod.list_generic_suggestions()
    groupable_devices = discovery.discover_groupable_devices()

    try:
        output_path.mkdir(parents=False)
    except OSError as error:
        print(f"Error: Could not create bundle directory: {error}")
        return 1

    report_dir = output_path / "report"
    report_dir.mkdir()

    _write_bundle_json(
        report_dir / "system-report.json",
        wrap_json("system_report", system_report_to_json_dict(report)),
        written_files,
        bundle_warnings,
        rel_path="report/system-report.json",
        kind="json",
        description="Full system report.",
        required=True,
    )

    try:
        buf = io.StringIO()
        with redirect_stdout(buf):
            print_system_report(report, as_json=False)
        (report_dir / "system-report.txt").write_text(buf.getvalue())
        written_files.append(SupportBundleFile(
            path="report/system-report.txt",
            kind="text",
            description="System report text summary.",
            required=False,
        ))
    except OSError as error:
        bundle_warnings.append(f"Could not write report/system-report.txt: {error}")

    inventory_dir = output_path / "inventory"
    inventory_dir.mkdir()

    all_devices = (
        list(report.devices.video)
        + list(report.devices.audio_inputs)
        + list(report.devices.audio_outputs)
    )
    _write_bundle_json(
        inventory_dir / "environment.json",
        wrap_json("environment", to_json_data(report.environment)),
        written_files,
        bundle_warnings,
        rel_path="inventory/environment.json",
        kind="json",
        description="GStreamer environment facts.",
        required=False,
    )
    _write_bundle_json(
        inventory_dir / "devices.json",
        wrap_json("devices", to_json_data(all_devices)),
        written_files,
        bundle_warnings,
        rel_path="inventory/devices.json",
        kind="json",
        description="All discovered devices.",
        required=False,
    )
    _write_bundle_json(
        inventory_dir / "audio-inputs.json",
        wrap_json("audio_inputs", to_json_data(list(report.devices.audio_inputs))),
        written_files,
        bundle_warnings,
        rel_path="inventory/audio-inputs.json",
        kind="json",
        description="Discovered ALSA audio input devices.",
        required=False,
    )
    _write_bundle_json(
        inventory_dir / "audio-outputs.json",
        wrap_json("audio_outputs", to_json_data(list(report.devices.audio_outputs))),
        written_files,
        bundle_warnings,
        rel_path="inventory/audio-outputs.json",
        kind="json",
        description="Discovered ALSA audio output devices.",
        required=False,
    )
    _write_bundle_json(
        inventory_dir / "groups.json",
        wrap_json("composite_groups", to_json_data(list(report.groups))),
        written_files,
        bundle_warnings,
        rel_path="inventory/groups.json",
        kind="json",
        description="Discovered composite device groups.",
        required=False,
    )
    _write_bundle_json(
        inventory_dir / "grouping-metadata.json",
        wrap_json("grouping_metadata", to_json_data(groupable_devices)),
        written_files,
        bundle_warnings,
        rel_path="inventory/grouping-metadata.json",
        kind="json",
        description="Raw grouping metadata records.",
        required=False,
    )

    config_dir = output_path / "config"
    config_dir.mkdir()

    config_paths_data = {
        "applied": False,
        "paths": [str(p) for p in config_paths],
        "required": False,
    }
    _write_bundle_json(
        config_dir / "config-path.json",
        wrap_json("config_path", config_paths_data),
        written_files,
        bundle_warnings,
        rel_path="config/config-path.json",
        kind="json",
        description="Configuration search paths.",
        required=False,
    )
    _write_bundle_json(
        config_dir / "config-show.json",
        wrap_json("config_show", config_validation_result_to_json_dict(config_result)),
        written_files,
        bundle_warnings,
        rel_path="config/config-show.json",
        kind="json",
        description="Effective configuration.",
        required=False,
    )
    _write_bundle_json(
        config_dir / "config-validate.json",
        wrap_json("config_validate", config_validation_result_to_json_dict(config_result)),
        written_files,
        bundle_warnings,
        rel_path="config/config-validate.json",
        kind="json",
        description="Configuration validation result.",
        required=False,
    )

    schemas_dir = output_path / "schemas"
    schemas_dir.mkdir()

    _write_bundle_json(
        schemas_dir / "schema-list.json",
        wrap_json(
            "schema_list",
            {"schemas": [schema_document_summary_to_json_dict(d) for d in schema_documents]},
        ),
        written_files,
        bundle_warnings,
        rel_path="schemas/schema-list.json",
        kind="json",
        description="Known schema document list.",
        required=False,
    )

    suggestions_dir = output_path / "suggestions"
    suggestions_dir.mkdir()

    _write_bundle_json(
        suggestions_dir / "suggestions-list.json",
        wrap_json(
            "suggestion_catalog",
            {"suggested_commands": [suggested_command_to_json_dict(s) for s in suggestions]},
        ),
        written_files,
        bundle_warnings,
        rel_path="suggestions/suggestions-list.json",
        kind="json",
        description="Generic suggested command catalog.",
        required=False,
    )

    tui_dir = output_path / "tui"
    tui_dir.mkdir()

    try:
        tui_model = build_tui_review_model(
            report=report,
            presets=presets.list_presets(),
            config=config_result,
            schema_documents=schema_documents,
        )
        snapshot = "\n".join(render_overview_lines(tui_model)) + "\n"
        (tui_dir / "snapshot.txt").write_text(snapshot)
        written_files.append(SupportBundleFile(
            path="tui/snapshot.txt",
            kind="text",
            description="TUI overview snapshot.",
            required=False,
        ))
    except OSError as error:
        bundle_warnings.append(f"Could not write tui/snapshot.txt: {error}")

    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    manifest = SupportBundleManifest(
        schema_version=JSON_SCHEMA_VERSION,
        tool_version=__version__,
        kind="support_bundle_manifest",
        created_at=created_at,
        bundle_format="directory",
        files=tuple(written_files),
        warnings=tuple(bundle_warnings),
        notes=(
            "This bundle contains read-only inspection data. "
            "No pipelines were executed and no media was captured.",
        ),
    )

    try:
        manifest_payload = wrap_json(
            "support_bundle_manifest",
            support_bundle_manifest_to_json_dict(manifest),
        )
        (output_path / "manifest.json").write_text(
            json.dumps(manifest_payload, indent=2, sort_keys=True)
        )
    except OSError as error:
        print(f"Error: Could not write manifest: {error}")
        return 1

    print_support_bundle_written(output_path_str, written_files)
    return 0


def _write_bundle_json(
    file_path: Path,
    data: dict,
    written_files: list[SupportBundleFile],
    warnings: list[str],
    rel_path: str,
    kind: str,
    description: str,
    required: bool,
) -> None:
    try:
        file_path.write_text(json.dumps(data, indent=2, sort_keys=True))
        written_files.append(SupportBundleFile(
            path=rel_path,
            kind=kind,
            description=description,
            required=required,
        ))
    except OSError as error:
        warnings.append(f"Could not write {rel_path}: {error}")
