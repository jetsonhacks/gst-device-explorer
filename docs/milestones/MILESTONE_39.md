# Milestone 39 — Safe Audio Input Activity Test Implementation

Status: Implemented

## Theme

Add the first bounded microphone/audio-input test to the GUI without turning `gst-device-explorer` into a recorder.

Milestone 37 defined the audio test policy. Milestone 38 implemented the safer first half of audio execution with a bounded speaker tone test for audio output endpoints. Milestone 39 implements the corresponding audio input side, but deliberately keeps the first version narrow: a **non-recording input activity test** for the selected audio input endpoint.

The goal is to confirm that an audio input endpoint can be opened and exercised by a generated GStreamer pipeline. The first implementation should not save audio, retain audio, stream audio, or present itself as a recording feature.

## Product Intent

When a user selects a microphone or audio-input endpoint, the Audio Input Explore tab should help answer:

- What audio input endpoint is selected?
- What generated input pipeline corresponds to the selected/default mode?
- Can the selected endpoint be opened by a bounded generated test pipeline?
- Is the test currently idle, starting, running, stopping, exited, failed, or unavailable?
- Can the user start and stop the test explicitly?
- Is it clear that the test does **not** record, save, or retain microphone audio?

This milestone should preserve the inspector-first pattern:

```text
Endpoint summary
Audio Input Mode
Generated input pipeline / code-copy surface
Audio Input Activity Test
```

The generated command remains the persistent dry-run representation. The test control appears only after the generated command/code-copy surface.

## Scope

Implement a safe, bounded, non-recording audio input activity test for audio input endpoints.

### In Scope

- Add an **Audio Input Activity Test** or similarly named section to the Audio Input Explore surface.
- Place the test section after the generated input pipeline/code-copy surface.
- Use generated structured argv for the selected audio input endpoint only.
- Delegate process start/stop/cleanup to the existing GUI-facing runner/service pattern introduced for camera preview and reused for audio output tests.
- Preserve structured command handling:
  - use structured argv / `PreviewCommand`-style data
  - do not start processes from shell strings
  - do not derive execution from user-editable text
- Use a bounded, non-recording GStreamer pipeline.
- Prefer a sink that does not write media to disk, such as `fakesink`.
- The first version may be an activity/open test rather than a graphical level meter.
- Show clear test state using the shared state vocabulary:
  - `Idle`
  - `Ready`
  - `Starting`
  - `Running`
  - `Stopping`
  - `Exited`
  - `Failed`
  - `Unavailable`
- Provide explicit **Start Test** and **Stop Test** controls.
- Clearly state in the UI that the test does not record, save, or retain microphone audio.
- Stop/cleanup on:
  - Stop button
  - endpoint change
  - mode change
  - refresh
  - application/window close
  - partial start failure
  - unexpected process exit
  - endpoint unavailability
- Add tests using fakes/test doubles so automated tests do not require a microphone, display, GStreamer, Jetson, or real audio hardware.
- Update `docs/GUI_ROADMAP.md` to mark Milestone 39 as implemented when complete and keep future ordering consistent.

### Possible Generated Pipeline Shape

The exact pipeline should follow the project’s existing command-generation style. The intent is:

```text
alsasrc device=<selected-device> !
audio/x-raw,<selected-mode-caps-if-exact-and-safe> !
fakesink sync=false
```

If a bounded buffer count or duration can be expressed safely and consistently, use it. If the existing runner controls lifetime more reliably, keep the pipeline simple and rely on explicit Stop/cleanup. Avoid a long-running hidden process.

If using a GStreamer `level` element is straightforward and testable without expanding process/bus parsing infrastructure too much, it may be included as a future-friendly element in the generated pipeline. However, a graphical level meter is not required for this milestone.

## Out of Scope

Do not implement:

- audio recording
- file capture
- saving microphone audio
- retaining microphone samples
- streaming microphone audio
- arbitrary file output paths
- graphical waveform display
- full graphical level meter, unless it falls out trivially without new bus-parsing architecture
- audio input device configuration changes
- ALSA mixer mutation
- PulseAudio or PipeWire mutation
- system route changes
- gain or volume changes
- arbitrary GStreamer pipeline editing
- arbitrary user-authored pipeline execution
- shell-string execution
- `shell=True`
- synchronized audio/video capture
- group-based execution
- Commands/Reproduce expansion
- Reports expansion

## Safety Boundaries

Preserve all existing safety boundaries:

- generated structured commands only
- selected endpoint only
- explicit user action only
- no hidden command execution
- no arbitrary pipeline execution
- no user-authored pipeline execution
- no shell strings
- no `shell=True`
- no recording or retained audio
- no file capture
- no system audio mutation
- no mixer, gain, volume, or routing mutation
- no group-based execution
- no synchronized audio/video behavior
- no package installation
- no remote behavior

The UI must clearly communicate that the audio input test is an activity/open test, not a recording tool.

## Design Notes

### Why not a recorder?

A recorder changes the product meaning and introduces privacy, file-management, and retention questions. This milestone should avoid those. The safe first step is to prove that the selected microphone endpoint can be opened by a generated pipeline and stopped cleanly.

### Why not require a level meter yet?

A true level meter usually requires reading and interpreting GStreamer bus messages, especially from the `level` element. That may be useful later, but it is not required to validate the first safe audio input hardware interaction.

### Why reuse the existing runner/service seam?

Milestone 36 introduced the process-runner seam for camera preview. Milestone 38 reused that pattern for speaker testing. Milestone 39 should continue using that architecture unless a very small extension is needed. Qt widgets should not own raw subprocess logic.

### Suggested UI Shape

```text
[Generated Input Pipeline]
gst-launch-1.0 alsasrc ... ! fakesink sync=false
[Copy]

[Audio Input Activity Test]
This test opens the selected microphone with a generated pipeline.
It does not record, save, or retain microphone audio.

Status: Ready

[Start Test] [Stop Test]
```

The exact labels may be adjusted to match existing GUI naming, but the safety message should remain clear.

## Implementation Guidance

Likely files to inspect or modify:

- `src/gst_device_explorer/gui/qt_audio_input_explorer.py`
- `src/gst_device_explorer/gui/qt_explore.py`
- existing runner/service code introduced in Milestone 36
- audio output test widget/module introduced in Milestone 38
- GUI shell/detail tests
- audio input Explore tests
- `docs/milestones/MILESTONE_39.md`
- `docs/GUI_ROADMAP.md`

Prefer creating a focused module if needed, such as:

```text
src/gst_device_explorer/gui/qt_audio_input_test.py
```

Do not let `qt_explore.py` or the audio input explorer become a process-management file.

## Suggested Tests

Add or update tests that verify:

- Audio Input Explore includes an Audio Input Activity Test section.
- The test section appears after the generated input pipeline/code-copy surface.
- The test section clearly states that microphone audio is not recorded, saved, or retained.
- Start Test is available only when an eligible generated input command exists.
- Stop Test delegates to the runner cleanup path.
- The test uses structured argv / command data, not shell strings.
- The test does not expose arbitrary pipeline editing.
- The test does not expose file output path controls.
- Endpoint change, refresh, and window close trigger cleanup.
- Existing camera preview behavior remains intact.
- Existing audio output speaker test behavior remains intact.
- Group views still do not expose group-based execution.

Suggested commands:

```sh
uv run python -m pytest tests/test_gui_preview_runner.py tests/test_gui_detail_pane.py tests/test_gui_shell.py
uv run python -m pytest tests/test_gui_model.py tests/test_gui_camera.py tests/test_gui_detail_pane.py tests/test_gui_shell.py
uv run python -m pytest
```

Adjust the exact test list based on the implementation.

## HIL Validation Notes

Automated tests should not require audio hardware.

If hardware-in-the-loop validation is performed, record:

- platform
- audio input endpoint
- generated command shown in GUI
- observed Start/Stop behavior
- whether the test opens the endpoint successfully
- whether cleanup occurs on Stop and close
- confirmation that no file is produced
- confirmation that no system mixer/route/volume setting is changed

