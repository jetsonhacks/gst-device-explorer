from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.core.suggestions import (
    SuggestedCommand,
    _make_id,
    list_generic_suggestions,
    suggest_audio_input_pipeline,
    suggest_audio_input_pipeline_diagnostics,
    suggest_audio_input_profile,
    suggest_audio_input_run_dry_run,
    suggest_audio_inputs_command,
    suggest_audio_output_pipeline,
    suggest_audio_output_pipeline_diagnostics,
    suggest_audio_output_profile,
    suggest_audio_output_run_dry_run,
    suggest_audio_outputs_command,
    suggest_config_show,
    suggest_devices_command,
    suggest_env_command,
    suggest_group_list,
    suggest_group_validation,
    suggest_gst_inspect,
    suggest_preset_command,
    suggest_preset_list,
    suggest_profile,
    suggest_report,
    suggest_schema_list,
    suggest_video_pipeline,
    suggest_video_pipeline_diagnostics,
    suggest_video_profile,
    suggest_video_run_dry_run,
)


def test_suggested_command_is_frozen_dataclass() -> None:
    cmd = suggest_env_command()
    assert isinstance(cmd, SuggestedCommand)


def test_suggested_command_command_property_joins_argv() -> None:
    cmd = suggest_video_pipeline("/dev/video0")
    assert cmd.command == "gst-device-explorer pipeline video /dev/video0"


def test_suggested_command_command_property_quotes_spaces() -> None:
    cmd = SuggestedCommand(
        id="test",
        title="Test",
        argv=("echo", "hello world"),
        purpose="test",
        source="test",
        safety="inspection",
    )
    assert cmd.command == "echo 'hello world'"


def test_suggested_command_is_hashable() -> None:
    cmd = suggest_env_command()
    assert {cmd} == {cmd}


def test_suggested_command_equality() -> None:
    assert suggest_env_command() == suggest_env_command()


def test_make_id_skips_tool_name() -> None:
    argv = ("gst-device-explorer", "env")
    assert _make_id(argv) == "env"


def test_make_id_slugifies_flags() -> None:
    argv = ("gst-device-explorer", "pipeline", "video", "/dev/video0", "--diagnostics")
    result = _make_id(argv)
    assert "diagnostics" in result
    assert "--" not in result


def test_make_id_is_deterministic() -> None:
    argv = ("gst-device-explorer", "pipeline", "video", "/dev/video0")
    assert _make_id(argv) == _make_id(argv)


def test_suggest_env_command() -> None:
    cmd = suggest_env_command()
    assert cmd.command == "gst-device-explorer env"
    assert cmd.safety == "inspection"
    assert cmd.source == "environment"
    assert cmd.target_kind is None
    assert cmd.target is None


def test_suggest_devices_command() -> None:
    cmd = suggest_devices_command()
    assert cmd.command == "gst-device-explorer devices"


def test_suggest_audio_inputs_command() -> None:
    cmd = suggest_audio_inputs_command()
    assert cmd.command == "gst-device-explorer audio-inputs"


def test_suggest_audio_outputs_command() -> None:
    cmd = suggest_audio_outputs_command()
    assert cmd.command == "gst-device-explorer audio-outputs"


def test_suggest_group_list() -> None:
    cmd = suggest_group_list()
    assert cmd.command == "gst-device-explorer groups"


def test_suggest_group_validation() -> None:
    cmd = suggest_group_validation("my-group-id")
    assert cmd.command == "gst-device-explorer validate group my-group-id"
    assert cmd.target == "my-group-id"
    assert cmd.target_kind == "group"


def test_suggest_report() -> None:
    cmd = suggest_report()
    assert cmd.command == "gst-device-explorer report"


def test_suggest_schema_list() -> None:
    cmd = suggest_schema_list()
    assert cmd.command == "gst-device-explorer schema list"


def test_suggest_config_show() -> None:
    cmd = suggest_config_show()
    assert cmd.command == "gst-device-explorer config show"


def test_suggest_preset_list() -> None:
    cmd = suggest_preset_list()
    assert cmd.command == "gst-device-explorer preset list"


def test_suggest_video_profile() -> None:
    cmd = suggest_video_profile("/dev/video0")
    assert cmd.command == "gst-device-explorer profile video /dev/video0"
    assert cmd.target == "/dev/video0"
    assert cmd.target_kind == "video"


