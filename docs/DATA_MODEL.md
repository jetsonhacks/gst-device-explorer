# Data Model

This document defines the first conceptual data model for `gst-device-explorer`.
It is high-level and implementation-oriented, but it does not define Python
classes or module structure yet.

The model should support GStreamer-oriented device exploration first while
leaving room for additional hardware exploration plugins over time.

## Device

A device is a discovered thing attached to or exposed by the system.

Initial media examples include:

- Video input
- Audio input
- Audio output

Future extension examples may include:

- Actuator
- Servo bus
- Sensor
- Robot peripheral

Devices should describe what was found without deciding which pipeline or user
action is best.

## Capability

A capability is something a device can do, produce, or report.

Initial media examples include:

- Video format, resolution, and frame rate
- Audio sample format, channel count, and sample rate

Future extension examples may include:

- Actuator range
- Protocol
- Device ID
- Telemetry support

Capabilities should be normalized before they are ranked, filtered, or rendered
to users.

## EnvironmentFact

An environment fact is a fact about the host system or media stack.

Examples include:

- GStreamer version
- Installed GStreamer elements
- Available NVIDIA elements
- Available ALSA / PulseAudio / PipeWire tools
- Platform hints such as Jetson or generic Linux

Environment facts should help profiles and pipeline builders understand the
system without forcing them to parse raw command output.

## Profile

A profile is a named set of preferences or known-good patterns.

Profiles may represent:

- Generic Linux
- Jetson
- JetPack-specific behavior
- Linux for Tegra behavior
- Future hardware families

Profiles should express preferences, not patches. They may use normalized
devices, capabilities, and environment facts, but implementation should prefer
capability detection over hard-coded version checks.

## PipelineCandidate

A pipeline candidate is a structured recommendation for a GStreamer pipeline.

It should include:

- Candidate ID
- Purpose
- Display command
- Execution argv
- Confidence
- Reasons
- Warnings
- Required elements
- Selected profile, if any

The candidate ID identifies the pipeline strategy or family. It should be stable
enough for CLI selection, documentation, tests, and future GUI use, but it does
not need to encode every caps detail.

The display command is for humans. The execution argv is for subprocess
execution. Rendered shell command strings are not executed.

The command is only one representation of the candidate. The surrounding
metadata should explain why the candidate exists, what it requires, and what
tradeoffs or risks a user should understand.

## ExecutionPlan

An execution plan is a selected pipeline candidate prepared for safe execution.

It should include:

- Candidate ID
- Execution argv
- Display command
- Warnings

The display command is rendered for humans before execution. The argv list is
passed to `subprocess.Popen(argv)`. These forms are related, but they are not
interchangeable: runtime correctness depends on argv, not shell quoting in the
display command.

## RendererOutput

Renderer output is a presentation of model data for a user or tool.

Examples include:

- Human-readable CLI output
- JSON output
- Future GUI panel

Renderer output should display structured data. It should not contain probing
logic or pipeline-selection logic.

## Boundaries

Probes produce devices, capabilities, and environment facts.

Profiles consume normalized facts and express preferences.

Pipeline builders produce pipeline candidates.

Renderers display structured data.

Renderers should not contain probing or pipeline-selection logic.
