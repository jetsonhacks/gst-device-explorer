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

## CLI and GUI are renderers

The CLI and GUI present probe results, normalized models, and pipeline
candidates. They should not own discovery logic or pipeline construction rules.

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

## Python file size

Python files should generally stay limited to about **250 to 300 lines**.

When a Python file grows beyond that range, it is usually a sign that the file
is handling too many areas of concern. The implementation should be reviewed for
clearer separation of responsibilities.

When a Python file exceeds **400 lines**, there should be an explicit review
before continuing to add functionality to that file. The review should consider
whether to split the file by responsibility, such as:

- UI widget construction
- application service logic
- model adaptation
- command generation
- formatting/rendering helpers
- process execution
- tests or fixtures

The goal is not to enforce an arbitrary line count. The goal is to keep the
codebase understandable, testable, and easy to reshape as the product evolves.
