# Specification

## Purpose

`gst-device-explorer` is intended to provide a GStreamer-oriented exploration
environment where a user can discover and understand devices attached to a
computer.

The first real domain is media exploration through GStreamer. The project should
discover video inputs, audio inputs, audio outputs, and local GStreamer
environment details, then normalize that information and generate structured
pipeline candidates that can be inspected by users or rendered by tools.

## Audience

The initial audience is developers, integrators, and technical users working
with cameras, microphones, speakers, and GStreamer pipelines on Linux systems.
Generic Linux users should be supported, and NVIDIA Jetson users are a primary
concern because JetPack / Linux for Tegra environments often benefit from
platform-specific pipeline preferences.

## Initial Scope

Milestone 1 planning targets these areas:

- Video input discovery
- Audio input discovery
- Audio output discovery
- GStreamer environment inspection
- Pipeline candidate generation

Discovery should focus on gathering enough information to describe available
devices and propose reasonable pipeline candidates. Generated candidates should
be structured data that can later be rendered as CLI output, JSON, or UI views.

## Profiles

The project should be profile-aware. Profiles describe platform and
operating-system-specific behavior, including:

- Generic Linux
- NVIDIA Jetson running different JetPack / Linux for Tegra versions
- Other platform profiles added later

Profiles may describe Jetson / JetPack / Linux for Tegra behavior, but
implementation should prefer capability detection over hard-coded version
checks. Profiles should express preferences and known-good patterns. They should
not be used as arbitrary patch buckets or as a replacement for direct capability
detection.

## Extensibility

The architecture should leave room for future exploration plugins. Although the
first implementation focuses on GStreamer media devices, later plugins may
inspect other device classes, such as robot hardware, actuators, Dynamixel
servos, sensors, or other attached hardware.

This is an architectural goal, not Milestone 1 implementation work. The project
should be framed as GStreamer-oriented device exploration first, extensible
hardware exploration later.

## Non-Goals

The following are out of scope for now:

- GUI implementation
- Live preview execution
- Recording
- Editing
- Full media playback application behavior
- Generic hardware inventory as a first milestone

These may become future capabilities, but they should not shape the first
implementation phase beyond preserving clean interfaces.
