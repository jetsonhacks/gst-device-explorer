# gst-device-explorer

`gst-device-explorer` is a GUI-first Linux / Jetson media device explorer. It
discovers camera, microphone, speaker, and grouped composite devices, then lets
the user inspect capabilities and safely try generated GStreamer actions.

The mental model is:

```text
camera-caps for modern Jetson media devices.
```

The CLI remains important as a backend, debug interface, and testable probe
layer, but the GUI is now the primary product direction.

Its first real domain is media exploration: video inputs, audio inputs, audio
outputs, grouped composite USB devices, the local GStreamer environment, and
useful generated pipeline candidates.

Pipeline candidates carry a profile label identifying the generation strategy,
such as a generic Linux preview or a Jetson/NVIDIA accelerated preview. The
project also provides `DeviceProfile` endpoint summaries that combine discovery,
candidate, diagnostic, and grouping information for CLI inspection and system
reports.

Future work should be judged by whether it improves the GUI media exploration
experience. Additional backend infrastructure should support the sidebar,
detail panes, grouping views, diagnostics, and safe generated actions rather
than becoming a separate industrial diagnostics platform.

The project is currently in an early implementation phase. It has initial
probing models, CLI renderers, video and audio pipeline candidate generation,
and safe execution for selected video preview and ALSA audio test candidates. It
can also create short, explicit, bounded capture files from generated video and
audio-input candidates. Composite device groups are computed from discovered
device metadata. Milestone 19 adds toolkit-neutral GUI application models for a
future sidebar/main-pane application, but no actual GUI window or toolkit
dependency is implemented yet. Editing, audio loopback, group-based execution,
and preview-window lifecycle management are not implemented yet.

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

## Support Bundle Export

Use `support bundle` to create a portable support/debug bundle from existing
safe inspection surfaces:

```sh
gst-device-explorer support bundle --output ./my-support-bundle
```

The command creates a new directory at the explicit output path. The path must
not already exist and its parent directory must exist.

The bundle includes:

- `manifest.json` — bundle metadata, file list, and creation timestamp
- `report/system-report.json` — full system report in JSON envelope format
- `report/system-report.txt` — compact system report text summary
- `inventory/` — per-kind device, environment, and group listings
- `config/` — configuration search paths, effective configuration, and validation
- `schemas/` — known schema document list
- `suggestions/` — generic suggested command catalog
- `tui/snapshot.txt` — TUI overview snapshot

The support bundle is an export of already-safe inspection data. It does not:

- run GStreamer pipelines or capture media
- execute suggested commands
- install packages or change system configuration
- require special system privileges beyond normal device probing

The bundle is intended for attaching to GitHub issues, comparing Jetson systems,
and field debugging without requiring direct access to the target hardware.

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

## Composite Device Validation

Use `validate group` to summarize the endpoint health of one composite device:

```sh
gst-device-explorer validate group <group-id>
gst-device-explorer validate group <group-id> --json
```

Validation reuses existing group evidence and endpoint profiles. It reports a
simple group status, per-endpoint status, candidate counts, aggregated missing
GStreamer elements, and suggested endpoint-level next commands.

Group validation is explanatory only. It does not run pipelines, does not run
capture, does not generate group-level pipelines, and does not choose endpoints
automatically. Use individual endpoint commands such as `profile`, `recommend`,
`run`, and `capture` to inspect or test a specific video or audio endpoint.

## Presets

Use `preset` to discover named workflows over existing safe commands:

```sh
gst-device-explorer preset list
gst-device-explorer preset show camera-preview
gst-device-explorer preset command camera-preview video /dev/video0
gst-device-explorer preset command short-video-capture video /dev/video0 --duration 5 --output sample.avi
```

Presets are built-in descriptions and command suggestions. They return
structured argv internally and render readable command text or JSON externally.
They do not execute commands, do not accept arbitrary GStreamer pipelines, and
do not introduce group execution. Use the suggested endpoint commands when you
are ready to inspect, run, capture, recommend, or validate.

## Suggested Command Catalog

Use `suggestions list` to browse a catalog of generic suggested commands:

```sh
gst-device-explorer suggestions list
gst-device-explorer suggestions list --json
```

The catalog lists broad starting-point commands covering discovery, environment
inspection, group listing, report generation, schema browsing, and configuration.
It is a read-only reference and does not execute any command. Each entry includes
a title, full argv, rendered command string, purpose, safety classification, and
optional notes.

