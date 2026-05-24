# Setup

`gst-device-explorer` is a Python project managed with `uv`. It also depends on
external Linux media tools for device and environment inspection.

On Jetson and Ubuntu systems, install the system prerequisites before running
the project commands.

## 1. Install System Prerequisites

The current probes use system tools for V4L2 video devices, ALSA audio devices,
and GStreamer environment inspection.

```sh
sudo apt update
sudo apt install -y v4l-utils alsa-utils gstreamer1.0-tools
```

These packages provide:

- `v4l-utils`: provides `v4l2-ctl`
- `alsa-utils`: provides `arecord` and `aplay`
- `gstreamer1.0-tools`: provides `gst-launch-1.0` and `gst-inspect-1.0`

## 2. Optional GStreamer Plugins

Generic Ubuntu systems may need additional GStreamer plugins for useful media
inspection and future pipeline exploration:

```sh
sudo apt install -y \
  gstreamer1.0-plugins-base \
  gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-bad \
  gstreamer1.0-plugins-ugly \
  gstreamer1.0-libav
```

On Jetson systems, NVIDIA-specific GStreamer elements such as `nvvidconv`,
`nvjpegdec`, `nvv4l2decoder`, `nveglglessink`, and `nv3dsink` come from JetPack
/ NVIDIA multimedia packages, not this Python project.

## 3. Set Up the Python Project

```sh
uv sync
uv run python -m pytest
```

## 4. Verify System Tools

Check that expected tools are available:

```sh
which v4l2-ctl
which arecord
which aplay
which gst-launch-1.0
which gst-inspect-1.0
```

Inspect local devices and GStreamer elements:

```sh
v4l2-ctl --list-devices
arecord -l
aplay -l
gst-inspect-1.0 v4l2src
gst-inspect-1.0 nvvidconv
```

`nvvidconv` may not exist on generic Linux systems.

## 5. Run gst-device-explorer

Start with the general commands:

```sh
uv run gst-device-explorer --help
uv run gst-device-explorer env
uv run gst-device-explorer devices
uv run gst-device-explorer audio-inputs
uv run gst-device-explorer audio-outputs
uv run gst-device-explorer groups
uv run gst-device-explorer video /dev/video0
uv run gst-device-explorer pipeline video /dev/video0
```

Useful pipeline candidate variants:

```sh
uv run gst-device-explorer pipeline video /dev/video0 --limit 1
uv run gst-device-explorer pipeline video /dev/video0 --all
uv run gst-device-explorer pipeline video /dev/video0 --json --limit 1
```

## 6. Verify Milestone 2 Pipeline Execution

Inspect generated candidates first:

```sh
uv run gst-device-explorer pipeline video /dev/video0
```

Check the selected command without starting GStreamer:

```sh
uv run gst-device-explorer run video /dev/video0 --dry-run
```

Run the selected candidate:

```sh
uv run gst-device-explorer run video /dev/video0
```

The real run command may open a GStreamer preview window depending on the
selected sink. Press Ctrl+C in the terminal to stop a running pipeline.

## 7. Verify Milestone 3 Composite Groups

Inspect computed composite device groups:

```sh
uv run gst-device-explorer groups
uv run gst-device-explorer groups --json
uv run gst-device-explorer groups --metadata
uv run gst-device-explorer groups --metadata --json
```

On systems where `uv` is installed outside `PATH`, use the absolute command:

```sh
/home/jim/.local/bin/uv run gst-device-explorer groups
/home/jim/.local/bin/uv run gst-device-explorer groups --json
```

If a group is found, inspect it by ID:

```sh
uv run gst-device-explorer group <group-id>
```

Milestone 3 group output can include exact USB-device groups and parent
USB-family groups. Exact USB-device groups contain devices sharing the same USB
parent path. Parent USB-family groups sit above those child groups when they
share a meaningful USB ancestor, USB vendor ID, and non-generic product-family
token.

Expected Reachy Mini-style output:

```text
Composite devices:
- Reachy Mini Audio
  id: usb-device-1-4-1-1
  ...

- Reachy Mini Camera
  id: usb-device-1-4-1-4
  ...

- Reachy Mini
  id: usb-family-1-4-1
  confidence: 0.80
  members:
    - audio-input: hw:0,0
    - audio-output: hw:0,0
    - camera: /dev/video0
    - camera: /dev/video1
```

Groups are computed from discovered device metadata. Systems without shared ALSA
card metadata or USB topology metadata may report no composite groups. Devices
that do not share the required evidence, such as a separate Orbbec Femto Bolt,
remain independent. Use `groups --metadata` as the diagnostic view for the
normalized records feeding the grouping engine.

