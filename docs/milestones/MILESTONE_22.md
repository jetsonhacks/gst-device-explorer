# Milestone 22 — GUI Detail Pane Polish

Repository target path:

```text
docs/milestones/MILESTONE_22.md
```

Status: Completed

## Theme

Make the live PySide6 GUI more useful by improving the selected-item detail pane.

Milestones 19–21 established the GUI direction:

- Milestone 19 added a toolkit-neutral GUI application model.
- Milestone 20 added a PySide6 GUI shell with deterministic demo data.
- Milestone 21 added live read-only snapshot refresh from existing discovery/probe/profile/grouping paths.

Milestone 22 should improve what the user sees after selecting a group or endpoint in the sidebar. This milestone is still read-only. It should not introduce preview, capture, audio tests, process execution, or command execution.

The purpose is to make the GUI feel like a practical media explorer rather than a thin rendering of raw model fields.

## Product Goal

The GUI should help a Jetson/Linux user answer:

- What did the tool discover?
- What does this selected device or endpoint represent?
- What capabilities are available?
- What generated candidates are available or unavailable?
- What action would I try next?
- What is missing if something cannot work?
- What command or pipeline can I copy for terminal use?

The selected item in the sidebar should drive a clear, readable main-pane detail view.

## Scope

### 1. Detail Pane Layout Improvements

Improve the detail pane rendering so that selected items are easier to understand.

Possible sections:

- Header / identity
- Summary
- Capabilities
- Candidate pipelines
- Diagnostics
- Missing elements
- Suggested commands
- Safe actions
- Notes / limitations

The implementation may use standard PySide6 widgets such as labels, group boxes, tables, tree widgets, scroll areas, buttons, and read-only text widgets.

The detail pane does not need to be beautiful, but it should be organized and readable.

### 2. Group Detail Pane Polish

For selected composite groups, show:

- group ID
- group label/name
- group status if available
- grouping evidence
- constituent endpoints
- endpoint kinds:
  - video
  - audio input
  - audio output
- per-endpoint status summaries if available
- suggested next commands/actions

The group pane should reinforce that groups are informational. It must not imply group-based execution or synchronized capture.

### 3. Camera Detail Pane Polish

For selected video endpoints, show:

- device path
- driver/card/bus metadata when available
- supported formats
- resolutions
- frame rates when available
- candidate pipeline list
- recommended candidate when available
- candidate availability
- diagnostics/missing elements
- suggested commands/actions

The pane may use a table for formats and candidate pipelines.

### 4. Audio Input Detail Pane Polish

For selected audio input endpoints, show:

- ALSA device identifier
- card/device metadata when available
- available generated input/test/capture candidates
- recommended candidate when available
- diagnostics/missing elements
- suggested commands/actions

### 5. Audio Output Detail Pane Polish

For selected audio output endpoints, show:

- ALSA device identifier
- card/device metadata when available
- available generated output/test candidates
- recommended candidate when available
- diagnostics/missing elements
- suggested commands/actions

### 6. Copy Affordances

Add safe copy-to-clipboard affordances for display-only information, such as:

- suggested command strings
- generated pipeline command strings
- selected endpoint identifiers
- selected group IDs

Copy buttons are allowed because they do not execute anything.

When something is copied, show a small status message in the GUI, such as the window status bar.

### 7. Empty, Loading, and Error States

Improve empty/loading/error detail panes:

- no devices discovered
- refresh failed
- selected item no longer exists after refresh
- unknown detail pane fallback
- GUI extra not installed should remain a CLI-level error if applicable

Messages should be user-oriented, not stack traces.

## Commands

Existing commands remain:

```sh
gst-device-explorer gui
gst-device-explorer gui --demo
```

No new command is required for this milestone.

## HIL / Manual Testing

A hardware-in-the-loop environment is available for manual validation.

Normal automated tests should remain synthetic and hardware-free.

Manual validation commands:

