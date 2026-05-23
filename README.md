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
probing models and CLI renderers, but no pipeline generation, preview/run
behavior, GUI, recording, or editing support yet.

## Setup

See `docs/SETUP.md` for Python setup, required Linux tools, useful GStreamer
packages, verification commands, and prerequisites for useful CLI output.

See the `docs/` directory for the specification, architecture notes, development
principles, pipeline candidate design, and Milestone 1 scope.
