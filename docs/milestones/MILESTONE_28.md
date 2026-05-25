# Milestone 28 — Camera Explore Full Capability Population

Status: **Implemented**

Version: `0.28.0`

Corrections:

- See `docs/milestones/MILESTONE_28_1.md` for the `0.28.1` raw V4L2 capability-source correction after live validation.
- See `docs/milestones/MILESTONE_28_2.md` for the `0.28.2` Camera Explore layout and controls UX cleanup.
- See `docs/milestones/MILESTONE_28_3.md` for the `0.28.3` Camera Controls read-only widget-surface correction.
- See `docs/milestones/MILESTONE_28_4.md` for the `0.28.4` Camera Controls vertical-responsiveness correction.

## Purpose

Milestone 28 continues work on the camera **Explore** pane.

The goal is to make the camera Explore pane fully populated from the camera capability and control dataset, while keeping the interface usable on smaller screens such as **1280x720**.

Milestone 27 improved the organization of the camera Explore pane into:

- Camera Summary
- Camera Settings
- Generated Pipeline
- Camera Controls

Milestone 28 should deepen that work by making sure the camera Explore pane is driven by the full available camera dataset, not by a partial or report-shaped subset.

This milestone is about data completeness and practical exploration, not preview or execution.

## Product Intent

The camera Explore pane should help the user answer:

> What settings does this camera support, and what GStreamer pipeline do those settings produce?

The first priority is to read and represent the camera capabilities and controls correctly.

The second priority is to present that information in a way that remains usable on constrained screens.

The full dataset should shape the interaction, not become a raw dump.

## Target User Workflow

The user should be able to:

1. Select a camera from the sidebar.
2. Open the default **Explore** tab.
3. See a compact summary of the selected camera.
4. Browse all discovered pixel formats.
5. Select a pixel format and see all valid image sizes for that format.
6. Select an image size and see all valid frame duration / FPS choices for that size.
7. Select a concrete mode and see the generated GStreamer pipeline for that mode when available.
8. Copy the generated pipeline.
9. Review all discovered camera controls in a read-only form.
10. Understand menu values, inactive flags, ranges, defaults, and current values where the probe provides them.

## Current State

After Milestone 27:

- the camera Explore pane is organized around camera exploration instead of report output
- the disabled preview affordance has been removed
- camera controls have been split into a focused module
- camera GUI files are below the 400-line review threshold

Reported line counts after Milestone 27:

```text
qt_camera_explorer.py: 327 lines
qt_camera_controls.py: 113 lines
```

Milestone 28 should avoid turning either file into a new monolith.

## Scope

Required scope:

- Populate the camera Explore pane from the full camera capability dataset.
- Ensure all discovered pixel formats are available in the format selector.
- Ensure each selected pixel format exposes the correct image sizes.
- Ensure each selected image size exposes the correct frame durations / FPS values.
- Ensure the selected concrete mode is summarized clearly.
- Ensure the generated pipeline reflects the selected concrete mode when supported by existing backend data.
- Populate the camera controls area from the full discovered control dataset.
- Preserve read-only control rendering.
- Preserve menu annotations such as `value=2 (60 Hz)` where available.
- Preserve inactive/read-only flag display where available.
- Preserve compact layout suitable for 1280x720-class screens.
- Use scroll areas, compact sections, or other Qt layout techniques where needed.
- Add or update tests for full capability/control population.
- Preserve demo mode and live mode.

## Out of Scope

Do not implement:

- camera preview
- camera capture
- embedded video
- external preview process management
- audio input explorer
- audio output explorer
- group dashboard
- reports area
- Device Information redesign
- service-layer redesign
- arbitrary pipeline execution
- arbitrary user-authored pipelines
- V4L2 control writes
- `v4l2-ctl --set-ctrl`
- package installation
- system configuration changes
- remote behavior

## Layout Guidance for Smaller Screens

The camera Explore pane should be usable at approximately **1280x720**.

This does not require pixel-perfect layout in this milestone, but the structure should avoid unnecessary vertical sprawl.

Recommended visual priority:

```text
Top: compact camera identity
Middle: camera mode selectors
Below: generated pipeline
Bottom: controls in a scrollable or compact area
```

Suggested structure:

```text
Camera Summary
  Compact identity: label, device path, driver, group if available

Camera Settings
  Pixel Format        Image Size        Frame Duration / FPS
  [list]              [list]            [list]

Selected Mode
  MJPG, 3840x2592, 30 fps

Generated Pipeline
  gst-launch-1.0 ...
  [Copy Pipeline]

Camera Controls
  scrollable compact read-only controls
```

Avoid expanding every low-level detail at once.

