# Milestone 10 — Composite Device Validation

Status: Implemented

## Theme

Validate a composite device without making group behavior magical.

## Goal

Add a group-oriented validation command that summarizes the health of all known endpoints in a composite device group.

Milestone 10 should help users understand whether a physical device made up of multiple Linux endpoints is usable, without introducing group-based pipeline execution or Reachy-specific behavior.

The goal is validation and explanation, not automation.

## Why This Matters

By Milestone 9, `gst-device-explorer` can:

- discover audio and video endpoints
- group related endpoints using evidence-based metadata
- generate structured pipeline candidates
- safely run selected bounded preview/test candidates
- explain candidate availability
- summarize endpoint profiles
- export whole-system reports
- recommend which candidate to try first
- perform short bounded capture tests

Many real devices appear as multiple Linux endpoints. A USB camera with microphones may expose:

- one or more `/dev/video*` nodes
- one or more ALSA capture devices
- one or more ALSA playback devices
- shared USB parent metadata
- shared manufacturer/product metadata

Milestone 10 should help answer:

```text
Does this composite device look healthy as a whole?
```

This is especially useful for:

- hardware validation
- GitHub issue reports
- remote debugging
- comparing Jetson systems
- checking known-good setups
- validating robot or sensor peripherals that expose multiple endpoints

## Guiding Principles

Milestone 10 should continue the existing project principles:

- Probe first, build later.
- Normalize raw system output into structured models before making decisions.
- Treat pipeline candidates as structured objects, not just strings.
- Treat CLI, JSON, future GUI, and future agent integrations as renderers over shared core models.
- Prefer capability detection over hard-coded JetPack version checks.
- Avoid Reachy-specific behavior.
- Avoid arbitrary user-supplied pipeline execution.
- Keep grouping evidence-based and explainable.
- Keep each milestone narrow and testable.
- Use synthetic tests that do not require real hardware.

Milestone 10 should also follow these group-validation-specific principles:

- Groups are informational and evidence-based.
- Validation should summarize endpoint status; it should not invent new group pipelines.
- Endpoint behavior remains endpoint-based.
- A group command may recommend endpoint-level next steps, but it must not run them automatically.
- The command should make grouping evidence visible and explainable.
- Missing endpoints or weak evidence should be represented clearly.
- The implementation should not hard-code Reachy Mini, Jetson models, or device-specific USB IDs.

## Scope

Milestone 10 should add composite group validation.

Possible commands:

```sh
gst-device-explorer validate group <group-id>
gst-device-explorer validate group <group-id> --json
```

Optional, only if small and consistent:

```sh
gst-device-explorer profile group <group-id>
gst-device-explorer report group <group-id>
```

Preferred first slice:

- Implement `validate group <group-id>`.
- Add JSON output.
- Add compact text output.
- Reuse existing group discovery, endpoint profiles, diagnostics, recommendations, and capture/report summaries where practical.
- Do not run preview, test, or capture pipelines.

## First Implementation Slice

The first slice should add a structured group validation model and a group validation command.

Recommended scope:

- Add a structured model, perhaps named `GroupValidation`.
- Add endpoint validation summaries for each video, audio input, and audio output endpoint in the group.
- Include group evidence and grouping method.
- Include endpoint profiles or profile-derived summaries.
- Include candidate availability summary.
- Include recommendation summary if available from Milestone 8 logic.
- Include missing GStreamer elements aggregated across the group.
- Include suggested endpoint-level next commands.
- Add text output.
- Add JSON output.
- Add synthetic tests.

Do not add group-level execution.

Do not add group-level capture.

Do not generate synchronized audio/video pipelines.

## Validation Contents

A group validation result should include:

- validation kind/name
- group ID
- group label or description, if available
- group type or grouping method
- grouping evidence
- endpoint counts
- video endpoints
- audio input endpoints
- audio output endpoints
- per-endpoint validation status
- candidate availability summary per endpoint
- recommendation summary per endpoint, if available
- missing GStreamer elements aggregated across endpoints
- suggested endpoint-level next commands
- warnings or ambiguities

