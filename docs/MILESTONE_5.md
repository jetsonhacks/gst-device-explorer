# Milestone 5 — Pipeline Diagnostics and Explainability

Status: Complete

Target version: `v0.5.0`

## Theme

Milestone 5 adds structured diagnostics for pipeline candidate generation.

The tool can already discover devices, inspect media capabilities, generate video and audio pipeline candidates, group related endpoints, and safely run selected candidates. The next step is to explain candidate decisions more clearly.

This milestone focuses on making the tool answer:

- Why was this pipeline candidate generated?
- Why was a candidate not generated?
- Which required GStreamer elements are available or missing?
- Which device facts were used to make the decision?
- What should the user check next?

The goal is not to add more pipeline types. The goal is to make existing candidate generation easier to understand, debug, test, and eventually present in a GUI.

## Slice 1 Status

Implemented in the first slice:

- a small `PipelineDiagnostic` model
- structured diagnostics for the ALSA audio input level-test candidate
- structured diagnostics for the ALSA audio output sine-test candidate
- audio diagnostics text output through `pipeline audio-input --diagnostics`
- audio diagnostics JSON output through `pipeline audio-input --diagnostics --json`
- audio diagnostics text output through `pipeline audio-output --diagnostics`
- audio diagnostics JSON output through `pipeline audio-output --diagnostics --json`
- missing required element explanations with `gst-inspect-1.0 <element>` checks
- tests using synthetic ALSA devices and synthetic GStreamer environment facts

Still deferred:

- video pipeline diagnostics
- additional audio pipeline families
- audio loopback
- group-based diagnostics or execution

## Slice 2 Status

Implemented in the second slice:

- structured diagnostics for generic V4L2 MJPEG preview candidates
- structured diagnostics for generic V4L2 YUYV preview candidates
- structured diagnostics for Jetson/NVIDIA MJPEG preview candidates
- video diagnostics text output through `pipeline video --diagnostics`
- video diagnostics JSON output through `pipeline video --diagnostics --json`
- missing required element explanations with `gst-inspect-1.0 <element>` checks
- tests using synthetic V4L2 capabilities and synthetic GStreamer environment facts

Diagnostics now cover the existing audio and video candidate families. The milestone remains in progress while broader documentation and any remaining explainability refinements are evaluated.

Still deferred:

- new video pipeline families
- new audio pipeline families
- audio loopback
- group-based diagnostics or execution

## Slice 3 Status

Implemented in the integration/documentation slice:

- shared diagnostic helpers for required-element availability, missing elements, and `gst-inspect-1.0 <element>` checks
- consistent text and JSON diagnostic rendering for audio and video
- README workflow examples for candidate inspection, diagnostics, dry-run, and run
- setup documentation for audio and video diagnostics validation
- tests for shared diagnostic helper ordering and suggested checks

## Completion Status

Milestone 5 is complete for the `v0.5.0` release.

Implemented:

- structured `PipelineDiagnostic` records
- shared required-element diagnostic helpers
- audio diagnostics for existing ALSA input and output candidates
- video diagnostics for existing generic V4L2 and Jetson/NVIDIA candidates
- text diagnostics through existing `pipeline ... --diagnostics` commands
- JSON diagnostics through existing `pipeline ... --diagnostics --json` commands
- stable missing-element ordering
- `gst-inspect-1.0 <element>` suggested checks for missing elements
- documentation for the discover, inspect, diagnose, dry-run, and run workflow
- synthetic test coverage for audio diagnostics, video diagnostics, CLI output, JSON output, and shared helpers

Candidate families covered:

- `generic-alsa-audio-input-level-fakesink`
- `generic-alsa-audio-output-sine-alsasink`
- `generic-v4l2-mjpeg-jpegdec-autovideosink`
- `generic-v4l2-yuyv-videoconvert-autovideosink`
- `jetson-uvc-mjpeg-nvjpeg-nveglglessink`

Still intentionally deferred:

- new audio or video pipeline families
- audio loopback
- group-based diagnostics or execution
- ASR, TTS, and WebRTC
- PulseAudio and PipeWire
- effects and echo cancellation
- recording workflows
- synchronized audio/video workflows
- Reachy-specific behavior
- JetPack-version-specific behavior

## Goals

Add a structured diagnostics layer for pipeline candidate generation.

The diagnostics should be useful for:

- CLI users
- JSON consumers
- tests
- future GUI renderers
- debugging Jetson / Linux media setups

Diagnostics should be evidence-based and derived from existing probe results, device facts, candidate requirements, and environment facts.

## Non-goals

Milestone 5 should not add:

- new video pipeline families
- new audio pipeline families
- audio loopback
- synchronized audio/video capture
- group-based pipeline execution
- ASR
- TTS
- WebRTC
- PulseAudio
- PipeWire
- effects
- echo cancellation
- recording workflows
- Reachy-specific hard-coding
- JetPack-version-specific hard-coding
- arbitrary user-supplied GStreamer execution

## Design Principles

- Probe first, explain later.
- Keep diagnostics structured, not just formatted strings.
- CLI and future GUI are renderers.
- Avoid ad hoc string matching where structured facts already exist.
- Candidate diagnostics should be stable enough for tests.
- Missing candidates should be explainable.
- Diagnostics should not change candidate generation behavior unless an existing bug is discovered.
- Keep the milestone narrow.

## Proposed Model Concepts

Milestone 5 may add one or more lightweight diagnostic models.

Possible names:

- `PipelineDiagnostic`
- `CandidateDiagnostic`
- `PipelineRequirementStatus`
- `CandidateDecision`
- `MissingRequirement`

The exact names should follow the style of the existing codebase.

A diagnostic record may include:

- candidate ID
- device kind
- device identifier
- candidate label/name
- decision status
  - `available`
  - `unavailable`
  - `filtered`
  - `not_applicable`
- reason
- required elements
- available required elements
- missing required elements
- relevant device facts
- relevant environment facts
- suggested next checks

Example shape:

```json
{
  "candidate_id": "generic-alsa-audio-output-sine-alsasink",
  "device_kind": "audio-output",
  "device": "hw:0,0",
  "status": "available",
  "reason": "ALSA playback device and required GStreamer elements are available.",
  "required_elements": [
    "audiotestsrc",
    "audioconvert",
    "audioresample",
    "alsasink"
  ],
  "available_elements": [
    "audiotestsrc",
    "audioconvert",
    "audioresample",
    "alsasink"
  ],
  "missing_elements": [],
  "suggested_next_checks": []
}
```

Example missing-elements shape:

```json
{
  "candidate_id": "generic-alsa-audio-output-sine-alsasink",
  "device_kind": "audio-output",
  "device": "hw:0,0",
  "status": "unavailable",
  "reason": "Required GStreamer elements are missing.",
  "required_elements": [
    "audiotestsrc",
    "audioconvert",
    "audioresample",
    "alsasink"
  ],
  "available_elements": [
    "audiotestsrc",
    "audioconvert",
    "audioresample"
  ],
  "missing_elements": [
    "alsasink"
  ],
  "suggested_next_checks": [
    "Check that the GStreamer ALSA plugin is installed.",
    "Run: gst-inspect-1.0 alsasink"
  ]
}
```

## Candidate Coverage

Diagnostics should cover existing candidate families.

### Video Candidates

The second slice implements diagnostics for existing video candidate availability, including:

- source element requirements
- decoder requirements
- converter requirements
- sink requirements
- caps/profile assumptions where already available
- missing required elements

Examples:

- generic V4L2 preview candidate
- Jetson NVIDIA MJPEG decode preview candidate
- existing video candidates already supported by the project

### Audio Candidates

The first slice implements diagnostics for existing audio candidate availability, including:

- audio input level-test candidate
- audio output sine-test candidate
- required ALSA/GStreamer elements
- missing required elements

Existing Milestone 4 candidate IDs:

- `generic-alsa-audio-input-level-fakesink`
- `generic-alsa-audio-output-sine-alsasink`

## CLI Shape

Add diagnostics in a way that mirrors existing command structure.

Implemented first-slice command shapes:

```sh
gst-device-explorer pipeline audio-input hw:0,0 --diagnostics
gst-device-explorer pipeline audio-input hw:0,0 --diagnostics --json

gst-device-explorer pipeline audio-output hw:0,0 --diagnostics
gst-device-explorer pipeline audio-output hw:0,0 --diagnostics --json
```

Implemented video command shapes:

```sh
gst-device-explorer pipeline video /dev/video0 --diagnostics
gst-device-explorer pipeline video /dev/video0 --diagnostics --json
```

