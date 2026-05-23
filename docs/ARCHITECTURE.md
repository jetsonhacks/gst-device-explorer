# Architecture

`gst-device-explorer` should be organized around separate layers that each own a
specific responsibility. The goal is to make probing, modeling, profile
selection, pipeline construction, and presentation evolve independently.

The first implementation domain is GStreamer-oriented media exploration. The
architecture should also leave room for future exploration plugins without
turning Milestone 1 into a generic hardware inventory system.

The core architecture should separate the exploration framework from the initial
media-specific probes. GStreamer video/audio support is the first domain, not
the only possible domain.

## Probes

Probes inspect the local system and collect raw information from tools and APIs
such as GStreamer, v4l2, ALSA, PulseAudio, PipeWire, and platform-specific
commands. They should avoid making final product decisions.

Initial probes should focus on video inputs, audio inputs, audio outputs, and
the local GStreamer environment.

## Normalized Models

Normalized models convert raw probe output into consistent representations of
devices, capabilities, formats, environment facts, warnings, and availability.
Later layers should depend on these models instead of parsing command output
directly.

## Profiles

Profiles express preferences for particular platforms, operating systems, and
workflows. Example profiles include generic Linux, NVIDIA Jetson running
different JetPack / Linux for Tegra versions, and other platform profiles added
later.

A Jetson profile, for example, may prefer hardware-accelerated or
Jetson-specific GStreamer elements when the local system reports that they are
available. Profiles should capture preferences and known-good patterns, not
random patches.

## Pipeline Builders

Pipeline builders consume normalized models and profiles to produce structured
pipeline candidates. Builders should record assumptions, requirements, ranking
signals, and warnings alongside the rendered GStreamer pipeline string.

Pipeline builders are part of the initial media exploration domain. Other future
exploration plugins may have their own candidate builders or recommendation
objects.

## Grouping Engine

The grouping pipeline has two core-layer steps:

```text
discovery -> grouping metadata -> grouping engine -> composite devices
```

The grouping metadata step converts discovered `Device` objects into
`GroupableDevice` records. It may read directly available normalized metadata or
safe sysfs files, including V4L2 video device paths and ALSA sound device
paths, but it should not call shell commands or depend on optional external
tools.

The grouping engine consumes normalized grouping metadata and emits
`CompositeDevice` objects. It should not call shell commands, parse raw probe
output, or depend on live hardware directly.

Grouping is evidence-based. A group records member `DeviceRef` objects,
confidence, and `GroupingEvidence` so renderers can show uncertainty instead of
hiding it. The grouping layer enriches discovery; it does not replace raw
individual device views.

Milestone 3 emits exact USB-device groups for devices sharing the same USB
parent path. It can also emit a parent USB-family group above multiple exact
USB-device groups when they share a meaningful USB ancestor, USB vendor ID, and
non-generic product-family token. Devices without that evidence remain
independent; for example, a separate Orbbec Femto Bolt attached alongside a
robot is not folded into the robot's USB-family group.

The CLI renders computed groups through `groups`, `groups --json`, `group
<group-id>`, and `group <group-id> --json`. It can also render the normalized
metadata feeding the grouping engine through `groups --metadata` and
`groups --metadata --json`. Group rendering is presentation only; group-based
pipeline generation and execution are outside the current scope.

## Renderers

Renderers turn normalized models and pipeline candidates into user-facing
representations. The first renderer is expected to be a CLI. A future GUI should
use the same underlying models and builders rather than duplicating discovery or
pipeline logic.

## Execution Flow

Safe execution is a separate layer that consumes structured pipeline candidates.
The CLI acts as a renderer/controller: it asks probes and builders for data,
renders the selected plan for the user, and delegates subprocess handling to the
execution helper.

```text
probe device
  -> normalize capabilities
  -> build ranked PipelineCandidate objects
  -> select candidate
  -> create ExecutionPlan
  -> render display command
  -> execute argv
```

Pipeline generation and pipeline execution remain separate. A
`PipelineCandidate` contains both a display command and an argv representation.
The display command is for humans; the argv list is what execution passes to
`subprocess.Popen(argv)`.

## Exploration Plugins

The core architecture should allow future exploration plugins to add new probe
families, normalized models, profiles, builders, and renderers. A later plugin
might inspect robot hardware such as actuators, Dynamixel servos, sensors, or
other device classes.

This extensibility should remain secondary to the first domain. Milestone 1
should establish GStreamer-oriented device exploration first and leave clean
extension points for hardware exploration later.

## Separation of Concerns

Each layer should communicate through explicit data structures. Probes should not
format CLI output. Renderers should not inspect hardware directly. Profiles
should guide selection without hiding probe failures or capability gaps. This
separation keeps Milestone 1 small while leaving room for richer interfaces and
future exploration plugins later.
