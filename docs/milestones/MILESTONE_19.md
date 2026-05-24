# Milestone 19 — GUI Product Scope and Application Model

## Status

Completed.

## Theme

Reset the project around the GUI as the primary product direction.

`gst-device-explorer` has accumulated a strong CLI and core backend: discovery, grouping, diagnostics, recommendations, reports, support bundles, safe execution, and bounded capture. That work is useful, but the project has drifted away from the original goal: a richer graphical media device explorer inspired by `camera-caps`, expanded to audio input, audio output, and composite devices.

Milestone 19 re-anchors the project around the GUI and defines the application model needed for a sidebar/main-pane experience.

## Product Direction

The GUI is now the primary product direction.

The CLI remains valuable as:

- a backend/debug surface
- a validation surface
- a scriptable probe interface
- a way to test core models without GUI dependencies

But future work should be judged by whether it improves the GUI media exploration experience.

## Target Experience

The target GUI shape is a two-pane application:

```text
┌────────────────────────────────────────────────────────────┐
│ gst-device-explorer                                       │
├───────────────────────┬────────────────────────────────────┤
│ Sidebar               │ Main Detail Pane                   │
│                       │                                    │
│ ▾ Composite Device    │ Selected: Camera /dev/video0       │
│   📷 Camera           │                                    │
│   🎙 Microphone        │ Capabilities                       │
│   🔊 Speaker           │ Candidate Pipelines                │
│                       │ Diagnostics                        │
│ ▸ USB Camera          │ Controls                           │
│ ▸ Built-in Audio      │                                    │
│                       │ [Preview] [Dry Run] [Copy]         │
└───────────────────────┴────────────────────────────────────┘
```

The sidebar represents discovered devices and groups. Groups expand into constituent components. Selecting an item in the sidebar populates the main pane with details and safe controls for that item.

## Scope

Milestone 19 is a product and model milestone, not a full GUI implementation milestone.

Implement or document:

- `docs/GUI_PRODUCT_SCOPE.md`
- this milestone document
- a GUI-facing application model, if implementation is included
- sidebar node model
- selected-item detail pane model
- safe GUI action model
- mapping from existing backend concepts to GUI concepts
- tests for model construction, if implementation is included

Possible implementation location:

```text
src/gst_device_explorer/gui/model.py
```

or:

```text
src/gst_device_explorer/core/gui_model.py
```

The exact path can be chosen during implementation, but the model should remain toolkit-independent.

## GUI-Facing Concepts

### MediaExplorerSnapshot

Represents the current GUI-facing system snapshot.

Possible fields:

- generated timestamp
- sidebar roots
- selected node id, if any
- summary status

### SidebarNode

Represents one item in the sidebar tree.

Possible fields:

- id
- label
- kind
- status
- children
- target kind
- target identifier
- relationship to a group, if applicable

Example node kinds:

```text
overview
composite_groups_root
composite_group
cameras_root
camera_endpoint
audio_inputs_root
audio_input_endpoint
audio_outputs_root
audio_output_endpoint
```

### DetailPaneModel

Represents the main pane for the selected sidebar node.

Possible fields:

- selected id
- title
- kind
- summary lines
- sections
- actions
- diagnostics summary

### DetailSection

Represents a section of the detail pane.

Possible section kinds:

- summary
- capabilities
- metadata
- candidates
- diagnostics
- grouping_evidence
- suggested_next_steps

### GuiAction

Represents a button or user action in the GUI.

Possible fields:

- id
- label
- action kind
- enabled flag
- safety classification
- related `SuggestedCommand`, if applicable
- disabled reason

GUI actions should map to existing generated candidates, suggested commands, or bounded backend actions. They must not create an arbitrary execution surface.

## Detail Pane Requirements

### Group Detail Pane

Should show:

- group identity
- grouping evidence
- constituent endpoints
- endpoint status summary
- group validation status, when available
- missing elements aggregated across endpoints, when available
- suggested next actions

Allowed controls:

- refresh group
- validate group
- copy summary
- export report or support bundle, if backed by existing safe functionality

Not allowed:

- group-based pipeline execution
- synchronized capture
- automatic endpoint selection for execution

