# Milestone 44 — Camera Control Write Implementation and HIL Validation

Status: Implementation complete; HIL validation blocked by unavailable camera device

## Theme

Implement the scoped camera-control write behavior approved in Milestone 43 and validate it with real hardware.

Milestone 29 intentionally kept camera controls read-only. Milestone 36 added safe camera preview. Milestone 40 validated preview on real hardware and fixed command provenance. Milestone 43 then defined the policy for safely opening a narrow camera-control write boundary.

Milestone 44 implements that boundary:

```text
Write supported active camera controls for the currently selected camera endpoint using structured control requests.
```

The goal is not to build a full V4L2 control editor. The goal is to make camera preview useful for real HIL testing by allowing common camera controls such as brightness, exposure, gain, and white balance to be adjusted safely and visibly.

## Product Intent

A user testing a camera should be able to:

- start camera preview
- inspect discovered camera controls
- adjust supported active writable controls
- see changes affect the live preview image
- reset individual controls to their reported defaults when available
- trust that writes target only the selected camera endpoint
- trust that the GUI is not running arbitrary shell commands or mutating unrelated devices

## Scope

Implement scoped camera-control writes in Camera Explore.

### Required behavior

- Use structured camera-control write requests.
- Write only to the currently selected camera endpoint.
- Enable editing only for controls that are active and writable under the approved first-pass scope.
- Keep inactive controls visibly muted/disabled.
- Keep read-only or unsupported controls visible but non-editable.
- Apply supported control writes immediately when the user changes a value.
- Allow writes while preview is running.
- Allow writes while preview is stopped if the selected endpoint remains valid.
- Refresh control values/states after writes when needed.
- Provide per-control Reset/Default only when the device reports a default value.
- Prevent stale writes after endpoint changes, refresh, or page rebuild.
- Preserve camera preview behavior and command provenance.
- Preserve audio output, audio input, and group behavior.

### Supported first-pass control types

Implement support for the common control types already represented by the GUI model:

- integer controls with min/max/step
- boolean controls
- menu controls

Button controls may be left read-only/deferred unless their safety semantics are already clear in the model and tests.

Keep these deferred unless explicitly simple and safe:

- compound controls
- string controls
- unknown/private controls without safe metadata
- controls without stable id/name/value representation
- global reset all
- automatic restore-on-close
- camera presets

## User Experience

The existing grouped camera-control area should remain:

- Image Adjustment
- Exposure & Gain
- White Balance
- Advanced

The user-facing state should distinguish:

```text
Readable
Writable
Active
Inactive
Unavailable
```

Implementation should make these distinctions visible through enabled state, muted styling, status labels, tooltips, or equivalent existing UI conventions.

Recommended behavior:

- writable active integer controls use editable spin/slider behavior
- writable active boolean controls use editable checkboxes
- writable active menu controls use editable combo boxes
- inactive controls are disabled/muted
- read-only controls are visible but disabled/non-editable
- unsupported controls are visible with clear unavailable/read-only text
- reset/default action appears only when a default value is known

## Backend Write Model

Implement a structured write path.

Conceptual flow:

```text
selected camera endpoint
+ discovered control id/name
+ typed value from widget
    -> structured camera-control write request
    -> camera-control writer/helper
    -> V4L2 write mechanism
```

Invalid flows:

```text
UI label -> shell command string -> execution
display text -> parsed command
arbitrary user-entered control name -> write
group selection -> write to multiple endpoints
stale endpoint path -> write after selection changed
```

If the implementation uses `v4l2-ctl`, it must use structured argv only and never `shell=True`.

Prefer a small project-local helper over broad architecture changes. Do not build a large V4L2 library in this milestone.

## Stale Endpoint Protection

The write path must protect against stale state.

Required:

- Control widgets must be bound to the selected camera endpoint used when they were built.
- Endpoint change invalidates old control widgets/write targets.
- Refresh invalidates old control widgets/write targets.
- Writes should fail safely if the selected endpoint no longer matches the control widget's endpoint.
- Group selections must not expose camera-control writes.
- Audio selections must not expose camera-control writes.

## Auto/Manual Dependency Handling

Use device-reported active/inactive state as the source of truth.

After a successful write that may affect other controls:

- refresh control values/states for the selected endpoint, or
- update the affected control state if the backend already provides reliable state data

Do not hard-code camera-specific dependency behavior beyond display grouping. For example, do not assume every device uses the same auto-exposure or auto-white-balance semantics.

## HIL Validation

HIL validation is required.

Use a real camera with writable controls.

Validation should prove more than preview opening.

Record:

