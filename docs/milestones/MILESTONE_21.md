# Milestone 21 — Live GUI Snapshot Refresh

Status: Completed

## Theme

Make the PySide6 GUI useful with real discovered devices while preserving the safe, metadata-only GUI action model.

Milestone 20 introduced a launchable GUI shell that renders a deterministic demo `MediaExplorerSnapshot`. Milestone 21 connects that shell to the existing discovery/profile/grouping backend so the GUI can refresh and display the current system state.

This milestone should remain focused on **refreshing and rendering live discovery data**. It should not add preview, audio testing, capture, pipeline execution, or process lifecycle controls.

## Product Goal

The GUI should begin to behave like the intended product:

- open the application
- see discovered media devices and groups in the sidebar
- expand groups into constituent endpoints
- select a group or endpoint
- see details, diagnostics, and safe suggested actions in the main pane
- refresh the view after devices are plugged in or removed

The GUI is still a media explorer, not a control panel.

## User-Facing Commands

Existing commands remain:

```sh
gst-device-explorer gui
gst-device-explorer gui --demo
```

Expected behavior:

- `gst-device-explorer gui --demo` continues to show deterministic synthetic data.
- `gst-device-explorer gui` builds a live GUI snapshot from existing probe/discovery functions.
- The GUI provides a visible refresh control.
- Refresh updates the sidebar and detail pane from newly discovered data.

## Scope

### Add live GUI snapshot building

Add a GUI-facing live snapshot builder that uses existing core/CLI discovery paths to produce a `MediaExplorerSnapshot`.

Possible location:

```text
src/gst_device_explorer/gui/live.py
```

The live builder should reuse existing project functions where practical. Avoid duplicating device discovery logic in the GUI layer.

The live builder may gather:

- GStreamer environment summary
- V4L2 video devices/capabilities
- ALSA audio input endpoints
- ALSA audio output endpoints
- composite device groups
- endpoint profiles/details where already available
- suggested actions as metadata only

### Add refresh controller behavior

Add a narrow refresh path for the GUI shell.

Possible responsibilities:

- build live snapshot
- update sidebar tree
- update detail pane
- preserve or safely reset selection
- show loading state
- show error state if probing fails

The refresh implementation should be easy to test without launching Qt when possible.

### Preserve demo mode

Demo mode is important for deterministic testing and screenshots.

Requirements:

- `gst-device-explorer gui --demo` must not probe real hardware.
- demo snapshot data must remain deterministic.
- demo mode should still render grouped camera/audio endpoints.

### Add loading and error states

The GUI should have a reasonable visual response when live refresh starts or fails.

Possible states:

- loading detail pane: “Refreshing devices…”
- empty state: “No media devices discovered.”
- error detail pane: clear error summary and suggested next action

Avoid exposing raw stack traces in the primary GUI view. Detailed exception text may be logged or shown in a diagnostic section if useful.

### Keep GUI actions as metadata only

Buttons may be rendered, disabled, or display command text, but they must not run anything in this milestone.

Allowed:

- display action labels
- display safety metadata
- display suggested command text
- copy command/pipeline text if already implemented safely, or defer it

Not allowed:

- run preview pipeline
- test speaker
- record microphone
- capture video/audio
- launch subprocesses
- execute `SuggestedCommand`
- run preset workflows

## Suggested Implementation Shape

### Possible files

New or modified files may include:

```text
src/gst_device_explorer/gui/live.py
src/gst_device_explorer/gui/qt_app.py
src/gst_device_explorer/gui/qt_main_window.py
src/gst_device_explorer/gui/qt_sidebar.py
src/gst_device_explorer/gui/qt_detail.py
tests/test_gui_live_snapshot.py
tests/test_gui_shell.py
README.md
docs/SETUP.md
docs/GUI_PRODUCT_SCOPE.md
docs/ARCHITECTURE.md
docs/milestones/MILESTONE_21.md
pyproject.toml
src/gst_device_explorer/__init__.py
uv.lock
```

### Suggested model/controller seam

Prefer a seam like:

```python
build_live_media_explorer_snapshot() -> MediaExplorerSnapshot
```

and, if helpful:

```python
build_loading_detail_pane() -> DetailPaneModel
build_error_detail_pane(message: str, details: str | None = None) -> DetailPaneModel
build_empty_snapshot() -> MediaExplorerSnapshot
```

The Qt layer should mostly render `MediaExplorerSnapshot` and `DetailPaneModel`, not own discovery policy.

## Testing Requirements

Normal automated tests should remain synthetic and not require hardware, a desktop session, or Qt display server.

Add tests for:

