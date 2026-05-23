# Specification

## Purpose

`gst-device-explorer` is intended to discover media devices on Jetson and
generic Linux systems, normalize their capabilities, and generate structured
GStreamer pipeline candidates that can be inspected by users or rendered by
tools.

## Audience

The initial audience is developers, integrators, and technical users working
with cameras, microphones, speakers, and GStreamer pipelines on Linux systems.
Jetson users are a primary concern, but the project should remain useful on
generic Linux hardware.

## Initial Scope

Milestone 1 planning targets these areas:

- Video input discovery
- Audio input discovery
- Audio output discovery
- Environment inspection
- Pipeline candidate generation

Discovery should focus on gathering enough information to describe available
devices and propose reasonable pipeline candidates. Generated candidates should
be structured data that can later be rendered as CLI output, JSON, or UI views.

## Non-Goals

The following are out of scope for now:

- GUI implementation
- Live preview execution
- Recording
- Editing
- Full media playback application behavior

These may become future capabilities, but they should not shape the first
implementation phase beyond preserving clean interfaces.