- host and environment
- camera endpoint
- camera model/name if available
- discovered writable controls
- controls left read-only and why
- preview start/stop behavior
- at least one successful visible image-control write if supported
- brightness or equivalent write behavior if supported
- exposure or equivalent write behavior if supported
- gain or equivalent write behavior if supported
- white balance or equivalent write behavior if supported
- inactive control behavior
- reset/default behavior where supported
- endpoint-change stale-write protection
- refresh stale-write protection
- tests run
- safety confirmation

Milestone 44 is not complete unless at least one supported visual camera-control write is validated on real hardware, assuming the HIL camera exposes such a control.

If the HIL camera exposes no writable visual controls, record that explicitly and validate the write-unavailable behavior. Do not pretend this validates visual control writes.

## Tests

Add or update automated tests for:

- active writable controls are editable
- inactive controls remain disabled/muted
- read-only controls remain non-editable
- unsupported controls remain non-editable
- integer control changes generate structured write requests
- boolean control changes generate structured write requests
- menu control changes generate structured write requests
- reset/default writes only when default value is known
- writes target the selected endpoint
- stale endpoint writes are blocked
- endpoint change invalidates old write targets
- refresh invalidates old write targets
- no shell-string execution is used
- group selections do not expose control writes
- audio selections do not expose control writes
- existing camera preview tests still pass
- existing audio output quality tests still pass
- existing audio input activity tests still pass
- existing group navigation tests still pass

Suggested commands:

```sh
uv run python -m pytest tests/test_gui_camera.py tests/test_gui_detail_pane.py tests/test_gui_shell.py
uv run python -m pytest tests/test_gui_preview_runner.py tests/test_gui_detail_pane.py tests/test_gui_shell.py
uv run python -m pytest
```

Adjust test file list to match the actual test organization.

## Safety Boundaries

Milestone 44 deliberately opens only this scoped boundary:

```text
Write supported active camera controls for the currently selected camera endpoint using structured control requests.
```

All other safety boundaries remain:

- No arbitrary command execution.
- No arbitrary user-authored V4L2 commands.
- No shell-string execution.
- No `shell=True`.
- No hidden command execution.
- No package installation.
- No system configuration changes beyond the selected camera control value.
- No remote behavior.
- No group-based camera-control writes.
- No writes to unrelated endpoints.
- No synchronized capture.
- No video recording/capture workflow.
- No audio recording.
- No mixer, volume, route, ALSA, PulseAudio, or PipeWire mutation.
- No Commands/Reproduce expansion.
- No Reports expansion.

## Out of Scope

Do not implement:

- global Reset All
- automatic restore-on-close
- camera presets
- user-authored V4L2 command entry
- arbitrary V4L2 command execution
- broad V4L2 library rewrite
- group-level camera-control writes
- synchronized capture
- recording/capture workflows
- Commands/Reproduce sections
- Reports area
- README rewrite
- broad service-layer cleanup beyond what is required for safe writes

## Suggested Files to Inspect or Modify

Likely source files:

- `src/gst_device_explorer/gui/qt_camera_controls.py`
- `src/gst_device_explorer/gui/qt_camera_explorer.py`
- `src/gst_device_explorer/gui/qt_camera_preview.py`
- `src/gst_device_explorer/gui/camera.py`
- `src/gst_device_explorer/gui/qt_detail.py`
- `src/gst_device_explorer/gui/qt_explore.py`
- camera/V4L2 probe or model files in `src/gst_device_explorer/core/` or `src/gst_device_explorer/probes/`
- any existing serializers/models that represent camera controls

Likely tests:

- `tests/test_gui_camera.py`
- `tests/test_gui_detail_pane.py`
- `tests/test_gui_shell.py`
- camera control/model tests if present
- V4L2 probe/model tests if write helpers are added

## Documentation Updates

Update:

- `docs/milestones/MILESTONE_44.md`
- `docs/GUI_ROADMAP.md`

Record implementation notes, HIL findings, tests run, and safety confirmation.

## Acceptance Criteria

Milestone 44 is complete when:

- supported active camera controls can be written for the selected endpoint
- writes use structured camera-control requests
- no shell-string execution or arbitrary command execution is introduced
- writes are blocked for inactive/read-only/unsupported controls
- stale endpoint writes are blocked
- per-control reset/default works where default values are known
- camera preview still works
- audio output quality test still works
- audio input activity test still works
- HIL validates at least one real visual camera-control write when supported by the camera
- automated tests pass
- safety boundaries remain intact
- documentation is updated

## Completion Notes

Implementation is complete, but Milestone 44 is not fully complete because required real-camera HIL validation could not be performed in this session. The HIL host was `jetsonhacks`, but no `/dev/video*` device nodes were present.

Files changed:

- `src/gst_device_explorer/gui/camera_control_writer.py`
- `src/gst_device_explorer/gui/qt_camera_controls.py`
- `src/gst_device_explorer/gui/qt_camera_control_widgets.py`
- `src/gst_device_explorer/gui/qt_camera_explorer.py`
- `src/gst_device_explorer/gui/qt_explore.py`
- `src/gst_device_explorer/gui/qt_detail.py`
- `src/gst_device_explorer/gui/qt_main_window.py`
- `src/gst_device_explorer/gui/qt_app.py`
- `src/gst_device_explorer/gui/camera.py`
- `src/gst_device_explorer/probes/v4l2.py`
- `tests/test_gui_detail_pane.py`
- `docs/milestones/MILESTONE_44.md`
- `docs/GUI_ROADMAP.md`

Write mechanism chosen:

- Camera-control writes use `CameraControlWriteRequest`.
- The live GUI wires `CameraControlWriter` only for non-demo launches.
- The writer delegates to `write_v4l2_control()`.
- `write_v4l2_control()` invokes `v4l2-ctl` with structured argv:

```text
["v4l2-ctl", "--device", endpoint, "--set-ctrl", "control=value"]
```

- No shell string and no `shell=True` path is used.

Supported control types:

- integer controls with known min/max
- boolean controls
- menu controls with discovered choices

Deferred control types:

- compound controls
- string controls
- unknown/private controls without safe metadata
- button controls with unclear safety semantics
- controls without stable id/name/value representation

UI behavior implemented:

- Supported active writable integer controls are editable through the existing slider/spin presentation.
- Supported active writable boolean controls are editable as checkboxes.
- Supported active writable menu controls are editable as combo boxes.
- Writes apply immediately on value change.
- Writes remain separate from preview pipeline execution.
- After successful boolean/menu writes, the selected endpoint's controls are re-discovered and the camera-control area is rebuilt so auto/manual dependencies can enable or disable dependent controls.
- Integer slider/spin writes do not rebuild the control area during adjustment, avoiding scroll jumps while the user is setting a value.
- Read-only, inactive, and unsupported controls remain visible but disabled/non-editable.
- Demo-mode windows do not wire a real camera-control writer.

Reset/default behavior:

- Per-control Default buttons are enabled only for active writable controls with reported defaults.
- Reset writes only that control's reported default value.
- No global Reset All was added.
- No automatic restore-on-close was added.

Stale endpoint protection:

- Control widgets are built for the endpoint shown in the selected camera detail pane.
- The write path checks the current selected endpoint before writing.
- If the current selected endpoint differs from the widget's endpoint, the write is blocked and reported as stale.
- Endpoint changes and full refresh rebuild the camera control widgets.
- Successful boolean/menu control writes schedule a selected-endpoint control refresh before dependent controls are used again.
- Group and audio Explore pages do not expose camera-control write widgets.

HIL hardware used:

- Host: `jetsonhacks`
- Kernel: Linux 6.8.12-tegra, aarch64
- `v4l2-ctl`: `/usr/bin/v4l2-ctl`
- Camera endpoint: unavailable
- Camera model/name: unavailable

HIL validation result:

- `ls -l /dev/video*` returned no video device nodes.
- Preview start/stop could not be validated.
- Writable visual controls could not be discovered.
- Brightness, exposure, gain, and white-balance writes could not be validated.
- Inactive control behavior could not be validated on real hardware.
- Reset/default behavior could not be validated on real hardware.
- Endpoint-change and refresh stale-write behavior were validated by automated tests, not by HIL.
- Auto/manual dependency refresh was validated by automated tests that simulate White Balance Temperature becoming editable after Auto White Balance is disabled.
- Slider/spin writes were validated not to rebuild the scrolled controls pane during adjustment.

Milestone 44 is therefore not complete by the HIL acceptance standard. It requires a follow-up HIL pass on a host with a real camera exposing writable visual controls.

Tests run:

- `uv run python -m pytest tests/test_gui_detail_pane.py -q` -> 66 passed
- `uv run python -m pytest tests/test_gui_preview_runner.py tests/test_gui_detail_pane.py tests/test_gui_shell.py -q` -> 83 passed
- `uv run python -m pytest -q` -> 625 passed
- `python -m compileall -q src/gst_device_explorer/gui src/gst_device_explorer/probes/v4l2.py`

Safety confirmation:

- Only the scoped camera-control write boundary was opened.
- No arbitrary command execution was added.
- No arbitrary user-authored V4L2 command entry was added.
- No shell-string execution was added.
- No `shell=True` path was added.
- No group-based camera-control writes were added.
- No writes to unrelated endpoints were added.
- No synchronized capture, recording, Commands/Reproduce, Reports, README, or broad service-layer work was added.

Deferred work:

- Perform HIL validation on a host with a real camera.
- Record preview start/stop behavior.
- Record writable controls discovered.
- Validate at least one visible image-control write when supported.
- Validate brightness, exposure, gain, and white-balance behavior where supported.
- Validate reset/default behavior on hardware.
- Validate inactive control behavior on hardware.