A JSON shape might look like this:

```json
{
  "kind": "group_validation",
  "group_id": "usb-family-046d-0825",
  "group_label": "USB composite device",
  "grouping_method": "usb-parent-family",
  "evidence": [],
  "endpoints": {
    "video": [],
    "audio_inputs": [],
    "audio_outputs": []
  },
  "endpoint_summaries": [
    {
      "endpoint_kind": "video",
      "endpoint": "/dev/video0",
      "status": "ok",
      "available_candidate_count": 2,
      "recommended_candidate_id": "video-preview-generic",
      "missing_elements": [],
      "suggested_next_commands": []
    }
  ],
  "diagnostics": {
    "missing_elements": []
  },
  "suggested_next_commands": []
}
```

This is only a starting point. The implementation should follow existing project model and JSON conventions.

## Validation Status

Keep validation status simple and explainable.

Possible group-level statuses:

- `ok`
- `partial`
- `unavailable`
- `unknown`

Possible endpoint-level statuses:

- `ok`
- `no_candidates`
- `candidates_unavailable`
- `missing_capabilities`
- `unknown`

The exact names should follow existing project style.

A first implementation can derive status from simple facts:

- endpoint exists and has available candidates: `ok`
- endpoint exists but all candidates unavailable: `candidates_unavailable`
- endpoint exists but no candidates were generated: `no_candidates`
- endpoint lacks required capabilities or probe data: `missing_capabilities` or `unknown`
- group has mixed endpoint status: `partial`

Do not over-engineer the health model.

## Text Output Direction

Text output should be compact and practical.

Example:

```text
Composite group validation: usb-family-046d-0825

Status: partial
Grouping method: usb-parent-family

Endpoints:
- Video: /dev/video0
  Status: ok
  Available candidates: 2
  Recommended: video-preview-generic

- Audio input: hw:2,0
  Status: ok
  Available candidates: 1
  Recommended: audio-input-test

- Audio output: hw:2,0
  Status: candidates_unavailable
  Missing elements: autoaudiosink

Suggested next commands:
- gst-device-explorer profile video /dev/video0
- gst-device-explorer recommend video /dev/video0
- gst-device-explorer profile audio-input hw:2,0
```

If the group ID is not found:

```text
Group not found: usb-family-046d-0825

Run:
gst-device-explorer groups
```

## JSON-First Direction

Milestone 10 should include JSON output because group validation will be useful for:

- hardware validation scripts
- GitHub issue reports
- future GUI tools
- future TUI tools
- future agent integrations
- comparing systems

The JSON does not need a formal public schema yet. Formal schema versioning remains deferred to a later schema-stability milestone.

## Relationship to Existing Features

### Groups

Group validation should reuse existing composite group discovery and evidence.

It should not change grouping rules unless a small bug fix is required.

### DeviceProfile

Group validation may reuse `DeviceProfile` summaries for individual endpoints.

It should not change what `DeviceProfile` means.

### Recommendations

Group validation may include recommended endpoint candidates from Milestone 8, but it should not add a new ranking framework.

### Reports

Group validation may share aggregation ideas with `SystemReport`, but it should not require changing the full system report unless the change is small and useful.

### Capture

Group validation should not run capture commands. It may suggest endpoint-level capture commands as next steps if that is small and safe.

## Documentation

Update documentation to describe:

- what group validation does
- what group validation does not do
- how validation relates to group discovery
- how validation relates to endpoint profiles
- how validation relates to recommendations
- why group validation does not execute pipelines
- why group validation does not generate group-level pipelines
- how to inspect or test individual endpoints after validation

Likely documentation targets:

- `README.md`
- `docs/SETUP.md`
- `docs/milestones/MILESTONE_10.md`
- `docs/ARCHITECTURE.md`, if the validation layer needs to be described
- `docs/DATA_MODEL.md`, if new validation models are added

