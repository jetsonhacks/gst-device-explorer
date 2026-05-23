# Development Principles

## Probe first, build later

The project should begin by observing the host system and its available media
devices before proposing pipelines or user-facing choices. Discovery data is the
foundation for later behavior.

## Normalize before deciding

Raw output from GStreamer, ALSA, PulseAudio, PipeWire, v4l2, and platform tools
should be converted into normalized models before ranking, filtering, or
presenting options.

## Profiles express preferences, not hacks

Profiles should encode platform and workflow preferences, such as Jetson-aware
pipeline element choices, without becoming scattered conditional workarounds.

## Pipeline candidates are structured objects, not just strings

A pipeline candidate should carry its purpose, required devices, assumptions,
ranking metadata, warnings, and rendered GStreamer string. The string is only
one representation of a richer object.

## CLI and future GUI are renderers

The CLI and any future GUI should present probe results, normalized models, and
pipeline candidates. They should not own discovery logic or pipeline construction
rules.

## Prefer capability detection over hard-coded JetPack version checks

When possible, the project should detect available elements, plugins, device
capabilities, and system services directly instead of branching on JetPack or
Linux distribution versions.

## Keep Milestone 1 narrow

Milestone 1 should establish the documentation, project metadata, and later a
small CLI/probe foundation. It should avoid GUI work, live preview, recording,
editing, and broad media playback features.