def test_suggest_video_pipeline() -> None:
    cmd = suggest_video_pipeline("/dev/video0")
    assert cmd.command == "gst-device-explorer pipeline video /dev/video0"
    assert cmd.safety == "inspection"


def test_suggest_video_pipeline_diagnostics() -> None:
    cmd = suggest_video_pipeline_diagnostics("/dev/video0")
    assert "--diagnostics" in cmd.command
    assert cmd.safety == "inspection"


def test_suggest_video_run_dry_run() -> None:
    cmd = suggest_video_run_dry_run("/dev/video0")
    assert "--dry-run" in cmd.command
    assert cmd.safety == "dry_run"


def test_suggest_audio_input_profile() -> None:
    cmd = suggest_audio_input_profile("hw:0,0")
    assert cmd.command == "gst-device-explorer profile audio-input hw:0,0"
    assert cmd.target_kind == "audio-input"


def test_suggest_audio_input_pipeline() -> None:
    cmd = suggest_audio_input_pipeline("hw:0,0")
    assert cmd.command == "gst-device-explorer pipeline audio-input hw:0,0"


def test_suggest_audio_input_pipeline_diagnostics() -> None:
    cmd = suggest_audio_input_pipeline_diagnostics("hw:0,0")
    assert "--diagnostics" in cmd.command


def test_suggest_audio_input_run_dry_run() -> None:
    cmd = suggest_audio_input_run_dry_run("hw:0,0")
    assert "--dry-run" in cmd.command
    assert cmd.safety == "dry_run"


def test_suggest_audio_output_profile() -> None:
    cmd = suggest_audio_output_profile("hw:1,0")
    assert cmd.command == "gst-device-explorer profile audio-output hw:1,0"
    assert cmd.target_kind == "audio-output"


def test_suggest_audio_output_pipeline() -> None:
    cmd = suggest_audio_output_pipeline("hw:1,0")
    assert cmd.command == "gst-device-explorer pipeline audio-output hw:1,0"


def test_suggest_audio_output_pipeline_diagnostics() -> None:
    cmd = suggest_audio_output_pipeline_diagnostics("hw:1,0")
    assert "--diagnostics" in cmd.command


def test_suggest_audio_output_run_dry_run() -> None:
    cmd = suggest_audio_output_run_dry_run("hw:1,0")
    assert "--dry-run" in cmd.command
    assert cmd.safety == "dry_run"


def test_suggest_profile_dispatches_video() -> None:
    cmd = suggest_profile("video", "/dev/video0")
    assert cmd.command == "gst-device-explorer profile video /dev/video0"


def test_suggest_profile_dispatches_audio_input() -> None:
    cmd = suggest_profile("audio-input", "hw:0,0")
    assert cmd.command == "gst-device-explorer profile audio-input hw:0,0"


def test_suggest_profile_dispatches_audio_output() -> None:
    cmd = suggest_profile("audio-output", "hw:1,0")
    assert cmd.command == "gst-device-explorer profile audio-output hw:1,0"


def test_suggest_gst_inspect() -> None:
    cmd = suggest_gst_inspect("v4l2src")
    assert cmd.command == "gst-inspect-1.0 v4l2src"
    assert cmd.safety == "external_check"
    assert cmd.source == "diagnostics"


def test_suggest_preset_command() -> None:
    cmd = suggest_preset_command("camera-preview", "video", "/dev/video0")
    assert "preset" in cmd.command
    assert "camera-preview" in cmd.command
    assert "video" in cmd.command
    assert "/dev/video0" in cmd.command


def test_list_generic_suggestions_returns_nonempty_list() -> None:
    catalog = list_generic_suggestions()
    assert len(catalog) > 0


def test_list_generic_suggestions_all_are_suggested_commands() -> None:
    catalog = list_generic_suggestions()
    assert all(isinstance(cmd, SuggestedCommand) for cmd in catalog)


def test_list_generic_suggestions_ids_are_unique() -> None:
    catalog = list_generic_suggestions()
    ids = [cmd.id for cmd in catalog]
    assert len(ids) == len(set(ids))


def test_list_generic_suggestions_all_have_non_empty_titles() -> None:
    catalog = list_generic_suggestions()
    assert all(cmd.title for cmd in catalog)


def test_list_generic_suggestions_all_have_valid_safety() -> None:
    valid_safety = {"inspection", "dry_run", "bounded_capture", "safe_execution", "external_check"}
    catalog = list_generic_suggestions()
    assert all(cmd.safety in valid_safety for cmd in catalog)