## Tests

Use synthetic tests.

Tests should verify:

- group validation model construction
- group validation for a synthetic group with video and audio endpoints
- group validation for a group with only video endpoints
- group validation for a group with only audio endpoints
- group validation when one endpoint has available candidates
- group validation when one endpoint has no candidates
- group validation when one endpoint has unavailable candidates
- group-level status aggregation
- endpoint-level status derivation
- missing-element aggregation
- suggested command deduplication
- grouping evidence is preserved
- JSON output has expected top-level shape
- text output includes group ID, status, endpoints, and suggested commands
- CLI `validate group <group-id>` works with mocked discovery/probe functions
- CLI `validate group <group-id> --json` works with mocked discovery/probe functions
- group-not-found behavior is clear
- no pipeline execution is invoked
- no capture execution is invoked
- existing device, group, profile, diagnostic, report, recommendation, capture, and run behavior remains unchanged

Tests should not require:

- a real camera
- a real microphone
- a real speaker
- real GStreamer execution
- real ALSA hardware access
- Jetson-specific hardware
- Reachy Mini hardware

## Non-Goals

Milestone 10 should not add:

- group-based pipeline execution
- group-based capture
- group-generated pipelines
- synchronized audio/video capture
- automatic endpoint selection for execution
- long-running validation loops
- background tests
- arbitrary user-supplied pipelines
- package installation
- system configuration changes
- new grouping heuristics unless required for a small bug fix
- device-specific hard-coding
- Reachy-specific hard-coding
- JetPack-version-specific hard-coding
- ASR
- TTS
- WebRTC
- PulseAudio support
- PipeWire support
- effects
- echo cancellation
- GUI behavior
- TUI behavior
- MCP or agent descriptor generation

## Deferred Work

Possible follow-on work after the first slice:

- group-level profile summaries
- group report command
- group validation included in `SystemReport`
- validation-aware recommendation output
- validation-aware capture suggestions
- group-level known-good examples
- comparison of group validation reports across systems
- JSON schema for group validation
- GUI/TUI group validation views
- agent-facing group validation consumption
- synchronized audio/video capture as a separate future milestone

## Implemented First Slice

The implemented first slice adds:

- `gst-device-explorer validate group <group-id>`
- `gst-device-explorer validate group <group-id> --json`
- structured `GroupValidation`, `EndpointValidationSummary`,
  `GroupValidationEndpointCounts`, and `GroupValidationDiagnostics` models
- a pure validation builder that consumes a selected `CompositeDevice` and
  existing endpoint profiles
- per-endpoint status derived from profile candidate availability
- simple group status aggregation
- grouping evidence preservation
- missing-element aggregation
- suggested command deduplication
- compact text output
- JSON serialization
- synthetic tests for model, builder, renderer, serializer, CLI, and
  group-not-found behavior

The first slice does not add group-based execution, group-based capture,
group-generated pipelines, profile group commands, report group commands, or
new grouping heuristics.

## Completion Criteria

Milestone 10 can be considered complete when:

- a structured group validation model exists
- group validation reuses existing group discovery and endpoint facts
- endpoint-level validation summaries are produced
- group-level status is derived simply and explainably
- missing elements are aggregated across endpoints
- suggested endpoint-level next commands are included
- `gst-device-explorer validate group <group-id>` works
- `gst-device-explorer validate group <group-id> --json` works
- group-not-found behavior is clear
- validation does not execute pipelines
- validation does not execute capture commands
- documentation describes scope and non-goals
- synthetic tests cover model, builder, rendering, JSON, and CLI behavior
- the full test suite passes

## Validation Command

Run:

```sh
/home/jim/.local/bin/uv run python -m pytest
```

Expected final Codex report should include:

- files changed
- group validation model added
- validation builder behavior
- CLI behavior added
- JSON shape chosen
- text output behavior
- tests added
- test result
- deferred work
