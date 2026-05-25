# Milestone 28.1 — Camera Explore Raw Capability Correction

Status: **Implemented**

Version: `0.28.1`

## Purpose

Milestone 28.1 corrects the Milestone 28 camera Explore data source.

Live validation showed that the Camera Explore selectors could display the small demo-style mode set:

```text
MJPG
  640x480
    30 fps
    15 fps
YUYV
```

instead of the live Reachy Mini camera's raw V4L2 capability graph. That is incorrect for live exploration.

## Root Cause

The Camera Explore mode tree was being reconstructed from GUI summary sections:

- `Camera Modes`
- `Frame Rates`

Those sections are derived from capabilities, but they are not the raw capability graph and are too easy to confuse with reduced, summarized, or fixture-derived data.

The correction adds an explicit raw camera capability section generated directly from the selected `Device.capabilities` objects and makes Camera Explore prefer that raw section. The older summary-section path remains only as a fallback when raw capability data is unavailable.

## Raw Capability Source

The GUI now receives a `Raw Camera Capabilities` detail section produced directly from `Device.capabilities`.

For live cameras, those capabilities come from:

```text
v4l2-ctl --device=<device> --list-formats-ext
```

through the existing `discover_v4l2_capabilities()` probe path.

The Camera Explore mode tree now prefers `Raw Camera Capabilities` over `Camera Modes` / `Frame Rates`.

## Raw Control Source

Camera controls continue to come from the selected camera's `CameraControlSet`, which is populated in live mode by:

```text
v4l2-ctl --device=<device> --list-ctrls-menus
```

through the existing `discover_v4l2_controls()` probe path.

Controls remain read-only and display current values, ranges, defaults, steps, flags, and menu choices where parsed.

## Reachy Mini Fixture

Added a regression fixture matching the live Reachy Mini camera shape:

```text
MJPG:
  3840x2592 @ 30 fps
  1920x1080 @ 60 fps
  3840x2160 @ 30 fps
  3264x2448 @ 30 fps

YUYV:
  3840x2592 @ 1 fps
  1920x1080 @ 5 fps
  3840x2160 @ 1 fps
  3264x2448 @ 1 fps
```

The test asserts that `640x480` fallback/demo data is not shown when raw capabilities exist.

## Implementation Summary

- Added `Raw Camera Capabilities` to camera detail panes.
- Made `qt_camera_modes.camera_mode_tree()` prefer raw capability rows.
- Preserved format descriptions from raw capability rows for selector labels.
- Preserved fallback behavior for older or synthetic detail panes without raw capability rows.
- Added regression tests for the live Reachy-style capability graph.
- Added regression tests for raw control-set display, including menu choices and inactive flags.
- Bumped the patch version from `0.28.0` to `0.28.1`.

## Files Changed

- `src/gst_device_explorer/gui/builders.py`
  - Adds `Raw Camera Capabilities` from `Device.capabilities`.
- `src/gst_device_explorer/gui/qt_camera_explorer.py`
  - Treats raw camera capabilities as Explore-only camera content.
- `src/gst_device_explorer/gui/qt_camera_modes.py`
  - Prefers raw capability rows for the selector tree.
  - Keeps summary-section parsing as fallback only.
- `tests/test_gui_detail_pane.py`
  - Adds Reachy Mini raw capability fixture tests.
  - Adds raw camera control fixture tests.
- `README.md`
  - Updates JSON envelope examples to `0.28.1`.
- `pyproject.toml`
  - Bumps version to `0.28.1`.
- `src/gst_device_explorer/__init__.py`
  - Bumps `__version__` to `0.28.1`.
- `tests/test_support_bundle.py`
  - Updates version-sensitive expectations to `0.28.1`.
- `uv.lock`
  - Bumps editable package version to `0.28.1`.

## Line-Count Notes

```text
qt_camera_explorer.py: 295 lines
qt_camera_modes.py: 208 lines
qt_camera_controls.py: 145 lines
```

Camera GUI modules remain below the 400-line review threshold.

`src/gst_device_explorer/gui/builders.py` is now 809 lines. That file was already large and should be reviewed for a future split, but this correction kept the data-path change intentionally small.

## Tests Run

Targeted tests:

```sh
/home/jim/.local/bin/uv run python -m pytest tests/test_gui_camera.py tests/test_gui_detail_pane.py tests/test_v4l2_probe.py
```

Result:

```text
47 passed in 0.07s
```

Pre-version-bump full suite:

```text
564 passed in 1.32s
```

Post-version-bump full suite:

```sh
/home/jim/.local/bin/uv run python -m pytest
```

Result:

```text
564 passed in 1.48s
```

## Hardware Validation

No live hardware command was run during this correction. The regression test uses a fixture matching the Reachy Mini `v4l2-ctl --list-formats-ext` shape reported during live validation.

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
- no `v4l2-ctl --set-ctrl`
- no GUI preview/capture/test behavior

## Deferred

- Live hardware re-validation against `/dev/video0`.
- Camera Device Information cleanup.
- Further split of large GUI builder modules.
- Preview policy and any preview implementation.
- Audio Explore views.
- Group dashboard.