### Camera Detail Pane

Should show:

- device path
- card, driver, bus, and sysfs metadata where available
- supported formats
- supported resolutions
- supported frame rates
- generated preview candidates
- recommended candidate
- candidate diagnostics
- missing GStreamer elements

Allowed controls:

- preview using a generated candidate
- dry run
- copy generated pipeline or command
- short bounded capture
- show diagnostics

### Audio Input Detail Pane

Should show:

- ALSA endpoint identifier
- card and device metadata where available
- generated audio input candidates
- recommended test or capture candidate
- candidate diagnostics
- missing GStreamer elements

Allowed controls:

- input test using a generated candidate
- short bounded WAV capture
- dry run
- copy generated pipeline or command
- show diagnostics

### Audio Output Detail Pane

Should show:

- ALSA endpoint identifier
- card and device metadata where available
- generated audio output candidates
- recommended speaker test candidate
- candidate diagnostics
- missing GStreamer elements

Allowed controls:

- speaker test using a generated candidate
- dry run
- copy generated pipeline or command
- show diagnostics

## Safety Boundaries

Preserve existing project safety boundaries.

Allowed:

- local discovery
- endpoint inspection
- group inspection
- generated safe preview/test actions
- generated bounded capture actions
- dry-run display
- copying generated commands
- report/support bundle export

Disallowed:

- arbitrary raw pipeline execution
- user-authored pipeline scripts
- plugin execution
- remote execution
- background workflows
- hidden retries
- package installation
- system configuration changes
- group-based execution
- synchronized multi-endpoint capture
- Reachy-specific hard-coding
- JetPack-version-specific hard-coding

## Out of Scope

Milestone 19 does not implement:

- a full GUI shell
- live preview widgets
- camera preview
- audio test controls
- capture file dialogs
- PySide6 packaging
- GUI process management
- GUI theme/polish
- MCP integration
- agent descriptors
- GUI plugin systems
- server mode
- remote support workflows

Those belong to later milestones.

## Recommended Follow-On Milestones

```text
20. Minimal GUI Shell
21. Sidebar Device/Group Tree
22. Endpoint Detail Panes
23. Safe GUI Actions
24. Camera Preview and Audio Test UX
25. Reachy Mini-Style Composite Device Validation
26. Packaging and Demo Documentation
```

## Completion Criteria

Milestone 19 is complete when:

- [x] `docs/GUI_PRODUCT_SCOPE.md` exists and clearly defines the GUI-first product direction.
- [x] The milestone document explains the sidebar/main-pane interaction model.
- [x] The milestone document identifies group, camera, audio input, and audio output detail panes.
- [x] The safe GUI action model is defined.
- [x] The out-of-scope list explicitly pauses unrelated infrastructure expansion.
- [x] GUI-facing models are toolkit-independent and covered by synthetic tests.
- [x] No GUI toolkit dependency is introduced.
- [x] No execution, capture, subprocess, or arbitrary pipeline behavior is added.
- [x] Version metadata is bumped to `0.19.0`.

## Validation Guidance

If implementation is included, normal test execution should remain:

```sh
/home/jim/.local/bin/uv run python -m pytest
```

Tests should not require real hardware or a graphical desktop.

## Notes

This milestone is intentionally corrective. It exists to prevent the project from drifting farther into infrastructure work before a tangible GUI exists.

The north star for the next phase is a useful local GUI screenshot, not another backend schema.

## Implementation Summary

Milestone 19 adds `src/gst_device_explorer/gui/` with frozen dataclasses for:

- `MediaExplorerSnapshot`
- `SidebarNode`
- `DetailPaneModel`
- `DetailSection`
- `GuiAction`
- `GuiActionResult`

It also adds pure builder functions for:

- sidebar tree construction
- group detail panes
- video detail panes
- audio input detail panes
- audio output detail panes
- unknown/empty selection fallback panes
- full media explorer snapshots

The builders consume existing core models and `SuggestedCommand` metadata. They
do not perform discovery, execute pipelines, capture media, start subprocesses,
or import a GUI/web toolkit.

Synthetic tests live in `tests/test_gui_model.py`.
