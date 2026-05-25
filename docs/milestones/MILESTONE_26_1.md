# Milestone 26.1 — Split GUI Detail Pane Responsibilities

Status: **Implemented**

Version: `0.26.1`

## Purpose

Milestone 26.1 is a focused refactor after Milestone 26.

Milestone 26 introduced the selected-item `Explore` and `Device Information` tab structure, but `src/gst_device_explorer/gui/qt_detail.py` had grown to approximately 819 lines. That exceeded the review threshold established in Milestone 25 and mixed too many responsibilities in one module.

The goal of this milestone was to split responsibilities before beginning Milestone 27 camera Explore cleanup.

## Why The Refactor Was Needed

`qt_detail.py` was handling:

- selected-item detail orchestration
- tab construction
- Explore tab content
- Device Information tab content
- camera explorer UI
- group/audio placeholders
- reusable section widgets
- copy-button behavior
- formatting helpers

That made future GUI changes risky because camera UX work, report rendering, copy helpers, and tab orchestration were all coupled in the same file.

## Implementation Summary

The selected-item behavior remains the same as Milestone 26:

- selected-item main pane uses two tabs
- `Explore` is first and selected by default
- `Device Information` is second
- camera explorer remains under `Explore`
- report-style content remains under `Device Information`
- group/audio Explore tabs remain lightweight deferred placeholders
- copy behavior remains display/copy only

No new device behavior was added.

## Module Responsibility Split

### `src/gst_device_explorer/gui/qt_detail.py`

High-level selected-item orchestration only:

- creates the `QTabWidget`
- creates the `Explore` and `Device Information` scroll areas
- coordinates tab builders
- resets the active tab to `Explore` on render
- re-exports existing helper functions used by tests and callers

### `src/gst_device_explorer/gui/qt_camera_explorer.py`

Camera-specific Explore rendering:

- camera format list
- image size list
- frame duration / FPS list
- generated pipeline display
- copy pipeline action
- dynamic read-only V4L2 control rendering
- camera-specific helper parsing

### `src/gst_device_explorer/gui/qt_explore.py`

Explore tab construction:

- dispatches to camera explorer when available
- renders group/audio lightweight placeholders
- provides Explore-tab accessible text for tests

### `src/gst_device_explorer/gui/qt_device_info.py`

Device Information tab construction:

- identity section
- summary section
- report-style detail sections
- copy section
- safe action metadata section
- Device Information accessible text for tests

### `src/gst_device_explorer/gui/qt_sections.py`

Shared helpers:

- section title normalization
- section kind classification
- identity rows
- safe copy metadata helpers
- clipboard abstraction
- shared Qt labels, copy buttons, copyable rows, and section tables

## Line Counts

Before:

```text
819 src/gst_device_explorer/gui/qt_detail.py
```

After:

```text
 84 src/gst_device_explorer/gui/qt_detail.py
379 src/gst_device_explorer/gui/qt_camera_explorer.py
 76 src/gst_device_explorer/gui/qt_explore.py
119 src/gst_device_explorer/gui/qt_device_info.py
271 src/gst_device_explorer/gui/qt_sections.py
```

`qt_camera_explorer.py` is the largest new module at 379 lines. It is below the 400-line explicit review threshold, but it should be watched during Milestone 27. If camera Explore cleanup adds much more behavior, split camera controls, mode selection, or pipeline display into smaller helpers before the file becomes another dumping ground.

## Files Changed

- `src/gst_device_explorer/gui/qt_detail.py`
  - Reduced to tab orchestration and compatibility exports.
- `src/gst_device_explorer/gui/qt_camera_explorer.py`
  - Added camera-specific exploration widget and helpers.
- `src/gst_device_explorer/gui/qt_explore.py`
  - Added Explore tab builder and placeholder behavior.
- `src/gst_device_explorer/gui/qt_device_info.py`
  - Added Device Information tab builder.
- `src/gst_device_explorer/gui/qt_sections.py`
  - Added shared formatting, copy, and section-widget helpers.
- `README.md`
  - Updated JSON envelope version examples to `0.26.1`.
- `pyproject.toml`
  - Bumped version to `0.26.1`.
- `src/gst_device_explorer/__init__.py`
  - Bumped `__version__` to `0.26.1`.
- `tests/test_support_bundle.py`
  - Updated version-sensitive expectations to `0.26.1`.
- `uv.lock`
  - Bumped editable package version to `0.26.1`.
- `docs/milestones/MILESTONE_26_1.md`
  - Added this milestone record.

## Tests Run

Targeted GUI tests:

```sh
/home/jim/.local/bin/uv run python -m pytest tests/test_gui_detail_pane.py tests/test_gui_camera.py tests/test_gui_shell.py
```

Result:

```text
33 passed in 0.10s
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
561 passed in 1.44s
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
- no V4L2 control writes
- no `v4l2-ctl --set-ctrl`
- no GUI preview/capture/test behavior unless deliberately scoped in a later milestone

## Version Notes

Version bumped from `0.26.0` to `0.26.1` after the refactor passed the full test suite.

## Deferred Work

- Milestone 27 camera Explore cleanup.
- Further split of `qt_camera_explorer.py` if camera-specific work expands.
- Group Explore dashboard.
- Audio input Explore view.
- Audio output Explore view.
- Device Information redesign beyond preserving existing placement.
- Reports area.
- Preview policy and dry-run UX.
- Camera preview implementation.
- Any capture, audio test, V4L2 write, or group execution behavior.
