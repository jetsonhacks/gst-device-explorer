# GUI Information Architecture

## Purpose

The GUI should make `gst-device-explorer` feel like a media hardware exploration tool, not a rendered backend report.

The primary surface is:

- **Explore**: work with the selected device

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
    └── Explore
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

## Camera Explore

The camera Explore tab should prioritize:

- compact device summary
- pixel format selection
- image size selection
- frame duration / FPS selection
- generated GStreamer pipeline
- copy pipeline action
- active camera controls, including writable controls where the device supports them

Camera selectors should be derived from the selected camera endpoint. The generated pipeline should update from the selected format, size, and frame duration. Active camera controls are writable where the device reports them as writable and active; inactive and read-only controls are shown but cannot be changed.

The default camera Explore tab should not show:

- full raw V4L2 capability text
- full identity and metadata blocks
- every candidate pipeline
- recommended candidate internals
- diagnostic reports
- support bundle details
- raw JSON or envelope output
- long lists of suggested commands

## Audio Input Explore

The audio input Explore tab prioritizes:

- compact device summary
- supported format selection
- supported sample-rate selection
- supported channel-count selection
- generated input pipeline
- copy pipeline action
- audio input activity test (bounded non-recording endpoint check)

## Audio Output Explore

The audio output Explore tab prioritizes:

- compact device summary
- supported format selection
- supported sample-rate selection
- supported channel-count selection
- generated output or test pipeline
- copy pipeline action
- audio output test: bounded generated tone or local file playback

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


## Reports And Diagnostics

Reports and diagnostics should live outside the default Explore tab.

Broader diagnostic artifacts should live outside the default Explore view, in a future Reports or Diagnostics area, including:

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

Command-reproduction information belongs in a future Commands area. This includes:

- `gst-device-explorer` CLI equivalents
- `v4l2-ctl` inspection commands
- ALSA inspection commands
- GStreamer commands for selected generated pipelines
- suggested commands used for support or debugging

The GUI may display commands and support copy actions, but it should not execute arbitrary commands or user-authored pipeline scripts.
