# GUI Information Architecture

## Purpose

The GUI should make `gst-device-explorer` feel like a media hardware exploration tool, not a rendered backend report.

The main distinction is:

- **Explore**: work with the selected device
- **Device Information**: understand the selected device

## Main Window

Recommended structure:

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

## Sidebar Purpose

The sidebar answers:

> What device or group am I looking at?

It should organize discovered items into stable, scannable categories:

- Groups
- Cameras
- Audio Inputs
- Audio Outputs

The sidebar should support refresh and selection without becoming a report browser. It should show enough identity to distinguish devices, but detailed capability and diagnostic output belongs in the main pane.

## Main Pane Purpose

The main pane answers:

> What can I do with the selected item?

For selected endpoints, the main pane should default to **Explore**. The user should immediately see the controls and generated pipeline most relevant to working with the selected device.

For selected groups, the main pane should summarize the physical device and offer endpoint-level entry points.

## Default Tab Behavior

The default tab for any selected item should be **Explore**.

The GUI may remember the last active tab during a short session, but changing to a new selected item should not make lower-level report output feel like the primary experience. If in doubt, return selection changes to **Explore**.

## Explore Tab Role

The Explore tab is the default working surface. It should contain controls that help the user make a useful selection from discovered device capabilities.

Explore should include:

- compact device summary
- device-derived selectors
- generated GStreamer pipeline for current selections
- copy pipeline action
- safe read-only controls when useful
- disabled placeholders only when they communicate deliberately deferred behavior

Explore should not become a dump of every model field the backend knows.

## Device Information Tab Role

The Device Information tab is the secondary explanatory surface. It should contain lower-level details that help a user understand, debug, report, or reproduce discovery.

Device Information may include:

- identity
- hardware metadata
- raw capabilities
- candidate pipelines
- recommended candidate
- diagnostics
- grouping evidence
- reproduce with CLI

## Camera Explore

The camera Explore tab should prioritize:

- compact device summary
- pixel format selection
- image size selection
- frame duration / FPS selection
- generated GStreamer pipeline
- copy pipeline action
- dynamic read-only camera controls

Camera selectors should be derived from the selected camera endpoint. The generated pipeline should update from the selected format, size, and frame duration. V4L2 controls should remain read-only until a later milestone explicitly designs control writes.

The default camera Explore tab should not show:

- full raw V4L2 capability text
- full identity and metadata blocks
- every candidate pipeline
- recommended candidate internals
- diagnostic reports
- support bundle details
- raw JSON or envelope output
- long lists of suggested commands

## Camera Device Information

The camera Device Information tab should contain:

- identity
- hardware metadata
- raw V4L2 capabilities
- candidate pipelines
- recommended candidate
- diagnostics
- reproduce with CLI

Useful reproduction commands may include:

```sh
gst-device-explorer video /dev/video0
gst-device-explorer profile video /dev/video0
gst-device-explorer pipeline video /dev/video0
v4l2-ctl --device=/dev/video0 --list-formats-ext
v4l2-ctl --device=/dev/video0 --list-ctrls-menus
```

These commands should teach and reproduce. They should not crowd the camera exploration workflow.

## Audio Input Explore

The audio input Explore tab should eventually prioritize:

- compact device summary
- supported format selection
- supported sample-rate selection
- supported channel-count selection
- generated input pipeline
- copy pipeline action
- placeholder for future level or capture testing

No audio capture or test execution should be introduced unless a later milestone explicitly scopes it.

## Audio Output Explore

The audio output Explore tab should eventually prioritize:

- compact device summary
- supported format selection
- supported sample-rate selection
- supported channel-count selection
- generated output or test pipeline
- copy pipeline action
- placeholder for future speaker testing

No speaker test execution should be introduced unless a later milestone explicitly scopes it.

## Group View Behavior

Groups represent evidence-based physical-device organization.

The group Explore tab should contain:

- physical-device summary
- endpoint cards for camera, microphone, speaker, and other discovered endpoints
- actions to explore endpoints directly

Group endpoint cards should summarize each endpoint and provide clear navigation to the endpoint Explore tab.

Groups should not provide:

- group-based execution
- synchronized capture
- combined audio/video launch behavior
- hidden endpoint execution
- assumptions that endpoints are usable together without validation

The group Device Information tab should explain why endpoints were grouped. It may include USB parent evidence, ALSA card relationships, endpoint metadata, diagnostics, and CLI reproduction commands.

## Reports And Diagnostics

Reports and diagnostics should live outside the default Explore tab.

Short, relevant diagnostics may appear inside Device Information for the selected item. Broader artifacts should move to a future Reports or Diagnostics area, including:

- full device reports
- system reports
- support bundles
- raw JSON
- JSON envelopes and error envelopes
- schema documents
- validation output
- detailed diagnostic command output

## Command Reproduction

Generated pipelines belong in Explore when they reflect the current GUI selections.

Command-reproduction information belongs in Device Information or a future Commands area. This includes:

- `gst-device-explorer` CLI equivalents
- `v4l2-ctl` inspection commands
- ALSA inspection commands
- GStreamer commands for selected generated pipelines
- suggested commands used for support or debugging

The GUI may display commands and support copy actions, but it should not execute arbitrary commands or user-authored pipeline scripts.
