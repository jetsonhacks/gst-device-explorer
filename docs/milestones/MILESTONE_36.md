# Milestone 36 — Safe Camera Preview Implementation

Status: Implemented

## Theme

Implement the first GUI hardware interaction: safe camera preview from a structured, generated camera preview candidate.

Milestone 35 intentionally defined preview policy before implementation. Milestone 36 applies that policy narrowly to camera preview only. The goal is not to create a general pipeline runner, recording system, capture workflow, or multimedia test framework. The goal is to allow the user to start and stop a selected generated camera preview pipeline from the Camera Explore pane while preserving the inspector-first GUI model and all safety boundaries.

The guiding product rule remains:

```text
Inspect first.
Generate safe commands from structured selections.
Only then allow explicitly scoped hardware interaction.
```

## Product Intent

A user selecting a camera endpoint should be able to:

- inspect the camera endpoint and selected camera mode
- see the generated GStreamer preview command before any execution control appears
- understand that preview uses the generated command for the selected endpoint/mode
- start a preview explicitly
- stop the preview explicitly
- see clear preview state feedback
- trust that preview cleanup happens on stop, endpoint change, window close, partial start failure, and unexpected process exit

This milestone should make the smallest useful preview interaction real without expanding the execution surface.

## Policy Inherited from Milestone 35

Milestone 36 must implement the Milestone 35 policy decisions:

- Preview eligibility is limited to structured, generated camera preview candidates for the selected endpoint/mode.
- The existing generated pipeline/code-copy surface is the persistent dry-run representation.
- Preview controls appear only after the generated command is visible.
- Process states are:
  - `Idle`
  - `Ready`
  - `Starting`
  - `Running`
  - `Stopping`
  - `Exited`
  - `Failed`
  - `Unavailable`
- Cleanup is required on:
  - explicit Stop
  - endpoint change
  - app/window close
  - partial start failure
  - unexpected process exit
- Qt widgets must not own raw subprocess logic.
- A small GUI-facing preview runner/service should accept structured argv/command data, not shell strings.

## Scope

Implement safe camera preview in two slices.

## Slice 1 — Preview Runner / Service

### Goal

Create the smallest GUI-facing process runner needed for camera preview, without embedding raw subprocess management directly in Qt widgets.

### Required behavior

The runner/service should:

- accept structured command data, preferably `list[str]` argv or an existing structured pipeline candidate object
- reject or avoid shell-string execution
- never use `shell=True`
- expose a simple state model compatible with the Milestone 35 states
- support `start()`
- support `stop()`
- clean up subprocesses predictably
- detect normal process exit
- detect failed start
- expose useful failure text when start fails
- remain independent enough to test without real camera hardware
- be small and focused

### Suggested implementation shape

The exact names may vary, but the implementation should introduce a small GUI-facing component such as:

```text
src/gst_device_explorer/gui/preview_runner.py
```

Possible class names:

```text
PreviewRunner
CameraPreviewRunner
GuiPreviewRunner
```

Possible supporting enum/value object:

```text
PreviewState
PreviewCommand
```

The runner may use Qt process infrastructure if that fits the existing GUI architecture, for example `QProcess`, or a carefully managed Python subprocess abstraction if that is already the project norm. The important boundary is that widgets should interact with a small runner/service API rather than own low-level process details.

### Tests

Add tests that validate runner behavior without requiring a real camera:

- runner starts from structured argv
- runner does not accept or run arbitrary shell strings
- stop transitions toward cleanup
- failed start produces `Failed` state or equivalent
- normal process exit produces `Exited` state or equivalent
- no `shell=True` path is introduced

Tests may use harmless commands such as the Python executable with short sleep/exit behavior, if consistent with the project test style. Avoid tests that require GStreamer, camera hardware, display hardware, or a Jetson.

## Slice 2 — Camera Explore Integration

### Goal

Add preview controls to the Camera Explore pane using the runner/service from Slice 1.

### Required behavior

The Camera Explore pane should:

- continue to show endpoint summary and Camera Mode selection
- continue to show the generated pipeline/code-copy surface
- add preview controls only after the generated pipeline surface
- enable preview only for eligible generated camera preview candidates
- provide clear Start Preview / Stop Preview behavior
- show current preview state
- avoid offering preview for unavailable candidates
- stop preview on endpoint change
- stop preview on window/app close where practical
- clean up if the preview process exits unexpectedly
- preserve existing copy behavior and camera-control inspector behavior

### Suggested UI shape