Milestone 3 does not add group-based pipeline generation or group-based
execution. Pipeline generation and execution still target individual devices.

## 8. Verify Milestone 4 Audio Pipelines

Discover audio devices and groups first:

```sh
/home/jim/.local/bin/uv run gst-device-explorer audio-inputs
/home/jim/.local/bin/uv run gst-device-explorer audio-outputs
/home/jim/.local/bin/uv run gst-device-explorer groups
```

On the Reachy Mini hardware validated so far, the ALSA input and output are
`hw:0,0`. Inspect the generated candidates:

```sh
/home/jim/.local/bin/uv run gst-device-explorer pipeline audio-input hw:0,0
/home/jim/.local/bin/uv run gst-device-explorer pipeline audio-input hw:0,0 --json
/home/jim/.local/bin/uv run gst-device-explorer pipeline audio-output hw:0,0
/home/jim/.local/bin/uv run gst-device-explorer pipeline audio-output hw:0,0 --json
```

Check the selected commands without starting GStreamer:

```sh
/home/jim/.local/bin/uv run gst-device-explorer run audio-input hw:0,0 --dry-run
/home/jim/.local/bin/uv run gst-device-explorer run audio-output hw:0,0 --dry-run
```

Run the selected audio tests:

```sh
/home/jim/.local/bin/uv run gst-device-explorer run audio-input hw:0,0
/home/jim/.local/bin/uv run gst-device-explorer run audio-output hw:0,0
```

Expected behavior:

- The audio input level test should run without audible output.
- The audio output sine test should produce a 440 Hz tone.
- Press Ctrl+C to stop a running audio pipeline.

Audio loopback is intentionally deferred because it can create feedback or
surprising routing behavior. ASR, TTS, WebRTC, PulseAudio, PipeWire, effects,
echo cancellation, general-purpose recording workflows, synchronized audio/video
workflows, and group-based execution are also out of scope.

## 9. Verify Milestone 5 Diagnostics

Diagnostics explain why existing pipeline candidates are available or
unavailable. They do not execute pipelines.

Recommended workflow:

```sh
/home/jim/.local/bin/uv run gst-device-explorer devices
/home/jim/.local/bin/uv run gst-device-explorer audio-inputs
/home/jim/.local/bin/uv run gst-device-explorer audio-outputs
/home/jim/.local/bin/uv run gst-device-explorer groups
```

Inspect candidates, then inspect diagnostics if a candidate is missing or you
want to see required elements:

```sh
/home/jim/.local/bin/uv run gst-device-explorer pipeline video /dev/video0
/home/jim/.local/bin/uv run gst-device-explorer pipeline video /dev/video0 --diagnostics
/home/jim/.local/bin/uv run gst-device-explorer pipeline video /dev/video0 --diagnostics --json

/home/jim/.local/bin/uv run gst-device-explorer pipeline audio-input hw:0,0
/home/jim/.local/bin/uv run gst-device-explorer pipeline audio-input hw:0,0 --diagnostics
/home/jim/.local/bin/uv run gst-device-explorer pipeline audio-input hw:0,0 --diagnostics --json

/home/jim/.local/bin/uv run gst-device-explorer pipeline audio-output hw:0,0
/home/jim/.local/bin/uv run gst-device-explorer pipeline audio-output hw:0,0 --diagnostics
/home/jim/.local/bin/uv run gst-device-explorer pipeline audio-output hw:0,0 --diagnostics --json
```

When diagnostics report missing GStreamer elements, check them directly:

```sh
gst-inspect-1.0 autovideosink
gst-inspect-1.0 alsasink
```

Then dry-run and run the selected candidate:

```sh
/home/jim/.local/bin/uv run gst-device-explorer run video /dev/video0 --dry-run
/home/jim/.local/bin/uv run gst-device-explorer run video /dev/video0

/home/jim/.local/bin/uv run gst-device-explorer run audio-input hw:0,0 --dry-run
/home/jim/.local/bin/uv run gst-device-explorer run audio-input hw:0,0

/home/jim/.local/bin/uv run gst-device-explorer run audio-output hw:0,0 --dry-run
/home/jim/.local/bin/uv run gst-device-explorer run audio-output hw:0,0
```

## 10. Verify Milestone 6 Device Profiles

Device profiles summarize discovered device information, group membership,
pipeline candidate availability, and suggested next commands in one view.

Discover devices and groups first:

```sh
/home/jim/.local/bin/uv run gst-device-explorer devices
/home/jim/.local/bin/uv run gst-device-explorer audio-inputs
/home/jim/.local/bin/uv run gst-device-explorer audio-outputs
/home/jim/.local/bin/uv run gst-device-explorer groups
```

Inspect profiles:

