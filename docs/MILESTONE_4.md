# Milestone 4 — Audio Pipeline Candidates

## Goal

Add GStreamer audio pipeline candidate generation for discovered audio input and audio output devices.

Milestones 1–3 established the core shape of the project:

- Milestone 1: discover devices, probe capabilities, and generate video pipeline candidates
- Milestone 2: safely execute selected video pipeline candidates
- Milestone 3: group related Linux device endpoints into composite hardware

Milestone 4 extends the candidate-generation model to audio.

The tool discovers ALSA audio input and output devices. It can also group related audio devices, such as the Reachy Mini audio input and output. Milestone 4 adds structured generation and safe execution for basic ALSA input and output test pipeline candidates.

Milestone 4 adds structured audio pipeline candidates without turning the project into a full audio routing, recording, or speech stack.

## Completion Status

Milestone 4 is complete for the `v0.4.0` release.

Implemented:

- structured ALSA audio input level-test candidate generation
- structured ALSA audio output sine-test candidate generation
- stable audio candidate IDs
- text and JSON candidate inspection for audio input and output devices
- safe `run audio-input` and `run audio-output` execution
- `--candidate` selection for audio run commands, matching video behavior
- argv-only subprocess execution through the existing execution helper
- tests using synthetic audio devices and environment facts

Deferred by design:

- audio loopback
- group-based execution
- ASR, TTS, and WebRTC
- PulseAudio and PipeWire
- effects and echo cancellation
- recording workflows
- synchronized audio/video workflows

## Slice 1 Status

Implemented in the first slice:

- structured ALSA audio input level-test candidate generation
- structured ALSA audio output sine-test candidate generation
- CLI rendering for `pipeline audio-input` and `pipeline audio-output`
- JSON rendering for audio pipeline candidates
- GStreamer element availability checks for the required audio elements
- unit tests using synthetic ALSA devices and synthetic environment facts

Candidate IDs added:

```text
generic-alsa-audio-input-level-fakesink
generic-alsa-audio-output-sine-alsasink
```

Still out of scope for this slice:

- loopback candidate generation
- PulseAudio or PipeWire support
- recording workflows
- synchronized audio/video capture
- group-based pipeline execution

## Slice 2 Status

Implemented in the second slice:

- safe `run audio-input` support for the existing input level-test candidate
- safe `run audio-output` support for the existing output sine-test candidate
- `--dry-run` support for audio input and output execution commands
- `--candidate` selection support matching the existing video run command
- argv-based subprocess execution through the existing execution helper
- mocked CLI execution tests that do not require real audio hardware

Commands added:

```sh
gst-device-explorer run audio-input hw:0,0 --dry-run
gst-device-explorer run audio-output hw:0,0 --dry-run
gst-device-explorer run audio-input hw:0,0
gst-device-explorer run audio-output hw:0,0
```

Execution remains intentionally bounded:

- only generated `PipelineCandidate.argv` values are executed
- no arbitrary user-supplied pipeline strings are accepted
- subprocess execution does not use `shell=True`
- Ctrl+C cleanup continues to use the existing execution helper

Validation:

```sh
/home/jim/.local/bin/uv run python -m pytest
```

Latest result:

```text
154 passed
```

Still out of scope after this slice:

- loopback candidate generation or execution
- group-based audio execution
- PulseAudio or PipeWire support
- recording workflows
- synchronized audio/video capture

## Why This Milestone

Reachy Mini exposes useful audio devices:

- an audio input
- an audio output

Before Milestone 4, the tool could discover these devices and group them, but it could not yet answer the next practical question:

> What GStreamer pipeline can I use to test or use this audio device?

Milestone 4 should provide that answer.

This keeps the project on the same architectural path:

```text
probe device
  -> normalize facts
  -> build structured PipelineCandidate objects
  -> render candidate commands
  -> optionally execute selected candidates
```

## Scope

Milestone 4 adds audio pipeline candidate generation for:

- audio input test pipelines
- audio output test pipelines

The first version should favor simple, inspectable, reliable pipelines over complex audio processing.

## Non-Goals

This milestone intentionally does not add:

- ASR
- TTS
- WebRTC
- speech agent integration
- PulseAudio routing
- PipeWire routing
- audio effects
- echo cancellation
- beamforming
- recording management
- file output workflows
- synchronized audio/video capture
- group-based pipeline execution
- robot behavior logic
- Reachy-specific hard-coding

Those may become future milestones, but they should not be pulled into Milestone 4.

## Candidate Types

### Audio Input Preview/Test

Generate candidates that prove an audio input device can produce samples.

Implemented command family:

```sh
gst-launch-1.0 alsasrc device=hw:0,0 ! audioconvert ! audioresample ! level interval=1000000000 ! fakesink
```

The `level ! fakesink` style is useful because it can validate input activity without creating a feedback loop.

### Audio Output Test

Generate candidates that prove an audio output device can play sound.

Implemented command family:

```sh
gst-launch-1.0 audiotestsrc wave=sine freq=440 ! audioconvert ! audioresample ! alsasink device=hw:0,0
```

### Audio Loopback

Audio loopback is intentionally deferred.

Possible command family:

```sh
gst-launch-1.0 alsasrc device=hw:0,0 ! audioconvert ! audioresample ! alsasink device=hw:0,0
```

Loopback can create feedback on speakers/microphones or route audio in surprising ways. It should be explicit, clearly labeled, and separate from the default input and output tests.

## User-Facing Commands

Audio pipeline candidate commands:

