# Milestone 25 — Product and GUI Structure Reset

Status: **Implemented**

Version: `0.25.0`

## Purpose

Milestone 25 pauses feature momentum and resets `gst-device-explorer` around a clearer product shape before additional GUI implementation continues.

The backend now has substantial and valuable infrastructure:

- GStreamer environment probing
- V4L2 video capability probing
- ALSA input/output discovery
- video pipeline candidate generation
- audio input/output pipeline candidate generation
- safe execution paths for selected generated candidates
- diagnostics
- recommendations
- composite device grouping
- profiles
- system reports
- support bundles
- JSON envelopes and error envelopes
- structured suggested commands
- PySide6 GUI shell
- live GUI refresh
- sidebar device/group browsing
- camera explorer pane
- dynamic read-only V4L2 controls

That infrastructure remains valuable, but the GUI should not drift toward rendered report output. The application should feel like a media hardware exploration tool.

## Current Problem

The current selected-device page presents sections such as:

- Identity
- Summary
- Identity and Metadata
- Capabilities
- Candidate Pipelines
- Recommended Candidate
- Copy
- Safe Actions

These are mostly report functions. Some of this data should be summarized on the default exploration page, but most of it belongs in a secondary information view, diagnostics area, reports area, or command-reproduction section.

The default view should answer:

> How do I explore and try this device?

It should not primarily answer:

> What did the backend discover?

## Product Direction

`gst-device-explorer` is a GUI-first media endpoint explorer for Jetson and Linux systems.

The application should help a user:

- discover connected cameras, microphones, speakers, and grouped physical devices
- select hardware capabilities through a GUI instead of manually reading command-line probe output
- generate useful GStreamer commands from selected settings
- preview or test selected configurations only when explicitly supported by a scoped milestone
- inspect lower-level device information when needed
- reproduce the same investigation from the CLI when desired

The main GUI distinction is:

```text
Explore = work with the selected device
Device Information = understand the selected device
```

## Deliverables

Created:

- `docs/APP_PRODUCT_SPEC.md`
- `docs/GUI_INFORMATION_ARCHITECTURE.md`

Updated:

- `docs/milestones/MILESTONE_25.md`

Version updated from `0.24.0` to `0.25.0` in:

- `pyproject.toml`
- `src/gst_device_explorer/__init__.py`
- `uv.lock`
- `tests/test_support_bundle.py`
- `README.md`

## Acceptance Criteria

Milestone 25 is complete when:

- the product direction is written down clearly
- the one-sentence product definition is documented
- primary and secondary users are defined
- the main first-run workflow is defined
- what the application is and is not are documented
- core device concepts are defined:
  - camera endpoint
  - audio input endpoint
  - audio output endpoint
  - composite group
- the distinction between exploration, information, reports, diagnostics, and commands is explicit
- the sidebar plus tabbed-main-pane structure is described
- the default selected-device tab is specified as Explore
- the Explore and Device Information tab roles are described
- camera Explore and Camera Device Information contents are defined
- group Explore behavior is described as endpoint dashboarding, not group-based execution
- reports, diagnostics, and command-reproduction information are assigned to secondary areas
- default Explore tabs are protected from raw report output
- development principles are documented, including first-principles work and Python file size review guidance
- safety boundaries are preserved
- full tests are run and the result is recorded

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

Safe read-only discovery, copy-to-clipboard behavior, and generated command rendering remain allowed.

## Implementation Notes

This milestone is design/specification oriented. It deliberately does not perform a large GUI rewrite.

The new product specification defines the application as a GUI-first media endpoint explorer and separates exploration, information, reports, diagnostics, and commands.

The new GUI information architecture defines the intended main window structure:

```text
Main Window
├── Sidebar
│   ├── Groups
│   ├── Cameras
│   ├── Audio Inputs
│   └── Audio Outputs
└── Main Pane
    ├── Explore
    └── Device Information
```

The intended default behavior is:

- Sidebar selection chooses the group or endpoint.
- Main pane defaults to Explore.
- Explore focuses on working with the selected device.
- Device Information explains what was discovered.
- Reports and diagnostics remain available without dominating selected-device exploration.
- Command reproduction is separated from the default workflow except for the currently generated pipeline.

## Development Principles

Work from first principles.

Do not simply expose everything the backend already knows. Ask what the user is trying to do before exposing backend data.

Keep the default GUI focused on exploration.

Keep report, debug, and support data in secondary areas.

Do not make the GUI feel like rendered JSON or rendered CLI output.

Preserve grouping as evidence-based physical-device organization.

Do not introduce Reachy-specific hard-coding.

Do not add arbitrary pipeline execution.

Do not add preview, capture, or test behavior in this milestone.

Prefer small, reversible changes.

Python files should generally stay around **250 to 300 lines** when practical.

When a Python file grows beyond that range, review whether it has too many responsibilities.

When a Python file exceeds **400 lines**, stop and explicitly review whether it should be split before adding more behavior.

Line-count guidance is not arbitrary enforcement. It is a prompt to check separation of concerns.

## Deferred

- Main pane tab implementation.
- Camera Explore tab cleanup beyond the existing Milestone 24 work.
- Camera Device Information tab implementation.
- Group Explore view implementation.
- Group Device Information tab implementation.
- Audio input Explore redesign.
- Audio output Explore redesign.
- Commands and Reproduce sections.
- Reports or Diagnostics area.
- GUI preview policy.
- Camera preview implementation.
- Audio capture or speaker testing.
- V4L2 control writes.
- Any synchronized or group-based execution.

## Tests Run

Command:

```sh
/home/jim/.local/bin/uv run python -m pytest
```

Result:

```text
557 passed in 1.47s
```

The full suite was also run before the version bump and passed with `557 passed in 1.38s`.
