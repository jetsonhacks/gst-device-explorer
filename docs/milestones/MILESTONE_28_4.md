# Milestone 28.4 — Camera Controls Vertical Responsiveness

Status: **Implemented**

Version: `0.28.4`

## Purpose

Milestone 28.4 fixes the remaining Camera Controls layout issue after the 28.3 read-only widget conversion.

Camera Controls should be the vertically expanding part of the Camera Explore pane. Header, settings, and generated pipeline sections should stay compact while Camera Controls absorbs extra height.

This is not a preview, capture, execution, audio, group, Device Information, reset, or V4L2-write milestone.

## Responsive Sizing Issue

Camera Controls already had an internal scroll area, but the Explore layout could still leave extra vertical space outside the controls section.

The key issue was ownership of the extra height:

- the camera explorer widget was expandable
- the Camera Controls section was expandable
- the internal scroll area was expandable
- but the parent Explore layout also added a trailing stretch after the camera explorer

That trailing stretch could compete with Camera Controls for vertical space and leave the controls section under-allocated.

## Implementation Summary

The Camera Explore layout now gives extra height to the camera explorer and, inside that explorer, to Camera Controls.

The hierarchy is:

```text
Explore tab
└── Camera Explorer widget          stretch 1
    ├── camera header               stretch 0
    ├── Camera Settings             stretch 0
    ├── Generated Pipeline          stretch 0
    └── Camera Controls             stretch 1
        └── QScrollArea             stretch 1, widgetResizable=True
```

For camera pages, the parent Explore layout no longer adds a competing trailing stretch.

The Camera Controls section now has:

- object name `cameraControlsSection`
- expanding horizontal and vertical size policy
- minimum height of 180 pixels
- child scroll area with object name `cameraControlsScrollArea`
- widget-resizable scroll area
- expanding horizontal and vertical size policy on the scroll area
- scroll area added to the controls layout with stretch `1`

## Spin Box Alignment

Integer camera controls still render as disabled slider plus spin box widgets.

The integer spin box now right-aligns its numeric text:

```text
[ slider ---------------- ] [   4600 ]
```

The spin box remains disabled and read-only. No values are written to the device.

## Files Changed

- `src/gst_device_explorer/gui/qt_explore.py`
  - Removed the trailing stretch for camera Explore pages so it no longer competes with the camera explorer widget for vertical space.
- `src/gst_device_explorer/gui/qt_camera_controls.py`
  - Made the controls scroll area minimum height match the section's intended minimum.
  - Added object names for the controls section, controls scroll area, and integer spin box.
  - Added the scroll area to the controls layout with stretch `1`.
  - Set the scroll content to a vertically expandable size policy.
  - Right-aligned integer spin box text.
- `src/gst_device_explorer/gui/qt_detail.py`
  - Made tab scroll areas explicitly expanding.
- `README.md`
  - Updated JSON envelope examples to `0.28.4`.
- `pyproject.toml`
  - Bumped version to `0.28.4`.
- `src/gst_device_explorer/__init__.py`
  - Bumped `__version__` to `0.28.4`.
- `tests/test_support_bundle.py`
  - Updated version-sensitive expectations to `0.28.4`.
- `uv.lock`
  - Bumped editable package version to `0.28.4`.

## Verification

Qt offscreen smoke check confirmed:

```text
{
  'controls_stretch': 1,
  'controls_vpolicy_expanding': True,
  'scroll_resizable': True,
  'scroll_vpolicy_expanding': True,
  'spin_right': True,
  'combo_count': 1
}
```

This verifies that the Camera Controls section itself receives stretch from the camera explorer layout, the internal scroll area is resizable and expanding, and integer spin boxes are right-aligned.

## Line-Count Notes

```text
qt_camera_controls.py: 346 lines
qt_camera_explorer.py: 317 lines
qt_camera_modes.py: 208 lines
qt_explore.py: 76 lines
qt_detail.py: 85 lines
```

Camera GUI modules remain below the 400-line review threshold.

## Tests Run

Targeted GUI tests:

```sh
/home/jim/.local/bin/uv run python -m pytest tests/test_gui_camera.py tests/test_gui_detail_pane.py
```

Result:

```text
28 passed in 0.06s
```

Pre-version-bump full suite:

```sh
/home/jim/.local/bin/uv run python -m pytest
```

Result:

```text
565 passed in 1.47s
```

Post-version-bump full suite:

```sh
/home/jim/.local/bin/uv run python -m pytest
```

Result:

```text
565 passed in 1.50s
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

All camera controls and Default buttons remain disabled.

## Version Notes

Version bumped from `0.28.3` to `0.28.4` after the layout correction and passing targeted and full tests.

## Deferred

- Live hardware visual re-validation.
- Actual V4L2 control writes.
- Reset-to-default behavior.
- Preview policy and camera preview.
- Camera Device Information cleanup.
