"""Synthetic tests for the Milestone 18 support bundle export command."""

from pathlib import Path
import json
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer import __version__
from gst_device_explorer.cli.main import main
from gst_device_explorer.cli.parser import build_parser
from gst_device_explorer.core.models import (
    Device,
    EnvironmentFact,
    ReportDevices,
    ReportDiagnostics,
    ReportProfiles,
    SystemReport,
)
from gst_device_explorer.core.support import (
    SupportBundleFile,
    SupportBundleManifest,
    validate_bundle_output_path,
)
import gst_device_explorer.cli.commands as cli_commands


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _minimal_report() -> SystemReport:
    return SystemReport(
        kind="system_report",
        tool_version=__version__,
        environment=[EnvironmentFact(name="gstreamer_version", value="1.20.0")],
        devices=ReportDevices(
            video=[
                Device(
                    id="/dev/video0",
                    kind="video_input",
                    name="video0",
                    metadata={"backend": "v4l2"},
                )
            ],
            audio_inputs=[],
            audio_outputs=[],
        ),
        groups=[],
        profiles=ReportProfiles(),
        diagnostics=ReportDiagnostics(),
        suggested_next_commands=[],
    )


def _mock_config():
    from gst_device_explorer.core.config import ConfigValidationResult, ExplorerConfig
    return ConfigValidationResult(
        valid=True,
        applied=False,
        path=None,
        config=ExplorerConfig(),
        errors=[],
        warnings=[],
    )


def _patch_all_probes(monkeypatch) -> None:
    """Patch every probe and data-source that run_support_bundle calls."""
    monkeypatch.setattr(cli_commands, "build_system_report", lambda: _minimal_report())
    monkeypatch.setattr(
        cli_commands.config, "effective_config", lambda path=None: _mock_config()
    )
    monkeypatch.setattr(cli_commands.config, "config_search_paths", lambda: [])
    monkeypatch.setattr(cli_commands.discovery, "discover_groupable_devices", lambda: [])
    monkeypatch.setattr(cli_commands.schema_mod, "list_schema_documents", lambda: [])
    monkeypatch.setattr(cli_commands.suggestions_mod, "list_generic_suggestions", lambda: [])
    monkeypatch.setattr(cli_commands.presets, "list_presets", lambda: ())
    monkeypatch.setattr(
        cli_commands, "build_tui_review_model", lambda **_kw: object()
    )
    monkeypatch.setattr(
        cli_commands, "render_overview_lines", lambda _model: ["TUI overview line"]
    )


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------


def test_parser_accepts_support_bundle_with_output() -> None:
    parser = build_parser()
    args = parser.parse_args(["support", "bundle", "--output", "/tmp/my-bundle"])
    assert args.command == "support"
    assert args.support_command == "bundle"
    assert args.output == "/tmp/my-bundle"


def test_parser_rejects_support_bundle_missing_output() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["support", "bundle"])
    assert exc_info.value.code != 0


def test_parser_rejects_support_without_subcommand() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["support"])
    assert exc_info.value.code != 0


# ---------------------------------------------------------------------------
# Path validation tests
# ---------------------------------------------------------------------------


def test_validate_bundle_output_path_rejects_existing_path(tmp_path) -> None:
    existing = tmp_path / "already-here"
    existing.mkdir()
    with pytest.raises(FileExistsError):
        validate_bundle_output_path(existing)


def test_validate_bundle_output_path_rejects_missing_parent(tmp_path) -> None:
    missing_parent = tmp_path / "no-such-dir" / "bundle"
    with pytest.raises(ValueError, match="does not exist"):
        validate_bundle_output_path(missing_parent)


def test_validate_bundle_output_path_rejects_non_directory_parent(tmp_path) -> None:
    file_as_parent = tmp_path / "a-file"
    file_as_parent.write_text("data")
    target = file_as_parent / "bundle"
    with pytest.raises((ValueError, FileExistsError, OSError)):
        validate_bundle_output_path(target)


def test_validate_bundle_output_path_accepts_valid_path(tmp_path) -> None:
    new_path = tmp_path / "my-bundle"
    validate_bundle_output_path(new_path)  # must not raise


# ---------------------------------------------------------------------------
# Rejection tests via CLI
# ---------------------------------------------------------------------------


def test_existing_output_path_is_rejected(tmp_path, capsys) -> None:
    existing = tmp_path / "bundle"
    existing.mkdir()

    exit_code = main(["support", "bundle", "--output", str(existing)])

    assert exit_code == 1
    assert "already exists" in capsys.readouterr().out


def test_missing_parent_path_is_rejected(tmp_path, capsys) -> None:
    missing_parent = tmp_path / "no-such-dir" / "bundle"

    exit_code = main(["support", "bundle", "--output", str(missing_parent)])

    assert exit_code == 1
    assert "does not exist" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Successful bundle creation tests