The Explore tab should stay focused on practical interaction. Full raw accounting belongs in Device Information.

## Camera Capability Requirements

The camera mode controls must be device-derived.

Do not hard-code camera formats, sizes, frame rates, or mode labels.

For each discovered format:

- show the format in the pixel format selector
- preserve useful labels or descriptions if available
- keep compressed/raw hints if already available in the underlying model

For each selected format:

- show only valid sizes for that format

For each selected size:

- show only valid frame duration / FPS choices for that format and size

For each selected frame duration:

- display an understandable FPS label
- preserve the exact duration value where useful
- update the selected mode summary
- update the generated pipeline when supported

Unsupported combinations must not be selectable.

## Generated Pipeline Requirements

The generated pipeline area should remain prominent and easy to copy.

Requirements:

- show one clear pipeline for the selected concrete mode when available
- keep a single obvious copy action
- avoid multiple competing copy buttons in Explore
- do not invent pipeline candidates beyond existing backend support
- if no pipeline is available for a selection, show an honest bounded message

This milestone should not add execution behavior.

## Camera Control Requirements

The camera controls area should use the full discovered control dataset.

For each discovered control, show useful read-only information where available:

- name
- current value
- type
- minimum
- maximum
- step
- default
- menu annotation or menu label
- inactive/read-only flags
- other meaningful flags already parsed by the backend

The presentation should remain compact.

The first pass may use one compact row per control, with secondary details shown in a smaller text line or tooltip if appropriate.

Controls must not appear editable.

The UI must not imply that values can be written.

## Device Information Tab

Do not redesign Device Information in this milestone.

Device Information should remain the lower-level accounting view.

Camera Device Information cleanup remains a later milestone.

## Implementation Guidance

Likely files:

```text
src/gst_device_explorer/gui/qt_camera_explorer.py
src/gst_device_explorer/gui/qt_camera_controls.py
src/gst_device_explorer/gui/qt_sections.py
tests/test_gui_camera.py
tests/test_gui_detail_pane.py
docs/milestones/MILESTONE_28.md
```

If capability selection logic grows, consider a focused split, such as:

```text
src/gst_device_explorer/gui/qt_camera_modes.py
```

If pipeline display logic grows, consider:

```text
src/gst_device_explorer/gui/qt_camera_pipeline.py
```

Only split where it improves clarity. Do not create unnecessary abstractions.

## Development Principles

Work from first principles.

For each piece of data, ask:

- Does this help the user explore the camera?
- Does this belong in Explore or Device Information?
- Is this information needed for selecting a supported mode?
- Is this information needed for understanding the generated pipeline?
- Is this information needed for safe read-only control inspection?

The full dataset should shape the interface. It should not become a raw dump.

Python file guidance:

- Keep Python files around 250 to 300 lines when practical.
- When a Python file grows beyond that range, review whether it has too many responsibilities.
- When a Python file exceeds 400 lines, explicitly consider splitting it before adding more functionality.

## Tests

Run the full test suite:

```sh
cd ~/gst-device-explorer
/home/jim/.local/bin/uv run python -m pytest
```

Also run targeted GUI tests if useful:

```sh
/home/jim/.local/bin/uv run python -m pytest tests/test_gui_camera.py tests/test_gui_detail_pane.py
```

Expected result: all tests pass.

Potential test themes:

- all camera formats from the probe appear in the format selector
- selecting each format exposes the correct sizes
- selecting each size exposes the correct frame duration / FPS values
- selected mode summary reflects the selected concrete mode
- generated pipeline remains available for supported selected modes
- generated pipeline copy action remains present
- controls with menu values show annotated labels
- inactive controls remain visible and marked
- control range/default/current values appear where available
- controls are read-only
- report-style sections remain out of the default camera Explore surface
- layout uses compact/scrollable sections suitable for smaller screens
- no physical hardware is required for tests

## Documentation

Updated `docs/milestones/MILESTONE_28.md` as the milestone record.

`README.md` was updated only for the versioned JSON envelope examples.

## Implementation Summary

The camera Explore pane now populates its working controls from the full available camera detail dataset:

- all discovered pixel formats are represented in the format selector
- format display labels preserve descriptions from capability metadata when available
- selecting a format drives the valid image-size list
- selecting an image size drives the valid frame duration / FPS list
- unsupported combinations are not selectable
- a new **Selected Mode** section summarizes the concrete selected mode
- generated pipeline text updates for the selected concrete mode
- a single Explore-surface `Copy Pipeline` action remains attached to the generated pipeline row
- camera controls remain dynamic and read-only
- control rows include compact current/type/range/default/step/flags/choices detail text where available
- camera controls are placed in a bounded scroll area so they remain secondary on smaller displays

