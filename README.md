# gst-device-explorer

`gst-device-explorer` is a GStreamer-oriented device exploration tool for
discovering media devices, inspecting capabilities, and generating useful
pipeline candidates, with an architecture intended to support additional
hardware exploration plugins over time.

Its first real domain is media exploration: video inputs, audio inputs, audio
outputs, the local GStreamer environment, and useful pipeline candidates.

Pipeline candidates carry a profile label identifying the generation strategy,
such as a generic Linux preview or a Jetson/NVIDIA accelerated preview. The
project also provides `DeviceProfile` endpoint summaries that combine discovery,
candidate, diagnostic, and grouping information for CLI inspection and system
reports.

The architecture should support GStreamer-oriented device exploration first and
extensible hardware exploration later. Future exploration plugins may inspect
other device classes, such as robot hardware, actuators, Dynamixel servos, or
sensors, but that is not part of the initial implementation scope.

The project is currently in an early implementation phase. It has initial
probing models, CLI renderers, video and audio pipeline candidate generation,
and safe execution for selected video preview and ALSA audio test candidates. It
can also render composite device groups computed from discovered device
metadata. GUI, recording, editing, audio loopback, group-based execution, and
preview-window lifecycle management are not implemented yet.

## System Report

Use `report` to capture the full media system state as a single structured
document:

```sh
gst-device-explorer report --json
gst-device-explorer report
```

The report gathers existing discovery, grouping, profile, candidate, and
diagnostic information in one place. It is read-only and does not run
pipelines. JSON output is the primary format and is suitable for GitHub
issues, hardware validation, comparing Jetson systems, and remote debugging.

The report includes:

- tool version and GStreamer environment facts
- discovered video, audio-input, and audio-output devices
- composite device groups
- endpoint profiles for each discovered device
- aggregated missing GStreamer elements
- suggested next commands per endpoint

Text output is a compact summary. File output (`--output`) is deferred.

## Candidate Ranking and Recommendations

Use `recommend` to rank generated pipeline candidates and identify the best one
to try first:

```sh
gst-device-explorer recommend video /dev/video0
gst-device-explorer recommend video /dev/video0 --json

gst-device-explorer recommend audio-input hw:0,0
gst-device-explorer recommend audio-input hw:0,0 --json

gst-device-explorer recommend audio-output hw:0,0
gst-device-explorer recommend audio-output hw:0,0 --json
```

`recommend` ranks the same candidates that `pipeline` generates, without
creating new pipelines or executing any of them. It explains why one candidate
is suggested over another, including availability status, missing GStreamer
elements, and confidence scores.

Text output lists all ranked candidates in order with reasons. JSON output
includes the full ranking with scores and reasons in machine-readable form.

To inspect or run the recommended candidate:

```sh
# Inspect all candidates first
gst-device-explorer pipeline video /dev/video0

# Dry-run the recommended (rank 1) candidate
gst-device-explorer run video /dev/video0 --dry-run

# Run a specific candidate by ID
gst-device-explorer run video /dev/video0 --candidate jetson-uvc-mjpeg-nvjpeg-nveglglessink
```

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
`pipeline` and `run` commands for individual video and audio devices.

## Device Profiles

Use `profile` to get a structured summary of a device endpoint:

```sh
gst-device-explorer profile video /dev/video0
gst-device-explorer profile video /dev/video0 --json

gst-device-explorer profile audio-input hw:0,0
gst-device-explorer profile audio-input hw:0,0 --json

gst-device-explorer profile audio-output hw:0,0
gst-device-explorer profile audio-output hw:0,0 --json
```

A device profile combines existing discovery, grouping, candidate, and
diagnostic information in one compact view. It answers:

- What is this device and what capabilities were discovered?
- Which pipeline candidates are available?
- Which candidates are blocked, and why?
- Is this endpoint part of a composite device group?
- What should I try next?

