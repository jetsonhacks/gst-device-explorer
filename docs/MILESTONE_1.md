# Milestone 1

Milestone 1 begins with documentation and project metadata, then later adds the
first CLI/probe foundation for GStreamer-oriented media exploration.

## This Commit

This first commit is expected to create only:

- Initial README
- Minimal uv-compatible `pyproject.toml`
- Development principles
- Specification
- Architecture notes
- Milestone 1 scope

No implementation code is expected in this first commit.

## Later Milestone 1 Work

Later work in Milestone 1 may add a narrow CLI and initial probes for video
input discovery, audio input discovery, audio output discovery, GStreamer
environment inspection, and pipeline candidate generation.

That later work should remain focused on discovery and structured output. It
should not add GUI support, live preview execution, recording, editing, or full
media playback application behavior.

## Profile Awareness

Milestone 1 should account for the concept of profiles in the design. Profiles
describe platform and operating-system-specific behavior, such as generic Linux
or Jetson / JetPack / Linux for Tegra behavior.

Initial implementation work may introduce only the smallest useful profile
foundation. Implementation should prefer capability detection over hard-coded
version checks. Profiles should express preferences and known-good patterns, not
random patches.

## Extensibility Boundary

The project should be designed as GStreamer-oriented device exploration first,
extensible hardware exploration later. Future exploration plugins may inspect
robot hardware, actuators, Dynamixel servos, sensors, or other device classes.

That plugin system is not part of Milestone 1 implementation. No non-media
exploration plugins are expected in this milestone.
