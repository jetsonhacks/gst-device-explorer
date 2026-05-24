# Milestone 15 — Interactive TUI Review Mode

Status: Implemented

## Theme

Add a read-only terminal user interface for reviewing discovered media-system information.

The project now has structured core models, broad JSON envelope coverage, profiles, reports, diagnostics, recommendations, presets, and configuration inspection. The next useful step is to make that information easier to browse on a Jetson or Linux system without building a full GUI.

Milestone 15 should introduce a conservative TUI review mode. It should help a user inspect what the tool already knows. It should not execute pipelines, capture media, edit configuration, or provide an arbitrary pipeline editor.

This milestone is about field review and navigation, not control.

## Current Context

The project is at version `0.14.0` after Milestone 14.

Implemented foundations include:

- device discovery
- video and audio pipeline candidate generation
- safe endpoint execution commands
- composite grouping
- diagnostics
- profiles
- system reports
- recommendations
- bounded capture tests
- group validation
- built-in presets
- bounded configuration inspection and validation
- JSON envelope coverage across major JSON outputs
- schema discovery for the shared JSON envelope and payload kinds

These features provide enough structured information to support a first interactive review surface.

## Guiding Principles

Continue to follow the project principles:

- Probe first, build later.
- Normalize raw system output into structured models before making decisions.
- Keep pipeline candidates as structured objects, not just strings.
- Treat CLI, JSON, future GUI, future TUI, and future agent integrations as renderers over shared core models.
- Prefer capability detection over hard-coded JetPack version checks.
- Avoid Reachy-specific behavior.
- Avoid arbitrary user-supplied pipeline execution.
- Keep grouping evidence-based and explainable.
- Keep each milestone narrow.
- Use synthetic tests where possible; do not require real hardware for normal tests.

Milestone-specific principles:

- TUI is a renderer/reviewer over existing commands and models.
- The first TUI should be read-only.
- No pipeline execution from the TUI.
- No capture from the TUI.
- No configuration editing from the TUI.
- No package installation or system changes.
- No arbitrary command entry.
- No hidden background workflows.
- No Reachy-specific UI.
- No JetPack-version-specific behavior.
- Keep the first interaction model simple enough to test.

## Desired Outcome

After this milestone, a user can run:

```sh
gst-device-explorer tui
```

and browse a read-only terminal interface showing a practical overview of the current media system.

The TUI should make it easier to inspect:

- environment summary
- discovered video devices
- discovered audio inputs
- discovered audio outputs
- composite groups
- profiles or suggested profile commands
- report summary
- schema kinds
- preset list
- configuration status

The first version does not need to show every detail from every command. It should establish a safe, useful, testable review shell.

## Proposed Scope

### Slice 1 — TUI Data Assembly Boundary

Create a small core or CLI-level data assembly layer for the TUI.

This layer should gather the same kinds of information used by existing commands, but it should avoid duplicating probing logic.

Possible model:

```text
TuiReviewModel
├── environment summary
├── video device summaries
├── audio input summaries
├── audio output summaries
├── composite group summaries
├── preset summaries
├── config status
└── schema kind summaries
```

The exact shape should follow existing models and serializers.

This model should be testable without requiring a real terminal UI.

### Slice 2 — Minimal Read-Only TUI Command

Add:

```sh
gst-device-explorer tui
```

The first screen may be simple:

```text
gst-device-explorer TUI

Environment
  GStreamer: available
  gst-launch-1.0: available
  gst-inspect-1.0: available

Devices
  Video: 1
  Audio inputs: 2
  Audio outputs: 2
  Composite groups: 1

Review Sections
  [1] Environment
  [2] Video Devices
  [3] Audio Inputs
  [4] Audio Outputs
  [5] Composite Groups
  [6] Presets
  [7] Configuration
  [8] Schemas

Press q to quit.
```

The first implementation can be keyboard-driven but should remain simple.

Acceptable navigation for the first slice:

- up/down or number keys to select sections
- enter to open a section
- escape/backspace to go back
- q to quit

If adding a full third-party TUI dependency is too much for this milestone, a minimal standard-library curses implementation is acceptable. If curses becomes awkward to test or support, consider a small internal screen/state abstraction with tests around state transitions.

### Slice 3 — Section Views

Implement a small set of read-only section views.

Minimum useful sections:

1. **Overview**
   - environment availability
   - device counts
   - group counts
   - config file status
   - schema/preset counts

2. **Devices**
   - video endpoints
   - audio input endpoints
   - audio output endpoints

3. **Groups**
   - composite group ids
   - group evidence summary
   - endpoint counts

4. **Presets**
   - built-in preset ids
   - descriptions
   - supported target kinds

5. **Configuration**
   - effective config path/status
   - defaults vs loaded config
   - validation errors, if any

6. **Schemas**
   - known schema/payload kinds
   - json-envelope availability

Do not try to reproduce every command’s full output in the first TUI. Prefer compact summaries and suggested next CLI commands.

### Slice 4 — Suggested Commands, Not Execution

Where useful, the TUI may display suggested CLI commands.

Examples:

```text
Suggested commands:
  gst-device-explorer report --json
  gst-device-explorer profile video /dev/video0
  gst-device-explorer pipeline video /dev/video0 --diagnostics
  gst-device-explorer preset command camera-preview video /dev/video0
```

The TUI must not execute those commands in Milestone 15.

This preserves the project’s safe command boundary.

### Slice 5 — Testing Strategy

Do not require real terminal interaction for normal tests.

Add tests for:

- TUI data assembly
- section list generation
- section rendering strings or line models
- navigation state transitions, if a state model is introduced
- command parser integration for `tui`
- graceful handling of no devices
- graceful handling of missing optional system tools
- no execution/capture side effects

If using curses or another TUI library, keep most logic outside the direct terminal rendering layer so tests can exercise it without opening a terminal.

Synthetic tests should remain the norm.

### Slice 6 — Documentation and Version Bump

Update documentation:

- `README.md`
- `docs/SETUP.md`
- `docs/ARCHITECTURE.md`
- `docs/DATA_MODEL.md`
- `docs/milestones/MILESTONE_15.md`

Documentation should make clear:

- TUI mode is read-only
- TUI mode does not run pipelines
- TUI mode does not capture media
- TUI mode does not edit configuration
- TUI mode summarizes existing discovery/profile/report/preset/config/schema information
- TUI mode suggests commands rather than executing them

Bump version to `0.15.0` in:

- `src/gst_device_explorer/__init__.py`
- `pyproject.toml`
- `uv.lock`

## Suggested Commands

Primary command:

```sh
gst-device-explorer tui
```

Optional future flags may be considered only if they remain simple:

```sh
gst-device-explorer tui --no-color
gst-device-explorer tui --snapshot
```

For Milestone 15, avoid adding flags unless needed for testability or basic terminal compatibility.

A `--snapshot` flag could be useful if it renders the initial TUI overview as plain text without entering interactive mode. However, this should only be added if it simplifies testing and documentation. It should not become a separate report system.

Implemented commands:

```sh
gst-device-explorer tui
gst-device-explorer tui --snapshot
```

The interactive command uses a thin standard-library curses runner. The snapshot
flag renders the same initial overview without entering interactive mode so
tests and smoke checks do not need a terminal.

## Expected Behavior

The TUI should:

- start safely
- show a useful overview
- allow basic navigation
- quit cleanly
- tolerate systems with no media devices
- tolerate missing optional tools
- suggest existing CLI commands
- avoid hidden side effects

The TUI should not:

- run GStreamer pipelines
- invoke `run`
- invoke `capture`
- edit config files
- install packages
- change system state
- execute arbitrary commands
- perform remote operations
- hide long-running probes behind navigation

## Completion Criteria

Milestone 15 is complete when:

- `gst-device-explorer tui` exists
- TUI mode is read-only
- TUI mode shows a useful overview of environment/devices/groups/presets/config/schema information
- TUI mode has at least a minimal section-navigation model
- TUI mode displays suggested commands rather than executing them
- logic is structured so most behavior can be tested without an interactive terminal
- synthetic tests cover the TUI data/view/state layer
- documentation is updated
- version is bumped to `0.15.0`
- full test suite passes

Implemented slices:

- Pure `TuiReviewModel`, `TuiSection`, and `TuiNavigationState` models.
- Deterministic overview and section line rendering.
- Minimal navigation for up/down, number keys, enter, escape/backspace, and quit.
- Thin curses terminal runner.
- Parser and CLI integration for `tui` and `tui --snapshot`.
- Synthetic tests for model rendering, no-device handling, navigation, parser
  integration, snapshot output, and no run/capture side effects.

## Non-Goals

Do not implement:

- pipeline execution from the TUI
- capture from the TUI
- preset execution from the TUI
- configuration editing from the TUI
- package installation
- system configuration changes
- arbitrary command entry
- arbitrary pipeline editing
- raw pipeline execution
- background workflows
- remote execution
- GUI mode
- web server mode
- MCP/tool descriptor generation
- user-authored workflow files
- plugin systems
- synchronized audio/video capture
- benchmarking
- Reachy-specific screens
- JetPack-version-specific screens

## Deferred Items

Possible future work:

- richer TUI navigation
- search/filter inside the TUI
- copy suggested command to clipboard, if safe and portable
- optional command execution prompts, if a later milestone explicitly scopes it
- profile detail drill-downs
- diagnostics detail drill-downs
- report viewer
- schema viewer
- config viewer with source annotations
- mouse support
- color themes
- accessibility/high-contrast mode
- GUI front end
- agent/tool descriptor generation

## Design Note

The TUI should feel like a field notebook, not a control panel.

It helps the user answer:

```text
What devices are present?
What groups were inferred?
What profiles and diagnostics are available?
What presets exist?
What does the config say?
What JSON payload kinds exist?
What command should I run next?
```

It should not answer:

```text
Should I run this pipeline for you?
Should I record media now?
Should I change your config?
Should I install missing packages?
```

Keeping that boundary clear makes the TUI useful without weakening the project’s safety model.