Suggested commands also appear inline inside `profile`, `validate group`,
`report`, and `tui` outputs, where they are tailored to the specific endpoint or
group being inspected. The `suggestions list` catalog gives a static overview of
the common commands available across the tool.

Safety classifications used throughout suggested commands:

- `inspection` — read-only probing, no side effects
- `dry_run` — prints a command without executing it
- `bounded_capture` — time-limited file write to an explicit output path
- `safe_execution` — runs a generated pipeline with Ctrl+C to stop
- `external_check` — invokes an external tool (e.g., `gst-inspect-1.0`)

## Configuration

Use `config` to inspect and validate bounded preferences:

```sh
gst-device-explorer config path
gst-device-explorer config show
gst-device-explorer config show --json
gst-device-explorer config validate
gst-device-explorer config validate --config ./gst-device-explorer.toml
```

Configuration is optional. Milestone 12 validates and displays configuration
only; preferences do not change candidate generation, ranking, presets, reports,
capture, validation, or execution yet. Config files cannot introduce arbitrary
pipelines, shell commands, scripts, package installation, or system
configuration changes.

## Machine-Readable JSON

Selected JSON outputs use a stable envelope for scripts and future interfaces:

```json
{
  "schema_version": "1.0",
  "tool_version": "0.19.0",
  "kind": "preset_list",
  "data": []
}
```

The envelope is used by config, preset, schema discovery, device discovery,
environment, grouping, video capability, pipeline candidate, pipeline
diagnostic, profile, report, recommendation, and group validation JSON outputs.
The `data` field contains the command-specific payload, preserving the older
payload shape under the envelope.

Selected known error paths return a companion error envelope:

```json
{
  "schema_version": "1.0",
  "tool_version": "0.19.0",
  "kind": "error",
  "error": {
    "code": "unknown_schema",
    "message": "Unknown schema: not-a-schema",
    "details": {
      "schema_id": "not-a-schema"
    },
    "suggested_commands": []
  }
}
```

Error envelopes use `kind: "error"` with an `error` object instead of `data`.
The `error.code` field is a stable snake_case identifier for scripts to match.
The `error.suggested_commands` list is advisory and is never executed automatically.

Error envelope coverage in Milestone 17:

- `schema show <unknown> --json` → `unknown_schema`
- `preset show <unknown> --json` → `unknown_preset`
- `preset command <unknown> ... --json` → `unknown_preset`
- `preset command <id> <wrong-kind> ... --json` → `wrong_preset_target_kind`
- `preset command <capture-preset> <video> <target> --json` (missing args) → `missing_required_argument`
- `group <unknown> --json` → `group_not_found`
- `validate group <unknown> --json` → `group_not_found`

Non-JSON invocations preserve existing human-readable text behavior.
Config JSON outputs remain in the success envelope with `valid: false`.

Inspect the envelope contracts with:

```sh
gst-device-explorer schema list
gst-device-explorer schema show json-envelope
gst-device-explorer schema show error-envelope
gst-device-explorer schema show error-envelope --json
```

## TUI Review Mode

Use `tui` to browse a read-only terminal overview:

```sh
gst-device-explorer tui
gst-device-explorer tui --snapshot
```

The TUI summarizes existing environment, device, group, preset, configuration,
schema, and suggested-command information. It is a review surface only: it does
not run pipelines, capture media, execute presets, edit configuration, install
packages, or change system settings. Suggested commands are displayed for the
user to run separately.

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

## Bounded Capture Tests

Use `capture` to create short endpoint-based validation files from generated
candidates only:

```sh
gst-device-explorer capture video /dev/video0 --duration 5 --output sample.avi
gst-device-explorer capture video /dev/video0 --duration 5 --output sample.avi --dry-run

gst-device-explorer capture audio-input hw:0,0 --duration 5 --output sample.wav
gst-device-explorer capture audio-input hw:0,0 --duration 5 --output sample.wav --dry-run
```

Capture requires an explicit positive duration and an explicit output path.
Dry-run prints the exact argv-backed command without starting GStreamer. Existing
output files are rejected; `--overwrite` is not implemented.

Capture is a bounded validation tool, not a recording framework. It does not
accept arbitrary pipeline strings, does not perform group-based capture, does
not run synchronized audio/video capture, and does not create background or
long-running recordings. The first video capture candidates write simple AVI
files; audio input capture writes WAV files.

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
