from pathlib import Path
import subprocess
import sys

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.core.capture import (
    build_audio_input_capture_candidates,
    build_video_capture_candidates,
    validate_capture_duration,
    validate_capture_output_path,
)
from gst_device_explorer.core.execution import create_execution_plan, run_execution_plan
from gst_device_explorer.core.models import Capability, Device, EnvironmentFact


def test_video_capture_candidate_from_mjpeg_capability(tmp_path) -> None:
    output_path = tmp_path / "sample.avi"

    candidates = build_video_capture_candidates(
        _video_device(),
        [_video_capability(pixel_format="MJPG", fps=[30.0])],
        _environment("v4l2src", "jpegparse", "avimux", "filesink"),
        duration_seconds=5,
        output_path=output_path,
    )

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.candidate_id == "generic-v4l2-mjpeg-avimux-filesink"
    assert candidate.argv == [
        "gst-launch-1.0",
        "-e",
        "v4l2src",
        "device=/dev/video0",
        "num-buffers=150",
        "!",
        "image/jpeg, width=640, height=480, framerate=30/1",
        "!",
        "jpegparse",
        "!",
        "avimux",
        "!",
        "filesink",
        f"location={output_path}",
    ]
    assert candidate.selected_profile == "generic-v4l2-video-capture"
    assert "duration: 5 seconds" in candidate.reasons
    assert f"output path: {output_path}" in candidate.reasons


def test_video_capture_candidate_from_yuyv_capability(tmp_path) -> None:
    candidates = build_video_capture_candidates(
        _video_device(),
        [_video_capability(pixel_format="YUYV")],
        _environment("v4l2src", "videoconvert", "jpegenc", "avimux", "filesink"),
        duration_seconds=1,
        output_path=tmp_path / "sample.avi",
    )

    assert len(candidates) == 1
    assert candidates[0].candidate_id == "generic-v4l2-yuyv-jpegenc-avimux-filesink"
    assert "jpegenc" in candidates[0].argv


def test_video_capture_candidate_warns_when_extension_is_not_avi(tmp_path) -> None:
    candidates = build_video_capture_candidates(
        _video_device(),
        [_video_capability(pixel_format="MJPG")],
        _environment("v4l2src", "jpegparse", "avimux", "filesink"),
        duration_seconds=1,
        output_path=tmp_path / "sample.mp4",
    )

    assert candidates[0].warnings == [
        "video capture candidate writes AVI content; prefer a .avi output path"
    ]


def test_video_capture_candidate_requires_generated_caps_and_elements(tmp_path) -> None:
    candidates = build_video_capture_candidates(
        _video_device(),
        [_video_capability(pixel_format="H264")],
        _environment("v4l2src", "jpegparse", "avimux", "filesink"),
        duration_seconds=1,
        output_path=tmp_path / "sample.avi",
    )

    assert candidates == []


def test_audio_input_capture_candidate(tmp_path) -> None:
    output_path = tmp_path / "sample.wav"

    candidates = build_audio_input_capture_candidates(
        _audio_input_device(),
        _environment("alsasrc", "audioconvert", "audioresample", "wavenc", "filesink"),
        duration_seconds=2.5,
        output_path=output_path,
    )

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.candidate_id == "generic-alsa-audio-input-wav-filesink"
    assert candidate.argv == [
        "gst-launch-1.0",
        "-e",
        "alsasrc",
        "device=hw:0,0",
        "num-buffers=125",
        "!",
        "audioconvert",
        "!",
        "audioresample",
        "!",
        "wavenc",
        "!",
        "filesink",
        f"location={output_path}",
    ]
    assert candidate.selected_profile == "generic-alsa-audio-input-capture"
    assert "file format: WAV" in candidate.reasons


