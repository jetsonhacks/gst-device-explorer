# Milestone 1

Milestone 1 establishes the first usable CLI/probe foundation for
GStreamer-oriented media exploration.

This milestone is a release candidate for discovery and pipeline candidate
generation. It is not a media playback, preview, recording, editing, or GUI
application.

## Current Status

Milestone 1 currently includes:

- Documentation and uv project metadata
- Core normalized data models
- GStreamer environment inspection
- V4L2 video device discovery
- V4L2 video capability parsing
- ALSA audio input discovery
- ALSA audio output discovery
- Generic Linux V4L2 video preview pipeline candidates
- Jetson NVIDIA MJPEG video preview pipeline candidates
- Human-readable CLI rendering
- JSON output for relevant commands

Latest smoke test result:

```text
73 tests passed
```

## CLI Commands

The current CLI commands are:

- `gst-device-explorer devices`
- `gst-device-explorer env`
- `gst-device-explorer audio-inputs`
- `gst-device-explorer audio-outputs`
- `gst-device-explorer video <device>`
- `gst-device-explorer pipeline video <device>`

Relevant commands support `--json`.

Pipeline candidate output is limited by default in text mode. The
`pipeline video` command shows the top candidates first and supports:

- `--all`
- `--limit N`

JSON pipeline output returns all candidates by default unless `--limit N` is
provided.

## Implemented Probe Scope

Hardware support is currently limited to:

- V4L2 video devices
- ALSA audio input devices
- ALSA audio output devices
- GStreamer environment inspection

PulseAudio and PipeWire probing are not implemented yet.

## Pipeline Candidate Scope

Pipeline candidates are generated but not executed.

Implemented pipeline candidate families:

- Generic Linux V4L2 video preview
- Jetson NVIDIA MJPEG video preview

Jetson candidate selection is based on detected capability and GStreamer element
availability. It does not rely on hard-coded JetPack version checks.

Audio pipeline generation is not implemented yet.

## Profile Awareness

Milestone 1 includes the first profile concepts through pipeline candidate
selection:

- `generic-linux-video-preview`
- `jetson-video-preview`

Profiles express preferences and known-good patterns. They should not become
random patch buckets.

## Explicit Non-Goals

Milestone 1 does not include:

- Pipeline execution
- Live preview windows
- Recording
- Editing
- GUI implementation
- Full media playback application behavior
- Audio pipeline generation
- PulseAudio probing
- PipeWire probing
- Non-media exploration plugins

## Extensibility Boundary

The project remains GStreamer-oriented device exploration first, extensible
hardware exploration later.

Future exploration plugins may inspect robot hardware, actuators, Dynamixel
servos, sensors, or other device classes. That plugin system is not part of
Milestone 1.
