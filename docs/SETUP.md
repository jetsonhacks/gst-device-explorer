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

## 7. Current Limitations

- GUI is not implemented.
- Audio pipeline generation is not implemented.
- Audio pipeline execution is not implemented.
- Preview-window lifecycle management is not implemented.
- PulseAudio and PipeWire probing are not implemented yet.
- Empty output may mean tools are missing, no matching hardware is present,
  permissions prevent access, or the device is not yet supported.