Profiles differ from raw discovery (`devices`, `audio-inputs`, `video`),
pipeline inspection (`pipeline`), and diagnostics (`pipeline --diagnostics`)
in that they summarize all of these into one place. Profiles do not re-probe
the device and do not execute pipelines.

### Profile Workflow

The recommended workflow when exploring a new device:

```sh
# 1. Discover devices
gst-device-explorer devices
gst-device-explorer audio-inputs
gst-device-explorer audio-outputs

# 2. Inspect groups (optional)
gst-device-explorer groups

# 3. Inspect profile
gst-device-explorer profile video /dev/video0
gst-device-explorer profile audio-input hw:0,0

# 4. Inspect pipeline candidates
gst-device-explorer pipeline video /dev/video0

# 5. Inspect diagnostics if a candidate is missing
gst-device-explorer pipeline video /dev/video0 --diagnostics

# 6. Dry-run
gst-device-explorer run video /dev/video0 --dry-run

# 7. Run
gst-device-explorer run video /dev/video0
```

### Group Membership in Profiles

When composite device groups include the endpoint, the profile lists matching
groups under a `Groups:` section. This is informational only — it does not
change candidate generation or which device is targeted. Group-based pipeline
generation and group-based execution remain out of scope. Group profiles are
deferred.

## Video Pipeline Candidates and Run

Use `pipeline` to inspect generated video preview candidates:

```sh
gst-device-explorer pipeline video /dev/video0
gst-device-explorer pipeline video /dev/video0 --json
gst-device-explorer pipeline video /dev/video0 --diagnostics
gst-device-explorer pipeline video /dev/video0 --diagnostics --json
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

## Audio Pipeline Candidates and Run

Use `pipeline` to inspect generated ALSA audio test candidates:

```sh
gst-device-explorer pipeline audio-input hw:0,0
gst-device-explorer pipeline audio-input hw:0,0 --json
gst-device-explorer pipeline audio-input hw:0,0 --diagnostics
gst-device-explorer pipeline audio-input hw:0,0 --diagnostics --json
gst-device-explorer pipeline audio-output hw:0,0
gst-device-explorer pipeline audio-output hw:0,0 --json
gst-device-explorer pipeline audio-output hw:0,0 --diagnostics
gst-device-explorer pipeline audio-output hw:0,0 --diagnostics --json
```

Use `run` to select and execute one generated audio candidate:

```sh
gst-device-explorer run audio-input hw:0,0 --dry-run
gst-device-explorer run audio-output hw:0,0 --dry-run
gst-device-explorer run audio-input hw:0,0
gst-device-explorer run audio-output hw:0,0
gst-device-explorer run audio-output hw:0,0 --candidate generic-alsa-audio-output-sine-alsasink
```

The audio input level test is intended to run without audible output. The audio
output sine test should play a 440 Hz tone. Audio execution uses generated
`PipelineCandidate.argv` values and does not accept arbitrary GStreamer pipeline
strings. Press Ctrl+C to stop a running audio pipeline.

## Diagnostics Workflow

Use diagnostics when a candidate is missing or when you want to understand why a
candidate is available:

```sh
gst-device-explorer devices
gst-device-explorer audio-inputs
gst-device-explorer audio-outputs
gst-device-explorer groups

gst-device-explorer pipeline video /dev/video0
gst-device-explorer pipeline video /dev/video0 --diagnostics
gst-device-explorer run video /dev/video0 --dry-run
gst-device-explorer run video /dev/video0
```

Diagnostics explain candidate availability and missing requirements; they do not
execute pipelines. Missing GStreamer elements are reported with suggested
checks such as:

```sh
gst-inspect-1.0 autovideosink
gst-inspect-1.0 alsasink
```

## Setup

See `docs/SETUP.md` for Python setup, required Linux tools, useful GStreamer
packages, verification commands, and prerequisites for useful CLI output.

See the `docs/` directory for the specification, architecture notes, development
principles, pipeline candidate design, and milestone scope.
