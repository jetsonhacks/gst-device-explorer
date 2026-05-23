# Pipeline Candidates

## Purpose

Pipeline candidates are recommendations, not executed commands. They describe
possible GStreamer pipelines that a user or renderer can inspect before any
future execution feature exists.

A candidate should explain why it was suggested, what it requires, what profile
influenced it, and what warnings apply. The rendered GStreamer command is one
part of the candidate, not the whole design.

## Inputs

Candidate builders consume normalized project models:

- `Device`
- `Capability`
- `EnvironmentFact`
- `Profile`

Builders should not parse raw probe output directly. Probes normalize system
facts first, profiles express preferences, and builders combine that information
into structured recommendations.

## Outputs

Candidate builders produce `PipelineCandidate` objects with:

- `purpose`
- `command`
- `confidence`
- `reasons`
- `warnings`
- `required_elements`
- `selected_profile`

The command should be constructed intentionally from model data and profile
preferences. It should not be rewritten afterward with ad hoc string patches.

## First Supported Media Case

The first implementation should focus on V4L2 video preview candidates.

The initial builder should take a discovered V4L2 video device, its video
capabilities, relevant GStreamer environment facts, and an applicable profile,
then produce one or more preview-oriented `PipelineCandidate` objects.

## Initial Profiles

The first profile concepts are:

- `generic-linux-video-preview`
- `jetson-video-preview`

`generic-linux-video-preview` should prefer broadly available GStreamer elements
for V4L2 preview on Linux.

`jetson-video-preview` may prefer NVIDIA elements when they are available and
the selected device capability is compatible. Jetson-specific behavior should be
chosen by capability and element availability, not only by JetPack version.

Profiles express preferences and known-good patterns. They are not buckets for
random patches.

## Known Jetson Lesson

JetPack 7 UVC MJPEG preview may benefit from this low-latency NVIDIA path:

```sh
v4l2src device=/dev/video0 io-mode=2 do-timestamp=true !
image/jpeg, width=1920, height=1080, framerate=60/1 !
jpegparse !
nvjpegdec !
video/x-raw(memory:NVMM), format=Y42B !
nvvidconv !
video/x-raw(memory:NVMM), format=NV12 !
nveglglessink sync=false
```

In this path:

- `io-mode=2` and `do-timestamp=true` are profile preferences for this
  low-latency preview case.
- `nveglglessink` is preferred over `nv3dsink` for preview resizing because it
  preserves aspect ratio better.
- The NVIDIA elements should be required elements for the candidate.
- The MJPEG capability, frame size, frame rate, and available elements should be
  reasons for selecting this candidate.

This lesson should become a `PipelineCandidate` with reasons and warnings, not a
hard-coded one-off patch.

## Non-Goals For First Pipeline Work

The first pipeline work should not:

- Execute pipelines
- Add preview windows
- Add recording
- Add audio pipelines yet
- Rewrite `gst-launch` strings after construction