- live snapshot builder can be exercised with mocked discovery inputs
- demo mode does not call live probing
- refresh controller updates the current snapshot
- refresh failure produces an error detail pane/model
- empty discovery produces a useful empty state
- sidebar stable IDs remain deterministic where possible
- GUI action metadata remains non-executable
- no subprocess execution is introduced by GUI refresh tests
- CLI parser still accepts `gui` and `gui --demo`
- CLI-only test runs do not require importing PySide6 unless GUI launch code is exercised

Run:

```sh
/home/jim/.local/bin/uv run python -m pytest
```

If GUI dependencies are needed for targeted shell tests:

```sh
/home/jim/.local/bin/uv sync --extra gui
/home/jim/.local/bin/uv run python -m pytest tests/test_gui_shell.py
```

## HIL / Manual Validation

A HIL system is available for manual GUI validation.

HIL validation is encouraged but must not be required for the normal automated test suite.

Suggested manual checks on a GUI-capable Jetson/Linux desktop session:

```sh
/home/jim/.local/bin/uv sync --extra gui
/home/jim/.local/bin/uv run gst-device-explorer gui --demo
/home/jim/.local/bin/uv run gst-device-explorer gui
```

Manual HIL checklist:

- demo GUI launches
- live GUI launches
- sidebar shows discovered cameras/audio endpoints/groups when present
- groups expand into constituent endpoints
- selecting a group updates the detail pane
- selecting a camera updates the detail pane
- selecting an audio input updates the detail pane
- selecting an audio output updates the detail pane
- refresh updates the tree without crashing
- unplug/replug behavior is reasonable if practical to test
- displayed actions do not execute anything
- closing the window exits cleanly

Document any HIL observations in the milestone doc or SETUP notes if useful.

## Safety Boundaries

Preserve all existing safety boundaries:

- no arbitrary raw pipeline execution
- no pipeline execution from GUI buttons
- no media capture
- no audio test playback/recording
- no subprocess calls from GUI actions
- no suggested-command execution
- no user-authored pipeline strings
- no package installation
- no system configuration changes
- no remote execution
- no background workflows
- no Reachy-specific hard-coding
- no JetPack-version-specific hard-coding

Live probing may use existing safe discovery/probe paths already present in the project.

## Documentation Updates

Update documentation to explain:

- `gst-device-explorer gui` now shows live discovered devices
- `gst-device-explorer gui --demo` remains deterministic
- PySide6 remains an optional dependency via `uv sync --extra gui`
- refresh is read-only
- GUI actions are still metadata-only in this milestone
- HIL/manual validation procedure

## Version

Bump version to:

```text
0.21.0
```

Update:

- `pyproject.toml`
- `src/gst_device_explorer/__init__.py`
- any tests that assert the current version
- `uv.lock`

## Completion Criteria

Milestone 21 is complete when:

- [x] `gst-device-explorer gui --demo` still launches deterministic demo mode
- [x] `gst-device-explorer gui` builds and renders a live snapshot from existing discovery functions
- [x] GUI includes a refresh control
- [x] refresh updates the sidebar/detail model
- [x] loading/empty/error states are represented cleanly
- [x] GUI actions remain display metadata only
- [x] normal automated tests pass without HIL or desktop requirements
- [x] HIL/manual GUI validation instructions are documented
- [x] version is bumped to `0.21.0`

## Deferred

Explicitly deferred:

- camera preview widgets
- audio input test UI
- audio output test UI
- video/audio capture dialogs
- process lifecycle controls
- safe GUI execution of generated candidates
- copy-to-clipboard polish if not already trivial
- support bundle GUI
- screenshots/demo docs
- packaging/installers
- GUI preferences
- group-based execution
- synchronized capture
- plugin/server/MCP surfaces

## Implementation Summary

Milestone 21 adds `src/gst_device_explorer/gui/live.py`, which builds live GUI
snapshot bundles from existing safe discovery, probe, profile, grouping,
ranking, and validation layers. It also provides loading, empty, and error
models for refresh states.

The PySide6 shell now has a visible Refresh toolbar action. Refresh rebuilds the
current snapshot, repopulates the sidebar, preserves the selected node where
possible, and renders a safe fallback if discovery fails. Demo mode keeps using
deterministic synthetic data and does not probe real hardware.

Synthetic tests cover mocked live discovery, empty/error states, selected-node
preservation, demo/live command separation, and metadata-only action behavior.
HIL/manual validation was not required for automated completion; the documented
manual commands remain:

```sh
/home/jim/.local/bin/uv sync --extra gui
/home/jim/.local/bin/uv run gst-device-explorer gui --demo
/home/jim/.local/bin/uv run gst-device-explorer gui
```
