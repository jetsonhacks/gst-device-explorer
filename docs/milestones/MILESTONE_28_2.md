# Milestone 28.2 — Camera Explore Layout and Controls UX Cleanup

Status: **Implemented**

Version: `0.28.2`

## Purpose

Milestone 28.2 cleans up the presentation of the Camera Explore pane after the raw-capability correction in `0.28.1`.

The goal was to keep the existing raw V4L2 capability and control data path while making the pane more usable, more compact, and less report-shaped.

This is not a preview, capture, execution, audio, group, or Device Information milestone.

## Observed UI Issues

- Camera controls looked like raw probe output rather than a read-only control panel.
- Control labels used code identifiers such as `power_line_frequency`.
- Control detail text was semicolon-heavy and hard to scan.
- The pane had too many nested containers.
- `Camera Explorer` and `Camera Summary` labels were redundant inside the already-selected Explore tab.
- The camera name was repeated.
- `Selected Mode` consumed a full pane instead of living with mode selection.
- The generated pipeline field could appear horizontally scrolled to the end.
- Camera Settings list boxes were taller than needed for small option counts.
- Camera Controls did not absorb extra vertical space naturally.
- Generic endpoint names such as `video0` were too weak when group context was available.

## Implementation Summary

The Camera Explore pane now uses a flatter structure:

```text
Camera header
Camera Settings
Generated Pipeline
Camera Controls
```

The old top-level `Camera Explorer` container and heavy `Camera Summary` box were removed.

The camera header is compact:

```text
Display Name - /dev/video0
Driver: uvcvideo - Group: ...
```

The selected mode now appears inside `Camera Settings`:

```text
Selected: MJPG, 1920x1080, 60 fps
```

The generated pipeline field resets its cursor position to `0` after text updates so the user sees the beginning of the command.

Camera Settings list widgets now have compact bounded heights.

Camera Controls now use readable rows with:

- title-cased control labels
- current value, with menu labels where available
- range / step
- default
- choices
- flags
- inactive messaging
- disabled `Default` button as a non-operational affordance for future control-write milestones

Controls remain read-only.

## Files Changed

- `src/gst_device_explorer/gui/qt_camera_explorer.py`
  - Removed redundant `Camera Explorer` container.
  - Replaced heavy summary box with compact header.
  - Moved selected mode into `Camera Settings`.
  - Reduced selector list heights.
  - Reset generated-pipeline cursor position to command start.
  - Let Camera Controls expand vertically.
- `src/gst_device_explorer/gui/qt_camera_controls.py`
  - Reworked read-only controls into structured rows.
  - Added margins, spacing, readable labels, human-readable menu current values, choice summaries, inactive messaging, and disabled `Default` buttons.
  - Made the controls section vertically expanding with a sensible minimum height.
- `src/gst_device_explorer/gui/qt_explore.py`
  - Avoided adding the generic Explore title above camera details.
- `src/gst_device_explorer/gui/builders.py`
  - Improved video display names using group labels when available.
- `tests/test_gui_detail_pane.py`
  - Updated camera Explore assertions for the flatter header and readable controls.
  - Added group-derived camera naming coverage.
- `README.md`
  - Updated JSON envelope examples to `0.28.2`.
- `pyproject.toml`
  - Bumped version to `0.28.2`.
- `src/gst_device_explorer/__init__.py`
  - Bumped `__version__` to `0.28.2`.
- `tests/test_support_bundle.py`
  - Updated version-sensitive expectations to `0.28.2`.
- `uv.lock`
  - Bumped editable package version to `0.28.2`.

## Naming Changes

Camera display names now prefer group context for grouped video endpoints.

If a video endpoint has group metadata and the endpoint name is generic, the display name uses the group label:

```text
Reachy Mini Camera - /dev/video0
```

If the group label already includes "camera", it is used as-is. Otherwise, `Camera` is appended for the video endpoint.

This avoids hard-coded product names while making grouped camera endpoints more human-readable.

## Resizing And 1280x720 Notes

The compact/preferred-height sections are:

- camera header
- Camera Settings
- Generated Pipeline

The expanding section is:

- Camera Controls

Camera Controls has a minimum height of 180 pixels and an expanding vertical size policy. The internal scroll area has a minimum height of 140 pixels and also expands vertically.

This keeps the primary mode/pipeline workflow visible on smaller screens while allowing the controls area to grow in taller windows.

## Line-Count Notes

```text
qt_camera_explorer.py: 317 lines
qt_camera_controls.py: 173 lines
qt_camera_modes.py: 208 lines
qt_explore.py: 76 lines
```

Camera GUI modules remain below the 400-line review threshold.

`src/gst_device_explorer/gui/builders.py` is 814 lines and remains a future split candidate.

## Tests Run

Targeted GUI tests:

```sh
/home/jim/.local/bin/uv run python -m pytest tests/test_gui_camera.py tests/test_gui_detail_pane.py
```

Result:

```text
28 passed in 0.09s
```

Qt offscreen smoke check confirmed:

- compact selector heights: 58 minimum, 104 maximum
- generated pipeline cursor position: `0`
- Camera Controls minimum height: `180`
- Camera Controls vertical policy: expanding
- old `Camera Explorer` and `Camera Summary` containers absent
- Explore remains tab index `0`

Pre-version-bump full suite:

```text
565 passed in 1.50s
```

Post-version-bump full suite:

```sh
/home/jim/.local/bin/uv run python -m pytest
```

Result:

```text
565 passed in 1.39s
```

## Safety Confirmation

No safety boundaries changed.

Preserved:

- no arbitrary pipeline execution
- no arbitrary user-authored pipeline scripts
- no hidden command execution
- no package installation
- no system configuration changes
- no remote behavior
- no group-based execution
- no synchronized capture
- no camera preview
- no camera capture
- no V4L2 control writes
- no reset-to-default execution
- no `v4l2-ctl --set-ctrl`
- no GUI preview/capture/test behavior

The `Default` buttons added to Camera Controls are disabled and non-operational.

## Version Notes

Version bumped from `0.28.1` to `0.28.2` after implementation and a passing full test run.

## Deferred

- Live hardware re-validation.
- Actual V4L2 control writes.
- Reset-to-default behavior.
- Preview policy and camera preview.
- Camera Device Information cleanup.
- Audio Explore views.
- Group dashboard.
- Reports area.
- Further split of large GUI builder modules.
