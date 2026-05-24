# Milestone 14 — Extend JSON Envelope Coverage

Status: Implemented

## Theme

Extend the machine-readable JSON envelope introduced in Milestone 13 to the older hardware-oriented JSON outputs.

Milestone 13 established the shared JSON response envelope for newer surfaces such as configuration, presets, and schema discovery. Milestone 14 should continue that work by wrapping the remaining important JSON-producing commands in the same outer structure, without changing the underlying probing, discovery, ranking, validation, capture, or execution behavior.

The goal is consistency at the serialization boundary, not new device behavior.

## Current Context

The project already supports JSON output across several command families. Some newer outputs are wrapped in a stable envelope:

```json
{
  "schema_version": "1.0",
  "tool_version": "0.14.0",
  "kind": "preset_list",
  "data": {}
}
```

Older JSON outputs predate this envelope and may return raw payloads directly.

This milestone should make JSON consumers see a more predictable top-level shape across the CLI.

## Guiding Principles

Continue to follow the project principles:

- Probe first, build later.
- Normalize raw system output into structured models before making decisions.
- Keep pipeline candidates as structured objects, not just strings.
- Treat CLI, JSON, future GUI, future TUI, and future agent integrations as renderers over shared core models.
- Prefer capability detection over hard-coded JetPack version checks.
- Avoid Reachy-specific behavior.
- Avoid arbitrary user-supplied pipeline execution.
- Keep grouping evidence-based and explainable.
- Keep each milestone narrow.
- Use synthetic tests where possible; do not require real hardware for normal tests.

Milestone-specific principles:

- Preserve existing core models.
- Preserve existing command behavior.
- Preserve existing text output behavior.
- Wrap JSON output at the CLI serialization boundary.
- Do not reinterpret or reshape payload internals unless required for envelope compatibility.
- Do not add new probing behavior.
- Do not add new execution behavior.
- Do not use this milestone to publish full JSON Schema documents for every payload.

## Desired Outcome

After this milestone, most major `--json` commands should return a consistent envelope:

```json
{
  "schema_version": "1.0",
  "tool_version": "0.14.0",
  "kind": "<payload-kind>",
  "data": {
    "...": "existing payload content"
  }
}
```

This makes the tool easier to consume from:

- GUI front ends
- future TUI review mode
- scripts
- automated test harnesses
- agents
- documentation examples
- support/debugging workflows

## Proposed Scope

### Slice 1 — Inventory JSON Outputs

Inventory existing `--json` outputs and classify them as:

1. Already wrapped by Milestone 13.
2. Hardware-independent and safe to wrap with simple synthetic tests.
3. Hardware-oriented but testable with synthetic/mocked data.
4. Hardware-oriented and better deferred if wrapping would require fragile tests or behavior changes.

The inventory should be documented in `docs/DATA_MODEL.md` or the milestone document.

Expected already-wrapped examples from Milestone 13:

- `config path --json`
- `config show --json`
- `config validate --json`
- `preset list --json`
- `preset show --json`
- `preset command --json`
- `schema list --json`
- `schema show json-envelope --json`

Likely candidates for Milestone 14 wrapping:

- environment JSON
- device discovery JSON
- audio input discovery JSON
- audio output discovery JSON
- video candidate JSON
- audio input candidate JSON
- audio output candidate JSON
- diagnostics JSON
- profile JSON
- report JSON
- recommendation JSON
- capture dry-run JSON, if present
- group listing JSON
- group metadata JSON
- group validation JSON

The final implemented set may be smaller if a command is difficult to test cleanly without real hardware.

Implemented Milestone 14 coverage:

- `devices --json` -> `devices`
- `env --json` -> `environment`
- `audio-inputs --json` -> `audio_inputs`
- `audio-outputs --json` -> `audio_outputs`
- `groups --json` -> `composite_groups`
- `groups --metadata --json` -> `grouping_metadata`
- `group <group-id> --json` -> `composite_group`
- `video <device> --json` -> `video_capabilities`
- `pipeline video <device> --json` -> `video_candidates`
- `pipeline audio-input <device> --json` -> `audio_input_candidates`
- `pipeline audio-output <device> --json` -> `audio_output_candidates`
- `pipeline ... --diagnostics --json` -> `pipeline_diagnostics`
- `profile ... --json` -> `device_profile`
- `report --json` -> `system_report`
- `recommend ... --json` -> `candidate_recommendation`
- `validate group <group-id> --json` -> `group_validation`

Deferred JSON surfaces:

- `capture ... --json`: no capture JSON flag exists in this milestone.
- stable JSON error envelopes, including group-not-found errors.

### Slice 2 — Extend Envelope Kinds

Add stable `kind` values for wrapped legacy outputs.

Possible kind names:

```text
environment
devices
video_devices
audio_inputs
audio_outputs
video_candidates
audio_input_candidates
audio_output_candidates
pipeline_diagnostics
device_profile
system_report
candidate_recommendation
capture_command
composite_groups
composite_group
group_validation
```

Prefer names that match existing domain concepts and command families.

