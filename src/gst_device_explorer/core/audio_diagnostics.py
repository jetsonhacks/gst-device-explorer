"""Audio pipeline diagnostic builders."""

from __future__ import annotations

from gst_device_explorer.core.audio_pipelines import (
    ALSA_AUDIO_INPUT_LEVEL_ELEMENTS,
    ALSA_AUDIO_OUTPUT_SINE_ELEMENTS,
)
from gst_device_explorer.core.diagnostics import build_requirement_diagnostic
from gst_device_explorer.core.models import Device, EnvironmentFact, PipelineDiagnostic


ALSA_AUDIO_INPUT_LEVEL_CANDIDATE_ID = "generic-alsa-audio-input-level-fakesink"
ALSA_AUDIO_OUTPUT_SINE_CANDIDATE_ID = "generic-alsa-audio-output-sine-alsasink"


def build_audio_input_test_diagnostics(
    device: Device,
    environment: list[EnvironmentFact],
) -> list[PipelineDiagnostic]:
    """Build diagnostics for the ALSA audio input level-test candidate."""

    if device.kind != "audio_input":
        return []

    return [
        build_requirement_diagnostic(
            candidate_id=ALSA_AUDIO_INPUT_LEVEL_CANDIDATE_ID,
            device_kind="audio-input",
            device_id=str(device.metadata.get("alsa_device", device.id)),
            available_reason=(
                "ALSA capture device and required GStreamer elements are available."
            ),
            required_elements=ALSA_AUDIO_INPUT_LEVEL_ELEMENTS,
            environment=environment,
        )
    ]


def build_audio_output_test_diagnostics(
    device: Device,
    environment: list[EnvironmentFact],
) -> list[PipelineDiagnostic]:
    """Build diagnostics for the ALSA audio output sine-test candidate."""

    if device.kind != "audio_output":
        return []

    return [
        build_requirement_diagnostic(
            candidate_id=ALSA_AUDIO_OUTPUT_SINE_CANDIDATE_ID,
            device_kind="audio-output",
            device_id=str(device.metadata.get("alsa_device", device.id)),
            available_reason=(
                "ALSA playback device and required GStreamer elements are available."
            ),
            required_elements=ALSA_AUDIO_OUTPUT_SINE_ELEMENTS,
            environment=environment,
        )
    ]