The actual Qt widget was smoke-tested in offscreen mode. The demo camera showed:

```text
cameraPixelFormatList: MJPG (Motion-JPEG, compressed), YUYV (YUYV 4:2:2)
cameraImageSizeList: 640x480
cameraFrameDurationList: 30 fps, 15 fps
Selected Mode: MJPG, 640x480, 30 fps
```

Device Information was not redesigned.

## Files Changed

- `src/gst_device_explorer/gui/qt_camera_explorer.py`
  - Added selected-mode summary.
  - Added stable object names for mode selectors.
  - Kept generated pipeline updates bound to selected format, size, and frame duration / FPS.
- `src/gst_device_explorer/gui/qt_camera_modes.py`
  - Added focused camera mode parsing and pipeline-selection helpers.
  - Preserved format descriptions in selector labels where available.
  - Exposed `camera_mode_tree()` for headless capability-population tests.
- `src/gst_device_explorer/gui/qt_camera_controls.py`
  - Made controls compact and scrollable.
  - Added secondary detail text for type, current value, range, step, default, flags, and choices.
  - Preserved read-only widgets and inactive display behavior.
- `tests/test_gui_detail_pane.py`
  - Added tests for selected-mode summary and full demo mode-tree population.
  - Updated camera Explore tests to verify settings/pipeline/control ordering.
- `pyproject.toml`
  - Bumped version to `0.28.0`.
- `src/gst_device_explorer/__init__.py`
  - Bumped `__version__` to `0.28.0`.
- `uv.lock`
  - Bumped editable package version to `0.28.0`.
- `tests/test_support_bundle.py`
  - Updated version-sensitive expectations to `0.28.0`.
- `README.md`
  - Updated JSON envelope version examples to `0.28.0`.
- `docs/milestones/MILESTONE_28.md`
  - Recorded implementation details, tests, safety boundaries, version notes, line counts, and deferred work.

## 1280x720 Usability Notes

The Explore pane keeps the primary workflow above the potentially long controls list:

```text
Camera Summary
Camera Settings
Selected Mode
Generated Pipeline
Camera Controls
```

Camera controls now live inside a bounded scroll area with a maximum height of 220 pixels. This keeps large real-camera control sets available without forcing the user to scroll through all controls before seeing mode selection or the generated pipeline.

The mode selector lists use compact heights and remain side-by-side, preserving the camera-caps-style workflow on 1280x720-class screens.

## Line-Count Notes

Before Milestone 28:

```text
qt_camera_explorer.py: 327 lines
qt_camera_controls.py: 113 lines
```

After Milestone 28:

```text
qt_camera_explorer.py: 292 lines
qt_camera_modes.py: 146 lines
qt_camera_controls.py: 145 lines
```

All camera GUI modules remain below the 400-line review threshold. The mode/pipeline helper split keeps `qt_camera_explorer.py` near the preferred 250 to 300 line range.

## Tests Run

Targeted GUI tests:

```sh
/home/jim/.local/bin/uv run python -m pytest tests/test_gui_detail_pane.py tests/test_gui_camera.py
```

Result:

```text
25 passed in 0.09s
```

Qt offscreen smoke test:

```text
2 Explore Device Information 0
```

Pre-version-bump full suite:

```text
562 passed in 1.45s
```

Post-version-bump full suite:

```sh
/home/jim/.local/bin/uv run python -m pytest
```

Result:

```text
562 passed in 1.37s
```

## Versioning

Version bumped from `0.27.0` to `0.28.0` after implementation and a passing full test run.

## Acceptance Criteria

Milestone 28 is complete when:

- the camera Explore pane is populated from the full camera capability dataset
- all discovered formats are represented
- valid sizes update based on selected format
- valid frame durations / FPS values update based on selected size
- selected mode summary is clear
- generated pipeline remains prominent and easy to copy
- full discovered camera controls are visible in compact read-only form
- menu annotations, inactive flags, current values, ranges, defaults, and steps are shown where available
- layout remains practical for smaller screens such as 1280x720
- no preview/capture/control-write behavior is added
- demo mode and live mode remain functional
- tests pass
- milestone documentation is updated

## Safety Boundaries

Preserve all existing safety boundaries:

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
- no GUI preview/capture/test behavior unless deliberately scoped in a later milestone

## Deferred to Later Milestones

Deferred work includes:

- Camera Device Information cleanup
- Group Explore View
- Group Device Information Tab
- Audio Input Explore Tab
- Audio Output Explore Tab
- Reports Area
- Preview Policy and Dry-Run UX
- Camera Preview Implementation