The implemented kind names use `devices` for combined discovery and
`video_capabilities` for `video <device> --json`.

Do not bikeshed this into a full schema taxonomy. The kind values should be clear, stable, and documented.

### Slice 3 — Wrap Selected JSON Outputs

Update CLI JSON rendering so selected older JSON outputs use the shared envelope helper from `core/schema.py`.

The wrapping should happen as late as practical, near the serialization/rendering boundary.

Avoid changing the existing internal serializer functions more than necessary. If existing serializers return useful payload dictionaries, keep them as `data`.

For example, a previous raw response like:

```json
{
  "devices": []
}
```

should become:

```json
{
  "schema_version": "1.0",
  "tool_version": "0.14.0",
  "kind": "video_devices",
  "data": {
    "devices": []
  }
}
```

### Slice 4 — Schema Discovery Updates

Update schema discovery so `schema list` includes newly wrapped payload kinds.

For Milestone 14, it is enough for schema discovery to say that these outputs use the shared JSON envelope and that detailed payload schemas are deferred.

`schema show json-envelope` should remain the canonical description of the shared envelope.

Do not add full JSON Schema files for every payload in this milestone unless it falls out trivially from existing work.

### Slice 5 — Tests

Add or update synthetic tests for wrapped JSON output.

Tests should check:

- top-level object has `schema_version`
- top-level object has `tool_version`
- top-level object has `kind`
- top-level object has `data`
- `kind` is correct for the command
- expected payload content moved under `data`
- text output remains unchanged where applicable
- command exit behavior remains unchanged

Prefer synthetic tests and existing mocked fixtures.

Do not require real V4L2, ALSA, USB, or GStreamer hardware for normal tests.

### Slice 6 — Documentation and Version Bump

Update documentation:

- `README.md`
- `docs/SETUP.md`
- `docs/ARCHITECTURE.md`
- `docs/DATA_MODEL.md`
- `docs/milestones/MILESTONE_14.md`

Documentation should explain:

- the JSON envelope now covers more command families
- older command payloads are preserved under `data`
- text output is unchanged
- full payload-specific JSON Schema documents remain deferred

Bump version to `0.14.0` in:

- `src/gst_device_explorer/__init__.py`
- `pyproject.toml`
- `uv.lock`

## Suggested Commands

Examples of commands that may be covered by this milestone, depending on the current CLI shape:

```sh
gst-device-explorer env --json
gst-device-explorer devices --json
gst-device-explorer audio-inputs --json
gst-device-explorer audio-outputs --json

gst-device-explorer pipeline video /dev/video0 --json
gst-device-explorer pipeline audio-input hw:0,0 --json
gst-device-explorer pipeline audio-output hw:0,0 --json

gst-device-explorer diagnostics video /dev/video0 --json
gst-device-explorer profile video /dev/video0 --json
gst-device-explorer report --json

gst-device-explorer recommend video /dev/video0 --json
gst-device-explorer validate group <group-id> --json

gst-device-explorer groups --json
gst-device-explorer groups --metadata --json

gst-device-explorer schema list --json
```

The exact command names should follow the repository’s existing parser. Do not invent new command families solely for this milestone.

## Expected JSON Shape

All newly wrapped outputs should follow the existing Milestone 13 envelope shape:

```json
{
  "schema_version": "1.0",
  "tool_version": "0.14.0",
  "kind": "system_report",
  "data": {
    "...": "existing report payload"
  }
}
```

The payload inside `data` should remain command-specific.

## Completion Criteria

Milestone 14 is complete when:

- a documented set of older JSON outputs is wrapped in the shared JSON envelope
- wrapped outputs use stable and documented `kind` values
- payload content is preserved under `data`
- existing text output remains unchanged
- synthetic tests cover the newly wrapped outputs
- schema discovery lists the newly wrapped kinds
- documentation is updated
- version is bumped to `0.14.0`
- full test suite passes

## Non-Goals

Do not implement:

- full JSON Schema documents for every payload
- schema generation from Python dataclasses
- breaking changes to payload internals
- stable error envelopes
- new probing behavior
- new device discovery behavior
- new candidate generation behavior
- new recommendation logic
- new capture behavior
- new validation behavior
- new execution behavior
- TUI mode
- GUI mode
- MCP/tool descriptor generation
- config-driven behavior changes
- user-authored pipelines
- plugin systems
- remote execution
- package installation
- system configuration changes
- Reachy-specific hard-coding
- JetPack-version-specific hard-coding

## Deferred Items

Possible future work:

- full payload-specific JSON Schema documents
- stable error envelopes
- JSON schema compatibility tests
- schema version migration policy
- wrapping any outputs intentionally deferred from Milestone 14
- TUI review mode consuming wrapped JSON-like internal structures
- GUI or agent integration boundaries
- MCP/tool descriptor generation

## Design Note

This milestone should feel mostly mechanical.

It is not about making the payloads perfect. It is about making the outer contract predictable.

A consumer should be able to ask:

```text
What version of the JSON shape is this?
What version of the tool produced it?
What kind of payload is this?
Where is the payload data?
```

And get the same answer for the major JSON command surfaces.
