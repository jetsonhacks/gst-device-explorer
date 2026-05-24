# Development Principles

## Probe first, build later

The project should begin by observing the host system and its available
GStreamer-relevant media devices before proposing pipelines or user-facing
choices. Discovery data is the foundation for later behavior.

## Normalize before deciding

Raw output from GStreamer, ALSA, PulseAudio, PipeWire, v4l2, and platform tools
should be converted into normalized models before ranking, filtering, or
presenting options.

## Profile labels identify strategies; future policy profiles should express preferences, not hacks

Candidate profile labels are string metadata that identify the generation
strategy used to build a pipeline candidate. The current labels are
`"generic-linux-video-preview"` and `"jetson-video-preview"`.

If a richer platform-policy Profile layer is added later, it should encode
platform, operating-system, and workflow preferences without becoming scattered
conditional workarounds. Any such profiles may describe JetPack / Linux for
Tegra differences, but they should prefer capability detection over hard-coded
version checks.

## Pipeline candidates are structured objects, not just strings

A pipeline candidate should carry its purpose, required devices, assumptions,
ranking metadata, warnings, and rendered GStreamer string. The string is only
one representation of a richer object.

## CLI and future GUI are renderers

The CLI and any future GUI should present probe results, normalized models, and
pipeline candidates. They should not own discovery logic or pipeline construction
rules.

## Prefer capability detection over hard-coded JetPack version checks

When possible, the project should detect available elements, plugins, device
capabilities, and system services directly instead of branching on JetPack or
Linux distribution versions.

## GStreamer first, extensible later

The first real domain is media exploration through GStreamer: video inputs,
audio inputs, audio outputs, GStreamer environment inspection, and useful
pipeline candidate generation.

The architecture should leave room for future exploration plugins, such as robot
hardware, actuators, Dynamixel servos, sensors, or other device classes. That
extensibility should not make the project sound or behave like a generic
hardware inventory system from day one.

## Keep Milestone 1 narrow

Milestone 1 should establish the documentation, project metadata, and later a
small CLI/probe foundation. It should avoid GUI work, live preview, recording,
editing, broad media playback features, and non-media exploration plugins.
