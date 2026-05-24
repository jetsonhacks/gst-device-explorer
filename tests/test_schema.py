import json

from gst_device_explorer import __version__
from gst_device_explorer.cli.main import main
from gst_device_explorer.core.schema import (
    JSON_SCHEMA_VERSION,
    get_schema_document,
    list_schema_documents,
    wrap_json,
)


def test_wrap_json_includes_stable_envelope_fields() -> None:
    envelope = wrap_json("example", {"value": 1})

    assert envelope == {
        "schema_version": JSON_SCHEMA_VERSION,
        "tool_version": __version__,
        "kind": "example",
        "data": {"value": 1},
    }


def test_schema_version_constant_is_stable() -> None:
    assert JSON_SCHEMA_VERSION == "1.0"


def test_schema_registry_contains_json_envelope() -> None:
    documents = list_schema_documents()

    assert [document.schema_id for document in documents] == ["json-envelope"]
    assert get_schema_document("json-envelope") == documents[0]
    assert get_schema_document("missing") is None


def test_config_path_json_is_wrapped(capsys) -> None:
    exit_code = main(["config", "path", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["schema_version"] == "1.0"
    assert payload["tool_version"] == __version__
    assert payload["kind"] == "config_path"
    assert "paths" in payload["data"]


def test_config_show_json_is_wrapped(capsys, monkeypatch, tmp_path) -> None:
    import gst_device_explorer.cli.main as cli_main

    monkeypatch.setattr(
        cli_main.config,
        "config_search_paths",
        lambda: (tmp_path / "missing.toml",),
    )

    exit_code = main(["config", "show", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["kind"] == "config_show"
    assert payload["data"]["valid"] is True
    assert payload["data"]["config"]["audio"]["output_test_frequency"] == 440


def test_config_validate_json_is_wrapped(capsys) -> None:
    exit_code = main(["config", "validate", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["kind"] == "config_validate"
    assert payload["data"]["valid"] is True


def test_preset_list_json_is_wrapped(capsys) -> None:
    exit_code = main(["preset", "list", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["kind"] == "preset_list"
    assert payload["data"][0]["preset_id"] == "camera-preview"


def test_preset_show_json_is_wrapped(capsys) -> None:
    exit_code = main(["preset", "show", "camera-preview", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["kind"] == "preset_show"
    assert payload["data"]["preset_id"] == "camera-preview"


def test_preset_command_json_is_wrapped(capsys) -> None:
    exit_code = main(
        ["preset", "command", "camera-preview", "video", "/dev/video0", "--json"]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["kind"] == "preset_command"
    assert payload["data"]["suggestions"][0]["argv"] == [
        "gst-device-explorer",
        "run",
        "video",
        "/dev/video0",
        "--dry-run",
    ]


def test_schema_list_text_output(capsys) -> None:
    exit_code = main(["schema", "list"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Available schema documents:" in output
    assert "json-envelope" in output


def test_schema_list_json_output(capsys) -> None:
    exit_code = main(["schema", "list", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["kind"] == "schema_list"
    assert payload["data"]["schemas"][0]["schema_id"] == "json-envelope"


def test_schema_show_text_output(capsys) -> None:
    exit_code = main(["schema", "show", "json-envelope"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "schema_version" in output
    assert "tool_version" in output
    assert "kind" in output
    assert "data" in output


def test_schema_show_json_output(capsys) -> None:
    exit_code = main(["schema", "show", "json-envelope", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["kind"] == "schema_show"
    assert payload["data"]["schema_id"] == "json-envelope"
    assert payload["data"]["fields"][0]["name"] == "schema_version"


def test_unknown_schema_returns_nonzero(capsys) -> None:
    exit_code = main(["schema", "show", "missing"])

    assert exit_code == 1
    assert capsys.readouterr().out == (
        "Schema not found: missing\n"
        "\n"
        "Try:\n"
        "  gst-device-explorer schema list\n"
    )
