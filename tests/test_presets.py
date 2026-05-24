from pathlib import Path
import json
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.cli.main import main
from gst_device_explorer.core.presets import (
    PresetCommandRequest,
    PresetMissingArgumentError,
    PresetTargetKindError,
    build_preset_command_suggestions,
    get_preset,
    list_presets,
)


def test_registry_contains_expected_preset_ids() -> None:
    assert [preset.preset_id for preset in list_presets()] == [
        "camera-preview",
        "video-diagnostics",
        "audio-input-test",
        "audio-output-test",
        "short-video-capture",
        "short-audio-capture",
        "composite-device-validation",
    ]


def test_list_presets_is_deterministic() -> None:
    assert list_presets() == list_presets()


def test_get_preset_returns_known_preset() -> None:
    preset = get_preset("camera-preview")

    assert preset is not None
    assert preset.title == "Camera Preview"
    assert preset.target_kind == "video"


def test_get_preset_returns_none_for_unknown_preset() -> None:
    assert get_preset("missing") is None


def test_camera_preview_suggestion_is_structured_argv() -> None:
    result = build_preset_command_suggestions(
        PresetCommandRequest(
            preset_id="camera-preview",
            target_kind="video",
            target="/dev/video0",
        )
    )

    assert result.suggestions[0].argv == (
        "gst-device-explorer",
        "run",
        "video",
        "/dev/video0",
        "--dry-run",
    )
    assert result.suggestions[0].dry_run is True


def test_video_diagnostics_uses_existing_pipeline_diagnostics_command() -> None:
    result = build_preset_command_suggestions(
        PresetCommandRequest(
            preset_id="video-diagnostics",
            target_kind="video",
            target="/dev/video0",
        )
    )

    assert result.suggestions[0].argv == (
        "gst-device-explorer",
        "pipeline",
        "video",
        "/dev/video0",
        "--diagnostics",
    )


def test_short_video_capture_requires_duration_and_output() -> None:
    try:
        build_preset_command_suggestions(
            PresetCommandRequest(
                preset_id="short-video-capture",
                target_kind="video",
                target="/dev/video0",
            )
        )
    except PresetMissingArgumentError as error:
        assert str(error) == "Preset `short-video-capture` requires --duration and --output."
    else:
        raise AssertionError("missing capture arguments were accepted")


def test_wrong_target_kind_is_rejected() -> None:
    try:
        build_preset_command_suggestions(
            PresetCommandRequest(
                preset_id="camera-preview",
                target_kind="audio-input",
                target="hw:0,0",
            )
        )
    except PresetTargetKindError as error:
        assert str(error) == (
            "Preset `camera-preview` requires target kind `video`. "
            "Received: audio-input"
        )
    else:
        raise AssertionError("wrong target kind was accepted")


def test_short_video_capture_suggestion_includes_duration_output_and_dry_run() -> None:
    result = build_preset_command_suggestions(
        PresetCommandRequest(
            preset_id="short-video-capture",
            target_kind="video",
            target="/dev/video0",
            duration="5",
            output="sample.avi",
        )
    )

    assert result.suggestions[0].argv == (
        "gst-device-explorer",
        "capture",
        "video",
        "/dev/video0",
        "--duration",
        "5",
        "--output",
        "sample.avi",
        "--dry-run",
    )


def test_composite_device_validation_suggestion() -> None:
    result = build_preset_command_suggestions(
        PresetCommandRequest(
            preset_id="composite-device-validation",
            target_kind="group",
            target="usb-device-1-2-3",
        )
    )

    assert result.suggestions[0].argv == (
        "gst-device-explorer",
        "validate",
        "group",
        "usb-device-1-2-3",
    )
    assert result.suggestions[0].dry_run is False