HIL validation is useful but not required for automated completion if test doubles cover the state and cleanup behavior.

## Acceptance Criteria

Milestone 39 is complete when:

- Audio Input Explore includes a safe audio input activity test section.
- The test section appears after the generated input pipeline/code-copy surface.
- The test uses generated structured argv for the selected audio input endpoint only.
- The test delegates process handling to the existing GUI runner/service seam.
- The UI clearly states that no microphone audio is recorded, saved, or retained.
- Start/Stop state behavior is visible and tested.
- Cleanup is triggered on Stop, endpoint/mode change, refresh, close, partial start failure, unexpected exit, and endpoint unavailability where practical.
- No recording, file capture, system audio mutation, arbitrary command execution, shell-string execution, or group-based execution is added.
- Existing camera preview and audio output speaker test behavior remains intact.
- Relevant tests pass.
- `docs/GUI_ROADMAP.md` is updated.

## Deferred Work

- graphical audio level meter
- audio input capture-to-file workflow
- waveform display
- microphone gain controls
- audio diagnostics/report surfacing
- Commands/Reproduce sections
- Reports area
- broader HIL validation pass

## Implementation Notes

Implemented in this milestone:

- Added an Audio Input Activity Test section after the generated input pipeline/code-copy surface.
- Reused the existing GUI-facing `PreviewRunner` / `PreviewCommand` structured-argv seam.
- Generated a bounded non-recording input activity command for the selected endpoint:
  - `gst-launch-1.0`
  - `alsasrc device=<selected-endpoint> num-buffers=20`
  - exact safe `audio/x-raw` caps when known
  - `audioconvert ! audioresample ! level interval=1000000000 ! fakesink sync=false`
- Added Start Test and Stop Test controls with `Ready`, `Running`, `Exited`, `Failed`, and `Unavailable` state text.
- Added UI text stating that the test opens the selected microphone with a generated pipeline and does not record, save, or retain microphone audio.
- Kept cleanup delegated through the runner path already used for endpoint changes, refresh, and window close.

Files changed:

- `src/gst_device_explorer/gui/qt_audio_input_test.py`
- `src/gst_device_explorer/gui/qt_audio_input_explorer.py`
- `src/gst_device_explorer/gui/qt_explore.py`
- `tests/test_gui_detail_pane.py`
- `docs/milestones/MILESTONE_39.md`
- `docs/GUI_ROADMAP.md`

Tests added or updated:

- Audio Input Explore accessible text now covers the activity test section and non-recording safety text.
- Audio input pipeline widget tests now assert the bounded `fakesink sync=false` command and visible Start/Stop controls.
- Added a fake-runner test proving Start Test delegates a structured argv command for the selected endpoint.
- Added a fake-runner Stop Test assertion.
- Added an unavailable-state test for audio input endpoints without an eligible generated activity command.
- Existing camera preview, audio output speaker test, group Explore, and GUI shell cleanup tests were included in the focused run.

Tests run:

```sh
uv run python -m pytest tests/test_gui_preview_runner.py tests/test_gui_detail_pane.py tests/test_gui_shell.py
uv run python -m pytest tests/test_gui_model.py tests/test_gui_camera.py tests/test_gui_detail_pane.py tests/test_gui_shell.py
uv run python -m pytest
```

Results:

- `63 passed`
- `78 passed`
- `605 passed`

HIL status:

- Hardware-in-the-loop validation was not run.

Safety confirmation:

- No microphone recording was added.
- No microphone audio is saved, retained, or written to disk.
- No capture-to-file workflow or arbitrary output path was added.
- No arbitrary pipeline editing or arbitrary user-authored pipeline execution was added.
- No shell-string execution or `shell=True` path was added.
- No ALSA mixer, PulseAudio, PipeWire, gain, volume, route, or system audio mutation was added.
- No synchronized audio/video behavior, group-based execution, Commands/Reproduce expansion, or Reports expansion was added.
