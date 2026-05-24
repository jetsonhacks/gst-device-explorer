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

## DeviceRef

A device reference points from a higher-level grouped object back to an existing
discovered device.

It should include:

- Role
- Device ID
- Device path, when one exists
- Subsystem

Example roles include `camera`, `audio-input`, `audio-output`, `control`,
`sensor`, `actuator-bus`, `hid`, `serial`, and `unknown`.

Example subsystems include `v4l2`, `alsa`, `gstreamer`, `usb`, `udev`,
`serial`, `hid`, and `unknown`.

Device references do not replace raw device discovery. They preserve a link from
a composite device back to the individual device views.

## GroupingEvidence

Grouping evidence describes why multiple devices may belong to the same
physical or logical unit.

It should include:

- Source
- Description
- Strength

The strength value represents confidence in one piece of evidence from 0.0 to
1.0. Grouping should be inspectable and evidence-based rather than hidden inside
hard-coded product assumptions.

## CompositeDevice

A composite device is a grouped physical or logical device.

It should include:

- ID
- Name
- Kind
- Confidence
- Member device references
- Grouping evidence

Example kinds include `robot`, `camera-system`, `audio-device`, and `unknown`.

Composite devices are Milestone 3 scaffolding. They model a future grouping
layer where related Linux devices can be presented together while the raw V4L2,
ALSA, serial, HID, or other individual device entries remain available.

## GroupableDevice

A groupable device is an internal input record for the grouping engine. It
combines a `DeviceRef`, a display name, and normalized metadata that has already
been collected elsewhere.

It should include:

- Device reference
- Name
- Metadata

The grouping engine consumes groupable devices and emits zero or more
`CompositeDevice` objects. It does not call Linux tools, inspect live hardware,
or parse raw command output directly.

The metadata map may include normalized fields such as `alsa_card`,
`alsa_device`, `alsa_card_name`, `v4l2_name`, `usb_parent_path`,
`usb_vendor_id`, `usb_product_id`, `usb_product`, `usb_manufacturer`, and
`usb_serial` when those facts are available. USB metadata may come from V4L2
sysfs paths or ALSA sound sysfs paths.

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

## Profile Label

A pipeline candidate profile label is a string attached to `PipelineCandidate`
objects. It identifies the generation strategy or family used to construct the
candidate, for example `"generic-linux-video-preview"` or
`"jetson-video-preview"`. Labels are candidate metadata; they are not policy
objects consumed by builders.

## DeviceProfile

`DeviceProfile` is an endpoint summary built after discovery and candidate
generation. It combines discovered device facts, a capability summary, pipeline
candidate summaries, group membership, and suggested next commands into a
structured view for CLI/JSON inspection and system reports. It does not control
pipeline generation.

A richer platform-policy Profile layer — where a named object expresses
preferences for particular platforms, operating systems, or workflows and is
consumed by pipeline builders — may be added in a later milestone but is not
part of the current implementation.

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
- Profile label, if any (a string identifying the generation strategy)

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

Pipeline builders consume normalized devices, capabilities, and environment
facts, then produce pipeline candidates. Candidates carry a profile label
identifying the generation strategy.

`DeviceProfile` summaries are built after candidate generation. They are
structured views for CLI/JSON inspection and system reports.

`GroupValidation` summaries are built from an existing `CompositeDevice` and
endpoint profiles. They preserve grouping evidence, summarize per-endpoint
candidate availability, aggregate missing elements, derive a simple group
status, and suggest endpoint-level next commands. They do not execute pipelines,
run capture, or generate group-level pipelines.

`PresetDefinition` records describe built-in named workflows over existing
commands. `PresetCommandSuggestion` records carry structured argv for suggested
commands. Presets are not pipeline candidates, device profiles, or platform
policy objects; they do not execute commands or accept arbitrary pipeline text.

`ExplorerConfig` records describe bounded preferences for future behavior.
`ConfigValidationResult` records describe the source, validity, parsed config,
warnings, and errors for defaults or TOML files. Configuration is display and
validation only in Milestone 12; it does not change command behavior or allow
raw pipelines, scripts, hooks, plugins, or arbitrary argv.

Renderers display structured data. They should not contain probing or
pipeline-selection logic.
