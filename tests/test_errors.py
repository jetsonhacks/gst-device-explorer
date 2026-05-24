from pathlib import Path
import json
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.cli.main import main
from gst_device_explorer.cli.renderer import print_json_error
from gst_device_explorer.cli.serializers import (
    error_response_to_json_dict,
    make_error_envelope,
)
from gst_device_explorer.core.errors import ErrorResponse
from gst_device_explorer.core.suggestions import (
    suggest_group_list,
    suggest_preset_list,
    suggest_preset_show,
    suggest_schema_list,
)
import gst_device_explorer.cli.commands as cli_commands
import gst_device_explorer.cli.main as cli_main


# ---------------------------------------------------------------------------
# ErrorResponse model
# ---------------------------------------------------------------------------


def test_error_response_creation() -> None:
    error = ErrorResponse(code="unknown_schema", message="Unknown schema: foo")
    assert error.code == "unknown_schema"
    assert error.message == "Unknown schema: foo"
    assert error.details == {}
    assert error.suggested_commands == ()


def test_error_response_with_details() -> None:
    error = ErrorResponse(
        code="group_not_found",
        message="Group not found: my-group",
        details={"group_id": "my-group"},
    )
    assert error.details == {"group_id": "my-group"}


def test_error_response_with_suggested_commands() -> None:
    cmd = suggest_schema_list()
    error = ErrorResponse(
        code="unknown_schema",
        message="Unknown schema: foo",
        suggested_commands=(cmd,),
    )
    assert len(error.suggested_commands) == 1
    assert error.suggested_commands[0].command == "gst-device-explorer schema list"


def test_error_response_is_frozen() -> None:
    error = ErrorResponse(code="foo", message="bar")
    try:
        error.code = "changed"  # type: ignore[misc]
        assert False, "should have raised"
    except Exception:
        pass



# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------


def test_error_response_to_json_dict_minimal() -> None:
    error = ErrorResponse(code="unknown_schema", message="msg")
    d = error_response_to_json_dict(error)
    assert d["code"] == "unknown_schema"
    assert d["message"] == "msg"
    assert d["details"] == {}
    assert d["suggested_commands"] == []


def test_error_response_to_json_dict_with_details() -> None:
    error = ErrorResponse(
        code="group_not_found",
        message="Group not found: x",
        details={"group_id": "x"},
    )
    d = error_response_to_json_dict(error)
    assert d["details"] == {"group_id": "x"}


def test_error_response_to_json_dict_with_suggested_commands() -> None:
    cmd = suggest_group_list()
    error = ErrorResponse(
        code="group_not_found",
        message="Group not found: x",
        suggested_commands=(cmd,),
    )
    d = error_response_to_json_dict(error)
    assert len(d["suggested_commands"]) == 1
    assert d["suggested_commands"][0]["command"] == "gst-device-explorer groups"
    assert d["suggested_commands"][0]["id"] == cmd.id


def test_make_error_envelope_shape() -> None:
    error = ErrorResponse(code="unknown_schema", message="msg")
    envelope = make_error_envelope(error)
    assert envelope["kind"] == "error"
    assert envelope["schema_version"] == "1.0"
    assert "tool_version" in envelope
    assert "error" in envelope
    assert "data" not in envelope


def test_make_error_envelope_kind_is_error() -> None:
    error = ErrorResponse(code="foo", message="bar")
    envelope = make_error_envelope(error)
    assert envelope["kind"] == "error"


def test_make_error_envelope_no_data_key() -> None:
    error = ErrorResponse(code="foo", message="bar")
    envelope = make_error_envelope(error)
    assert "data" not in envelope


def test_make_error_envelope_error_payload_structure() -> None:
    error = ErrorResponse(
        code="unknown_schema",
        message="Unknown schema: foo",
        details={"schema_id": "foo"},
        suggested_commands=(suggest_schema_list(),),
    )
    envelope = make_error_envelope(error)
    err = envelope["error"]
    assert err["code"] == "unknown_schema"
    assert err["message"] == "Unknown schema: foo"
    assert err["details"] == {"schema_id": "foo"}
    assert len(err["suggested_commands"]) == 1


def test_print_json_error_produces_valid_json(capsys) -> None:
    error = ErrorResponse(code="unknown_schema", message="msg")
    print_json_error(error)
    output = capsys.readouterr().out
    data = json.loads(output)
    assert data["kind"] == "error"


# ---------------------------------------------------------------------------
# CLI: schema show JSON error
# ---------------------------------------------------------------------------


