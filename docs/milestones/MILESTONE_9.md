# Milestone 9 — Bounded Capture Tests

Status: Implemented

## Theme

Generate short, controlled media samples.

## Goal

Add bounded capture commands that use generated, structured pipeline candidates to create short media files.

Milestone 9 should prove that a discovered endpoint can produce a usable file without turning `gst-device-explorer` into a general-purpose recording application.

The goal is a safe validation tool, not a capture framework.

## Why This Matters

By Milestone 8, `gst-device-explorer` can:

- discover audio and video endpoints
- generate structured pipeline candidates
- safely run selected bounded preview/test candidates
- explain candidate availability
- summarize endpoint profiles
- export whole-system reports
- recommend which existing candidate to try first

The next practical validation step is answering:

```text
Can this endpoint produce a short, usable media file?
```

A bounded capture command is useful for:

- hardware validation
- GitHub issue reproduction
- remote debugging
- comparing systems
- documenting known-good devices
- proving that a selected endpoint works beyond live preview
- collecting short samples for manual inspection

## Guiding Principles

Milestone 9 should continue the existing project principles:

- Probe first, build later.
- Normalize raw system output into structured models before making decisions.
- Treat pipeline candidates as structured objects, not just strings.
- Treat CLI, JSON, future GUI, and future agent integrations as renderers over shared core models.
- Prefer capability detection over hard-coded JetPack version checks.
- Avoid Reachy-specific behavior.
- Avoid arbitrary user-supplied pipeline execution.
- Keep grouping evidence-based and explainable.
- Keep each milestone narrow and testable.
- Use synthetic tests that do not require real hardware.

Milestone 9 should also follow these capture-specific principles:

- Capture must be explicitly requested.
- Capture must be bounded by duration.
- Capture must require an explicit output path.
- Capture must use generated candidates only.
- Capture must support `--dry-run`.
- Capture must not accept arbitrary raw pipelines.
- Capture must not create long-running recording behavior.
- Capture must not overwrite files unless explicit overwrite behavior is deliberately added and tested.
- Capture should remain endpoint-based, not group-based.
- Capture should prefer simple, inspectable file formats.

## Scope

Milestone 9 should add bounded capture tests for:

- video endpoint capture
- audio input endpoint capture

Audio output capture is not a natural first target because audio output is a sink/test endpoint, not a capture source.

Possible commands:

```sh
gst-device-explorer capture video /dev/video0 --duration 5 --output test.avi
gst-device-explorer capture video /dev/video0 --duration 5 --output test.avi --dry-run

gst-device-explorer capture audio-input hw:0,0 --duration 5 --output test.wav
gst-device-explorer capture audio-input hw:0,0 --duration 5 --output test.wav --dry-run
```

Optional, only if it fits the existing candidate-selection style cleanly:

```sh
gst-device-explorer capture video /dev/video0 --candidate <candidate-id> --duration 5 --output test.avi
gst-device-explorer capture video /dev/video0 --candidate 0 --duration 5 --output test.avi
```

Candidate selection should follow existing project conventions if already established for `run`.

## First Implementation Slice

The first implementation slice should be narrow.

Recommended first slice:

- Add structured capture candidate models for video and audio input, or extend existing candidate concepts only if that is cleaner.
- Add generated capture candidates for:
  - video to a short file
  - audio input to a short WAV file
- Add safe bounded execution using the existing subprocess execution approach.
- Add `--dry-run` support.
- Require `--duration`.
- Require `--output`.
- Add candidate selection by default, index, and/or candidate ID if consistent with existing `run` behavior.
- Add text output.
- Add JSON output only if the existing command pattern makes this small; otherwise defer JSON capture command output.
- Add synthetic tests for candidate generation, command construction, selection, safety, dry-run, and subprocess invocation.

The first slice should not attempt synchronized audio/video capture.

## Capture Candidate Contents

A capture candidate should be structured and inspectable.

It should include fields such as:

- candidate ID
- endpoint kind
- endpoint identifier
- description
- selected candidate profile label, if applicable
- container or file format
- expected output extension or media type
- duration
- output path
- GStreamer argv
- required elements
- warnings
- safety notes, if useful

The exact model should follow existing project conventions for `PipelineCandidate`.

## Candidate IDs

Capture candidate IDs should be stable and meaningful.

Examples:

```text
video-capture-generic-mp4
video-capture-jetson-mjpeg-mp4
audio-input-capture-wav
```

The exact names should follow the existing ID style in the repository.

## Output Files

Milestone 9 should require an explicit output path.

Example:

```sh
--output test.mp4
--output test.wav
```

Default output paths should be avoided in the first implementation. Explicit output makes the command safer and easier to reason about.

Overwrite behavior should be conservative.

Preferred first behavior:

- If the output file already exists, fail with a clear error.
- Defer `--overwrite` unless it is very small and well tested.

If `--overwrite` is added, it must be explicit and tested.

## Duration

Capture duration must be explicit and bounded.

Preferred first behavior:

- Require `--duration`.
- Accept a small positive number of seconds.
- Reject zero, negative, or invalid durations.
- Consider setting a reasonable maximum duration if that fits the existing project style.

The command should not create open-ended recording behavior.

## Execution Safety

Capture execution should follow existing safe execution rules:

- Build argv from structured candidates.
- Do not use `shell=True`.
- Do not accept arbitrary raw pipeline strings from the user.
- Clean up subprocesses on Ctrl+C.
- Use generated candidates only.
- Make dry-run output show the exact argv that would be executed.
- Keep file output explicit and bounded.

## Text Output Direction

Text output should make the action clear.

Dry run example:

```text
Capture candidate: video-capture-generic-mp4
Endpoint: /dev/video0
Duration: 5 seconds
Output: test.mp4

Dry run: command not executed.

gst-launch-1.0 ...
```

Execution example:

```text
Running capture candidate: video-capture-generic-mp4
Endpoint: /dev/video0
Duration: 5 seconds
Output: test.mp4

Capture completed.
```

Failure example:

```text
Capture not started.

Output file already exists:
test.mp4

Choose a different output path.
```

## JSON Direction

JSON output for capture inspection may be useful, but it should not expand the milestone unnecessarily.

Possible future command:

```sh
gst-device-explorer capture video /dev/video0 --duration 5 --output test.mp4 --dry-run --json
```

If JSON is implemented in the first slice, it should describe the selected generated candidate and argv, not execution logs.

Formal schema stability is deferred to a later schema milestone.

## Documentation

Update documentation to describe:

- capture commands
- required duration
- required output path
- dry-run behavior
- safe generated-candidate execution
- no arbitrary pipelines
- no long-running recording
- no synchronized audio/video capture
- no group-based capture
- no automatic overwrite, unless implemented explicitly

Likely documentation targets:

- `README.md`
- `docs/SETUP.md`
- `docs/milestones/MILESTONE_9.md`
- `docs/PIPELINE_CANDIDATES.md`, if capture candidates are added there

## Tests

Use synthetic tests.

Tests should verify:

- video capture candidates are generated from synthetic devices/capabilities
- audio input capture candidates are generated from synthetic devices
- candidate IDs are stable
- generated argv is structured and safe
- no `shell=True`
- dry-run does not invoke subprocess execution
- execution invokes the safe runner with generated argv
- duration is required
- invalid duration is rejected
- output path is required
- existing output file is rejected unless explicit overwrite behavior is implemented
- candidate selection follows existing conventions
- Ctrl+C cleanup behavior remains covered if existing runner tests can be reused
- CLI video capture works with mocked probes/builders
- CLI audio-input capture works with mocked probes/builders
- no arbitrary pipeline input is accepted
- existing device, group, profile, diagnostic, report, recommendation, and run behavior remains unchanged

Tests should not require:

- a real camera
- a real microphone
- a real speaker
- real GStreamer execution
- real ALSA hardware access
- Jetson-specific hardware
- Reachy Mini hardware

## Non-Goals

Milestone 9 should not add:

- long-running recording
- background recording
- streaming
- synchronized audio/video capture
- group-based capture
- group-based execution
- automatic endpoint selection from a group
- arbitrary user-supplied pipelines
- arbitrary transcoding workflows
- capture presets
- configuration files
- user preference files
- benchmark-based capture selection
- GUI behavior
- TUI behavior
- MCP or agent descriptor generation
- ASR
- TTS
- WebRTC
- PulseAudio support
- PipeWire support
- effects
- echo cancellation
- package installation
- system configuration changes
- Reachy-specific hard-coding
- JetPack-version-specific hard-coding

## Implemented First Slice

The implemented first slice adds:

- `capture video <device> --duration <seconds> --output <path> [--candidate <id-or-index>] [--dry-run]`
- `capture audio-input <device> --duration <seconds> --output <path> [--candidate <id-or-index>] [--dry-run]`
- video capture candidates using generated V4L2 caps and simple AVI output
- audio input capture candidates using generated ALSA/WAV output
- positive numeric duration validation
- explicit output path validation with existing-file rejection
- dry-run rendering that prints the selected candidate and command without execution
- safe argv execution through the shared execution helper, with a capture timeout guard
- synthetic tests for generation, validation, dry-run, selection, output safety, and execution boundaries

The implementation keeps capture endpoint-based. It does not add group capture,
audio output capture, arbitrary raw pipeline execution, synchronized audio/video
capture, or overwrite support.

## Deferred Work

Possible follow-on work after the first slice:

- `--overwrite`
- richer JSON dry-run output
- capture candidate summaries in `DeviceProfile`
- capture candidate summaries in `SystemReport`
- recommendation integration for capture candidates
- short video capture format alternatives
- short audio capture format alternatives
- capture presets
- group-level validation that includes capture checks
- synchronized audio/video capture
- report attachment workflow for GitHub issues
- GUI/TUI capture workflows
- agent-facing capture workflow descriptions

## Completion Criteria

Milestone 9 can be considered complete when:

- bounded video capture candidates exist
- bounded audio input capture candidates exist
- capture commands require explicit duration and output path
- capture commands support dry-run
- capture execution uses generated argv only
- capture execution does not use `shell=True`
- capture execution does not accept arbitrary raw pipelines
- existing candidate selection conventions are followed where applicable
- output file safety is handled
- documentation describes scope and non-goals
- synthetic tests cover candidate generation, command validation, dry-run, and execution boundaries
- the full test suite passes

## Validation Command

Run:

```sh
/home/jim/.local/bin/uv run python -m pytest
```

Expected final Codex report should include:

- files changed
- capture model or candidate behavior added
- video capture behavior added
- audio input capture behavior added
- CLI behavior added
- dry-run behavior
- output path safety behavior
- tests added
- test result
- deferred work