Milestone 5 uses `--diagnostics` on the existing `pipeline` commands because diagnostics explain the same candidate generation decision those commands already render.

## Text Output

Text output should be concise and practical.

Example:

```text
Pipeline diagnostics for audio-output hw:0,0

Candidate: generic-alsa-audio-output-sine-alsasink
Status: available
Reason: ALSA playback device and required GStreamer elements are available.

Required elements:
  ok: audiotestsrc
  ok: audioconvert
  ok: audioresample
  ok: alsasink

Suggested next step:
  gst-device-explorer run audio-output hw:0,0 --dry-run
```

Missing element example:

```text
Pipeline diagnostics for audio-output hw:0,0

Candidate: generic-alsa-audio-output-sine-alsasink
Status: unavailable
Reason: Required GStreamer elements are missing.

Required elements:
  ok: audiotestsrc
  ok: audioconvert
  ok: audioresample
  missing: alsasink

Suggested checks:
  gst-inspect-1.0 alsasink
```

## JSON Output

JSON output should expose structured diagnostics without requiring callers to parse human text.

The JSON should be stable enough for tests and future GUI use.

Possible shape:

```json
{
  "device_kind": "audio-output",
  "device": "hw:0,0",
  "diagnostics": [
    {
      "candidate_id": "generic-alsa-audio-output-sine-alsasink",
      "status": "available",
      "reason": "ALSA playback device and required GStreamer elements are available.",
      "required_elements": [
        "audiotestsrc",
        "audioconvert",
        "audioresample",
        "alsasink"
      ],
      "available_elements": [
        "audiotestsrc",
        "audioconvert",
        "audioresample",
        "alsasink"
      ],
      "missing_elements": [],
      "suggested_next_checks": []
    }
  ]
}
```

## Testing

Tests should use synthetic devices and synthetic environment facts.

Tests should not require real hardware.

Test coverage should include:

- available audio input candidate diagnostics
- available audio output candidate diagnostics
- missing audio input required element diagnostics
- missing audio output required element diagnostics
- available generic video candidate diagnostics
- missing generic video required element diagnostics
- available Jetson/NVIDIA MJPEG candidate diagnostics
- missing Jetson/NVIDIA required element diagnostics
- JSON diagnostic shape
- text diagnostic rendering
- CLI coverage for diagnostics commands or flags
- stable candidate IDs in diagnostics
- missing candidate explanation when required elements are unavailable
- no change to existing candidate generation behavior
- all existing tests continue to pass

## Documentation

Documentation now covers:

- how to inspect pipeline candidates
- how to inspect diagnostics
- how to use diagnostics before running a candidate
- how missing GStreamer elements are reported
- how diagnostics help with Jetson and Linux media setup debugging

Updated documentation:

- `README.md`
- `docs/SETUP.md`
- `docs/MILESTONE_5.md`

## Validation Commands

Run:

```sh
/home/jim/.local/bin/uv run python -m pytest
```

Optional manual checks:

```sh
/home/jim/.local/bin/uv run gst-device-explorer pipeline audio-input hw:0,0 --diagnostics
/home/jim/.local/bin/uv run gst-device-explorer pipeline audio-input hw:0,0 --diagnostics --json

/home/jim/.local/bin/uv run gst-device-explorer pipeline audio-output hw:0,0 --diagnostics
/home/jim/.local/bin/uv run gst-device-explorer pipeline audio-output hw:0,0 --diagnostics --json

/home/jim/.local/bin/uv run gst-device-explorer pipeline video /dev/video0 --diagnostics
/home/jim/.local/bin/uv run gst-device-explorer pipeline video /dev/video0 --diagnostics --json
```

## Completion Criteria

Milestone 5 completion criteria:

- pipeline diagnostics are represented as structured data
- diagnostics cover existing video candidates
- diagnostics cover existing audio candidates
- missing required GStreamer elements are clearly reported
- text output is concise and useful
- JSON output is structured and test-covered
- docs explain the diagnostic workflow
- all tests pass
- project version is bumped to `0.5.0`

## Deferred Beyond Milestone 5

The following remain out of scope:

- audio loopback
- group-based pipeline execution
- automatic package installation suggestions
- JetPack-version-specific behavior
- PulseAudio/PipeWire support
- ASR/TTS/WebRTC
- synchronized audio/video capture
- recording workflows
- effects
- echo cancellation
- GUI implementation