```sh
gst-device-explorer pipeline audio-input hw:0,0
gst-device-explorer pipeline audio-output hw:0,0
```

JSON output:

```sh
gst-device-explorer pipeline audio-input hw:0,0 --json
gst-device-explorer pipeline audio-output hw:0,0 --json
```

## Audio Execution

Milestone 4 extends the existing `run` command to the generated audio input and output candidates.

```sh
gst-device-explorer run audio-input hw:0,0 --dry-run
gst-device-explorer run audio-output hw:0,0 --dry-run
gst-device-explorer run audio-input hw:0,0
gst-device-explorer run audio-output hw:0,0
```

Execution remains limited to generated `PipelineCandidate.argv` values. The CLI does not accept arbitrary user-supplied GStreamer pipeline strings.

## Data Model

Reuse `PipelineCandidate`.

Audio candidates should use the same structured model as video candidates:

- stable candidate ID
- human-readable description
- command or structured command representation
- confidence
- profile
- required GStreamer elements
- reasons

Example candidate IDs:

```text
generic-alsa-audio-input-level-fakesink
generic-alsa-audio-output-sine-alsasink
```

Candidate IDs should describe the pipeline strategy, not every device detail.

## Profiles

Milestone 4 should keep profiles simple.

Initial profile families may include:

```text
generic-alsa-audio-input-test
generic-alsa-audio-output-test
```

Do not add a full external profile system yet unless needed.

## GStreamer Elements

Required elements for the implemented candidates:

```text
alsasrc
alsasink
audiotestsrc
audioconvert
audioresample
level
fakesink
```

The environment probe already checks for several audio-related GStreamer elements. Extend the element list only if required by the selected candidates.

Pipeline candidates should only be emitted when required elements are available.

## Design Rules

- Probe first, build later.
- Keep audio candidates structured.
- Do not generate ad hoc strings without reasons.
- Do not hard-code Reachy Mini.
- Prefer ALSA-first behavior for this milestone.
- Keep PulseAudio and PipeWire out of scope.
- Avoid feedback-prone loopback as the default.
- Keep CLI and future GUI as renderers.
- Preserve existing video pipeline behavior.
- Preserve existing run behavior.
- Preserve existing composite grouping behavior.

## Implementation Summary

- Added audio pipeline builder helpers.
- Added candidate generation for audio input test pipelines.
- Added candidate generation for audio output test pipelines.
- Added CLI support for audio pipeline candidate commands.
- Added JSON support.
- Added safe audio execution support.
- Added tests for candidate structure, CLI output, and execution behavior.
- Updated documentation and hardware validation guidance.
- Deferred loopback because it can create feedback or surprising routing behavior.

## Testing Plan

Tests cover:

- audio input candidate generation
- audio output candidate generation
- missing required GStreamer elements
- stable candidate IDs
- candidate reasons
- text CLI output
- JSON CLI output
- safe audio run and dry-run behavior
- existing video pipeline tests
- existing run tests
- existing grouping tests

Tests should not require live audio hardware. Use synthetic devices and environment facts.

## Acceptance Criteria

All completion criteria below are met for `v0.4.0`:

- The tool can generate at least one audio input test pipeline candidate.
- The tool can generate at least one audio output test pipeline candidate.
- Candidate output uses stable IDs.
- Candidate output includes required elements and reasons.
- Text and JSON output work.
- Existing video pipeline commands continue to work.
- Existing run commands continue to work.
- Existing group commands continue to work.
- Tests pass.
- Documentation includes audio pipeline examples.
- Hardware smoke tests work on Reachy Mini audio input and output.

## Hardware Smoke Tests

Use discovery first. On the Reachy Mini hardware validated so far, the ALSA input and output are `hw:0,0`; confirm that locally before running candidates.

```sh
/home/jim/.local/bin/uv run gst-device-explorer audio-inputs
/home/jim/.local/bin/uv run gst-device-explorer audio-outputs
/home/jim/.local/bin/uv run gst-device-explorer groups
```

Inspect the generated audio input candidate:

```sh
/home/jim/.local/bin/uv run gst-device-explorer pipeline audio-input hw:0,0
/home/jim/.local/bin/uv run gst-device-explorer pipeline audio-input hw:0,0 --json
```

Inspect the generated audio output candidate:

```sh
/home/jim/.local/bin/uv run gst-device-explorer pipeline audio-output hw:0,0
/home/jim/.local/bin/uv run gst-device-explorer pipeline audio-output hw:0,0 --json
```

Check the selected commands without starting GStreamer:

```sh
/home/jim/.local/bin/uv run gst-device-explorer run audio-input hw:0,0 --dry-run
/home/jim/.local/bin/uv run gst-device-explorer run audio-output hw:0,0 --dry-run
```

Run the audio tests:

```sh
/home/jim/.local/bin/uv run gst-device-explorer run audio-input hw:0,0
/home/jim/.local/bin/uv run gst-device-explorer run audio-output hw:0,0
```

Expected behavior:

- The audio input level test should run without audible output.
- The audio output sine test should produce a 440 Hz tone.
- Press Ctrl+C to stop a running audio pipeline.

Loopback remains deferred because it can create feedback or surprising routing behavior.

## Future Work

Potential future milestones:

- Audio loopback candidate generation
- PulseAudio and PipeWire discovery
- recording pipelines
- audio/video combined capture
- Reachy Mini conversation audio paths
- WebRTC integration
- ASR/TTS integration
- group-based pipeline generation
- profile system cleanup
