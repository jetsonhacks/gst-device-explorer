# Setup

`gst-device-explorer` is a GUI-first media endpoint explorer for cameras,
microphones, speakers, and composite USB devices. It generates GStreamer
commands from discovered device settings and lets you preview or test selected
configurations.

## Supported Systems

- NVIDIA Jetson running Jetson Linux 38+
- Ubuntu 24.04+

The GUI requires an X11 or Wayland display. The CLI is available for headless
and scripted use.

## Prerequisites

### System packages

Install Linux media tools before running the project:

```sh
sudo apt update
sudo apt install -y v4l-utils alsa-utils gstreamer1.0-tools
```

These provide:

- `v4l-utils` — `v4l2-ctl` for V4L2 camera device discovery
- `alsa-utils` — `arecord` and `aplay` for ALSA audio device discovery
- `gstreamer1.0-tools` — `gst-launch-1.0` and `gst-inspect-1.0` for GStreamer
  inspection and pipeline execution

### Optional GStreamer plugins

Generic Ubuntu systems may need additional GStreamer plugins for pipeline
execution:

```sh
sudo apt install -y \
  gstreamer1.0-plugins-base \
  gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-bad \
  gstreamer1.0-plugins-ugly \
  gstreamer1.0-libav
```

On Jetson systems, NVIDIA-specific GStreamer elements (`nvvidconv`, `nvjpegdec`,
`nvv4l2decoder`, `nveglglessink`, `nv3dsink`) come from JetPack / NVIDIA
multimedia packages, not this project.

### uv

Install `uv` if not already available:

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or with `wget`:

```sh
wget -qO- https://astral.sh/uv/install.sh | sh
```

Restart your shell or follow the installer instructions to update `PATH`.

## Install Project Dependencies

```sh
git clone https://github.com/jetsonhacks/gst-device-explorer.git
cd gst-device-explorer
uv sync
```

`uv sync` installs all runtime dependencies including PySide6. No extra flags
are required.

## Launch the GUI

```sh
uv run gst-device-explorer
```

The GUI opens a sidebar with discovered cameras, audio inputs, audio outputs,
and composite device groups. Select any item to open the Explore pane for that
device.

To launch with deterministic demo data (no hardware required):

```sh
uv run gst-device-explorer --demo
```

## Verify Camera Discovery

Camera endpoints appear in the GUI sidebar under **Cameras** and inside any
composite device groups they belong to.

To check camera discovery from the command line:

```sh
uv run gst-device-explorer-cli devices
v4l2-ctl --list-devices
```

Select a camera in the GUI to open the camera Explore pane. It shows:

- pixel format, image size, and frame duration selectors derived from the
  selected device
- generated GStreamer pipeline for the current selections
- copy pipeline button
- active camera controls, including writable controls where the device reports
  them as writable and active; inactive or read-only controls are shown but
  cannot be changed

## Verify Camera Preview and Pipeline Copy

In the camera Explore pane, select a pixel format, image size, and frame
duration. The generated pipeline updates automatically. Click **Copy Pipeline**
to copy the command to the clipboard.

To generate and inspect a pipeline from the CLI:

```sh
uv run gst-device-explorer-cli pipeline video /dev/video0
uv run gst-device-explorer-cli run video /dev/video0 --dry-run
uv run gst-device-explorer-cli run video /dev/video0
```

Press Ctrl+C in the terminal to stop a running pipeline.

## Verify Audio Input Discovery

Audio input endpoints appear in the GUI sidebar under **Audio Inputs**.

To check audio input discovery from the command line:

```sh
uv run gst-device-explorer-cli audio-inputs
arecord -l
```

Select an audio input in the GUI. The audio input Explore pane shows supported
format, sample rate, and channel count selectors, a generated input pipeline,
and a bounded audio input activity test that checks whether the endpoint opens
without recording.

To inspect and run an audio input test from the CLI:

```sh
uv run gst-device-explorer-cli pipeline audio-input hw:0,0
uv run gst-device-explorer-cli run audio-input hw:0,0 --dry-run
uv run gst-device-explorer-cli run audio-input hw:0,0
```

The audio input activity test runs without audible output. Press Ctrl+C to stop.

## Verify Audio Output Discovery and Testing

Audio output endpoints appear in the GUI sidebar under **Audio Outputs**.

To check audio output discovery from the command line:

```sh
uv run gst-device-explorer-cli audio-outputs
aplay -l
```

Select an audio output in the GUI. The audio output Explore pane shows
supported format, sample rate, and channel count selectors, a generated output
pipeline, and an audio output test that plays a brief generated tone or a
selected local file.

To inspect and run an audio output test from the CLI:

```sh
uv run gst-device-explorer-cli pipeline audio-output hw:0,0
uv run gst-device-explorer-cli run audio-output hw:0,0 --dry-run
uv run gst-device-explorer-cli run audio-output hw:0,0
```

The audio output test produces a 440 Hz sine tone. Press Ctrl+C to stop.

## CLI Verification Path

The full CLI is available for power users, headless systems, and scripts:

```sh
uv run gst-device-explorer-cli --help
```

