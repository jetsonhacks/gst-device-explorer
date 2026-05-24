from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.core.audio_pipelines import (
    build_audio_input_test_candidates,
    build_audio_output_test_candidates,
)
from gst_device_explorer.core.models import Device, EnvironmentFact


def test_audio_input_level_candidate() -> None:
    candidates = build_audio_input_test_candidates(
        _audio_input_device(),
        _environment_with_audio_input_elements(),
    )

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.candidate_id == "generic-alsa-audio-input-level-fakesink"
    assert candidate.purpose == "test ALSA audio input levels"
    assert candidate.command == (
        "gst-launch-1.0 alsasrc device=hw:0,0 ! audioconvert ! "
        "audioresample ! level interval=1000000000 ! fakesink"
    )
    assert candidate.argv == [
        "gst-launch-1.0",
        "alsasrc",
        "device=hw:0,0",
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
    assert candidate.required_elements == [
        "alsasrc",
        "audioconvert",
        "audioresample",
        "level",
        "fakesink",
    ]
    assert candidate.selected_profile == "generic-alsa-audio-input-test"
    assert candidate.reasons == [
        "selected ALSA input device: hw:0,0",
        "level element selected to expose input level messages",
        (
            "required elements available: alsasrc, audioconvert, "
            "audioresample, level, fakesink"
        ),
    ]


def test_audio_output_sine_candidate() -> None:
    candidates = build_audio_output_test_candidates(
        _audio_output_device(),
        _environment_with_audio_output_elements(),
    )

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.candidate_id == "generic-alsa-audio-output-sine-alsasink"
    assert candidate.purpose == "test ALSA audio output with sine wave"
    assert candidate.command == (
        "gst-launch-1.0 audiotestsrc wave=sine freq=440 ! "
        "audioconvert ! audioresample ! alsasink device=hw:0,0"
    )
    assert candidate.argv == [
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
        "device=hw:0,0",
    ]
    assert candidate.required_elements == [
        "audiotestsrc",
        "audioconvert",
        "audioresample",
        "alsasink",
    ]
    assert candidate.selected_profile == "generic-alsa-audio-output-test"
    assert candidate.reasons == [
        "selected ALSA output device: hw:0,0",
        "audiotestsrc selected to generate a 440 Hz sine wave",
        (
            "required elements available: audiotestsrc, audioconvert, "
            "audioresample, alsasink"
        ),
    ]


def test_audio_input_builder_ignores_non_input_device() -> None:
    candidates = build_audio_input_test_candidates(
        _audio_output_device(),
        _environment_with_audio_input_elements(),
    )

    assert candidates == []


def test_audio_output_builder_ignores_non_output_device() -> None:
    candidates = build_audio_output_test_candidates(
        _audio_input_device(),
        _environment_with_audio_output_elements(),
    )

    assert candidates == []


def test_audio_input_candidate_requires_all_elements() -> None:
    environment = [
        _element_fact("alsasrc", True),
        _element_fact("audioconvert", True),
        _element_fact("audioresample", True),
        _element_fact("level", True),
        _element_fact("fakesink", False),
    ]

    candidates = build_audio_input_test_candidates(_audio_input_device(), environment)

    assert candidates == []


def test_audio_output_candidate_requires_all_elements() -> None:
    environment = [
        _element_fact("audiotestsrc", True),
        _element_fact("audioconvert", True),
        _element_fact("audioresample", True),
        _element_fact("alsasink", False),
    ]

    candidates = build_audio_output_test_candidates(_audio_output_device(), environment)

    assert candidates == []


def _audio_input_device() -> Device:
    return Device(
        id="hw:0,0",
        kind="audio_input",
        name="USB Audio: Capture",
        metadata={"backend": "alsa", "alsa_device": "hw:0,0"},
    )


def _audio_output_device() -> Device:
    return Device(
        id="hw:0,0",
        kind="audio_output",
        name="USB Audio: Playback",
        metadata={"backend": "alsa", "alsa_device": "hw:0,0"},
    )


def _environment_with_audio_input_elements() -> list[EnvironmentFact]:
    return [
        _element_fact("alsasrc", True),
        _element_fact("audioconvert", True),
        _element_fact("audioresample", True),
        _element_fact("level", True),
        _element_fact("fakesink", True),
    ]


def _environment_with_audio_output_elements() -> list[EnvironmentFact]:
    return [
        _element_fact("audiotestsrc", True),
        _element_fact("audioconvert", True),
        _element_fact("audioresample", True),
        _element_fact("alsasink", True),
    ]


def _element_fact(element: str, available: bool) -> EnvironmentFact:
    return EnvironmentFact(
        name="gstreamer_element_available",
        value=available,
        source="gst-inspect-1.0",
        metadata={"element": element},
    )
