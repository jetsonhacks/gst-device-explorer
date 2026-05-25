# Milestone 26 — Main Pane Tab Redesign

Status: **Implemented**

Version: `0.26.0`

## Purpose

Milestone 26 begins the GUI restructuring defined in Milestone 25.

The goal is to refactor the selected-item main pane so it no longer feels like rendered CLI/report output. The selected item should now present a tabbed interface with a default **Explore** tab and a secondary **Device Information** tab.

This milestone should focus on structure, layout, and information placement. It should not add preview, capture, audio testing, V4L2 writes, arbitrary execution, or new hardware behavior.

## Product Intent

The GUI should help the user explore how a device works.

The sidebar answers:

> What device or group am I looking at?

The main pane answers:

> What do I want to do with it?

For Milestone 26, the main pane should consistently answer that question through two tabs:

```text
Explore
Device Information
```

The default tab should be **Explore**.

## Current Problem

The current selected-device view contains many report-like sections directly in the main pane, such as:

- Identity
- Summary
- Identity and Metadata
- Capabilities
- Candidate Pipelines
- Recommended Candidate
- Copy
- Safe Actions

This information is useful, but it has the wrong priority for the default user workflow.

The default view should not primarily answer:

> What did the backend discover?

It should answer:

> How do I start exploring this device?

## Scope

Milestone 26 should implement the selected-item tab structure.

Required scope:

- Add a tabbed main pane for selected items.
- Make **Explore** the first/default tab.
- Make **Device Information** the second tab.
- Move current report-style content into **Device Information**.
- Keep the **Explore** tab intentionally lightweight.
- Preserve existing sidebar selection behavior.
- Preserve demo mode and live mode behavior.
- Preserve existing camera explorer behavior as much as possible, but place it under the new tab structure.
- Preserve existing copy affordances where appropriate, but avoid crowding the Explore tab with report/debug copy buttons.
- Add or update tests for the new tab structure.

This is primarily a structural milestone.

## Out of Scope

Do not implement:

- camera preview
- camera capture
- audio input testing
- audio output testing
- group-based execution
- synchronized capture
- arbitrary pipeline execution
- arbitrary user-authored pipelines
- V4L2 control writes
- `v4l2-ctl --set-ctrl`
- package installation
- system configuration changes
- remote behavior
- major backend model redesign
- service-layer redesign beyond small helper extraction if necessary

## Explore Tab

The **Explore** tab is the default working surface.

For Milestone 26, it does not need to be the final polished Explore experience. That work can continue in Milestone 27.

The first version should establish the pattern:

- compact selected-item summary
- primary exploration widget for the selected item when available
- generated pipeline area when already supported
- a small number of practical actions, such as copying the selected generated pipeline
- no large raw report sections

For cameras, the Explore tab may contain the existing camera explorer pane, including:

- format selection
- size selection
- frame duration / FPS selection
- generated pipeline
- dynamic read-only controls

For audio input/output endpoints, if no specialized explorer exists yet, the Explore tab may show a compact placeholder explaining that audio Explore views are planned.

For groups, if no specialized group Explore view exists yet, the Explore tab may show a compact placeholder or simple endpoint summary. The full group dashboard is deferred to Milestone 29.

## Device Information Tab

The **Device Information** tab is the secondary accounting view.

Move or preserve report-style sections here, such as:

- Identity
- Summary
- Identity and Metadata
- Capabilities
- Candidate Pipelines
- Recommended Candidate
- Copy
- Safe Actions
- Diagnostics
- grouping metadata when relevant

The Device Information tab may still use the existing report/detail widgets internally. The goal is not to rewrite all information rendering yet. The goal is to put that information in the correct place.

## Behavior Requirements

- Selecting a sidebar item should update both tabs for that item.
- The Explore tab should be selected by default when a new item is selected.
- The GUI should still work in demo mode.
- The GUI should still work in live mode.
- Existing safe boundaries must remain unchanged.
- Existing tests should continue to pass.
- New tests should verify that selected-item pages contain the expected tab labels.
- New tests should verify that report-style sections are no longer in the default Explore surface when practical.
- Tests should avoid relying on physical hardware.

## Implementation Guidance

Prefer small, reversible changes.

Likely implementation areas:

- `src/gst_device_explorer/gui/qt_detail.py`
- existing GUI tests under `tests/`
- possibly small helper widgets if they keep files from growing too large

Do not turn this into a large service-layer refactor. That is deferred to Milestone 39.

If a file becomes too large, pause and consider extraction.

Python file guidance:

- Keep Python files around 250 to 300 lines when practical.
- If a file grows past that range, review whether it has too many responsibilities.
- If a file exceeds 400 lines, explicitly review whether to split it before adding more behavior.

