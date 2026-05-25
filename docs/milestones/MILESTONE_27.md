# Milestone 27 — Camera Explore Tab Cleanup

Status: **Implemented**

Version: `0.27.0`

## Purpose

Milestone 27 improves the camera **Explore** tab so it feels like a practical camera exploration surface rather than a lightly reorganized report view.

Milestone 26 introduced the selected-item tab structure:

```text
Explore
Device Information
```

Milestone 26.1 split the GUI detail pane responsibilities so camera work can continue from a cleaner structure.

Milestone 27 should now focus on the camera Explore experience only.

The goal is to make camera exploration feel closer to the original `camera-caps` interaction model while using cleaner layout and clearer information priority.

## Product Intent

The camera Explore tab should help the user answer:

> What settings does this camera support, and what GStreamer pipeline do those settings produce?

The default camera workflow should be:

1. Select a camera in the sidebar.
2. Use the **Explore** tab.
3. Select a pixel format.
4. Select an image size.
5. Select a frame duration / FPS.
6. See the generated GStreamer pipeline for that selection.
7. Copy the generated pipeline.
8. Review dynamic read-only camera controls if needed.

This milestone should not implement preview.

Preview policy and preview execution are deferred to later milestones.

## Current State

After Milestone 26.1:

- `qt_detail.py` is a small orchestration module.
- camera Explore behavior is in `qt_camera_explorer.py`.
- Explore tab dispatch is in `qt_explore.py`.
- Device Information rendering is in `qt_device_info.py`.
- shared section/copy helpers are in `qt_sections.py`.

Reported line counts after Milestone 26.1:

```text
qt_detail.py: 84 lines
qt_camera_explorer.py: 379 lines
qt_sections.py: 271 lines
qt_device_info.py: 119 lines
qt_explore.py: 76 lines
```

`qt_camera_explorer.py` is below the 400-line review threshold but close enough that new camera work should avoid turning it into another oversized file.

## Scope

Required scope:

- Improve the layout and information priority of the camera Explore tab.
- Keep the camera Explore tab focused on working with the camera.
- Preserve the camera-caps-style selection flow:
  - pixel format
  - image size
  - frame duration / FPS
  - generated pipeline
- Keep dynamic read-only V4L2 controls visible but secondary to the selection workflow.
- Keep the generated GStreamer pipeline prominent and easy to copy.
- Keep device identity compact.
- Avoid report-style sections in Explore.
- Preserve Device Information content.
- Preserve sidebar behavior.
- Preserve demo mode and live mode.
- Add or update GUI tests for the cleaned camera Explore layout.

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
- service-layer redesign
- arbitrary pipeline execution
- arbitrary user-authored pipelines
- V4L2 control writes
- `v4l2-ctl --set-ctrl`
- package installation
- system configuration changes
- remote behavior

## Desired Camera Explore Layout

The camera Explore tab should be organized as a working surface.

Suggested structure:

```text
Camera Summary
  Name / label
  Device path
  Driver
  Group, if available

Camera Settings
  Pixel Format        Image Size        Frame Duration / FPS
  [list]              [list]            [list]

Generated Pipeline
  gst-launch-1.0 ...
  [Copy Pipeline]

Camera Controls
  dynamically discovered read-only controls
```

The exact Qt widgets may differ, but the user should perceive the page in this order:

1. What camera is this?
2. What supported settings can I select?
3. What pipeline did that selection produce?
4. What controls does the device expose?

## Camera Settings Interaction

The settings selection should remain device-derived.

Do not hard-code camera formats, sizes, frame rates, or controls.

When the user selects a pixel format:

- available image sizes should update to match that format.

When the user selects an image size:

- available frame durations / FPS choices should update to match that size.

When the user selects a frame duration / FPS:

- the generated pipeline should reflect the selected concrete mode when supported by existing backend data.

The UI should avoid making unsupported combinations appear selectable.

## Generated Pipeline Area

The generated pipeline should be prominent.

It should show the practical GStreamer command produced for the selected settings.

The copy action should be easy to find.

Avoid multiple competing copy buttons in the Explore tab.

If more than one candidate exists, prefer the existing selected/recommended/default behavior rather than inventing a new ranking system in this milestone.

## Camera Controls

Camera controls are dynamic and device-advertised.

They must not be hard-coded.

For Milestone 27:

- controls should remain read-only
- inactive flags should remain visible where already supported
- menu annotations such as `value=2 (60 Hz)` should remain visible where already supported
- controls should not dominate the top of the Explore tab
- controls should not imply that the GUI can write control values

V4L2 control writing remains out of scope.

## Device Information Tab

Do not redesign the Device Information tab in this milestone.

It should continue to contain report-style information such as:

- identity
- metadata
- raw capabilities
- candidate pipelines
- recommended candidate
- diagnostics
- copy/safe-action sections where currently placed

Milestone 28 can refine Camera Device Information separately.

## Implementation Guidance

Prefer small, targeted changes.

Likely files:

```text
src/gst_device_explorer/gui/qt_camera_explorer.py
src/gst_device_explorer/gui/qt_sections.py
tests/test_gui_camera.py
tests/test_gui_detail_pane.py
docs/milestones/MILESTONE_27.md
```

If `qt_camera_explorer.py` grows significantly, split it before it exceeds the 400-line threshold.

Possible extraction targets:

```text
src/gst_device_explorer/gui/qt_camera_controls.py
src/gst_device_explorer/gui/qt_camera_modes.py
src/gst_device_explorer/gui/qt_camera_pipeline.py
```

