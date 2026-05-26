# Milestone 40 — Hardware Interface / HIL Validation Pass

Status: Implemented

## Theme

Validate that the GUI hardware interaction surfaces are actually driven by the selected hardware endpoints, not placeholder or test data, and verify the camera/audio hardware interfaces with real hardware-in-the-loop testing.

Milestone 40 should be treated as a sliced validation milestone. A small initial documentation slice recorded that the first validation environment had no visible camera or ALSA endpoints. That slice did not complete the milestone. The milestone remains open until the generated commands and hardware controls are validated against real visible devices.

The important question is:

```text
Do the GUI-generated commands and Start/Stop hardware interactions work for the selected real endpoint?
```

This milestone should not be used to add broad new features. It should validate the existing hardware interface work from Milestones 36, 38, and 39, and apply narrow fixes when validation exposes integration problems.

## Current Concern

During review, the generated GStreamer commands shown in the GUI appeared to be test data or generic placeholder data rather than data derived specifically from the currently selected hardware endpoint and mode.

This must be investigated and corrected before the project moves on to Commands/Reproduce, Reports, or broader presentation work.

The validation focus is therefore twofold:

1. **Command provenance**
   - The command displayed in Explore must be derived from the selected endpoint and selected/default mode.
   - The command passed to the runner must match the structured generated command for that endpoint.
   - The GUI must not use stale test fixtures, demo data, hard-coded placeholders, or display strings as execution input.

2. **Hardware interaction**
   - Camera Preview, Speaker Test, and Audio Input Activity Test must be validated on real hardware where endpoints are visible.
   - A HIL environment is available for testing.
   - Blocked validation is not completion.

## Prior Slice

### Slice 1 — Environment Record

Completed:

- Recorded a validation attempt on host `jetsonhacks`.
- Recorded kernel/system and GStreamer version.
- Confirmed no `/dev/video*` endpoints were visible.
- Confirmed `aplay -l` and `arecord -l` reported no soundcards.
- Ran automated tests.
- Applied no code fixes.

Outcome:

The validation procedure was recorded, but real endpoint validation was blocked. This slice does not complete Milestone 40.

## Slice 2 — Generated Command Provenance Audit

### Goal

Verify and, if necessary, fix how GUI Explore pages obtain generated commands for camera preview, audio output speaker test, and audio input activity test.

### Required checks

For each endpoint type:

- Camera Explore
- Audio Output Explore
- Audio Input Explore

Verify:

- The displayed generated command is derived from the selected endpoint.
- The selected/default mode influences the generated command where applicable.
- The command copied from the GUI matches the generated command shown to the user.
- The command passed to the runner is structured argv, not a shell string.
- The command passed to the runner is generated from the same selected endpoint/mode source as the display command.
- The command is not test fixture data.
- The command is not a stale value from a previous selected endpoint.
- The command is not a hard-coded placeholder.
- The command is not parsed back from user-visible text.

### Expected implementation behavior

The correct data flow should be conceptually:

```text
selected endpoint + selected/default mode
    -> structured candidate / generated command model
    -> displayed read-only code/copy surface
    -> PreviewCommand argv for runner
```

The incorrect data flows to eliminate are:

```text
test fixture / demo string -> GUI display -> runner
hard-coded placeholder -> GUI display -> runner
previous endpoint command -> current endpoint runner
display text -> parsed argv -> runner
shell string -> runner
```

### Scope

In scope:

- Audit generated command construction paths.
- Add or refine tests that prove commands are derived from selected endpoint data.
- Fix stale, placeholder, or fixture-derived command behavior.
- Fix mismatches between displayed command and runner command.
- Add explicit object names or test hooks only where needed for stable GUI tests.
- Keep fixes narrow and integration-focused.

Out of scope:

- New command catalog work.
- Reports UI.
- Arbitrary pipeline editing.
- Arbitrary pipeline execution.
- User-authored pipelines.
- New capture/recording workflows.
- Full service-layer rewrite.
- Broad GUI redesign.
- New device-specific hard-coding.

## Slice 3 — Real HIL Validation

### Goal

Run the GUI against real visible camera/audio endpoints and verify the hardware interaction loop.

A HIL environment is available for testing. Use it. If a required endpoint is not visible, record that as blocked for that endpoint only and continue validating any available endpoint categories.

### Camera validation

Preconditions:

- At least one `/dev/video*` endpoint is visible.
- The endpoint appears in the GUI.
- The camera Explore page shows the selected endpoint and generated pipeline.

Checks:

- The generated camera command references the selected camera endpoint.
- Changing camera mode changes the generated command when mode differences require it.
- Start Preview launches the generated structured command for the selected endpoint.
- Stop Preview stops the process and cleans up.
- Endpoint change stops or invalidates preview safely.
- Refresh stops or invalidates preview safely.
- Window/app close stops preview safely.
- Failure or unavailable states are understandable.

### Audio output validation

Preconditions:

- `aplay -l` shows at least one playback endpoint.
- The audio output endpoint appears in the GUI.
- The Audio Output Explore page shows the selected endpoint and generated output/test pipeline.

Checks:

- The generated output command references the selected output endpoint.
- The command is bounded.
- Start Test launches the generated structured command for the selected endpoint.
- The speaker test plays only a short generated tone.
- Stop Test stops and cleans up.
- Endpoint change, refresh, and close clean up safely.
- The test does not mutate volume, mixer, route, PulseAudio, PipeWire, or ALSA configuration.

### Audio input validation

Preconditions:

- `arecord -l` shows at least one capture endpoint.
- The audio input endpoint appears in the GUI.
- The Audio Input Explore page shows the selected endpoint and generated input/activity pipeline.

Checks:

- The generated input command references the selected capture endpoint.
- The command is bounded and non-recording.
- Start Test launches the generated structured command for the selected endpoint.
- The activity test does not save, retain, or expose microphone samples.
- Stop Test stops and cleans up.
- Endpoint change, refresh, and close clean up safely.
- The test does not mutate mixer, route, PulseAudio, PipeWire, or ALSA configuration.

## Slice 4 — Validation Record and Narrow Fixes

### Goal

Record HIL findings and apply only the narrow fixes needed to make the current hardware interfaces truthful and safe.

The milestone may include bug fixes if HIL reveals:

- generated command uses stale/test/placeholder data
- displayed command and runner command differ
- selected endpoint is not represented in the command
- Start/Stop state does not match process state
- cleanup is incomplete
- unavailable/failure state is unclear
- bounded audio tests are not actually bounded
- UI enables a test when no eligible command exists

The milestone should not expand the product surface beyond the existing camera preview, speaker test, and audio input activity test.

## Safety Boundaries

Preserve all existing safety boundaries:

- No arbitrary pipeline execution.
- No arbitrary user-authored pipeline scripts.
- No shell-string execution.
- No `shell=True`.
- No hidden command execution.
- No package installation.
- No system configuration changes.
- No remote behavior.
- No group-based execution.
- No synchronized audio/video behavior.
- No video recording/capture workflow.
- No microphone recording.
- No file capture.
- No retained microphone samples.
- No arbitrary file playback.
- No V4L2 writes.
- No `v4l2-ctl --set-ctrl`.
- No ALSA/PulseAudio/PipeWire configuration mutation.
- No mixer, volume, or route mutation.
- No Commands/Reproduce expansion.
- No Reports expansion.

## Suggested Files to Inspect

Likely source files:

- `src/gst_device_explorer/gui/preview_runner.py`
- `src/gst_device_explorer/gui/qt_camera_preview.py`
- `src/gst_device_explorer/gui/qt_camera_explorer.py`
- `src/gst_device_explorer/gui/qt_camera_modes.py`
- `src/gst_device_explorer/gui/qt_audio_output_test.py`
- `src/gst_device_explorer/gui/qt_audio_output_explorer.py`
- `src/gst_device_explorer/gui/qt_audio_input_test.py`
- `src/gst_device_explorer/gui/qt_audio_input_explorer.py`
- `src/gst_device_explorer/gui/qt_explore.py`
- `src/gst_device_explorer/gui/qt_detail.py`
- `src/gst_device_explorer/gui/qt_main_window.py`
- GUI model/builders/adapters involved in selected endpoint data.

Likely tests:

- `tests/test_gui_preview_runner.py`
- `tests/test_gui_detail_pane.py`
- `tests/test_gui_shell.py`
- `tests/test_gui_camera.py`
- any audio GUI tests already present in the repository.

## Suggested Automated Tests

Add or refine tests that prove:

- Camera generated command uses the selected camera endpoint path.
- Audio output generated command uses the selected playback endpoint identifier.
- Audio input generated command uses the selected capture endpoint identifier.
- Runner command argv matches the generated command source for the selected endpoint.
- Switching endpoints does not leave stale commands behind.
- Test/preview controls are disabled or unavailable when no eligible command exists.
- Copy surface and runner source remain consistent.
- Start/Stop state remains consistent with fake runner transitions.

Suggested commands:

```sh
uv run python -m pytest tests/test_gui_preview_runner.py tests/test_gui_detail_pane.py tests/test_gui_shell.py
uv run python -m pytest tests/test_gui_model.py tests/test_gui_camera.py tests/test_gui_detail_pane.py tests/test_gui_shell.py
uv run python -m pytest
```

## Suggested HIL Commands / Observations

Before launching the GUI, record:

```sh
uname -a
gst-launch-1.0 --version
ls -l /dev/video* || true
v4l2-ctl --list-devices || true
aplay -l || true
arecord -l || true
gst-device-explorer devices || true
gst-device-explorer groups || true
```

During GUI validation, record:

- visible endpoints
- selected endpoint IDs
- generated commands shown in Explore
- whether commands include the selected endpoint identifiers
- Start/Stop behavior
- cleanup behavior
- failure/unavailable messages
- any discrepancies between displayed command and hardware behavior

Do not record microphone audio. Do not save media files unless a later milestone explicitly scopes capture.

## Acceptance Criteria

Milestone 40 is complete only when:

- The generated command provenance audit is complete.
- Camera command provenance is verified or corrected.
- Audio output command provenance is verified or corrected.
- Audio input command provenance is verified or corrected.
- Automated tests cover selected-endpoint-derived command behavior.
- HIL validation is run for every endpoint category available in the HIL environment.
- Blocked endpoint categories are explicitly recorded with the reason they were blocked.
- Any narrow fixes required by validation are implemented and documented.
- The milestone document records actual HIL results, not only the test environment.
- Existing automated tests pass.
- Safety boundaries remain intact.
- Commands/Reproduce and Reports remain deferred.

## Completion Notes

Slice 2 through Slice 4 are complete.

Command provenance findings:

- Camera Explore was endpoint-derived but had two provenance bugs:
  - the selected/default mode could disagree with the generated command
  - MJPG preview used an invalid generic display/runner command on the HIL camera
- Camera Explore now derives the displayed command and runner argv from the selected endpoint, selected/default mode, and available candidate evidence.
- Audio Output Explore display text and runner argv already shared the same selected-endpoint structured argv helper.
- Audio Input Explore display text and runner argv already shared the same selected-endpoint structured argv helper.
- No runner command is parsed from display text or passed as a shell string.

HIL hardware used:

- Host: `jetsonhacks`
- Kernel/system: `Linux jetsonhacks 6.8.12-tegra #1 SMP PREEMPT Tue Dec 30 15:40:41 PST 2025 aarch64`
- GStreamer: `gst-launch-1.0 1.24.2`
- Camera endpoint validated: `/dev/video0`
- Audio output endpoint validated: `hw:0,0`
- Audio input endpoint validated: `hw:0,0`
- Composite groups visible: `Reachy Mini Audio`, `Reachy Mini Camera`, `HD Pro Webcam C920`, `Reachy Mini`

Fixes applied:

- Camera GUI selected-mode provenance was corrected.
- Camera GUI MJPG preview now uses the available Jetson MJPEG candidate path when advertised.
- Generic MJPG command generation now includes `jpegparse ! jpegdec`.
- Generic MJPG diagnostics now require `jpegparse` and `jpegdec`.
- Jetson MJPG candidates are no longer suppressed when generic `jpegdec` is missing.
- Tests were updated for the corrected command shapes and candidate provenance.

Tests run:

```sh
uv run python -m pytest tests/test_gui_camera.py tests/test_gui_detail_pane.py tests/test_pipelines.py tests/test_video_diagnostics.py
```

Result: `75 passed`.

Full suite result recorded in `docs/milestones/MILESTONE_40.md`: `606 passed`.

Safety confirmation:

- No arbitrary command execution, shell-string execution, `shell=True`, recording, file capture, retained microphone samples, V4L2 writes, mixer/volume/route mutation, group-based execution, Commands/Reproduce expansion, or Reports expansion was added.

Deferred work:

- Commands/Reproduce sections.
- Reports area.
- Richer microphone level visualization.
- Capture-to-file workflows.
- Synchronized audio/video workflows.
- Broader service-layer cleanup.