**Environment and discovery:**

```sh
uv run gst-device-explorer-cli env
uv run gst-device-explorer-cli devices
uv run gst-device-explorer-cli audio-inputs
uv run gst-device-explorer-cli audio-outputs
uv run gst-device-explorer-cli groups
uv run gst-device-explorer-cli groups --metadata
```

Composite device groups represent evidence-based physical groupings — for
example, a USB device that exposes a camera, microphone, and speaker as
separate Linux endpoints. Use `groups --metadata` to inspect the normalized
metadata feeding the grouping engine. Inspect or validate a specific group
by ID:

```sh
uv run gst-device-explorer-cli group <group-id>
uv run gst-device-explorer-cli validate group <group-id>
uv run gst-device-explorer-cli validate group <group-id> --json
```

**Pipeline candidates and diagnostics:**

```sh
uv run gst-device-explorer-cli pipeline video /dev/video0
uv run gst-device-explorer-cli pipeline video /dev/video0 --diagnostics
uv run gst-device-explorer-cli pipeline video /dev/video0 --json --limit 1

uv run gst-device-explorer-cli pipeline audio-input hw:0,0
uv run gst-device-explorer-cli pipeline audio-input hw:0,0 --diagnostics

uv run gst-device-explorer-cli pipeline audio-output hw:0,0
uv run gst-device-explorer-cli pipeline audio-output hw:0,0 --diagnostics
```

When diagnostics report missing GStreamer elements, check them directly:

```sh
gst-inspect-1.0 autovideosink
gst-inspect-1.0 alsasink
```

**Device profiles:**

```sh
uv run gst-device-explorer-cli profile video /dev/video0
uv run gst-device-explorer-cli profile video /dev/video0 --json

uv run gst-device-explorer-cli profile audio-input hw:0,0
uv run gst-device-explorer-cli profile audio-output hw:0,0
```

A profile summarizes device identity, capabilities, pipeline candidate
availability, group membership, and suggested next commands.

**Bounded capture** (requires `--duration` and `--output`; does not overwrite
existing files):

```sh
uv run gst-device-explorer-cli capture video /dev/video0 --duration 5 --output sample.avi --dry-run
uv run gst-device-explorer-cli capture video /dev/video0 --duration 5 --output sample.avi

uv run gst-device-explorer-cli capture audio-input hw:0,0 --duration 5 --output sample.wav --dry-run
uv run gst-device-explorer-cli capture audio-input hw:0,0 --duration 5 --output sample.wav
```

Capture does not accept arbitrary pipelines, does not overwrite files, and does
not perform group-based or synchronized capture.

**Other CLI commands:**

```sh
uv run gst-device-explorer-cli preset list
uv run gst-device-explorer-cli preset show camera-preview
uv run gst-device-explorer-cli config show
uv run gst-device-explorer-cli schema list
uv run gst-device-explorer-cli tui
uv run gst-device-explorer-cli report
uv run gst-device-explorer-cli support bundle --output ./my-support-bundle
```

The support bundle collects environment, device inventory, pipeline candidates,
profiles, configuration, schema, and system report into a directory for
diagnostics or support use. The output path must not already exist.

## Developer Validation

Run the test suite:

```sh
uv run python -m pytest
```

Check the GStreamer environment and specific elements:

```sh
uv run gst-device-explorer-cli env
gst-inspect-1.0 v4l2src
gst-inspect-1.0 autovideosink
gst-inspect-1.0 alsasink
gst-inspect-1.0 nvvidconv    # Jetson only; expected to fail on generic Linux
```

Generate a system report or export a support bundle:

```sh
uv run gst-device-explorer-cli report
uv run gst-device-explorer-cli support bundle --output ./my-support-bundle
```

## Troubleshooting

**uv not found**

Restart your shell after installing `uv`, or use the absolute path the
installer reports (typically `~/.local/bin/uv`):

```sh
~/.local/bin/uv run gst-device-explorer
```

**PySide6 import error**

Run `uv sync` from the project root. PySide6 is a default dependency and
requires no extra flags.

**Missing GStreamer elements**

If pipeline candidates report missing elements, inspect them directly:

```sh
gst-inspect-1.0 autovideosink
gst-inspect-1.0 alsasink
gst-inspect-1.0 nvvidconv
```

Install missing plugins from the Optional GStreamer Plugins section, or check
whether the element is part of JetPack on Jetson systems.

**No camera devices found**

Check that the camera is connected and visible:

```sh
v4l2-ctl --list-devices
ls /dev/video*
```

If `/dev/video*` nodes exist but the application reports nothing, your user may
need `video` group membership:

```sh
sudo usermod -aG video $USER
```

Log out and back in for the change to take effect.

**No audio devices found**

Check ALSA device lists:

```sh
arecord -l
aplay -l
```

If ALSA devices exist but are not discovered, check `audio` group membership:

```sh
sudo usermod -aG audio $USER
```

**All commands return empty output**

Confirm that required system tools are installed:

```sh
which v4l2-ctl
which arecord
which aplay
which gst-launch-1.0
```

If any tool is missing, install the corresponding package from the System
packages section above.
