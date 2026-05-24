from pathlib import Path
import json
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.cli.main import main
from gst_device_explorer.cli.renderer import print_config_show, print_config_validate
from gst_device_explorer.cli.serializers import config_validation_result_to_json_dict
from gst_device_explorer.core.config import (
    ConfigIssue,
    ConfigValidationResult,
    ExplorerConfig,
    default_config,
    config_search_paths,
    effective_config,
    load_config_file,
    validate_config_mapping,
)
import gst_device_explorer.cli.main as cli_main


def test_default_config_is_deterministic() -> None:
    assert default_config() == default_config()
    assert default_config().video.prefer_jetson_acceleration is True
    assert default_config().audio.output_test_frequency == 440
    assert default_config().report.include_metadata is True


def test_config_search_paths_use_xdg_config_home(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    (tmp_path / "project").mkdir()
    monkeypatch.chdir(tmp_path / "project")

    assert config_search_paths() == (
        tmp_path / "xdg" / "gst-device-explorer" / "config.toml",
        tmp_path / "project" / "gst-device-explorer.toml",
    )


def test_valid_minimal_toml_loads_over_defaults(tmp_path) -> None:
    path = tmp_path / "config.toml"
    path.write_text("[audio]\noutput_test_frequency = 880\n")

    result = load_config_file(path)

    assert result.valid is True
    assert result.config is not None
    assert result.config.audio.output_test_frequency == 880
    assert result.config.video.prefer_jetson_acceleration is True


def test_valid_full_toml_loads_correctly(tmp_path) -> None:
    path = tmp_path / "config.toml"
    path.write_text(
        "[video]\n"
        'preferred_sink = "nveglglessink"\n'
        "prefer_jetson_acceleration = false\n"
        "max_preview_width = 1920\n"
        "max_preview_height = 1080\n"
        "\n"
        "[audio]\n"
        "output_test_frequency = 440\n"
        "prefer_silent_input_tests = false\n"
        "\n"
        "[report]\n"
        "include_metadata = false\n"
        "include_diagnostics = true\n"
    )

    result = load_config_file(path)

    assert result.valid is True
    assert result.config == ExplorerConfig(
        video=result.config.video.__class__(
            preferred_sink="nveglglessink",
            prefer_jetson_acceleration=False,
            max_preview_width=1920,
            max_preview_height=1080,
        ),
        audio=result.config.audio.__class__(
            output_test_frequency=440,
            prefer_silent_input_tests=False,
        ),
        report=result.config.report.__class__(
            include_metadata=False,
            include_diagnostics=True,
        ),
    )


def test_invalid_toml_is_reported_cleanly(tmp_path) -> None:
    path = tmp_path / "bad.toml"
    path.write_text("[audio\n")

    result = load_config_file(path)

    assert result.valid is False
    assert result.config is None
    assert result.errors[0].path == str(path)
    assert "invalid TOML" in result.errors[0].message


def test_wrong_types_are_errors() -> None:
    result = validate_config_mapping(
        {
            "video": {
                "preferred_sink": 123,
                "prefer_jetson_acceleration": "true",
            },
            "audio": {
                "output_test_frequency": "440",
                "prefer_silent_input_tests": "false",
            },
            "report": {
                "include_metadata": "true",
            },
        }
    )

    assert result.valid is False
    assert [issue.path for issue in result.errors] == [
        "audio.output_test_frequency",
        "audio.prefer_silent_input_tests",
        "report.include_metadata",
        "video.prefer_jetson_acceleration",
        "video.preferred_sink",
    ]


def test_non_positive_dimensions_and_frequency_are_errors() -> None:
    result = validate_config_mapping(
        {
            "video": {"max_preview_width": 0, "max_preview_height": -1},
            "audio": {"output_test_frequency": 0},
        }
    )

    assert result.valid is False
    assert [(issue.path, issue.message) for issue in result.errors] == [
        ("audio.output_test_frequency", "expected positive integer"),
        ("video.max_preview_height", "expected positive integer"),
        ("video.max_preview_width", "expected positive integer"),
    ]


def test_unknown_sections_and_keys_are_warnings() -> None:
    result = validate_config_mapping(
        {
            "unknown": {"enabled": True},
            "video": {"unknown_key": True},
        }
    )

    assert result.valid is True
    assert [(issue.path, issue.message) for issue in result.warnings] == [
        ("unknown", "unknown section"),
        ("video.unknown_key", "unknown key"),
    ]


def test_missing_explicit_config_is_error(tmp_path) -> None:
    result = effective_config(tmp_path / "missing.toml")

    assert result.valid is False
    assert result.errors == (
        ConfigIssue(str(tmp_path / "missing.toml"), "configuration file not found"),
    )


def test_missing_discovered_config_uses_defaults(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.chdir(tmp_path)

    result = effective_config()

    assert result.valid is True
    assert result.path is None
    assert result.config == default_config()


def test_discovered_config_file_is_loaded(monkeypatch, tmp_path) -> None:
    config_dir = tmp_path / "xdg" / "gst-device-explorer"
    config_dir.mkdir(parents=True)
    path = config_dir / "config.toml"
    path.write_text("[audio]\noutput_test_frequency = 220\n")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.chdir(tmp_path)

    result = effective_config()

    assert result.valid is True
    assert result.discovered is True
    assert result.path == str(path)
    assert result.config is not None
    assert result.config.audio.output_test_frequency == 220


def test_json_serialization_is_stable() -> None:
    result = ConfigValidationResult(
        path=None,
        valid=True,
        config=default_config(),
        warnings=(ConfigIssue("video.extra", "unknown key"),),
    )

    assert config_validation_result_to_json_dict(result) == {
        "applied": False,
        "config": {
            "audio": {
                "output_test_frequency": 440,
                "prefer_silent_input_tests": True,
            },
            "report": {
                "include_diagnostics": True,
                "include_metadata": True,
            },
            "video": {
                "max_preview_height": None,
                "max_preview_width": None,
                "prefer_jetson_acceleration": True,
                "preferred_sink": None,
            },
        },
        "errors": [],
        "source": None,
        "valid": True,
        "warnings": [{"message": "unknown key", "path": "video.extra"}],
    }


def test_text_rendering_includes_display_only_note(capsys) -> None:
    print_config_show(
        ConfigValidationResult(path=None, valid=True, config=default_config()),
        as_json=False,
    )

    assert (
        "Configuration is currently display/validation only"
        in capsys.readouterr().out
    )


def test_validate_rendering_includes_not_applied_note(capsys) -> None:
    print_config_validate(
        ConfigValidationResult(path=None, valid=True, config=default_config()),
        as_json=False,
    )

    assert (
        "Preferences are not applied to command behavior in Milestone 12."
        in capsys.readouterr().out
    )


def test_cli_config_show_json(monkeypatch, capsys, tmp_path) -> None:
    monkeypatch.setattr(
        cli_main.config,
        "config_search_paths",
        lambda: (tmp_path / "missing.toml",),
    )

    exit_code = main(["config", "show", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["kind"] == "config_show"
    assert data["data"]["valid"] is True
    assert data["data"]["config"]["audio"]["output_test_frequency"] == 440
    assert data["data"]["applied"] is False


def test_cli_config_validate_explicit_json(capsys, tmp_path) -> None:
    path = tmp_path / "config.toml"
    path.write_text("[report]\ninclude_metadata = false\n")

    exit_code = main(["config", "validate", "--config", str(path), "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["kind"] == "config_validate"
    assert data["data"]["source"] == str(path)
    assert data["data"]["config"]["report"]["include_metadata"] is False


def test_cli_config_validate_invalid_explicit_returns_nonzero(capsys, tmp_path) -> None:
    path = tmp_path / "config.toml"
    path.write_text("[audio]\noutput_test_frequency = 0\n")

    exit_code = main(["config", "validate", "--config", str(path)])

    assert exit_code == 1
    assert capsys.readouterr().out == (
        f"Configuration invalid: {path}\n"
        "Errors:\n"
        "  - audio.output_test_frequency: expected positive integer\n"
    )


def test_cli_config_path_text(monkeypatch, capsys, tmp_path) -> None:
    monkeypatch.setattr(
        cli_main.config,
        "config_search_paths",
        lambda: (
            tmp_path / "config.toml",
            tmp_path / "project" / "gst-device-explorer.toml",
        ),
    )

    exit_code = main(["config", "path"])

    assert exit_code == 0
    assert capsys.readouterr().out == (
        "Configuration search paths:\n"
        f"  1. {tmp_path / 'config.toml'}\n"
        f"  2. {tmp_path / 'project' / 'gst-device-explorer.toml'}\n"
        "\n"
        "No configuration file is required.\n"
        "Milestone 12 only validates and displays configuration; it does not apply preferences yet.\n"
    )
