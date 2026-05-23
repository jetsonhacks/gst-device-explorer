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
execution for selected video preview candidates. GUI, recording, editing, audio
pipeline generation, and preview-window lifecycle management are not implemented
yet.

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
