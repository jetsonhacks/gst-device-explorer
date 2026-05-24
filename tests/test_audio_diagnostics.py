from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.core.audio_diagnostics import (
    build_audio_input_test_diagnostics,
    build_audio_output_test_diagnostics,
)
from gst_device_explorer.core.audio_pipelines import build_audio_output_test_candidates
from gst_device_explorer.core.models import Device, EnvironmentFact


def test_audio_input_diagnostic_available() -> None:
    diagnostics = build_audio_input_test_diagnostics(
        _audio_input_device(),
        _environment_with_audio_input_elements(),
    )

    assert len(diagnostics) == 1
    diagnostic = diagnostics[0]
    assert diagnostic.candidate_id == "generic-alsa-audio-input-level-fakesink"
    assert diagnostic.device_kind == "audio-input"
    assert diagnostic.device == "hw:0,0"
    assert diagnostic.status == "available"
    assert diagnostic.reason == (
        "ALSA capture device and required GStreamer elements are available."
    )
    assert diagnostic.required_elements == [
        "alsasrc",
        "audioconvert",
        "audioresample",
        "level",
        "fakesink",
    ]
    assert diagnostic.available_elements == diagnostic.required_elements
    assert diagnostic.missing_elements == []
    assert diagnostic.suggested_next_checks == []


def test_audio_output_diagnostic_available() -> None:
    diagnostics = build_audio_output_test_diagnostics(
        _audio_output_device(),
        _environment_with_audio_output_elements(),
    )

    assert len(diagnostics) == 1
    diagnostic = diagnostics[0]
    assert diagnostic.candidate_id == "generic-alsa-audio-output-sine-alsasink"
    assert diagnostic.device_kind == "audio-output"
    assert diagnostic.device == "hw:0,0"
    assert diagnostic.status == "available"
    assert diagnostic.reason == (
        "ALSA playback device and required GStreamer elements are available."
    )
    assert diagnostic.required_elements == [
        "audiotestsrc",
        "audioconvert",
        "audioresample",
        "alsasink",
    ]
    assert diagnostic.available_elements == diagnostic.required_elements
    assert diagnostic.missing_elements == []
    assert diagnostic.suggested_next_checks == []


def test_audio_input_diagnostic_with_missing_required_element() -> None:
    environment = [
        _element_fact("alsasrc", True),
        _element_fact("audioconvert", True),
        _element_fact("audioresample", True),
        _element_fact("level", False),
        _element_fact("fakesink", True),
    ]

    diagnostics = build_audio_input_test_diagnostics(
        _audio_input_device(),
        environment,
    )

    diagnostic = diagnostics[0]
    assert diagnostic.status == "unavailable"
    assert diagnostic.reason == "Required GStreamer elements are missing."
    assert diagnostic.available_elements == [
        "alsasrc",
        "audioconvert",
        "audioresample",
        "fakesink",
    ]
    assert diagnostic.missing_elements == ["level"]
    assert diagnostic.suggested_next_checks == ["gst-inspect-1.0 level"]


def test_audio_output_diagnostic_with_missing_required_element() -> None:
    environment = [
        _element_fact("audiotestsrc", True),
        _element_fact("audioconvert", True),
        _element_fact("audioresample", True),
        _element_fact("alsasink", False),
    ]

    diagnostics = build_audio_output_test_diagnostics(
        _audio_output_device(),
        environment,
    )

    diagnostic = diagnostics[0]
    assert diagnostic.status == "unavailable"
    assert diagnostic.reason == "Required GStreamer elements are missing."
    assert diagnostic.available_elements == [
        "audiotestsrc",
        "audioconvert",
        "audioresample",
    ]
    assert diagnostic.missing_elements == ["alsasink"]
    assert diagnostic.suggested_next_checks == ["gst-inspect-1.0 alsasink"]


def test_audio_diagnostics_do_not_change_candidate_generation_behavior() -> None:
    environment = [
        _element_fact("audiotestsrc", True),
        _element_fact("audioconvert", True),
        _element_fact("audioresample", True),
        _element_fact("alsasink", False),
    ]

    diagnostics = build_audio_output_test_diagnostics(
        _audio_output_device(),
        environment,
    )
    candidates = build_audio_output_test_candidates(_audio_output_device(), environment)

    assert diagnostics[0].status == "unavailable"
    assert candidates == []


def test_audio_input_diagnostics_ignore_non_input_device() -> None:
    diagnostics = build_audio_input_test_diagnostics(
        _audio_output_device(),
        _environment_with_audio_input_elements(),
    )

    assert diagnostics == []


def test_audio_output_diagnostics_ignore_non_output_device() -> None:
    diagnostics = build_audio_output_test_diagnostics(
        _audio_input_device(),
        _environment_with_audio_output_elements(),
    )

    assert diagnostics == []


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
