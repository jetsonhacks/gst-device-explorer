# Milestone 38 — Safe Audio Output Test Implementation

Status: Implemented

## Theme

Implement the first safe audio-output hardware test in the GUI: a bounded speaker tone test for a selected audio output endpoint.

Milestone 37 established the audio test policy and UX direction. The key decision is to split audio output and audio input implementation. Audio output is implemented first because a short generated tone test is easier to scope, explain, and validate than microphone input activity monitoring. Audio input remains deferred to the next milestone.

The goal is not to build a mixer, media player, soundboard, routing tool, or arbitrary audio pipeline launcher. The goal is to give the user a small, explicit, bounded way to confirm that a selected speaker/audio-output endpoint can produce sound using a generated structured command.

## Product Intent

A user selecting an audio output endpoint should be able to:

- inspect the endpoint and its generated output/test pipeline,
- see that audio output testing is possible only for the selected endpoint,
- start a short bounded generated tone test deliberately,
- stop the test if needed,
- see clear state feedback while the test is starting, running, stopping, exited, failed, or unavailable,
- trust that the GUI will not change system audio settings, volume, mixer state, routes, or configuration.

## Design Context

Milestone 36 added safe camera preview with a GUI-facing runner/service seam. Milestone 38 should reuse that architectural lesson:

```text
Structured generated command data -> GUI-facing runner/service -> endpoint-specific controls
```

Qt widgets should not own raw subprocess logic. Widgets may own presentation, enabled/disabled state, and user-facing state text, but process lifecycle behavior belongs in a narrow runner/service layer.

If the existing camera `PreviewRunner` is general enough, it may be reused. If the camera naming is now misleading, the implementation may introduce a small generic media process runner or audio-test runner facade. Keep the change narrow and avoid a broad service-layer cleanup.

## Scope

### In Scope

1. Add safe audio output test controls to the Audio Output Explore page.
   - Controls should appear after the generated output pipeline/code-copy surface.
   - The generated command remains the persistent dry-run representation.
   - Controls should be visible only where an audio output endpoint has an eligible generated structured test command.
   - Controls should be unavailable, disabled, or replaced with clear explanatory text when a test command cannot be generated safely.

2. Implement a bounded generated tone test.
   - Use generated structured argv only.
   - Do not execute shell strings.
   - Do not derive execution argv from user-visible display text.
   - Prefer a short bounded duration.
   - Provide an explicit Stop affordance for cleanup even if the test is normally short.
   - Do not save audio, read from user files, or play arbitrary media.

3. Reuse or minimally generalize the existing runner/service seam.
   - The runner/service should accept structured command data, not raw shell strings.
   - It should expose state transitions suitable for GUI presentation.
   - It should own subprocess start/stop/cleanup behavior.
   - It should avoid `shell=True`.

4. Preserve the Milestone 37 state vocabulary.
   - `Idle`
   - `Ready`
   - `Starting`
   - `Running`
   - `Stopping`
   - `Exited`
   - `Failed`
   - `Unavailable`

5. Implement required cleanup.
   - Stop action
   - endpoint change
   - mode change
   - refresh
   - window/app close
   - partial start failure
   - unexpected process exit
   - endpoint unavailability

6. Add automated tests using fakes/test doubles.
   - Tests should not require real audio hardware.
   - Tests should not require GStreamer.
   - Tests should not play sound.
   - Tests should verify structured argv handling, state transitions, cleanup, and UI placement/availability.

7. Update documentation.
   - Mark Milestone 38 implemented when complete.
   - Update `docs/GUI_ROADMAP.md` if milestone names or ordering changed in Milestone 37.
   - Record tests run and HIL status.

## Out of Scope

Do not implement:

- microphone input activity testing,
- microphone recording,
- audio capture to file,
- speaker playback from arbitrary files,
- media player behavior,
- soundboard behavior,
- volume controls,
- mixer controls,
- audio route changes,
- ALSA configuration mutation,
- PulseAudio or PipeWire configuration mutation,
- system audio mutation,
- arbitrary pipeline editing,
- arbitrary user-authored pipeline execution,
- execution from shell strings,
- `shell=True`,
- synchronized audio/video behavior,
- group-based execution,
- Commands/Reproduce expansion,
- Reports area expansion,
- broad service-layer cleanup unrelated to the audio output test.

## Safety Boundaries

Preserve all existing safety boundaries:

- generated structured commands only,
- explicit user action,
- no arbitrary command execution,
- no hidden command execution,
- no shell-string execution,
- no package installation,
- no remote behavior,
- no system configuration changes,
- no volume/mixer/route mutation,
- no group-based execution.

The test may produce sound, so the UI should make that explicit before the user starts it. The application must not attempt to raise volume, change the default output device, change routes, or work around a quiet/muted system by mutating settings.

## Suggested UI Shape

On an Audio Output Explore page:

```text
Endpoint Summary

Audio Output Mode
Sample Format: ...
Sample Rate: ...
Channels: ...

Generated Output Pipeline
[read-only code/copy command surface]

Speaker Test
Status: Ready
[Start Test] [Stop]
Small note: Plays a short generated tone on this selected endpoint. Does not change volume, mixer, or system audio routing.
```

If unavailable:

```text
Speaker Test
Status: Unavailable
No safe generated speaker-test command is available for this endpoint/mode.
```

## Implementation Guidance

Likely files to inspect:

- `src/gst_device_explorer/gui/preview_runner.py`
- `src/gst_device_explorer/gui/qt_audio_output_explorer.py`
- `src/gst_device_explorer/gui/qt_explore.py`
- `src/gst_device_explorer/gui/qt_detail.py`
- `src/gst_device_explorer/gui/qt_main_window.py`
- audio pipeline/candidate builders used by the Audio Output Explore page
- existing preview runner tests
- existing audio output Explore tests

Potential implementation choices:

- Keep `PreviewRunner` if it is already a generic structured-argv process runner despite the name.
- Or introduce a narrow generic runner such as `MediaProcessRunner`, then adapt camera preview and audio output test to share it.
- Or keep camera preview unchanged and add a very small audio output runner facade using the same structured-process approach.

Choose the smallest design that avoids duplicating unsafe process logic and keeps Qt widgets from owning subprocess lifecycle details.

## Testing Expectations

Add or update tests that verify:

- audio output endpoint pages expose a speaker-test area only after the generated command surface,
- eligible audio output commands create structured argv test commands,
- the runner/service rejects or avoids shell strings,
- no `shell=True` behavior is introduced,
- Start delegates to the runner/service,
- Stop delegates cleanup to the runner/service,
- endpoint change cleans up a running test,
- refresh cleans up a running test,
- window/app close cleans up a running test,
- state text updates for starting/running/stopping/exited/failed/unavailable conditions,
- unavailable endpoints/modes do not expose an enabled Start action,
- camera preview tests from Milestone 36 still pass,
- audio input Explore remains non-executing,
- group views remain non-executing.

Suggested commands:

```sh
uv run python -m pytest tests/test_gui_preview_runner.py tests/test_gui_detail_pane.py tests/test_gui_shell.py
uv run python -m pytest tests/test_gui_model.py tests/test_gui_camera.py tests/test_gui_detail_pane.py tests/test_gui_shell.py
uv run python -m pytest
```

Adjust the exact test list to match the files changed.

## HIL Validation

Automated tests should not require hardware.

Hardware-in-the-loop validation may be performed separately on Jetson/Linux hardware with a known audio output endpoint. If HIL is not run, document that explicitly in the milestone implementation notes.

Suggested HIL checks:

- Select a known audio output endpoint.
- Confirm the generated output pipeline/code-copy surface appears first.
- Confirm Speaker Test controls appear after the generated command.
- Start a short tone test.
- Confirm the test exits or can be stopped.
- Confirm endpoint change or refresh cleans up the test.
- Confirm the application does not change volume, mixer, or route settings.

## Acceptance Criteria