```sh
/home/jim/.local/bin/uv sync --extra gui
/home/jim/.local/bin/uv run gst-device-explorer gui --demo
/home/jim/.local/bin/uv run gst-device-explorer gui
```

Recommended HIL validation:

1. Launch the demo GUI.
2. Verify the sidebar shows grouped demo endpoints.
3. Select the demo group and verify a richer group detail pane.
4. Select the demo camera and verify camera-specific sections.
5. Select the demo audio input and output endpoints and verify audio-specific sections.
6. Test copy buttons for suggested commands or pipeline text.
7. Launch the live GUI on a Jetson/Linux system.
8. Verify live discovered devices render without crashing.
9. Refresh and verify selection preservation still works when possible.
10. Confirm no preview, capture, audio test, or command execution occurs.

## Safety Boundaries

This milestone must preserve the existing GUI safety boundaries:

- No camera preview.
- No audio input test.
- No audio output test.
- No media capture.
- No pipeline execution.
- No suggested-command execution.
- No arbitrary subprocess execution.
- No arbitrary user-supplied pipeline strings.
- No system configuration changes.
- No package installation.
- No remote behavior.
- No group-based execution.
- No synchronized capture.

GUI buttons in this milestone may copy text or change the visible pane. They must not run generated commands.

## Testing Expectations

Add or update synthetic tests for:

- detail pane rendering helpers where practical
- copyable command/action metadata
- empty/error/unknown state rendering
- GUI shell imports remain safe for CLI-only use
- demo snapshot still renders
- live snapshot refresh still renders
- no subprocess execution from detail pane actions
- no capture/preview/test side effects

Automated tests should not require Qt display access unless they are already protected/skipped appropriately in headless environments.

## Documentation Updates

Update:

- `README.md`
- `docs/SETUP.md`
- `docs/ARCHITECTURE.md`
- `docs/GUI_PRODUCT_SCOPE.md`
- `docs/milestones/MILESTONE_22.md`

Documentation should describe the GUI as a read-only explorer at this stage, with copy-only action affordances.

## Completion Criteria

Milestone 22 is complete when:

- [x] selecting a group shows an improved group detail pane
- [x] selecting a video endpoint shows an improved camera detail pane
- [x] selecting an audio input endpoint shows an improved microphone/input detail pane
- [x] selecting an audio output endpoint shows an improved speaker/output detail pane
- [x] copy buttons/affordances exist for safe display-only strings
- [x] empty/error/unknown states are cleaner
- [x] demo mode continues to work
- [x] live mode continues to work
- [x] tests pass
- [x] no execution, preview, capture, or audio test behavior is introduced
- [x] documentation is updated
- [x] version is bumped to `0.22.0`

## Deferred

Explicitly deferred:

- camera preview
- embedded video preview widgets
- audio input test controls
- audio output test controls
- media capture dialogs
- process lifecycle controls
- safe GUI execution
- group-based execution
- synchronized capture
- support bundle GUI
- screenshots/demo docs
- packaging/installers
- GUI theming/polish beyond basic readability

## Implementation Summary

Milestone 22 improves `src/gst_device_explorer/gui/qt_detail.py` with organized
identity, summary, table-style section rendering, safe-action metadata, and copy
affordances for displayed identifiers and suggested commands. Copy actions use
the local clipboard and status bar only; they do not execute commands.

Group detail panes now include an explicit notes/limitations section explaining
that composite groups are informational and that group-based execution and
synchronized capture are unavailable.

Synthetic tests in `tests/test_gui_detail_pane.py` cover group, video, audio
input, audio output, empty/error/unknown rendering helpers, copy affordances,
and subprocess-free detail behavior.

Manual HIL validation was not required for automated completion. Suggested
manual commands remain:

```sh
/home/jim/.local/bin/uv sync --extra gui
/home/jim/.local/bin/uv run gst-device-explorer gui --demo
/home/jim/.local/bin/uv run gst-device-explorer gui
```
