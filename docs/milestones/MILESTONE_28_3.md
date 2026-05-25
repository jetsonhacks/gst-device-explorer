# Milestone 28.3 — Camera Controls UX Correction

Status: **Implemented**

Version: `0.28.3`

## Purpose

Milestone 28.3 corrects a Camera Controls presentation regression introduced during the 28.2 layout cleanup.

The Camera Explore pane should show camera controls as a read-only control surface. It should not make users read a descriptive report table to understand sliders, menus, booleans, defaults, and inactive states.

This is not a preview, capture, execution, audio, group, Device Information, or V4L2-write milestone.

## Observed UI Regression

The Camera Controls rows had become readable but too report-like:

```text
Brightness                         4
Range: -64 to 64, step 1 - Default: 0 - Type: int
```

That made metadata the primary content rather than using the metadata to configure appropriate disabled controls.

## Implementation Summary

Camera Controls now builds a small toolkit-neutral control rendering plan for each raw V4L2 control row.

The plan maps raw control metadata to disabled widgets:

- integer controls render as a disabled horizontal slider plus disabled spin box
- boolean controls render as a disabled checkbox
- menu controls render as a disabled combo box populated from the raw menu choices
- button controls render as a disabled button
- unsupported controls fall back to a compact read-only value label

The raw metadata is still preserved, but it configures the widgets and appears in tooltips/accessibility text instead of dominating the visible row.

Disabled `Default` buttons remain non-operational. They are present only when a default value is available and continue to signal a deferred future capability.

Controls remain read-only.

## Metadata As Widget Configuration

The GUI now uses control metadata this way:

- `minimum` and `maximum` set slider/spin-box bounds
- `step` sets slider/spin-box step
- `value` sets the current widget state
- `choices` populate menu combo boxes
- `default` determines the disabled Default affordance and tooltip
- `flags` mark inactive controls as disabled/muted
- `type` selects the read-only widget kind

Prominent visible row text is now user-oriented:

```text
Power Line Frequency    [60 Hz v]    [Default disabled]
White Balance Auto      [x]          [Default disabled]
```

The actual Qt widgets are disabled; no values are written.

## Files Changed

- `src/gst_device_explorer/gui/qt_camera_controls.py`
  - Added `CameraControlWidgetPlan` as a non-Qt rendering plan.
  - Reworked control rows to render disabled widgets rather than descriptive text rows.
  - Kept metadata in tooltips/accessibility text.
  - Preserved scrollable, vertically expanding Camera Controls behavior.
- `tests/test_gui_detail_pane.py`
  - Added assertions that raw controls map to combo, slider/spin, and checkbox plans.
  - Preserved raw-control coverage for readable labels, menu labels, inactive flags, and no synthetic controls.
- `README.md`
  - Updated JSON envelope examples to `0.28.3`.
  - Clarified that camera controls are displayed as disabled read-only widgets.
- `pyproject.toml`
  - Bumped version to `0.28.3`.
- `src/gst_device_explorer/__init__.py`
  - Bumped `__version__` to `0.28.3`.
- `tests/test_support_bundle.py`
  - Updated version-sensitive expectations to `0.28.3`.
- `uv.lock`
  - Bumped editable package version to `0.28.3`.

## Responsive Sizing

The Camera Controls section keeps the 28.2 sizing behavior:

- minimum height on the section
- internal scroll area
- expanding vertical size policy
- Camera Settings and Generated Pipeline remain compact
- Camera Controls absorbs extra vertical space

An offscreen Qt smoke check confirmed the controls section still has a scroll area and expanding vertical policy while rendering slider, combo, and checkbox widgets.

## Line-Count Notes

```text
qt_camera_controls.py: 341 lines
qt_camera_explorer.py: 317 lines
qt_camera_modes.py: 208 lines
```

`qt_camera_controls.py` grew because it now owns both the rendering plan and the read-only widget mapping, but it remains below the 400-line review threshold.

## Tests Run

Targeted GUI tests:

```sh
/home/jim/.local/bin/uv run python -m pytest tests/test_gui_camera.py tests/test_gui_detail_pane.py
```

Result:

```text
28 passed in 0.09s
```

Qt offscreen smoke check:

```text
{'combos': 1, 'sliders': 1, 'checkboxes': 1, 'scrolls': 1, 'vpolicy': True}
```

Post-version-bump full suite:

```sh
/home/jim/.local/bin/uv run python -m pytest
```

Result:

```text
565 passed in 1.36s
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

All controls and Default buttons are disabled.

## Version Notes

Version bumped from `0.28.2` to `0.28.3` after the correction and passing targeted and full tests.

## Deferred

- Live hardware re-validation.
- Actual V4L2 control writes.
- Reset-to-default behavior.
- Preview policy and camera preview.
- Camera Device Information cleanup.