Do not create abstractions just to create abstractions. Split only where it improves responsibility boundaries.

## Development Principles

Work from first principles.

For each section of the camera Explore tab, ask:

- What is the user trying to do here?
- Is this part of exploring the camera, or understanding a report?
- Does this belong in Explore or Device Information?
- Is this shown because it is useful to the user now, or because the backend happens to expose it?

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

- camera Explore tab contains compact camera summary
- camera mode selectors appear in the expected order
- selecting format updates available sizes
- selecting size updates available frame duration / FPS choices
- generated pipeline updates or remains available for the selected mode
- copy pipeline affordance is present
- dynamic read-only controls remain visible
- report-style sections remain out of the default camera Explore surface
- Device Information content remains available
- no physical hardware is required for tests

## Documentation

Updated `docs/milestones/MILESTONE_27.md` as the milestone record.

`README.md` was updated only for the versioned JSON envelope examples.

## Implementation Summary

The camera Explore tab now presents camera work in this order:

```text
Camera Summary
Camera Settings
Generated Pipeline
Camera Controls
```

The **Camera Summary** section keeps identity compact:

- camera name
- device path
- driver, when present in metadata
- bus, when present in metadata
- group, when present

The **Camera Settings** section keeps the camera-caps-style selection flow:

- Pixel Format
- Image Size
- Frame Duration / FPS

The selectors remain device-derived. Selecting a pixel format updates available image sizes, selecting an image size updates frame duration / FPS choices, and the generated pipeline updates for the selected concrete mode.

The **Generated Pipeline** section is now its own prominent group with the pipeline text and a single `Copy Pipeline` action. The disabled `Preview Deferred` placeholder was removed from the camera Explore working surface so this milestone does not imply preview behavior.

The **Camera Controls** section remains below the settings/pipeline workflow. Controls are still dynamic and read-only.

Device Information was not redesigned. Report-style content remains there.

## Files Changed

- `src/gst_device_explorer/gui/qt_camera_explorer.py`
  - Reorganized the camera Explore widget into Summary, Settings, Generated Pipeline, and Camera Controls.
  - Added compact summary extraction from detail metadata.
  - Kept selector interactions and pipeline generation behavior.
  - Removed the disabled preview placeholder from the camera Explore pipeline row.
- `src/gst_device_explorer/gui/qt_camera_controls.py`
  - Added focused read-only V4L2 control rendering module split from `qt_camera_explorer.py`.
- `src/gst_device_explorer/gui/qt_explore.py`
  - Adjusted camera Explore accessible text so camera summary/settings/pipeline/controls are the primary surface rather than raw summary lines.
- `tests/test_gui_detail_pane.py`
  - Updated camera Explore tests to assert summary/settings/pipeline/control ordering, compact identity, copy pipeline visibility, and absence of report/preview content.
- `pyproject.toml`
  - Bumped version to `0.27.0`.
- `src/gst_device_explorer/__init__.py`
  - Bumped `__version__` to `0.27.0`.
- `uv.lock`
  - Bumped editable package version to `0.27.0`.
- `tests/test_support_bundle.py`
  - Updated version-sensitive expectations to `0.27.0`.
- `README.md`
  - Updated JSON envelope version examples to `0.27.0`.
- `docs/milestones/MILESTONE_27.md`
  - Recorded implementation details, tests, safety boundaries, version notes, and deferred work.

## Line-Count Notes

Before Milestone 27:

```text
qt_camera_explorer.py: 379 lines
qt_sections.py: 271 lines
qt_device_info.py: 119 lines
qt_explore.py: 76 lines
qt_detail.py: 84 lines
```

After Milestone 27:

```text
qt_camera_explorer.py: 327 lines
qt_camera_controls.py: 113 lines
qt_sections.py: 271 lines
qt_device_info.py: 119 lines
qt_explore.py: 76 lines
qt_detail.py: 84 lines
```

The new camera controls split kept `qt_camera_explorer.py` below the 400-line review threshold while preserving clear responsibility boundaries.

## Tests Run

Targeted GUI tests:

```sh
/home/jim/.local/bin/uv run python -m pytest tests/test_gui_detail_pane.py tests/test_gui_camera.py
```

Result:

```text
24 passed in 0.08s
```

Qt offscreen smoke test:

```text
2 Explore Device Information 0
```

Pre-version-bump full suite:

```text
561 passed in 1.49s
```

Post-version-bump full suite:

```sh
/home/jim/.local/bin/uv run python -m pytest
```

Result:

```text
561 passed in 1.39s
```

## Versioning

Version bumped from `0.26.1` to `0.27.0` after implementation and a passing full test run.

## Acceptance Criteria

Milestone 27 is complete when:

- the camera Explore tab is organized around camera exploration rather than report output
- camera identity is compact
- pixel format, image size, and frame duration / FPS selection are clear
- generated pipeline is prominent and easy to copy
- dynamic read-only camera controls remain available but secondary
- Device Information still contains lower-level report-style content
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

- Milestone 28 — Camera Device Information Tab
- Milestone 29 — Group Explore View
- Milestone 30 — Group Device Information Tab
- Milestone 31 — Audio Input Explore Tab
- Milestone 32 — Audio Output Explore Tab
- Milestone 34 — Reports Area
- Milestone 35 — Preview Policy and Dry-Run UX
- Milestone 36 — Camera Preview Implementation