def test_schema_show_unknown_json_error(capsys) -> None:
    exit_code = main(["schema", "show", "not-a-schema", "--json"])

    assert exit_code == 1
    data = json.loads(capsys.readouterr().out)
    assert data["kind"] == "error"
    assert data["error"]["code"] == "unknown_schema"
    assert "not-a-schema" in data["error"]["message"]
    assert data["error"]["details"]["schema_id"] == "not-a-schema"


def test_schema_show_unknown_json_suggested_commands(capsys) -> None:
    exit_code = main(["schema", "show", "not-a-schema", "--json"])

    assert exit_code == 1
    data = json.loads(capsys.readouterr().out)
    commands = [c["command"] for c in data["error"]["suggested_commands"]]
    assert "gst-device-explorer schema list" in commands


def test_schema_show_unknown_text_behavior(capsys) -> None:
    exit_code = main(["schema", "show", "not-a-schema"])

    assert exit_code == 1
    out = capsys.readouterr().out
    assert "not-a-schema" in out
    assert "{" not in out


def test_schema_show_known_still_works(capsys) -> None:
    exit_code = main(["schema", "show", "json-envelope"])

    assert exit_code == 0


def test_schema_show_known_json_is_success_envelope(capsys) -> None:
    exit_code = main(["schema", "show", "json-envelope", "--json"])

    assert exit_code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["kind"] == "schema_show"
    assert "data" in data
    assert "error" not in data


def test_schema_show_error_envelope_works(capsys) -> None:
    exit_code = main(["schema", "show", "error-envelope"])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "error-envelope" in out


def test_schema_show_error_envelope_json(capsys) -> None:
    exit_code = main(["schema", "show", "error-envelope", "--json"])

    assert exit_code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["kind"] == "schema_show"
    assert data["data"]["schema_id"] == "error-envelope"


def test_schema_list_includes_error_envelope(capsys) -> None:
    exit_code = main(["schema", "list"])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "error-envelope" in out


def test_schema_list_json_includes_error_envelope(capsys) -> None:
    exit_code = main(["schema", "list", "--json"])

    assert exit_code == 0
    data = json.loads(capsys.readouterr().out)
    schema_ids = [s["schema_id"] for s in data["data"]["schemas"]]
    assert "error-envelope" in schema_ids


# ---------------------------------------------------------------------------
# CLI: preset show JSON error
# ---------------------------------------------------------------------------


def test_preset_show_unknown_json_error(capsys) -> None:
    exit_code = main(["preset", "show", "not-a-preset", "--json"])

    assert exit_code == 1
    data = json.loads(capsys.readouterr().out)
    assert data["kind"] == "error"
    assert data["error"]["code"] == "unknown_preset"
    assert data["error"]["details"]["preset_id"] == "not-a-preset"


def test_preset_show_unknown_json_suggested_commands(capsys) -> None:
    exit_code = main(["preset", "show", "not-a-preset", "--json"])

    assert exit_code == 1
    data = json.loads(capsys.readouterr().out)
    commands = [c["command"] for c in data["error"]["suggested_commands"]]
    assert "gst-device-explorer preset list" in commands


def test_preset_show_unknown_text_behavior(capsys) -> None:
    exit_code = main(["preset", "show", "not-a-preset"])

    assert exit_code == 1
    out = capsys.readouterr().out
    assert "not-a-preset" in out
    assert "{" not in out


def test_preset_show_known_still_works(capsys) -> None:
    exit_code = main(["preset", "show", "camera-preview"])

    assert exit_code == 0


# ---------------------------------------------------------------------------
# CLI: preset command JSON errors
# ---------------------------------------------------------------------------


def test_preset_command_unknown_preset_json_error(capsys) -> None:
    exit_code = main(["preset", "command", "not-a-preset", "video", "/dev/video0", "--json"])

    assert exit_code == 1
    data = json.loads(capsys.readouterr().out)
    assert data["kind"] == "error"
    assert data["error"]["code"] == "unknown_preset"
    assert data["error"]["details"]["preset_id"] == "not-a-preset"


def test_preset_command_wrong_target_kind_json_error(capsys) -> None:
    exit_code = main(["preset", "command", "camera-preview", "audio-input", "hw:0,0", "--json"])

    assert exit_code == 1
    data = json.loads(capsys.readouterr().out)
    assert data["kind"] == "error"
    assert data["error"]["code"] == "wrong_preset_target_kind"
    assert data["error"]["details"]["preset_id"] == "camera-preview"
    assert data["error"]["details"]["target_kind"] == "audio-input"


