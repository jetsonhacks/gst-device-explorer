# Architecture

`gst-device-explorer` should be organized around separate layers that each own a
specific responsibility. The goal is to make probing, modeling, pipeline
construction, and presentation evolve independently.

## Probes

Probes inspect the local system and collect raw information from tools and APIs
such as GStreamer, v4l2, ALSA, PulseAudio, PipeWire, and platform-specific
commands. They should avoid making final product decisions.

## Normalized Models

Normalized models convert raw probe output into consistent representations of
devices, capabilities, formats, environment facts, warnings, and availability.
Later layers should depend on these models instead of parsing command output
directly.

## Profiles

Profiles express preferences for particular platforms or workflows. A Jetson
profile, for example, may prefer hardware-accelerated or Jetson-specific
GStreamer elements when the local system reports that they are available.

## Pipeline Builders

Pipeline builders consume normalized models and profiles to produce structured
pipeline candidates. Builders should record assumptions, requirements, ranking
signals, and warnings alongside the rendered GStreamer pipeline string.

## Renderers

Renderers turn normalized models and pipeline candidates into user-facing
representations. The first renderer is expected to be a CLI. A future GUI should
use the same underlying models and builders rather than duplicating discovery or
pipeline logic.

## Separation of Concerns

Each layer should communicate through explicit data structures. Probes should not
format CLI output. Renderers should not inspect hardware directly. Profiles
should guide selection without hiding probe failures or capability gaps. This
separation keeps Milestone 1 small while leaving room for richer interfaces
later.
