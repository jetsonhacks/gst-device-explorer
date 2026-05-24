"""Audio pipeline candidate builders."""

from __future__ import annotations

from gst_device_explorer.core.diagnostics import find_missing_elements
from gst_device_explorer.core.models import Device, EnvironmentFact, PipelineCandidate


GENERIC_ALSA_AUDIO_INPUT_TEST_PROFILE = "generic-alsa-audio-input-test"
GENERIC_ALSA_AUDIO_OUTPUT_TEST_PROFILE = "generic-alsa-audio-output-test"

ALSA_AUDIO_INPUT_LEVEL_ELEMENTS = [
    "alsasrc",
    "audioconvert",
    "audioresample",
    "level",
    "fakesink",
]
ALSA_AUDIO_OUTPUT_SINE_ELEMENTS = [
    "audiotestsrc",
    "audioconvert",
    "audioresample",
    "alsasink",
]


def build_audio_input_test_candidates(
    device: Device,
    environment: list[EnvironmentFact],
) -> list[PipelineCandidate]:
    """Build ALSA audio input level-test pipeline candidates."""

    if device.kind != "audio_input":
        return []

    if find_missing_elements(environment, ALSA_AUDIO_INPUT_LEVEL_ELEMENTS):
        return []

    alsa_device = _alsa_device_name(device)
    argv = [
        "gst-launch-1.0",
        "alsasrc",
        f"device={alsa_device}",
        "!",
        "audioconvert",
        "!",
        "audioresample",
        "!",
        "level",
        "interval=1000000000",
        "!",
        "fakesink",
    ]

    return [
        PipelineCandidate(
            candidate_id="generic-alsa-audio-input-level-fakesink",
            purpose="test ALSA audio input levels",
            command=" ".join(argv),
            confidence=0.8,
            argv=argv,
            reasons=[
                f"selected ALSA input device: {alsa_device}",
                "level element selected to expose input level messages",
                _required_elements_reason(ALSA_AUDIO_INPUT_LEVEL_ELEMENTS),
            ],
            warnings=[],
            required_elements=list(ALSA_AUDIO_INPUT_LEVEL_ELEMENTS),
            selected_profile=GENERIC_ALSA_AUDIO_INPUT_TEST_PROFILE,
        )
    ]


def build_audio_output_test_candidates(
    device: Device,
    environment: list[EnvironmentFact],
) -> list[PipelineCandidate]:
    """Build ALSA audio output sine-test pipeline candidates."""

    if device.kind != "audio_output":
        return []

    if find_missing_elements(environment, ALSA_AUDIO_OUTPUT_SINE_ELEMENTS):
        return []

    alsa_device = _alsa_device_name(device)
    argv = [
        "gst-launch-1.0",
        "audiotestsrc",
        "wave=sine",
        "freq=440",
        "!",
        "audioconvert",
        "!",
        "audioresample",
        "!",
        "alsasink",
        f"device={alsa_device}",
    ]

    return [
        PipelineCandidate(
            candidate_id="generic-alsa-audio-output-sine-alsasink",
            purpose="test ALSA audio output with sine wave",
            command=" ".join(argv),
            confidence=0.8,
            argv=argv,
            reasons=[
                f"selected ALSA output device: {alsa_device}",
                "audiotestsrc selected to generate a 440 Hz sine wave",
                _required_elements_reason(ALSA_AUDIO_OUTPUT_SINE_ELEMENTS),
            ],
            warnings=[],
            required_elements=list(ALSA_AUDIO_OUTPUT_SINE_ELEMENTS),
            selected_profile=GENERIC_ALSA_AUDIO_OUTPUT_TEST_PROFILE,
        )
    ]


def _alsa_device_name(device: Device) -> str:
    value = device.metadata.get("alsa_device", device.id)
    return str(value)


def _required_elements_reason(required_elements: list[str]) -> str:
    return "required elements available: " + ", ".join(required_elements)
