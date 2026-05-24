# Milestone 20 — Minimal PySide6 GUI Shell

Status: Completed

## Purpose

Milestone 20 turns the GUI-facing application model from Milestone 19 into a visible, launchable desktop shell.

The goal is not to build the full media explorer yet. The goal is to prove the project now has a concrete GUI direction: a PySide6 application with a sidebar for discovered devices and groups, and a main detail pane for the selected item.

This milestone should produce the first tangible screenshot of the project.

## Product Direction

`gst-device-explorer` is now a GUI-first media device explorer inspired by the original `camera-caps` idea, expanded to include:

- camera endpoints
- audio input endpoints
- audio output endpoints
- composite groups of related endpoints
- safe generated GStreamer-oriented actions
- diagnostic explanations

The CLI remains useful as a backend/debug interface, but the GUI is the primary product direction.

## Toolkit Decision

Milestone 20 uses **PySide6 / Qt** as the initial GUI toolkit.

Rationale:

- The desired interface is a conventional desktop utility.
- A tree sidebar maps naturally to Qt tree widgets/models.
- A split-pane layout maps naturally to Qt layout primitives.
- Future safe process execution can use Qt process/event primitives.
- PySide6 has LGPL licensing and is the official Qt for Python binding.
- The application model from Milestone 19 remains toolkit-neutral, so the backend should not become coupled to PySide6.

## High-Level User Experience

The first GUI shell should look conceptually like this:

```text
┌────────────────────────────────────────────────────────────┐
│ gst-device-explorer                                       │
├───────────────────────┬────────────────────────────────────┤
│ Devices / Groups      │ Detail Pane                        │
│                       │                                    │
│ ▾ Composite Group     │ Selected Item                      │
│   📷 Camera           │                                    │
│   🎙 Audio Input       │ Summary                            │
│   🔊 Audio Output      │ Sections                           │
│                       │ Actions                            │
│ ▸ Standalone Camera   │                                    │
└───────────────────────┴────────────────────────────────────┘
```

## Scope

Implement a minimal launchable PySide6 GUI shell that can render a `MediaExplorerSnapshot` produced by the GUI model layer.

The first shell should support:

- a main window
- a left sidebar representing `SidebarNode` objects
- expandable group nodes
- endpoint child nodes
- a right detail pane
- selecting a sidebar item updates the detail pane
- rendering `DetailPaneModel` content:
  - title
  - kind/status summary
  - sections
  - action metadata
- rendering actions as disabled or non-executing controls
- a synthetic/demo snapshot mode for deterministic tests and early screenshots
- a GUI launch command

Possible command:

```sh
gst-device-explorer gui
```

A temporary development/demo-only flag is acceptable if useful:

```sh
gst-device-explorer gui --demo
```

The exact CLI shape may be adjusted during implementation, but the milestone should avoid overbuilding.

## Hardware-in-the-Loop Availability

A hardware-in-the-loop environment is available for manual validation.

The implementation should still use synthetic automated tests for normal CI/development. HIL should be treated as a manual validation path, not a hard requirement for the test suite.

HIL validation may be used to confirm:

- the GUI launches on the target system
- the PySide6 dependency works on the target environment
- the window renders correctly on the Jetson desktop
- the sidebar/detail interaction works with a demo snapshot
- later, live device snapshots can be explored manually

Milestone 20 should not require HIL to pass automated tests.

## Non-Goals

Milestone 20 must not add:

- camera preview widgets
- audio playback controls
- audio recording controls
- media capture file dialogs
- GStreamer process lifecycle management
- subprocess execution from GUI buttons
- live probing inside the GUI event loop unless very narrowly scoped
- arbitrary user-supplied pipeline execution
- raw pipeline editor
- group-based execution
- synchronized capture
- support bundle GUI
- TUI work
- MCP/agent/server surfaces
- plugin systems

## Safety Boundaries

The GUI shell is a renderer over existing GUI model objects.

GUI action buttons in this milestone are metadata only. They may be displayed, but they must not execute commands, run pipelines, capture media, or spawn subprocesses.

The safe action rule remains:

```text
GUI displays generated safe actions before it executes anything.
```