```sh
/home/jim/.local/bin/uv run gst-device-explorer profile video /dev/video0
/home/jim/.local/bin/uv run gst-device-explorer profile video /dev/video0 --json

/home/jim/.local/bin/uv run gst-device-explorer profile audio-input hw:0,0
/home/jim/.local/bin/uv run gst-device-explorer profile audio-input hw:0,0 --json

/home/jim/.local/bin/uv run gst-device-explorer profile audio-output hw:0,0
/home/jim/.local/bin/uv run gst-device-explorer profile audio-output hw:0,0 --json
```

A profile includes:

- device kind, identifier, and display name when available
- subsystem metadata
- capabilities summary (video only: formats, max resolution, frame rates, mode count)
- pipeline candidate summary (available and unavailable, with missing elements listed)
- informational group membership when the endpoint belongs to a composite group
- suggested next commands

Profiles are read-only summaries. They do not execute pipelines and do not
change candidate or diagnostic behavior.

After inspecting a profile, follow the suggested next commands to inspect
candidates, view diagnostics, or dry-run the selected candidate:

```sh
/home/jim/.local/bin/uv run gst-device-explorer pipeline video /dev/video0
/home/jim/.local/bin/uv run gst-device-explorer pipeline video /dev/video0 --diagnostics
/home/jim/.local/bin/uv run gst-device-explorer run video /dev/video0 --dry-run
```

Group profiles are not implemented. Group membership shown in endpoint
profiles is informational only.

## 11. Verify Milestone 9 Bounded Capture

Bounded capture writes short validation files from generated candidates only.
Always dry-run first:

```sh
/home/jim/.local/bin/uv run gst-device-explorer capture video /dev/video0 --duration 5 --output sample.avi --dry-run
/home/jim/.local/bin/uv run gst-device-explorer capture audio-input hw:0,0 --duration 5 --output sample.wav --dry-run
```

Run the selected capture candidate only after inspecting the generated command:

```sh
/home/jim/.local/bin/uv run gst-device-explorer capture video /dev/video0 --duration 5 --output sample.avi
/home/jim/.local/bin/uv run gst-device-explorer capture audio-input hw:0,0 --duration 5 --output sample.wav
```

Capture requires `--duration` and `--output`. The duration must be a positive
number of seconds, and existing output files are rejected. Video capture uses a
simple AVI candidate in this first slice; audio input capture writes WAV.

Capture is endpoint-based. It does not accept arbitrary raw pipelines, does not
overwrite files, does not perform group-based capture, does not synchronize
audio and video, and does not create background or long-running recordings.

## 12. Verify Milestone 10 Composite Device Validation

Inspect groups first, then validate a selected group by ID:

```sh
/home/jim/.local/bin/uv run gst-device-explorer groups
/home/jim/.local/bin/uv run gst-device-explorer validate group <group-id>
/home/jim/.local/bin/uv run gst-device-explorer validate group <group-id> --json
```

Group validation summarizes existing endpoint profiles for the group's members.
It reports a group status, endpoint statuses, candidate counts, missing
GStreamer elements, grouping evidence, and suggested endpoint-level next
commands.

Validation does not run pipelines, does not run capture, and does not generate
group-level pipelines. Use endpoint commands such as `profile`, `recommend`,
`run`, and `capture` after validation when you want to inspect or test one
specific endpoint.

## 13. Verify Milestone 11 Presets

Inspect the built-in preset catalog and ask for command suggestions:

```sh
/home/jim/.local/bin/uv run gst-device-explorer preset list
/home/jim/.local/bin/uv run gst-device-explorer preset list --json
/home/jim/.local/bin/uv run gst-device-explorer preset show camera-preview
/home/jim/.local/bin/uv run gst-device-explorer preset command camera-preview video /dev/video0
/home/jim/.local/bin/uv run gst-device-explorer preset command short-video-capture video /dev/video0 --duration 5 --output sample.avi
```

Presets suggest existing `gst-device-explorer` commands. They do not run those
commands, do not accept raw GStreamer pipelines, do not add user-authored preset
files, and do not introduce group execution.

## 14. Verify Milestone 12 Configuration

Inspect configuration search paths, show defaults, and validate the effective
configuration:

```sh
/home/jim/.local/bin/uv run gst-device-explorer config path
/home/jim/.local/bin/uv run gst-device-explorer config show
/home/jim/.local/bin/uv run gst-device-explorer config show --json
/home/jim/.local/bin/uv run gst-device-explorer config validate
/home/jim/.local/bin/uv run gst-device-explorer config validate --json
```

Validate an explicit TOML file:

```sh
/home/jim/.local/bin/uv run gst-device-explorer config validate --config ./gst-device-explorer.toml
/home/jim/.local/bin/uv run gst-device-explorer config validate --config ./gst-device-explorer.toml --json
```

Configuration is optional. Milestone 12 validates and displays preferences only;
preferences do not alter candidate generation, ranking, presets, reports,
capture, validation, or execution yet. Config files cannot introduce arbitrary
pipelines, shell commands, scripts, package installation, or system
configuration changes.

## 15. Verify Milestone 13 JSON Schema Envelope

Inspect wrapped JSON output and schema discovery:

```sh
/home/jim/.local/bin/uv run gst-device-explorer config path --json
/home/jim/.local/bin/uv run gst-device-explorer config show --json
/home/jim/.local/bin/uv run gst-device-explorer config validate --json
/home/jim/.local/bin/uv run gst-device-explorer preset list --json
/home/jim/.local/bin/uv run gst-device-explorer schema list
/home/jim/.local/bin/uv run gst-device-explorer schema show json-envelope
/home/jim/.local/bin/uv run gst-device-explorer schema show json-envelope --json
```

Selected config, preset, and schema JSON commands include the stable envelope
fields `schema_version`, `tool_version`, `kind`, and `data`. The nested `data`
payload remains command-specific, and full JSON Schema documents for every
payload are deferred.

## 16. Verify Milestone 14 Extended JSON Envelope Coverage

Inspect representative older command families now wrapped in the shared
envelope:

```sh
/home/jim/.local/bin/uv run gst-device-explorer env --json
/home/jim/.local/bin/uv run gst-device-explorer devices --json
/home/jim/.local/bin/uv run gst-device-explorer audio-inputs --json
/home/jim/.local/bin/uv run gst-device-explorer audio-outputs --json
/home/jim/.local/bin/uv run gst-device-explorer report --json
/home/jim/.local/bin/uv run gst-device-explorer schema list --json
```

These commands preserve their command-specific payload under `data`. Text output
is unchanged, and payload-specific JSON Schema documents remain deferred.

## 17. Verify Milestone 15 TUI Review Mode

Check the TUI parser and non-interactive snapshot:

```sh
/home/jim/.local/bin/uv run gst-device-explorer tui --help
/home/jim/.local/bin/uv run gst-device-explorer tui --snapshot
```

If the terminal supports curses, run the interactive TUI:

```sh
/home/jim/.local/bin/uv run gst-device-explorer tui
```

The TUI is read-only. It summarizes environment, devices, composite groups,
presets, configuration, schema kinds, and suggested commands. It does not run
pipelines, capture media, execute presets, edit configuration, install
packages, or change system settings.

## 18. Verify Milestone 18 Support Bundle Export

Create a support bundle directory:

```sh
/home/jim/.local/bin/uv run gst-device-explorer support bundle --output ./my-support-bundle
```

Inspect the bundle contents:

```sh
ls ./my-support-bundle/
cat ./my-support-bundle/manifest.json
cat ./my-support-bundle/report/system-report.txt
cat ./my-support-bundle/report/system-report.json
cat ./my-support-bundle/inventory/devices.json
```

Expected layout:

```text
my-support-bundle/
├── manifest.json
├── report/
│   ├── system-report.json
│   └── system-report.txt
├── inventory/
│   ├── environment.json
│   ├── devices.json
│   ├── audio-inputs.json
│   ├── audio-outputs.json
│   ├── groups.json
│   └── grouping-metadata.json
├── config/
│   ├── config-path.json
│   ├── config-show.json
│   └── config-validate.json
├── schemas/
│   └── schema-list.json
├── suggestions/
│   └── suggestions-list.json
└── tui/
    └── snapshot.txt
```

The bundle output path must not already exist. The parent directory must exist.

The support bundle does not run GStreamer pipelines, does not capture media,
and does not execute suggested commands.

## 19. Current Limitations

- GUI is not implemented.
- Audio loopback is not implemented.
- Group-based pipeline generation is not implemented.
- Group-based pipeline execution is not implemented.
- Group-based capture is not implemented.
- Direct preset execution is not implemented.
- Config-driven behavior changes are not implemented.
- TUI execution/capture/config editing controls are not implemented.
- Complete JSON Schema files for every payload are not implemented.
- Stable JSON error envelopes are not implemented.
- Synchronized audio/video capture is not implemented.
- Preview-window lifecycle management is not implemented.
- PulseAudio and PipeWire probing are not implemented.
- ASR, TTS, WebRTC, effects, echo cancellation, general-purpose recording workflows, and
  synchronized audio/video workflows are not implemented.
- Empty output may mean tools are missing, no matching hardware is present,
  permissions prevent access, or the device is not yet supported.
