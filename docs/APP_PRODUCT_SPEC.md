# Application Product Specification

## Product Definition

`gst-device-explorer` is a GUI-first media endpoint explorer for Jetson and Linux systems that helps users discover local cameras, microphones, and speakers, choose device-derived settings, and generate reproducible GStreamer commands.

## Primary User

The primary user is a Jetson/Linux developer exploring local media hardware for bring-up, debugging, validation, examples, tutorials, or application prototyping.

This user is comfortable with Linux and GStreamer, but should not have to read raw probe output or hand-build every pipeline before seeing what a device can do.

## Secondary Users

Secondary users include:

- Linux users who want a practical GStreamer-oriented media device explorer.
- Support engineers collecting device facts and reproducible commands.
- Tutorial authors documenting camera, microphone, and speaker capabilities.
- Hardware integrators validating a composite USB device with several media endpoints.
- CLI users who want the same investigation to be reproducible outside the GUI.

## Main First-Run Workflow

A first run should feel like this:

1. Launch `gst-device-explorer gui`.
2. See discovered physical groups and individual media endpoints in the sidebar.
3. Select a group, camera, audio input, or audio output.
4. Use the default **Explore** view to work with that selected item.
5. Pick settings from choices discovered from the device.
6. See a generated GStreamer pipeline for the selected settings.
7. Copy the pipeline for use in a terminal, script, tutorial, or issue report.
8. For lower-level device facts, raw capabilities, or reproduction commands, use the `gst-device-explorer` CLI or the system report.

## What The Application Is

`gst-device-explorer` is:

- a media endpoint exploration tool
- a GUI-first companion to GStreamer device bring-up
- a bridge between local hardware probing and useful GStreamer commands
- a way to inspect cameras, microphones, speakers, and evidence-based physical groups
- a reproducibility aid for CLI-driven investigation
- a safe surface for selected, generated media workflows

## What The Application Is Not

`gst-device-explorer` is not:

- a generic hardware inventory tool
- a rendered JSON viewer
- a rendered CLI report viewer
- a full media capture, editing, streaming, or playback suite
- a general-purpose GStreamer pipeline IDE
- a package installer or system configuration tool
- a remote device management tool
- a Reachy-specific application
- a place for arbitrary user-authored pipeline execution

## Core Device Concepts

### Camera Endpoint

A camera endpoint is a video capture device that exposes image formats, sizes, frame intervals, and optional V4L2 controls.

The GUI should help the user choose among device-derived camera settings and generate a matching GStreamer pipeline. Lower-level V4L2 identity, raw capability output, candidate rankings, diagnostics, and command reproduction belong in secondary information views.

### Audio Input Endpoint

An audio input endpoint is a microphone or capture-capable ALSA/GStreamer device.

The GUI should help the user identify the input, choose supported audio settings when known, and generate a capture-oriented GStreamer pipeline. Future testing or level-meter behavior must be explicitly scoped before implementation.

### Audio Output Endpoint

An audio output endpoint is a speaker, headset, HDMI sink, or playback-capable ALSA/GStreamer device.

The GUI should help the user identify the output, choose supported playback settings when known, and generate an output or test-oriented GStreamer pipeline. Future speaker test behavior must be explicitly scoped before implementation.

### Composite Group

A composite group is an evidence-based physical-device grouping of related endpoints, such as a USB device that exposes a camera, microphone, and speaker.

Groups help users understand physical hardware organization. A group view may summarize endpoints and offer actions to explore each endpoint directly, but it must not imply group-based execution, synchronized capture, or combined media workflows unless a later milestone explicitly designs those behaviors.

## Exploration, Information, Reports, Diagnostics, And Commands

**Exploration** is the working surface for the selected device. It answers: "How do I explore and try this device?" It should contain compact identity, device-derived setting selectors, generated pipeline text, copy actions, and safe read-only controls.

**Information** explains the selected device. It answers: "What did the backend discover about this device?" It may include identity, hardware metadata, raw capabilities, candidate pipelines, recommended candidates, grouping evidence, diagnostics summaries, and reproduction commands.

**Reports** are broader artifacts for support, validation, or archival use. They may include full device reports, system reports, support bundles, raw JSON, schema output, and validation output. Reports should not dominate the default selected-device view.

**Diagnostics** are troubleshooting details and health checks. They should remain available, but they belong in secondary areas or targeted diagnostic sections rather than the default exploration workflow.

**Commands** are reproducibility aids. Generated pipelines may appear in Explore when they are the direct result of current selections. CLI reproduction commands, probe commands, suggested commands, and report commands belong in a future Commands/Reports area.

## Safety Boundaries

These safety boundaries apply:

- no arbitrary pipeline execution
- no arbitrary user-authored pipeline scripts
- no hidden command execution
- no package installation
- no system configuration changes
- no remote behavior
- no group-based execution
- no synchronized capture
- V4L2 control writes are bounded to discovered active camera controls through the GUI; no arbitrary v4l2-ctl command execution as a user-facing workflow
- GUI execution is bounded to generated, deliberate workflows; no arbitrary pipeline scripts or user-authored commands

Safe read-only discovery, copy-to-clipboard behavior, and generated command rendering remain allowed.