```text
Endpoint Summary

Camera Mode
Pixel Format | Image Size | Frame Rate

Generated Pipeline
[ read-only command/code/copy surface ]

Preview
State: Ready
[Start Preview]
```

When running:

```text
Preview
State: Running
[Stop Preview]
```

When unavailable:

```text
Preview
State: Unavailable
Preview is unavailable for this generated candidate.
```

### Preview eligibility

Preview should be eligible only when the selected camera mode produces a structured generated preview candidate that is expected to be safe to run.

The GUI should not:

- accept a user-edited command
- run arbitrary pasted pipeline text
- synthesize shell strings from display-only text
- run group-level commands
- infer preview behavior from raw report text

### Tests

Add or update GUI tests to verify:

- preview controls appear after the generated pipeline surface
- preview controls are present for eligible camera preview candidates
- preview controls are disabled or unavailable when no eligible preview candidate exists
- Start Preview delegates to the preview runner/service using structured command data
- Stop Preview delegates cleanup to the preview runner/service
- endpoint change triggers preview cleanup
- existing Camera Explore labels and code/copy behavior remain intact
- audio input/output Explore pages do not gain execution controls
- group Explore pages do not gain execution controls

Use test doubles or fakes for the runner where practical. Automated GUI tests should not require hardware preview.

## Out of Scope

Do not implement:

- arbitrary pipeline editing
- arbitrary command execution
- arbitrary user-authored pipeline scripts
- audio input testing
- audio output testing
- speaker playback
- microphone capture
- recording or file capture
- screenshots or image capture
- synchronized audio/video behavior
- group-based execution
- V4L2 control writes
- `v4l2-ctl --set-ctrl`
- mixer, volume, route, PulseAudio, PipeWire, or ALSA mutation
- package installation
- system configuration changes
- remote behavior
- Commands/Reproduce expansion
- Reports/Diagnostics area expansion

## Safety Boundaries

Milestone 36 must preserve these boundaries:

- generated camera preview candidates only
- structured command data only
- no shell-string execution
- no `shell=True`
- explicit user action required to start preview
- visible generated command before preview controls
- clear stop behavior
- cleanup on stop and lifecycle changes
- endpoint-specific preview only
- no group-level preview
- no audio behavior

## Implementation Guidance

Prefer small, focused changes.

Likely files to inspect or modify:

- `src/gst_device_explorer/gui/qt_camera_explorer.py`
- `src/gst_device_explorer/gui/qt_explore.py`
- `src/gst_device_explorer/gui/qt_detail.py`
- `src/gst_device_explorer/gui/builders.py`
- existing pipeline candidate/model code
- existing safe CLI runner code, if any can inform the design
- `tests/test_gui_camera.py`
- `tests/test_gui_detail_pane.py`
- `tests/test_gui_shell.py`

Possible new files:

- `src/gst_device_explorer/gui/preview_runner.py`
- `tests/test_gui_preview_runner.py`

Keep modules within the existing roadmap maintainability guidance. If a file is already near the 250–300 line target or approaching the 400-line review threshold, prefer a small focused module rather than adding unrelated responsibilities.

## Hardware-in-the-Loop Validation

Automated tests should not require real hardware.

After implementation, perform a HIL smoke test on a Jetson or Linux system with a camera where practical:

```sh
uv run gst-device-explorer gui
```

Manual validation checklist:

- select a camera endpoint
- choose a known-good camera mode
- confirm generated pipeline appears before preview controls
- click Start Preview
- confirm a preview window appears or the configured preview sink starts
- click Stop Preview
- confirm the preview process exits cleanly
- start preview again
- change endpoint or close the GUI
- confirm cleanup happens
- confirm no audio tests or group execution controls appear

Document HIL results in this milestone file when complete.

## Acceptance Criteria

Milestone 36 is complete when:

- a small GUI-facing preview runner/service exists
- the runner accepts structured argv/command data rather than shell strings
- no `shell=True` preview path exists
- runner state transitions are testable
- Camera Explore shows preview controls after the generated pipeline surface
- preview is limited to eligible generated camera preview candidates
- Start Preview and Stop Preview work through the runner/service
- preview cleanup occurs on Stop and lifecycle changes where practical
- existing camera inspector behavior remains intact
- audio input/output Explore pages remain read-only inspector surfaces
- group views remain read-only navigation/evidence surfaces
- automated tests cover runner behavior and GUI integration without requiring real hardware
- HIL validation notes are added when available
- documentation is updated
- Commands/Reproduce and Reports remain deferred

## Suggested Test Commands

Adjust based on the final test names and project organization:

```sh
uv run python -m pytest tests/test_gui_preview_runner.py
uv run python -m pytest tests/test_gui_camera.py tests/test_gui_detail_pane.py tests/test_gui_shell.py
uv run python -m pytest tests/test_gui_model.py tests/test_gui_camera.py tests/test_gui_detail_pane.py tests/test_gui_shell.py
uv run python -m pytest
```

## Documentation Updates

When implemented:

- mark this milestone as `Implemented`
- record files changed
- record behavior implemented
- record tests added/updated
- record tests run and results
- record HIL validation results, or explicitly state if HIL validation was not run
- confirm that no audio execution, arbitrary command execution, V4L2 writes, mixer mutation, system audio mutation, or group-based execution was added

## Implementation Notes

Implemented:

- Added a small GUI-facing preview runner/service:
  - `PreviewState`
  - `PreviewCommand`
  - `PreviewRunner`
- The runner accepts structured argv data through `PreviewCommand`.
- Shell-string preview commands are rejected.
- The runner starts preview through argv form only and does not use `shell=True`.
- The runner supports start, poll, stop, cleanup, normal exit detection, failed exit detection, failed start state, and terminate/kill cleanup.
- Added structured camera preview argv generation for selected camera modes without parsing the visible command text.
- Added a compact **Preview** section to Camera Explore after the generated pipeline/code-copy surface and before camera controls.
- Preview controls show state, concise status text, **Start Preview**, and **Stop Preview**.
- Preview controls are enabled only when the camera detail has an eligible generated preview action and a structured command can be produced for the selected mode.
- Start Preview delegates to the preview runner with a `PreviewCommand`.
- Stop Preview delegates cleanup to the preview runner.
- Detail pane rendering cleans up preview when the selected endpoint changes.
- Main window refresh and close paths clean up the preview runner.
- Existing camera generated-pipeline copy behavior and camera-control inspector behavior were preserved.
- Audio input/output Explore pages remain read-only inspector surfaces.
- Group Explore remains a read-only navigation dashboard.

Files changed:

- `src/gst_device_explorer/gui/preview_runner.py`
- `src/gst_device_explorer/gui/qt_camera_preview.py`
- `src/gst_device_explorer/gui/qt_camera_explorer.py`
- `src/gst_device_explorer/gui/qt_camera_modes.py`
- `src/gst_device_explorer/gui/qt_detail.py`
- `src/gst_device_explorer/gui/qt_explore.py`
- `src/gst_device_explorer/gui/qt_main_window.py`
- `tests/test_gui_preview_runner.py`
- `tests/test_gui_detail_pane.py`
- `tests/test_gui_shell.py`
- `docs/milestones/MILESTONE_36.md`
- `docs/GUI_ROADMAP.md`

Tests added or updated:

- Preview runner start from structured argv.
- Preview command rejection of shell-string input.
- Preview failed-start state.
- Preview normal-exit state.
- Preview failed-exit state.
- Preview stop/terminate cleanup.
- Preview timeout kill cleanup.
- Camera Explore preview control placement after the generated pipeline surface.
- Start Preview delegation to the runner with structured command data.
- Stop Preview delegation to runner cleanup.
- Preview unavailable state for cameras without eligible generated candidates.
- Endpoint-change preview cleanup.
- Main-window close preview cleanup.
- Audio output and audio input Explore pages do not gain preview execution controls.

Tests run:

- `uv run python -m pytest tests/test_gui_preview_runner.py tests/test_gui_camera.py tests/test_gui_detail_pane.py tests/test_gui_shell.py`
- `uv run python -m pytest tests/test_gui_model.py tests/test_gui_camera.py tests/test_gui_detail_pane.py tests/test_gui_shell.py`
- `uv run python -m pytest`

HIL validation:

- Not run in this implementation pass. Automated tests use fakes/test doubles and do not require camera hardware, display hardware, GStreamer, or Jetson.

Versioning:

- No version bump was made. Recent post-28 roadmap milestones in this working tree are not currently bumping package metadata per milestone.

No audio execution, arbitrary command execution, shell-string execution, `shell=True`, V4L2 writes, mixer mutation, system audio mutation, route change, recording/capture workflow, synchronized audio/video behavior, remote behavior, package installation, or group-based execution was added.

## Deferred Work

The following should remain deferred:

- audio input/output test policy and implementation
- bounded microphone capture or level display
- bounded speaker test tone or sound-file playback
- Commands/Reproduce sections
- Reports/Diagnostics area
- broader service-layer cleanup, unless preview implementation reveals a necessary narrow seam
- polish and full HIL validation pass