def test_preset_list_text_output(capsys) -> None:
    exit_code = main(["preset", "list"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert output.startswith("Available presets:\n")
    assert "camera-preview" in output
    assert "composite-device-validation" in output


def test_preset_list_json_output(capsys) -> None:
    exit_code = main(["preset", "list", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data[0]["preset_id"] == "camera-preview"
    assert data[-1]["preset_id"] == "composite-device-validation"


def test_preset_show_text_output(capsys) -> None:
    exit_code = main(["preset", "show", "camera-preview"])

    assert exit_code == 0
    assert capsys.readouterr().out == (
        "Preset: camera-preview\n"
        "Title: Camera Preview\n"
        "Target kind: video\n"
        "Related command: run video\n"
        "\n"
        "Description:\n"
        "  Preview a video endpoint using the existing safe video run flow.\n"
        "\n"
        "Safety:\n"
        "  - Uses generated candidates only.\n"
        "  - Suggests dry-run first.\n"
        "  - Delegates execution to `gst-device-explorer run video`.\n"
    )


def test_preset_show_json_output(capsys) -> None:
    exit_code = main(["preset", "show", "camera-preview", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["preset_id"] == "camera-preview"
    assert data["target_kind"] == "video"
    assert data["safety_notes"] == [
        "Uses generated candidates only.",
        "Suggests dry-run first.",
        "Delegates execution to `gst-device-explorer run video`.",
    ]


def test_preset_command_camera_preview_text_output(capsys) -> None:
    exit_code = main(["preset", "command", "camera-preview", "video", "/dev/video0"])

    assert exit_code == 0
    assert capsys.readouterr().out == (
        "Preset: camera-preview\n"
        "Target: video /dev/video0\n"
        "\n"
        "Suggested command:\n"
        "  gst-device-explorer run video /dev/video0 --dry-run\n"
        "  Inspect the generated video preview command before execution.\n"
        "\n"
        "This command was not executed.\n"
        "Review the dry-run output before running a non-dry-run command.\n"
    )


def test_preset_command_camera_preview_json_output(capsys) -> None:
    exit_code = main(
        ["preset", "command", "camera-preview", "video", "/dev/video0", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data == {
        "preset_id": "camera-preview",
        "suggestions": [
            {
                "argv": [
                    "gst-device-explorer",
                    "run",
                    "video",
                    "/dev/video0",
                    "--dry-run",
                ],
                "description": "Inspect the generated video preview command before execution.",
                "dry_run": True,
            }
        ],
        "target": "/dev/video0",
        "target_kind": "video",
    }


def test_preset_command_short_video_capture_text_output(capsys) -> None:
    exit_code = main(
        [
            "preset",
            "command",
            "short-video-capture",
            "video",
            "/dev/video0",
            "--duration",
            "5",
            "--output",
            "sample.avi",
        ]
    )

    assert exit_code == 0
    assert "gst-device-explorer capture video /dev/video0 --duration 5 --output sample.avi --dry-run" in capsys.readouterr().out


def test_preset_command_short_audio_capture_json_output(capsys) -> None:
    exit_code = main(
        [
            "preset",
            "command",
            "short-audio-capture",
            "audio-input",
            "hw:0,0",
            "--duration",
            "5",
            "--output",
            "sample.wav",
            "--json",
        ]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["suggestions"][0]["argv"] == [
        "gst-device-explorer",
        "capture",
        "audio-input",
        "hw:0,0",
        "--duration",
        "5",
        "--output",
        "sample.wav",
        "--dry-run",
    ]


def test_preset_command_wrong_target_kind_error(capsys) -> None:
    exit_code = main(
        ["preset", "command", "camera-preview", "audio-input", "hw:0,0"]
    )

    assert exit_code == 1
    assert capsys.readouterr().out == (
        "Preset `camera-preview` requires target kind `video`. "
        "Received: audio-input\n"
    )


def test_preset_command_missing_required_argument_error(capsys) -> None:
    exit_code = main(
        ["preset", "command", "short-video-capture", "video", "/dev/video0"]
    )

    assert exit_code == 1
    assert capsys.readouterr().out == (
        "Preset `short-video-capture` requires --duration and --output.\n"
    )


def test_preset_show_unknown_preset_error(capsys) -> None:
    exit_code = main(["preset", "show", "missing"])

    assert exit_code == 1
    assert capsys.readouterr().out == (
        "Preset not found: missing\n"
        "\n"
        "Try:\n"
        "  gst-device-explorer preset list\n"
    )