Possible extraction targets:

- tab container widget
- Explore tab builders
- Device Information tab builders
- compact summary helpers
- report-section placement helpers

## Implementation Summary

Implemented the selected-item main pane as a two-tab Qt widget:

```text
Explore
Device Information
```

The **Explore** tab is first and is reset as the active tab every time a selected item is rendered. This means sidebar selection changes return the user to the working surface for the newly selected item.

For cameras, **Explore** renders the existing camera explorer surface:

- pixel format selection
- image size selection
- frame duration / FPS selection
- generated GStreamer pipeline
- copy pipeline action
- dynamic read-only V4L2 controls

For groups and audio endpoints, **Explore** now shows lightweight deferred placeholders rather than report-style sections. Specialized group, audio input, and audio output explorers remain deferred.

The **Device Information** tab preserves the existing report-style material:

- Identity
- Summary
- Identity and Metadata
- Capabilities
- Candidate Pipelines
- Recommended Candidate
- Copy
- Safe Actions
- diagnostics and grouping sections where present

Toolkit-neutral helper functions were added so tests can verify tab labels and tab content placement without requiring physical hardware or a display.

`src/gst_device_explorer/gui/qt_detail.py` was already above the 400-line review threshold before this milestone. A split is warranted soon, but this milestone kept the edit localized so the tab redesign remained small and reversible. Widget extraction remains deferred to the service/widget cleanup work already noted below.

## Files Changed

- `src/gst_device_explorer/gui/qt_detail.py`
  - Added `QTabWidget` selected-item rendering.
  - Added `Explore` and `Device Information` tab labels.
  - Moved camera explorer rendering into the default Explore tab.
  - Moved report-style rendering into Device Information.
  - Added lightweight placeholders for group and audio Explore tabs.
  - Added headless helper text functions for tab-placement tests.
- `tests/test_gui_detail_pane.py`
  - Added tests for tab labels.
  - Added tests that camera explorer content appears in Explore.
  - Added tests that report-style content appears in Device Information.
  - Added tests that group and audio Explore tabs remain lightweight placeholders.
- `pyproject.toml`
  - Bumped version to `0.26.0`.
- `src/gst_device_explorer/__init__.py`
  - Bumped `__version__` to `0.26.0`.
- `uv.lock`
  - Bumped editable package version to `0.26.0`.
- `tests/test_support_bundle.py`
  - Updated version-sensitive expectations to `0.26.0`.
- `README.md`
  - Updated JSON envelope examples to `0.26.0`.
- `docs/milestones/MILESTONE_26.md`
  - Recorded implementation details, tests, version notes, safety boundaries, and deferred work.

## Tests Run

Run the full test suite:

```sh
cd ~/gst-device-explorer
/home/jim/.local/bin/uv run python -m pytest
```

Pre-version-bump full suite:

```text
561 passed in 1.39s
```

Post-version-bump full suite:

```text
561 passed in 1.44s
```

Targeted GUI tests:

```text
33 passed in 0.10s
```

Qt offscreen smoke test:

```text
2 Explore Device Information 0
```

The smoke test confirms the concrete Qt detail widget has two tabs and defaults to tab index `0`, **Explore**.

## Documentation

Updated `docs/milestones/MILESTONE_26.md` as the milestone record.

`docs/GUI_INFORMATION_ARCHITECTURE.md` already describes the intended `Explore` and `Device Information` structure from Milestone 25, so no additional architecture-document change was needed for this structural implementation step.

## Versioning

Version bumped from `0.25.0` to `0.26.0` after implementation and a passing full test run.

## Acceptance Criteria

Milestone 26 is complete when:

- selected-item main pane uses a tabbed interface
- the first/default tab is **Explore**
- the second tab is **Device Information**
- report-style content is moved out of the default view
- camera exploration still works under the new structure
- groups and audio endpoints have safe, non-misleading Explore behavior even if specialized views are deferred
- demo mode and live mode remain functional
- no new execution behavior is added
- safety boundaries remain intact
- tests pass
- milestone documentation is updated

## Safety Boundaries

Preserve these boundaries:

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

## Deferred to Later Milestones

Deferred work includes:

- Milestone 27 — Camera Explore Tab Cleanup
- Milestone 28 — Camera Device Information Tab
- Milestone 29 — Group Explore View
- Milestone 30 — Group Device Information Tab
- Milestone 31 — Audio Input Explore Tab
- Milestone 32 — Audio Output Explore Tab
- Milestone 34 — Reports Area
- Milestone 35 — Preview Policy and Dry-Run UX
- Milestone 36 — Camera Preview Implementation
- Milestone 39 — Service-Layer Cleanup
