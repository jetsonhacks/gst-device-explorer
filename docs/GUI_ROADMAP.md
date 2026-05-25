# GUI Roadmap

This roadmap describes the proposed GUI-centered development path for `gst-device-explorer` after version 0.24.0.

The intent is to pause feature momentum and re-center the application around device exploration rather than report rendering. The existing discovery, probing, grouping, pipeline generation, diagnostics, and reporting code remains valuable, but the GUI should present a cleaner workflow for selecting, understanding, and testing media devices.

## Product Direction

`gst-device-explorer` should be treated as a GUI-first media endpoint explorer for Jetson and Linux systems.

The application should help a user:

- discover connected cameras, microphones, speakers, and grouped physical devices
- select hardware capabilities through a GUI instead of manual command-line probing
- generate useful GStreamer commands from selected settings
- preview or test selected configurations when explicitly supported
- inspect lower-level device information when needed
- reproduce the same investigation from the CLI when desired

The primary GUI distinction should be:

- **Explore**: work with the selected device
- **Device Information**: understand the selected device

Report-oriented data should not dominate the default view.

## Development Principles

Development should proceed from first principles rather than simply exposing whatever the backend already knows.

Each milestone should ask:

- What is the user trying to do?
- What device concept is being represented?
- What is the smallest useful interaction?
- What information must be visible now?
- What information belongs in a secondary view?
- What should remain internal, diagnostic, or support-only?

Python files should generally stay limited to about **250 to 300 lines**.

When a Python file grows beyond that range, it is usually a sign that the file is handling too many areas of concern. The implementation should be reviewed for clearer separation of responsibilities.

When a Python file exceeds **400 lines**, there should be an explicit review before continuing to add functionality to that file. The review should consider whether to split the file by responsibility, such as:

- UI widget construction
- application service logic
- model adaptation
- command generation
- formatting/rendering helpers
- process execution
- tests or fixtures

The goal is not to enforce an arbitrary line count. The goal is to keep the codebase understandable, testable, and easy to reshape as the product direction becomes clearer.

## Milestone 25 — Product and GUI Structure Reset

Define the application as a GUI-first media device explorer.

Establish:

- one-sentence product definition
- primary user
- main first-run workflow
- sidebar behavior
- selected-device tab structure
- group role
- what belongs in Explore views
- what belongs in Device Information views
- what remains report, diagnostic, or support infrastructure

This should be a design/spec milestone, not a feature milestone.

## Milestone 26 — Main Pane Tab Redesign

Refactor selected-device pages into a default **Explore** tab and a secondary **Device Information** tab.

The Explore tab should be the working surface for the selected device.

The Device Information tab should contain lower-level identity, metadata, capabilities, diagnostics, and command-reproduction information.

## Milestone 27 — Camera Explore Tab Cleanup

Make the camera page feel like a working control surface rather than rendered report output.

The page should prioritize:

- compact device summary
- pixel format selection
- image size selection
- frame duration / FPS selection
- generated GStreamer pipeline
- copy action
- dynamic read-only camera controls

The interaction model should follow the successful camera-caps direction while using cleaner layout and implementation practices.

## Milestone 28 — Camera Device Information Tab

Move report-style camera information into organized secondary sections.

Possible sections:

- identity
- hardware metadata
- raw V4L2 capabilities
- candidate pipelines
- recommended candidate
- diagnostics
- reproduce with CLI

This preserves the existing discovery work without making it the default user experience.

## Milestone 29 — Group Explore View

Make composite groups useful as physical-device dashboards.

For devices such as Reachy Mini, the group view should show endpoint cards for:

- camera
- microphone
- speaker
- any other discovered endpoints

Each card should summarize the endpoint and provide a clear action to explore that endpoint directly.

Group views should not imply group-based execution.

## Milestone 30 — Group Device Information Tab

Show why endpoints were grouped.

Possible sections:

- grouping evidence
- USB parent relationship
- ALSA card relationship
- endpoint metadata
- diagnostics
- reproduce with CLI

This should keep grouping evidence-based and explainable.

## Milestone 31 — Audio Input Explore Tab

Create a microphone-oriented explorer.

The page should include:

- compact device summary
- supported formats
- supported sample rates
- supported channel counts
- generated input pipeline
- copy action
- placeholder area for future level or capture testing

The first version should avoid overbuilding audio controls until the interaction model is validated.

## Milestone 32 — Audio Output Explore Tab

Create a speaker-oriented explorer.

The page should include:

- compact device summary
- supported formats
- supported sample rates
- supported channel counts
- generated output or test pipeline
- copy action
- placeholder area for future speaker testing

## Milestone 33 — Commands and Reproduce Sections

Add curated command sections in Device Information views.

Commands may include:

- `gst-device-explorer` commands
- `v4l2-ctl` commands for camera inspection
- ALSA commands for audio inspection
- GStreamer commands for pipeline testing

These commands should teach the user how to reproduce GUI-derived discovery from the command line without cluttering the Explore tab.

## Milestone 34 — Reports Area

Add a dedicated Reports or Diagnostics area.

This area should contain:

- full device reports
- support bundles
- raw JSON
- schema-related output
- diagnostic summaries
- development/debug information

This keeps report functions available while removing them from the main exploration workflow.

## Milestone 35 — Preview Policy and Dry-Run UX

Define and implement the first safe GUI execution policy for preview behavior.

The policy should preserve existing safety boundaries:

- generated pipelines only
- explicit user action
- no arbitrary user-authored pipelines
- dry-run visibility
- safe subprocess handling
- clear stop behavior
- process cleanup

## Milestone 36 — Camera Preview Implementation

Allow the camera Explore tab to launch and stop a selected generated preview pipeline safely.

This milestone should focus on camera preview only.

It should not introduce arbitrary pipeline editing, synchronized capture, recording workflows, or group-based execution.

## Milestone 37 — Audio Test Policy and UX

Define safe GUI behavior for audio input and output tests before implementing them.

The design should answer:

- what constitutes a safe microphone test
- what constitutes a safe speaker test
- whether the first version should use level display, bounded capture, test tone playback, or command generation only
- how the user starts and stops tests
- what pipelines are allowed

## Milestone 38 — Audio Test Implementation

Add bounded audio input and output tests using generated pipelines only.

Possible scope:

- short microphone capture
- input level test
- speaker test tone
- explicit start/stop behavior
- dry-run visibility
- safe process cleanup

## Milestone 39 — Service-Layer Cleanup

Introduce purpose-built GUI-facing services so widgets consume exploration models instead of raw CLI/report structures.

Possible services:

- `MediaExplorerService`
- `CameraExplorerService`
- `AudioExplorerService`
- `GroupExplorerService`

The goal is to prevent the GUI from becoming a rendered version of CLI output.

## Milestone 40 — Polish and HIL Validation

Validate the redesigned GUI on Jetson and Reachy Mini-style hardware.

This milestone should include:

- hardware-in-the-loop validation
- layout refinement
- removal of development remnants from the main UI
- documentation updates
- regression tests
- confirmation that safety boundaries remain intact

## Safety Boundaries

Until deliberately changed by a scoped milestone, preserve these boundaries:

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
- no GUI preview/capture/test behavior unless deliberately scoped

## Working Summary

The GUI should be organized around exploration first.

A useful distinction:

- **Explore** means selecting settings and trying how a device works.
- **Device Information** means understanding what the system discovered.
- **Reports** means creating a full accounting for support, debugging, or documentation.
- **Commands** means teaching how to reproduce the investigation outside the GUI.

The development path should keep these concerns separate.
