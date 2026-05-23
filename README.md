# gst-device-explorer

`gst-device-explorer` is a GStreamer-oriented device exploration tool for
discovering media devices, inspecting capabilities, and generating useful
pipeline candidates, with an architecture intended to support additional
hardware exploration plugins over time.

Its first real domain is media exploration: video inputs, audio inputs, audio
outputs, the local GStreamer environment, and useful pipeline candidates.

The project is profile-aware. Profiles describe platform and
operating-system-specific behavior, such as generic Linux or NVIDIA Jetson
systems running different JetPack / Linux for Tegra versions. Profiles should
capture preferences and known-good patterns, not random patches.

The architecture should support GStreamer-oriented device exploration first and
extensible hardware exploration later. Future exploration plugins may inspect
other device classes, such as robot hardware, actuators, Dynamixel servos, or
sensors, but that is not part of the initial implementation scope.

The project is currently in an early implementation phase. It has initial
probing models, CLI renderers, video pipeline candidate generation, and safe
execution for selected video preview candidates. It can also render composite
device groups computed from discovered device metadata. GUI, recording, editing,
audio pipeline generation, and preview-window lifecycle management are not
implemented yet.

## Composite Device Groups

Use `groups` to inspect higher-level composite devices inferred from discovered
V4L2 and ALSA devices:

```sh
gst-device-explorer groups
gst-device-explorer groups --json
gst-device-explorer groups --metadata
gst-device-explorer groups --metadata --json
gst-device-explorer group <group-id>
```

Milestone 3 emits two USB grouping levels when the evidence is available:

- exact USB-device groups for devices sharing the same USB parent path
- parent USB-family groups for child composite groups that share a USB ancestor,
  USB vendor ID, and non-generic product-family token

Example output on Reachy Mini hardware:

```text
Composite devices:
- Reachy Mini Audio
  id: usb-device-1-4-1-1
  kind: unknown
  confidence: 0.90
  members:
    - audio-input: hw:0,0
    - audio-output: hw:0,0

- Reachy Mini Camera
  id: usb-device-1-4-1-4
  kind: unknown
  confidence: 0.90
  members:
    - camera: /dev/video0
    - camera: /dev/video1

- Reachy Mini
  id: usb-family-1-4-1
  kind: unknown
  confidence: 0.80
  members:
    - audio-input: hw:0,0
    - audio-output: hw:0,0
    - camera: /dev/video0
    - camera: /dev/video1
```

Grouping enriches discovery output. Raw individual device commands such as
`devices`, `audio-inputs`, `audio-outputs`, and `video <device>` remain
available. Separate devices that do not share the grouping evidence, such as an
Orbbec Femto Bolt attached alongside the robot, remain independent.

Use `groups --metadata` as the diagnostic view for the normalized records
feeding the grouping engine when a group is missing or unexpected. Group-based
pipeline generation and group-based execution are not included; use the existing
`pipeline video <device>` and `run video <device>` commands for individual video
devices.

## Video Pipeline Candidates and Run

Use `pipeline` to inspect generated video preview candidates:

```sh
gst-device-explorer pipeline video /dev/video0
```

Use `run` to select and execute one generated candidate:

```sh
gst-device-explorer run video /dev/video0 --dry-run
gst-device-explorer run video /dev/video0
gst-device-explorer run video /dev/video0 --candidate 0
gst-device-explorer run video /dev/video0 --candidate jetson-uvc-mjpeg-nvjpeg-nveglglessink
```

`--dry-run` prints the selected candidate ID and GStreamer command without
starting GStreamer. Without `--dry-run`, the selected candidate is executed with
an argv-style subprocess call. Press Ctrl+C to stop a running pipeline.

## Setup

See `docs/SETUP.md` for Python setup, required Linux tools, useful GStreamer
packages, verification commands, and prerequisites for useful CLI output.

See the `docs/` directory for the specification, architecture notes, development
principles, pipeline candidate design, and milestone scope.
