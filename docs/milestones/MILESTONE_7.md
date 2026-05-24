# Milestone 7 — Exportable System Reports

Status: Complete

Target version: `v0.7.0`

## Theme

Capture the whole media system state into one report.

## Goal

Add a `report` command that gathers existing discovery, grouping, profile, candidate, and diagnostic information into a single structured system report.

The first implementation should be JSON-first and should reuse the existing project models and builders wherever possible.

The report should be useful for:

- GitHub issues
- hardware validation
- comparing Jetson systems
- debugging remote machines
- documenting known-good setups
- future GUI integrations
- future agent integrations

## Guiding Principles

Milestone 7 should continue the existing project direction:

- Probe first, build later.
- Normalize raw system output into structured models before making decisions.
- Treat pipeline candidates as structured objects, not just strings.
- Treat CLI, JSON, future GUI, and future agent integrations as renderers over shared core models.
- Prefer capability detection over hard-coded JetPack version checks.
- Avoid Reachy-specific behavior.
- Avoid arbitrary user-supplied pipeline execution.
- Keep grouping evidence-based and explainable.
- Keep the milestone narrow and testable.
- Use synthetic tests that do not require real hardware.

## First Implementation Slice

The first slice should add a minimal structured system report.

Recommended scope:

- Add a structured report model, likely named `SystemReport`.
- Add a report builder that gathers existing facts from discovery, grouping, profiles, candidates, and diagnostics.
- Add JSON report output.
- Add a CLI command:

```sh
gst-device-explorer report --json
```

Optional, only if small and natural:

```sh
gst-device-explorer report
```

Defer file output unless it is trivial:

```sh
gst-device-explorer report --output report.json
```

The first slice should focus on the data shape and JSON output before polishing text output.

## Report Contents

The initial report should include, where existing project functionality already provides the information:

- report kind or name
- tool version, if easily available
- system environment summary
- discovered video devices
- discovered audio input devices
- discovered audio output devices
- composite device groups
- endpoint profiles
- pipeline candidate summaries
- diagnostic summaries
- simple missing GStreamer element aggregation
- suggested next checks or commands, if already available from profiles or diagnostics

The report should not invent new probing behavior just to fill every field.

If some information is unavailable, the report should represent that cleanly rather than failing unnecessarily.

## JSON-First Direction

The first report implementation should prioritize JSON because the report is intended to serve multiple future consumers:

- command-line users
- bug reports
- automated validation scripts
- future GUI tools
- future agent integrations

The JSON shape should be practical and stable-looking, but this milestone does not need to formalize a public schema contract yet.

Formal JSON schemas and compatibility policy are deferred to a later schema-stability milestone.

## Suggested JSON Shape

A first report shape might look like this:

```json
{
  "kind": "system_report",
  "tool_version": "0.7.0",
  "environment": {},
  "devices": {
    "video": [],
    "audio_inputs": [],
    "audio_outputs": []
  },
  "groups": [],
  "profiles": {
    "video": [],
    "audio_inputs": [],
    "audio_outputs": []
  },
  "diagnostics": {
    "missing_elements": [],
    "candidate_summaries": []
  },
  "suggested_next_commands": []
}
```

This is only a starting point. The implementation should follow the existing project model and JSON conventions.

## Tests

Milestone 7 should use synthetic tests.

Tests should verify:

- a `SystemReport` can be constructed from synthetic discovery, grouping, profile, and diagnostic data
- JSON serialization produces the expected top-level shape
- `gst-device-explorer report --json` works in a mocked or synthetic environment
- report generation does not run pipelines
- existing behavior for devices, groups, profiles, candidates, diagnostics, and execution remains unchanged

The tests should not require:

- a real camera
- a real microphone
- a real speaker
- GStreamer hardware access
- ALSA hardware access
- Jetson-specific hardware
- Reachy Mini hardware

## Non-Goals

Milestone 7 should not add:

- pipeline execution behavior
- recording media
- arbitrary user-supplied pipeline execution
- package installation
- system configuration changes
- new video pipeline families
- new audio pipeline families
- audio loopback
- group-based execution
- group-based pipeline generation
- group validation behavior
- recommendation or ranking behavior
- capture tests
- presets
- configuration files or preferences
- schema formalization
- TUI behavior
- GUI behavior
- MCP or agent descriptor generation
- ASR
- TTS
- WebRTC
- PulseAudio support
- PipeWire support
- effects
- echo cancellation
- synchronized audio/video capture
- Reachy-specific hard-coding
- JetPack-version-specific hard-coding

## Deferred Work

Possible follow-on work after the first slice:

- polished text report rendering
- `--output report.json`
- report examples in documentation
- missing-element grouping improvements
- report-level suggested next commands
- report comparison workflow
- group-level report summaries
- stable JSON schema
- schema versioning
- GUI-facing report consumption
- agent-facing report consumption

## Completion Criteria

Milestone 7 can be considered complete when:

- `SystemReport` or equivalent structured model exists
- report generation reuses existing discovery, grouping, profile, candidate, and diagnostic functionality
- `gst-device-explorer report --json` emits a useful structured report
- synthetic tests cover report generation and JSON output
- report generation does not execute pipelines
- documentation describes the report command, scope, and non-goals
- the full test suite passes

## Validation Command

Run:

```sh
/home/jim/.local/bin/uv run python -m pytest
```

Expected final Codex report should include:

- files changed
- report model added
- report builder behavior
- CLI behavior added
- JSON shape chosen
- tests added
- test result
- deferred work