Execution and process lifecycle behavior belong in a later milestone.

## Suggested Implementation Shape

Possible new package structure:

```text
src/gst_device_explorer/gui/
  __init__.py
  model.py              # existing Milestone 19 model/builders, if not already there
  qt_app.py             # QApplication entrypoint helpers
  qt_main_window.py     # main window layout
  qt_sidebar.py         # sidebar rendering/helpers
  qt_detail.py          # detail pane rendering/helpers
  demo.py               # deterministic demo snapshot builder
```

The exact module layout is flexible, but keep toolkit-specific code separate from toolkit-neutral model code.

## Dependency Handling

Add PySide6 as an explicit project dependency or optional dependency, whichever best fits the existing project structure.

If optional dependencies are used, prefer a clear install target such as:

```text
[project.optional-dependencies]
gui = ["PySide6"]
```

Then document the GUI install/run path.

Avoid importing PySide6 from non-GUI modules so CLI-only functionality does not require Qt imports at runtime.

## Automated Testing Expectations

Add synthetic tests where practical.

Possible coverage:

- GUI command parser accepts the selected command shape
- GUI command dispatch can be invoked in demo/headless-safe mode if feasible
- demo snapshot produces expected sidebar/detail data
- Qt-specific rendering helpers can be tested without showing a real window, if practical
- non-GUI imports do not require PySide6
- GUI action controls remain non-executing metadata
- no subprocess execution is triggered by rendering

Do not make automated tests depend on physical hardware, display server availability, or live media devices.

If Qt widget tests are brittle in the environment, keep automated tests focused on command wiring, demo snapshot generation, and model-to-view mapping helpers.

## Manual Validation

Suggested manual checks:

```sh
/home/jim/.local/bin/uv run python -m pytest
/home/jim/.local/bin/uv run gst-device-explorer gui --demo
```

On the HIL target, validate that the demo GUI launches and that selecting sidebar items updates the detail pane.

If live snapshot wiring is included, validate only inspection/rendering behavior. Do not add GUI execution behavior in this milestone.

## Documentation Updates

Update:

- `README.md`
- `docs/SETUP.md`
- `docs/ARCHITECTURE.md`
- `docs/GUI_PRODUCT_SCOPE.md`
- this milestone document

Document:

- PySide6 was selected for the first GUI shell
- the GUI is currently a shell over the GUI application model
- actions are displayed only and do not execute yet
- HIL is available for manual validation but not required for automated tests

## Completion Criteria

Milestone 20 is complete when:

- [x] PySide6 is selected and documented as the initial GUI toolkit
- [x] `gst-device-explorer gui` launch command exists
- [x] `gst-device-explorer gui --demo` deterministic demo mode exists
- [x] a minimal main window can be launched
- [x] the window has a sidebar and detail pane
- [x] the sidebar can render grouped device nodes from a `MediaExplorerSnapshot`
- [x] selecting an item updates the detail pane
- [x] action metadata is displayed but not executed
- [x] a deterministic demo snapshot is available for early screenshots/testing
- [x] tests pass without hardware
- [x] no GUI execution/capture/preview behavior is introduced
- [x] version is bumped to `0.20.0`

## Deferred

Deferred to later milestones:

- live device refresh in the GUI
- camera preview
- audio input level/testing UI
- audio output test UI
- safe GUI execution of generated actions
- process lifecycle controls
- capture file dialogs
- real grouped-device workflow validation
- GUI packaging
- screenshots and demo documentation

## Implementation Summary

Milestone 20 adds:

- optional PySide6 dependency via the `gui` extra
- `gst-device-explorer gui` and `gst-device-explorer gui --demo`
- deterministic GUI demo data in `src/gst_device_explorer/gui/demo.py`
- PySide6 launch/window/sidebar/detail modules under `src/gst_device_explorer/gui/`
- synthetic tests for parser wiring, demo determinism, sidebar/detail mapping,
  action metadata, and subprocess-free demo construction

The GUI shell is display-only. Buttons are rendered from `GuiAction` metadata,
but no button runs a pipeline, captures media, spawns a process, or executes a
suggested command.