def test_audio_input_capture_ignores_audio_output_device(tmp_path) -> None:
    candidates = build_audio_input_capture_candidates(
        Device(id="hw:0,0", kind="audio_output", name="Speaker"),
        _environment("alsasrc", "audioconvert", "audioresample", "wavenc", "filesink"),
        duration_seconds=1,
        output_path=tmp_path / "sample.wav",
    )

    assert candidates == []


def test_validate_capture_duration_accepts_positive_numeric_seconds() -> None:
    assert validate_capture_duration("2.5") == 2.5


@pytest.mark.parametrize("value", ["0", "-1", "not-a-number", "nan", "inf"])
def test_validate_capture_duration_rejects_unbounded_values(value: str) -> None:
    with pytest.raises(ValueError, match="duration must be a positive number"):
        validate_capture_duration(value)


def test_validate_capture_output_path_rejects_existing_file(tmp_path) -> None:
    output_path = tmp_path / "sample.wav"
    output_path.write_text("already here")

    with pytest.raises(FileExistsError):
        validate_capture_output_path(str(output_path))


def test_capture_execution_uses_safe_argv_form(tmp_path) -> None:
    calls = []
    process = _FakeProcess(return_code=0)
    candidate = build_audio_input_capture_candidates(
        _audio_input_device(),
        _environment("alsasrc", "audioconvert", "audioresample", "wavenc", "filesink"),
        duration_seconds=1,
        output_path=tmp_path / "sample.wav",
    )[0]
    plan = create_execution_plan(candidate)

    def fake_popen(*args, **kwargs):
        calls.append((args, kwargs))
        return process

    exit_code = run_execution_plan(plan, popen_factory=fake_popen, timeout_seconds=6)

    assert exit_code == 0
    assert calls == [((candidate.argv,), {})]


def test_capture_execution_timeout_terminates_child(tmp_path) -> None:
    process = _FakeProcess(return_code=0, timeout_on_first_wait=True)
    candidate = build_audio_input_capture_candidates(
        _audio_input_device(),
        _environment("alsasrc", "audioconvert", "audioresample", "wavenc", "filesink"),
        duration_seconds=1,
        output_path=tmp_path / "sample.wav",
    )[0]
    plan = create_execution_plan(candidate)

    exit_code = run_execution_plan(
        plan,
        popen_factory=lambda argv: process,
        terminate_timeout_seconds=0.01,
        timeout_seconds=6,
    )

    assert exit_code == 124
    assert process.terminated is True


def _video_device() -> Device:
    return Device(
        id="/dev/video0",
        kind="video_input",
        name="video0",
        metadata={"backend": "v4l2", "path": "/dev/video0"},
    )


def _audio_input_device() -> Device:
    return Device(
        id="hw:0,0",
        kind="audio_input",
        name="USB Audio",
        metadata={"backend": "alsa", "alsa_device": "hw:0,0"},
    )


def _video_capability(pixel_format: str, fps: list[float] | None = None) -> Capability:
    return Capability(
        name="video_format",
        values={
            "media_type": "video",
            "pixel_format": pixel_format,
            "width": 640,
            "height": 480,
            "fps": fps or [30.0],
        },
        source="v4l2-ctl",
    )


def _environment(*elements: str) -> list[EnvironmentFact]:
    return [
        EnvironmentFact(
            name="gstreamer_element_available",
            value=True,
            source="gst-inspect-1.0",
            metadata={"element": element},
        )
        for element in elements
    ]


class _FakeProcess:
    def __init__(self, return_code: int, timeout_on_first_wait: bool = False) -> None:
        self.return_code = return_code
        self.timeout_on_first_wait = timeout_on_first_wait
        self.wait_calls = 0
        self.terminated = False
        self.killed = False

    def wait(self, timeout=None):
        self.wait_calls += 1
        if self.timeout_on_first_wait and self.wait_calls == 1:
            raise subprocess.TimeoutExpired("gst-launch-1.0", timeout)
        return self.return_code

    def terminate(self) -> None:
        self.terminated = True

    def kill(self) -> None:
        self.killed = True
