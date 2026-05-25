# Milestone 23 — Camera Explorer Pane and Dynamic V4L2 Controls

Repository target path:

```text
docs/milestones/MILESTONE_23.md
```

Status: Completed

## Theme

Correct the GUI direction by making the selected camera pane a task-oriented camera explorer instead of a generic detail/report page.

The current PySide6 GUI has a useful sidebar, live discovery, detail panes, and copy affordances. However, the camera detail pane is drifting toward a rendered diagnostics/report view. The original reference application, `camera-caps`, is a camera-first GUI: it lets the user explore pixel formats, resolutions, frame durations, generated GStreamer pipeline text, and camera controls.

Milestone 23 should move the camera experience back toward that reference.

The important design point is that V4L2 controls are **device-advertised and dynamic**. Different cameras expose different controls. The GUI must not hard-code controls such as Brightness, Contrast, Saturation, Gain, Exposure, or White Balance. It should discover the controls for the selected camera and render the appropriate UI from structured control metadata.

The `camera-caps` project is available to the agent at:

```text
~/camera-caps
```

The agent should inspect it as a behavioral reference, especially the dynamic V4L2 control discovery and rendering approach.

## Product Goal

When a user selects a camera in the sidebar, the main pane should help them answer:

- What camera is selected?
- What pixel formats does it support?
- What resolutions are available for the selected format?
- What frame durations / frame rates are available for the selected resolution?
- What GStreamer pipeline would this mode generate?
- What V4L2 controls does this specific camera advertise?
- What are the current/default/min/max/step/menu values for those controls?
- What can be copied for terminal use?

This milestone should make the camera pane feel like an explorer/control surface, not a report page.

## Reference Behavior

Use `~/camera-caps` as the reference application.

The reference shows:

- camera selection
- camera identity
- driver/bus/capability information
- pixel format selection
- image size selection
- frame duration selection
- generated pipeline text
- copy pipeline button
- preview button
- dynamically discovered V4L2 controls:
  - sliders
  - spin boxes
  - check boxes
  - menu/dropdown values
  - default buttons

Milestone 23 should not copy the old code blindly. Instead, use it to understand behavior and model shape.

## Scope

### 1. Camera-Oriented Pane

Replace or augment the generic video endpoint detail pane with a camera-oriented explorer pane.

The camera pane should prioritize:

1. selected camera identity
2. pixel format selection
3. resolution selection
4. frame duration / frame rate selection
5. generated pipeline text
6. copy pipeline
7. dynamic V4L2 control display
8. diagnostics / advanced details as secondary information

The generic report-style sections may remain under an “Advanced”, “Details”, or “Diagnostics” section, but they should not dominate the camera pane.

### 2. Dynamic V4L2 Control Model

Add a structured model for camera controls.

The model should represent advertised V4L2 controls such as:

- control ID/name
- display label
- control type
- current value
- default value
- minimum value
- maximum value
- step
- menu choices where applicable
- flags or disabled/inactive state where available
- source device path

The model should support the common V4L2 control categories returned by tools such as `v4l2-ctl --list-ctrls` and `v4l2-ctl --list-ctrls-menus`.

Suggested model names:

```python
CameraControl
CameraControlChoice
CameraControlSet
```

Exact names are flexible, but the model should be testable without hardware.

### 3. Control Discovery

Add or adapt a V4L2 control discovery path for a selected camera device.

The discovery should normalize raw control output into the structured model.

Rules:

- Prefer existing project probe patterns.
- Keep probing separate from GUI rendering.
- Use synthetic test fixtures for normal automated tests.
- Do not require hardware for normal tests.
- Be robust to cameras with no advertised controls.
- Be robust to menu controls and disabled/inactive controls.
- Avoid hard-coded control lists.

### 4. Read-Only Control Rendering First

In this milestone, V4L2 controls should be rendered as read-only or non-mutating UI.

Allowed:

- show sliders/spin boxes/checkboxes/dropdowns representing current values
- disable controls if needed to prevent writes
- show default/current/min/max values
- show menu choices
- copy values or generated commands if useful

Not allowed in this milestone:

- applying new camera control values
- calling `v4l2-ctl --set-ctrl`
- mutating camera state
- reset-to-default actions that modify the device
- auto-applying changes while the user drags sliders

Changing V4L2 controls is a device mutation and should be scoped separately in a later milestone.

### 5. Camera Mode Selection

The camera pane should show mode exploration controls:

- pixel format list
- resolution list
- frame duration / frame rate list

The UI should update dependent choices when the selected format or resolution changes.

The generated pipeline text should update from the current selections where possible.

If the model does not yet contain enough structured mode information, add a small GUI-facing adapter that reshapes existing video capability data into camera-mode choices.

Suggested model names:

```python
CameraModeOption
CameraFormatOption
CameraResolutionOption
CameraFrameRateOption
CameraExplorerState
```

Exact names are flexible.

### 6. Generated Pipeline Text

Show a generated pipeline command/text field for the selected camera mode.

Allowed:

- show pipeline text
- copy pipeline text
- show unavailable reason if a pipeline cannot be generated
- show candidate ID/profile if useful

Not allowed:

- run preview
- run dry-run subprocess from the button
- execute pipeline
- capture media

A disabled “Preview” button may be shown if clearly labeled as unavailable/deferred, but it must not execute anything.

### 7. Diagnostics as Secondary