def test_preset_command_wrong_target_kind_suggested_commands(capsys) -> None:
    exit_code = main(["preset", "command", "camera-preview", "audio-input", "hw:0,0", "--json"])

    assert exit_code == 1
    data = json.loads(capsys.readouterr().out)
    commands = [c["command"] for c in data["error"]["suggested_commands"]]
    assert "gst-device-explorer preset show camera-preview" in commands
    assert "gst-device-explorer preset list" in commands


def test_preset_command_missing_required_arg_json_error(capsys) -> None:
    exit_code = main(["preset", "command", "short-video-capture", "video", "/dev/video0", "--json"])

    assert exit_code == 1
    data = json.loads(capsys.readouterr().out)
    assert data["kind"] == "error"
    assert data["error"]["code"] == "missing_required_argument"
    assert data["error"]["details"]["preset_id"] == "short-video-capture"


def test_preset_command_missing_required_arg_suggested_commands(capsys) -> None:
    exit_code = main(["preset", "command", "short-video-capture", "video", "/dev/video0", "--json"])

    assert exit_code == 1
    data = json.loads(capsys.readouterr().out)
    commands = [c["command"] for c in data["error"]["suggested_commands"]]
    assert "gst-device-explorer preset show short-video-capture" in commands


def test_preset_command_wrong_target_kind_text_behavior(capsys) -> None:
    exit_code = main(["preset", "command", "camera-preview", "audio-input", "hw:0,0"])

    assert exit_code == 1
    out = capsys.readouterr().out
    assert "{" not in out


# ---------------------------------------------------------------------------
# CLI: group command JSON error
# ---------------------------------------------------------------------------


def test_group_not_found_json_error(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_main.discovery, "discover_composite_devices", lambda: []
    )

    exit_code = main(["group", "missing-group", "--json"])

    assert exit_code == 1
    data = json.loads(capsys.readouterr().out)
    assert data["kind"] == "error"
    assert data["error"]["code"] == "group_not_found"
    assert data["error"]["details"]["group_id"] == "missing-group"


def test_group_not_found_json_suggested_commands(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_main.discovery, "discover_composite_devices", lambda: []
    )

    exit_code = main(["group", "missing-group", "--json"])

    assert exit_code == 1
    data = json.loads(capsys.readouterr().out)
    commands = [c["command"] for c in data["error"]["suggested_commands"]]
    assert "gst-device-explorer groups" in commands


def test_group_not_found_text_preserved(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_main.discovery, "discover_composite_devices", lambda: []
    )

    exit_code = main(["group", "missing-group"])

    assert exit_code == 1
    out = capsys.readouterr().out
    assert "Composite device group not found: missing-group" in out
    assert "{" not in out


# ---------------------------------------------------------------------------
# CLI: validate group JSON error
# ---------------------------------------------------------------------------


def test_validate_group_not_found_json_error(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli_commands, "build_group_validation", lambda group_id: None)

    exit_code = main(["validate", "group", "missing", "--json"])

    assert exit_code == 1
    data = json.loads(capsys.readouterr().out)
    assert data["kind"] == "error"
    assert data["error"]["code"] == "group_not_found"
    assert data["error"]["details"]["group_id"] == "missing"


def test_validate_group_not_found_json_envelope_shape(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli_commands, "build_group_validation", lambda group_id: None)

    exit_code = main(["validate", "group", "missing", "--json"])

    assert exit_code == 1
    data = json.loads(capsys.readouterr().out)
    assert "schema_version" in data
    assert "tool_version" in data
    assert "kind" in data
    assert "error" in data
    assert "data" not in data


# ---------------------------------------------------------------------------
# Exit codes are non-zero for all JSON errors
# ---------------------------------------------------------------------------


def test_all_json_errors_return_nonzero_exit_code(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli_commands, "build_group_validation", lambda group_id: None)

    cases = [
        (["schema", "show", "not-a-schema", "--json"], 1),
        (["preset", "show", "not-a-preset", "--json"], 1),
        (["preset", "command", "not-a-preset", "video", "/dev/video0", "--json"], 1),
        (["preset", "command", "camera-preview", "audio-input", "hw:0,0", "--json"], 1),
        (["validate", "group", "missing", "--json"], 1),
    ]
    for argv, expected_code in cases:
        capsys.readouterr()
        code = main(argv)
        assert code == expected_code, f"Expected {expected_code} for {argv}, got {code}"


# ---------------------------------------------------------------------------
# No execution side effects
# ---------------------------------------------------------------------------


def test_json_errors_do_not_execute_commands(monkeypatch, capsys) -> None:
    executed = []

    def fake_run(*args, **kwargs):
        executed.append(args)

    monkeypatch.setattr(cli_commands, "build_group_validation", lambda group_id: None)

    main(["validate", "group", "missing", "--json"])
    assert executed == [], "no commands should be executed on error"
