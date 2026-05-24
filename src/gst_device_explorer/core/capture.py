"""Bounded capture candidate builders and validation helpers."""

from __future__ import annotations

from pathlib import Path
import math

from gst_device_explorer.core.diagnostics import find_missing_elements
from gst_device_explorer.core.models import Capability, Device, EnvironmentFact, PipelineCandidate
from gst_device_explorer.core.pipelines import _build_caps, _first_fps


GENERIC_VIDEO_CAPTURE_PROFILE = "generic-v4l2-video-capture"
GENERIC_AUDIO_INPUT_CAPTURE_PROFILE = "generic-alsa-audio-input-capture"

VIDEO_CAPTURE_MJPEG_ELEMENTS = ["v4l2src", "jpegparse", "avimux", "filesink"]
VIDEO_CAPTURE_RAW_ELEMENTS = [
    "v4l2src",
    "videoconvert",
    "jpegenc",
    "avimux",
    "filesink",
]
AUDIO_INPUT_CAPTURE_WAV_ELEMENTS = [
    "alsasrc",
    "audioconvert",
    "audioresample",
    "wavenc",
    "filesink",
]


def validate_capture_duration(value: str) -> float:
    """Return a positive bounded duration in seconds."""

    try:
        duration = float(value)
    except ValueError as error:
        raise ValueError("duration must be a positive number of seconds") from error

    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("duration must be a positive number of seconds")

    return duration


def validate_capture_output_path(value: str) -> Path:
    """Return an explicit output path, rejecting existing files."""

    if not value:
        raise ValueError("output path is required")

    output_path = Path(value)
    if output_path.exists():
        raise FileExistsError(str(output_path))

    return output_path


def build_video_capture_candidates(
    device: Device,
    capabilities: list[Capability],
    environment: list[EnvironmentFact],
    duration_seconds: float,
    output_path: Path,
) -> list[PipelineCandidate]:
    """Build bounded V4L2 video capture candidates."""

    if device.kind != "video_input":
        return []

    candidates: list[PipelineCandidate] = []
    for capability in capabilities:
        values = capability.values
        if values.get("media_type") != "video":
            continue

        caps = _build_caps(values)
        if caps is None:
            continue

        pixel_format = values.get("pixel_format")
        required_elements = (
            VIDEO_CAPTURE_MJPEG_ELEMENTS
            if pixel_format == "MJPG"
            else VIDEO_CAPTURE_RAW_ELEMENTS
        )
        if find_missing_elements(environment, required_elements):
            continue

        candidates.append(
            _video_capture_candidate(
                device_path=_device_path(device),
                capability=capability,
                duration_seconds=duration_seconds,
                output_path=output_path,
                required_elements=required_elements,
            )
        )

    return candidates


def build_audio_input_capture_candidates(
    device: Device,
    environment: list[EnvironmentFact],
    duration_seconds: float,
    output_path: Path,
) -> list[PipelineCandidate]:
    """Build bounded ALSA audio input capture candidates."""

    if device.kind != "audio_input":
        return []

    if find_missing_elements(environment, AUDIO_INPUT_CAPTURE_WAV_ELEMENTS):
        return []

    alsa_device = _alsa_device_name(device)
    num_buffers = max(1, math.ceil(duration_seconds * 50))
    argv = [
        "gst-launch-1.0",
        "-e",
        "alsasrc",
        f"device={alsa_device}",
        f"num-buffers={num_buffers}",
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

    return [
        PipelineCandidate(
            candidate_id="generic-alsa-audio-input-wav-filesink",
            purpose="capture bounded ALSA audio input to WAV",
            command=" ".join(argv),
            confidence=0.8,
            argv=argv,
            reasons=[
                f"selected ALSA input device: {alsa_device}",
                f"duration: {_format_duration(duration_seconds)} seconds",
                f"output path: {output_path}",
                "file format: WAV",
                _required_elements_reason(AUDIO_INPUT_CAPTURE_WAV_ELEMENTS),
            ],
            warnings=[],
            required_elements=list(AUDIO_INPUT_CAPTURE_WAV_ELEMENTS),
            selected_profile=GENERIC_AUDIO_INPUT_CAPTURE_PROFILE,
        )
    ]


def _video_capture_candidate(
    device_path: str,
    capability: Capability,
    duration_seconds: float,
    output_path: Path,
    required_elements: list[str],
) -> PipelineCandidate:
    values = capability.values
    caps = _build_caps(values)
    if caps is None:
        raise ValueError("video capture candidate requires supported caps")

    fps = _first_fps(values)
    num_buffers = max(1, math.ceil(duration_seconds * float(fps or 30)))
    pixel_format = values.get("pixel_format")

    argv = [
        "gst-launch-1.0",
        "-e",
        "v4l2src",
        f"device={device_path}",
        f"num-buffers={num_buffers}",
        "!",
        caps,
        "!",
    ]

    if pixel_format == "MJPG":
        candidate_id = "generic-v4l2-mjpeg-avimux-filesink"
        argv.extend(["jpegparse", "!"])
    else:
        candidate_id = "generic-v4l2-yuyv-jpegenc-avimux-filesink"
        argv.extend(["videoconvert", "!", "jpegenc", "!"])

    argv.extend(["avimux", "!", "filesink", f"location={output_path}"])

    warnings = []
    if output_path.suffix.lower() not in {"", ".avi"}:
        warnings.append("video capture candidate writes AVI content; prefer a .avi output path")

    return PipelineCandidate(
        candidate_id=candidate_id,
        purpose="capture bounded V4L2 video input to AVI",
        command=" ".join(argv),
        confidence=0.8,
        argv=argv,
        reasons=[
            f"selected device path: {device_path}",
            f"selected pixel format: {pixel_format}",
            f"duration: {_format_duration(duration_seconds)} seconds",
            f"output path: {output_path}",
            "file format: AVI",
            _required_elements_reason(required_elements),
        ],
        warnings=warnings,
        required_elements=list(required_elements),
        selected_profile=GENERIC_VIDEO_CAPTURE_PROFILE,
    )


def _device_path(device: Device) -> str:
    path = device.metadata.get("path")
    if isinstance(path, str) and path:
        return path
    return device.id


def _alsa_device_name(device: Device) -> str:
    value = device.metadata.get("alsa_device", device.id)
    return str(value)


def _required_elements_reason(required_elements: list[str]) -> str:
    return "required elements available: " + ", ".join(required_elements)


def _format_duration(duration_seconds: float) -> str:
    duration = float(duration_seconds)
    if duration.is_integer():
        return str(int(duration))
    return str(duration)