Diagnostics should still be reachable, but secondary.

Possible approaches:

- collapsible “Diagnostics” section
- “Advanced Details” section
- tabbed pane with “Explorer” and “Details”
- summary warning with expandable details

The first thing a user sees for a camera should not be a generic report table.

## Commands

Existing GUI commands remain:

```sh
gst-device-explorer gui
gst-device-explorer gui --demo
```

No new command is required.

## HIL / Manual Testing

A hardware-in-the-loop environment is available for manual validation.

Normal automated tests must remain synthetic and hardware-free.

Manual validation commands:

```sh
/home/jim/.local/bin/uv sync --extra gui
/home/jim/.local/bin/uv run gst-device-explorer gui --demo
/home/jim/.local/bin/uv run gst-device-explorer gui
```

Recommended HIL validation:

1. Launch the demo GUI.
2. Select the demo camera.
3. Verify the camera pane is camera-oriented, not report-oriented.
4. Verify format/resolution/frame-rate controls are visible.
5. Verify generated pipeline text is prominent.
6. Verify copy pipeline works.
7. Verify dynamic V4L2 controls are shown from demo data.
8. Launch live GUI on the HIL machine.
9. Select a real camera.
10. Verify that advertised controls differ appropriately between cameras.
11. Verify controls are read-only/non-mutating.
12. Confirm no preview, capture, dry-run subprocess, `v4l2-ctl --set-ctrl`, or pipeline execution occurs.

## Safety Boundaries

Preserve these boundaries:

- No camera preview.
- No audio input test.
- No audio output test.
- No media capture.
- No pipeline execution.
- No dry-run subprocess from GUI buttons.
- No suggested-command execution.
- No arbitrary subprocess execution.
- No arbitrary user-supplied pipeline strings.
- No V4L2 control writes.
- No `v4l2-ctl --set-ctrl`.
- No reset-to-default control mutation.
- No system configuration changes.
- No package installation.
- No remote behavior.
- No group-based execution.
- No synchronized capture.

Copy-to-clipboard remains allowed.

## Testing Expectations

Add or update synthetic tests for:

- parsing / normalizing V4L2 controls from fixture text
- menu control parsing
- integer/boolean/menu/button/control type handling where applicable
- disabled/inactive control representation where applicable
- cameras with no controls
- camera mode option shaping from existing capability data
- generated pipeline text from selected mode
- camera explorer pane rendering with demo data
- copy pipeline behavior
- no V4L2 control writes
- no subprocess execution from GUI controls
- no preview/capture/audio-test side effects
- GUI shell remains import-safe for CLI-only use

Automated tests should not require a live display unless protected by existing headless-skip patterns.

## Documentation Updates

Update:

- `README.md`
- `docs/SETUP.md`
- `docs/ARCHITECTURE.md`
- `docs/GUI_PRODUCT_SCOPE.md`
- `docs/milestones/MILESTONE_23.md`

Documentation should explain that:

- the camera pane is now task-oriented
- V4L2 controls are discovered dynamically per camera
- controls are displayed read-only in this milestone
- applying camera control changes is deferred

## Completion Criteria

Milestone 23 is complete when:

- the selected camera pane is camera-oriented rather than report-oriented
- pixel format/resolution/frame-rate choices are visible and usable
- generated pipeline text is prominent and copyable
- V4L2 controls are discovered dynamically from advertised device controls
- control data is normalized into structured models
- demo mode includes representative dynamic controls
- live mode can show controls for real cameras on HIL/manual validation
- controls do not mutate device state
- tests pass
- no preview, capture, pipeline execution, dry-run subprocess, or control-write behavior is introduced
- documentation is updated
- version is bumped to `0.23.0`

## Implementation Summary

Milestone 23 adds immutable camera-control models, a read-only V4L2 control
discovery path, a camera-mode GUI adapter, and a camera-first Qt detail pane.
The demo snapshot now includes representative dynamic controls and multiple
camera modes. Live GUI refresh reads advertised controls with
`v4l2-ctl --list-ctrls-menus` and passes the normalized metadata to the detail
pane.

The selected camera pane now prioritizes:

- camera identity
- pixel format, resolution, and frame-rate choices
- generated display-only pipeline text
- copy pipeline and copy device affordances
- dynamic read-only V4L2 controls
- generic capabilities, candidates, recommendations, diagnostics, and notes as
  secondary detail

Controls are rendered from the selected device's advertised metadata rather than
from a fixed hard-coded list. Integer, boolean, menu/intmenu, inactive, and
unknown controls are represented without mutating device state.

## Validation

Automated tests cover V4L2 control parsing, camera explorer mode shaping,
pipeline text generation, demo camera rendering, copy metadata, live snapshot
integration, and non-execution boundaries.

Manual HIL validation remains optional for this milestone:

```sh
/home/jim/.local/bin/uv sync --extra gui
/home/jim/.local/bin/uv run gst-device-explorer gui --demo
/home/jim/.local/bin/uv run gst-device-explorer gui
```

## Deferred

Explicitly deferred:

- applying V4L2 control changes
- reset-to-default control actions
- camera preview
- embedded video preview widgets
- dry-run process execution from GUI
- media capture dialogs
- audio input explorer redesign
- audio output explorer redesign
- audio test controls
- process lifecycle controls
- support bundle GUI
- screenshots/demo docs
- packaging/installers
