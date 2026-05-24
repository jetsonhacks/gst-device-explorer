# Pipeline Candidates

## Purpose

Pipeline candidates are structured recommendations. They describe possible
GStreamer pipelines that a user or renderer can inspect before selecting one for
execution.

A candidate should explain why it was suggested, what it requires, what profile
label identifies its generation strategy, and what warnings apply. The rendered GStreamer command is one
part of the candidate, not the whole design.

## Inputs

Candidate builders consume normalized project models:

- `Device`
- `Capability`
- `EnvironmentFact`

Builders should not parse raw probe output directly. Probes normalize system
facts first, and builders combine that information into structured
recommendations.

## Outputs

Candidate builders produce `PipelineCandidate` objects with:

- `purpose`
- `candidate_id`
- `command`
- `argv`
- `confidence`
- `reasons`
- `warnings`
- `required_elements`
- `selected_profile`

The command should be constructed intentionally from model data and profile
preferences. It should not be rewritten afterward with ad hoc string patches.

`command` is the human-readable display form. `argv` is the subprocess execution
form. The execution path uses `argv`, not the rendered command string.

## Candidate IDs and Selection

Each candidate has a stable candidate ID that identifies the pipeline strategy
or family without encoding every caps detail.

Example IDs:

```text
jetson-uvc-mjpeg-nvjpeg-nveglglessink
generic-v4l2-mjpeg-jpegdec-autovideosink
generic-v4l2-yuyv-videoconvert-autovideosink
```

Candidate IDs are suitable for CLI selection, documentation, tests, and future
GUI use. Numeric indexes are convenient for quick terminal use, but they are
less stable than IDs because candidate ordering can change when capabilities or
available GStreamer elements change.

Candidate generation remains separate from execution. The `pipeline` command
renders candidates for inspection. The `run` command selects one generated
candidate, creates an execution plan, and executes the plan's argv form unless
`--dry-run` is requested.

The `capture` command follows the same generated-candidate boundary for short
file validation. It selects a generated capture candidate, creates an argv-based
execution plan, and runs it only when `--dry-run` is not requested. Capture does
not accept arbitrary raw pipeline strings.

## First Supported Media Case

The first implementation should focus on V4L2 video preview candidates.

The initial builder should take a discovered V4L2 video device, its video
capabilities, relevant GStreamer environment facts, and an applicable profile,
then produce one or more preview-oriented `PipelineCandidate` objects.

## Candidate Profile Labels

The first generation strategies are identified by these profile label strings:

- `generic-linux-video-preview`
- `jetson-video-preview`
- `generic-v4l2-video-capture`
- `generic-alsa-audio-input-capture`

`generic-linux-video-preview` identifies candidates using broadly available
GStreamer elements for V4L2 preview on Linux.

`jetson-video-preview` identifies candidates that use NVIDIA elements when they
are available and the selected device capability is compatible. Jetson-specific
behavior is selected by capability and element availability, not by JetPack
version.

These labels are string metadata stamped onto finished `PipelineCandidate`
objects. They identify the candidate's generation strategy and are not policy
objects consumed by builders.

## Capture Candidates

Bounded capture candidates are also `PipelineCandidate` objects. They include
the selected endpoint, duration, output path, file format, required elements,
warnings, and generated argv in the same structured fields used by preview and
test candidates.

The first capture slice supports:

- V4L2 video input to a simple AVI file
- ALSA audio input to a WAV file

Capture candidates require explicit duration and output path values before they
are built. Existing output files are rejected by the CLI before execution.
Capture remains endpoint-based and does not add group-level capture,
synchronized audio/video capture, background recording, long-running recording,
or arbitrary transcoding workflows.

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

## Non-Goals For Pipeline Candidate Generation

Pipeline candidate generation should not:

- Add preview windows
- Add general-purpose recording
- Rewrite `gst-launch` strings after construction