Milestone 38 is complete when:

- Audio Output Explore includes a safe speaker-test area after the generated command surface.
- Speaker test execution uses generated structured argv for the selected endpoint only.
- Qt widgets do not own raw subprocess logic.
- Start/Stop behavior is explicit and stateful.
- Cleanup is performed for stop, endpoint change, mode change, refresh, close, failure, and unexpected exit.
- No audio input test, recording, file capture, mixer mutation, volume mutation, route mutation, arbitrary command execution, or group-based execution is added.
- Existing camera preview behavior remains intact.
- Existing audio input Explore behavior remains non-executing.
- Tests pass.
- Documentation records implementation notes, tests, HIL status, and deferred work.

## Implementation Notes

Implemented:

- Added a **Speaker Test** section to Audio Output Explore after the generated output pipeline/code-copy surface.
- The generated output pipeline remains the persistent dry-run representation.
- The generated speaker-test command is now bounded with `samplesperbuffer=2400` and `num-buffers=20`.
- The Speaker Test section shows state text, concise status text, **Start Test**, **Stop Test**, and a safety note that the test plays a short generated tone without changing volume, mixer, or system audio routing.
- Start Test is enabled only for an eligible audio-output detail with an enabled generated audio-output test action.
- Start Test delegates to the GUI-facing runner/service with structured argv via `PreviewCommand`.
- Stop Test delegates cleanup to the runner/service.
- No user-visible command text is parsed back into execution argv.
- The existing runner/service boundary from Milestone 36 is reused; no broad service-layer cleanup was introduced.
- Existing endpoint-change, refresh, and window-close cleanup paths now also cover the audio output speaker test because it uses the same runner/service owned by the main window.
- Audio Input Explore remains non-executing.
- Camera preview behavior remains intact.
- Group Explore remains a non-executing navigation dashboard.

Files changed:

- `src/gst_device_explorer/gui/qt_audio_output_test.py`
- `src/gst_device_explorer/gui/qt_audio_output_explorer.py`
- `src/gst_device_explorer/gui/qt_explore.py`
- `tests/test_gui_detail_pane.py`
- `tests/test_gui_shell.py`
- `docs/milestones/MILESTONE_38.md`
- `docs/GUI_ROADMAP.md`

Tests added or updated:

- Audio Output Explore accessible text includes Speaker Test after the generated pipeline surface.
- Audio output pipeline/code-copy surface remains read-only and copyable.
- Speaker Test Start delegates to the runner with structured argv.
- Speaker Test Stop delegates to runner cleanup.
- Speaker Test unavailable state disables Start when no eligible generated test command exists.
- Refresh cleanup covers a running audio output speaker test.
- Audio Input Explore does not gain Start/Stop execution controls.
- Existing camera preview, group, shell, and GUI model tests were rerun.

Tests run:

- `uv run python -m pytest tests/test_gui_preview_runner.py tests/test_gui_detail_pane.py tests/test_gui_shell.py`
- `uv run python -m pytest tests/test_gui_model.py tests/test_gui_camera.py tests/test_gui_detail_pane.py tests/test_gui_shell.py`
- `uv run python -m pytest`

HIL validation:

- Not run in this implementation pass. Automated tests use fakes/test doubles and do not require audio hardware, Jetson, GStreamer, or actual speaker playback.

No microphone/audio-input testing, microphone recording, audio capture-to-file, speaker playback from arbitrary files, media-player behavior, soundboard behavior, volume controls, mixer controls, route changes, ALSA/PulseAudio/PipeWire configuration mutation, system audio mutation, arbitrary pipeline editing, arbitrary command execution, shell-string execution, `shell=True`, synchronized audio/video behavior, group-based execution, Commands/Reproduce expansion, or Reports expansion was added.

## Deferred Work

- Safe audio input activity test implementation.
- Full hardware interface / HIL validation pass.
- Commands/Reproduce sections.
- Reports area.
- Broader service-layer cleanup, if needed after audio input and output tests are proven.