# ---------------------------------------------------------------------------


def test_bundle_directory_is_created(tmp_path, monkeypatch) -> None:
    _patch_all_probes(monkeypatch)
    output = tmp_path / "my-bundle"

    exit_code = main(["support", "bundle", "--output", str(output)])

    assert exit_code == 0
    assert output.is_dir()


def test_manifest_file_is_written(tmp_path, monkeypatch) -> None:
    _patch_all_probes(monkeypatch)
    output = tmp_path / "bundle"

    main(["support", "bundle", "--output", str(output)])

    assert (output / "manifest.json").is_file()


def test_manifest_uses_success_envelope(tmp_path, monkeypatch) -> None:
    _patch_all_probes(monkeypatch)
    output = tmp_path / "bundle"

    main(["support", "bundle", "--output", str(output)])

    data = json.loads((output / "manifest.json").read_text())
    assert data["kind"] == "support_bundle_manifest"
    assert data["schema_version"] == "1.0"
    assert data["tool_version"] == __version__
    assert "data" in data


def test_manifest_tool_version_is_bumped(tmp_path, monkeypatch) -> None:
    _patch_all_probes(monkeypatch)
    output = tmp_path / "bundle"

    main(["support", "bundle", "--output", str(output)])

    data = json.loads((output / "manifest.json").read_text())
    assert data["tool_version"] == "0.27.0"


def test_manifest_lists_written_files_only(tmp_path, monkeypatch) -> None:
    _patch_all_probes(monkeypatch)
    output = tmp_path / "bundle"

    main(["support", "bundle", "--output", str(output)])

    data = json.loads((output / "manifest.json").read_text())
    manifest_data = data["data"]
    listed_paths = {f["path"] for f in manifest_data["files"]}

    for rel_path in listed_paths:
        assert (output / rel_path).exists(), f"Manifest lists {rel_path} but it was not written"


def test_manifest_does_not_list_manifest_itself(tmp_path, monkeypatch) -> None:
    _patch_all_probes(monkeypatch)
    output = tmp_path / "bundle"

    main(["support", "bundle", "--output", str(output)])

    data = json.loads((output / "manifest.json").read_text())
    manifest_data = data["data"]
    listed_paths = {f["path"] for f in manifest_data["files"]}
    assert "manifest.json" not in listed_paths


def test_system_report_json_is_written(tmp_path, monkeypatch) -> None:
    _patch_all_probes(monkeypatch)
    output = tmp_path / "bundle"

    main(["support", "bundle", "--output", str(output)])

    report_json = output / "report" / "system-report.json"
    assert report_json.is_file()
    data = json.loads(report_json.read_text())
    assert data["kind"] == "system_report"
    assert "data" in data


def test_system_report_txt_is_written(tmp_path, monkeypatch) -> None:
    _patch_all_probes(monkeypatch)
    output = tmp_path / "bundle"

    main(["support", "bundle", "--output", str(output)])

    report_txt = output / "report" / "system-report.txt"
    assert report_txt.is_file()
    assert len(report_txt.read_text()) > 0


def test_inventory_files_are_written(tmp_path, monkeypatch) -> None:
    _patch_all_probes(monkeypatch)
    output = tmp_path / "bundle"

    main(["support", "bundle", "--output", str(output)])

    inventory = output / "inventory"
    assert (inventory / "environment.json").is_file()
    assert (inventory / "devices.json").is_file()
    assert (inventory / "audio-inputs.json").is_file()
    assert (inventory / "audio-outputs.json").is_file()
    assert (inventory / "groups.json").is_file()
    assert (inventory / "grouping-metadata.json").is_file()


def test_config_files_are_written(tmp_path, monkeypatch) -> None:
    _patch_all_probes(monkeypatch)
    output = tmp_path / "bundle"

    main(["support", "bundle", "--output", str(output)])

    config_dir = output / "config"
    assert (config_dir / "config-path.json").is_file()
    assert (config_dir / "config-show.json").is_file()
    assert (config_dir / "config-validate.json").is_file()


def test_schemas_file_is_written(tmp_path, monkeypatch) -> None:
    _patch_all_probes(monkeypatch)
    output = tmp_path / "bundle"

    main(["support", "bundle", "--output", str(output)])

    assert (output / "schemas" / "schema-list.json").is_file()


def test_suggestions_file_is_written(tmp_path, monkeypatch) -> None:
    _patch_all_probes(monkeypatch)
    output = tmp_path / "bundle"

    main(["support", "bundle", "--output", str(output)])

    assert (output / "suggestions" / "suggestions-list.json").is_file()


