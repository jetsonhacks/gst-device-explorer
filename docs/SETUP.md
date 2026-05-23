# Setup

`gst-device-explorer` is a Python project managed with `uv`.

## Python / uv Setup

Install or activate `uv`, then set up the project and run the current CLI
commands:

```sh
uv sync
uv run python -m pytest
uv run gst-device-explorer --help
uv run gst-device-explorer env
uv run gst-device-explorer devices
uv run gst-device-explorer video /dev/video0
```

## System Tools

Some probes depend on external Linux tools. If a tool is missing, the related
probe should return an empty result or unavailable facts rather than raising an
exception.

On Ubuntu and Jetson systems, these packages are required or useful:

```sh
sudo apt update
sudo apt install -y v4l-utils alsa-utils gstreamer1.0-tools
```

These packages provide:

- `v4l-utils`: provides `v4l2-ctl`
- `alsa-utils`: provides `arecord` and `aplay`
- `gstreamer1.0-tools`: provides `gst-launch-1.0` and `gst-inspect-1.0`

## Optional GStreamer Plugins

Useful pipeline exploration may require additional GStreamer plugins, depending
on the system and attached devices.

On generic Ubuntu systems, commonly useful packages include:

- `gstreamer1.0-plugins-base`
- `gstreamer1.0-plugins-good`
- `gstreamer1.0-plugins-bad`
- `gstreamer1.0-plugins-ugly`
- `gstreamer1.0-libav`

On Jetson systems, NVIDIA-specific GStreamer elements such as `nvvidconv`,
`nvjpegdec`, `nvv4l2decoder`, `nveglglessink`, and `nv3dsink` come from JetPack
/ NVIDIA multimedia packages, not this Python project.

## Verification Commands

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

## Current Project Status

The current implementation is still early. Empty output may mean:

- The system tool is missing
- No matching hardware is present
- Permissions prevent access
- The device exists but is not yet supported by the current probe