def test_tui_snapshot_is_written(tmp_path, monkeypatch) -> None:
    _patch_all_probes(monkeypatch)
    output = tmp_path / "bundle"

    main(["support", "bundle", "--output", str(output)])

    snapshot = output / "tui" / "snapshot.txt"
    assert snapshot.is_file()
    assert "TUI overview line" in snapshot.read_text()


def test_inventory_json_uses_success_envelope(tmp_path, monkeypatch) -> None:
    _patch_all_probes(monkeypatch)
    output = tmp_path / "bundle"

    main(["support", "bundle", "--output", str(output)])

    env_json = json.loads((output / "inventory" / "environment.json").read_text())
    assert env_json["kind"] == "environment"
    assert "schema_version" in env_json
    assert "data" in env_json


def test_success_output_includes_bundle_path(tmp_path, monkeypatch, capsys) -> None:
    _patch_all_probes(monkeypatch)
    output = tmp_path / "bundle"

    exit_code = main(["support", "bundle", "--output", str(output)])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert str(output) in out
    assert "Support bundle written:" in out


def test_success_output_lists_manifest(tmp_path, monkeypatch, capsys) -> None:
    _patch_all_probes(monkeypatch)
    output = tmp_path / "bundle"

    main(["support", "bundle", "--output", str(output)])

    out = capsys.readouterr().out
    assert "manifest.json" in out


def test_success_output_lists_system_report(tmp_path, monkeypatch, capsys) -> None:
    _patch_all_probes(monkeypatch)
    output = tmp_path / "bundle"

    main(["support", "bundle", "--output", str(output)])

    out = capsys.readouterr().out
    assert "report/system-report.json" in out


# ---------------------------------------------------------------------------
# Safety boundary tests
# ---------------------------------------------------------------------------


def test_command_does_not_call_pipeline_execution(tmp_path, monkeypatch) -> None:
    _patch_all_probes(monkeypatch)

    pipeline_executed = []

    def _reject_pipeline(*args, **kwargs):
        pipeline_executed.append(True)
        raise AssertionError("Pipeline execution must not be called in support bundle")

    monkeypatch.setattr(cli_commands.execution, "run_execution_plan", _reject_pipeline)
    output = tmp_path / "bundle"

    exit_code = main(["support", "bundle", "--output", str(output)])

    assert exit_code == 0
    assert not pipeline_executed, "run_execution_plan was called unexpectedly"


def test_command_does_not_call_capture(tmp_path, monkeypatch) -> None:
    _patch_all_probes(monkeypatch)

    capture_called = []

    def _reject_capture(*args, **kwargs):
        capture_called.append(True)
        raise AssertionError("Media capture must not be called in support bundle")

    monkeypatch.setattr(cli_commands.capture, "build_video_capture_candidates", _reject_capture)
    monkeypatch.setattr(cli_commands.capture, "build_audio_input_capture_candidates", _reject_capture)
    output = tmp_path / "bundle"

    exit_code = main(["support", "bundle", "--output", str(output)])

    assert exit_code == 0
    assert not capture_called, "capture was called unexpectedly"


# ---------------------------------------------------------------------------
# Version metadata tests
# ---------------------------------------------------------------------------


def test_version_is_bumped_to_027() -> None:
    assert __version__ == "0.27.0"


def test_manifest_bundle_format_is_directory(tmp_path, monkeypatch) -> None:
    _patch_all_probes(monkeypatch)
    output = tmp_path / "bundle"

    main(["support", "bundle", "--output", str(output)])

    data = json.loads((output / "manifest.json").read_text())
    assert data["data"]["bundle_format"] == "directory"


def test_manifest_kind_field(tmp_path, monkeypatch) -> None:
    _patch_all_probes(monkeypatch)
    output = tmp_path / "bundle"

    main(["support", "bundle", "--output", str(output)])

    data = json.loads((output / "manifest.json").read_text())
    assert data["data"]["kind"] == "support_bundle_manifest"


# ---------------------------------------------------------------------------
# Core model tests
# ---------------------------------------------------------------------------


def test_support_bundle_file_is_frozen() -> None:
    f = SupportBundleFile(
        path="report/system-report.json",
        kind="json",
        description="System report",
        required=True,
    )
    with pytest.raises(Exception):
        f.path = "changed"  # type: ignore[misc]


def test_support_bundle_manifest_is_frozen() -> None:
    m = SupportBundleManifest(
        schema_version="1.0",
        tool_version="0.27.0",
        kind="support_bundle_manifest",
        created_at="2026-05-24T00:00:00+00:00",
        bundle_format="directory",
        files=(),
        warnings=(),
        notes=(),
    )
    with pytest.raises(Exception):
        m.tool_version = "changed"  # type: ignore[misc]
