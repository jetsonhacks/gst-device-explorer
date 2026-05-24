# Milestone 13 — Machine-Readable Schema Stability

Status: Implemented

## Theme

Treat selected JSON output as a stable external interface.

The project now exposes many structured outputs: devices, candidates, diagnostics, profiles, reports, recommendations, validation results, presets, and configuration. These outputs are useful for scripts, future GUI/TUI tools, issue reports, and possible agent integrations.

Milestone 13 should establish a small, explicit schema-stability boundary before the project adds more behavior that depends on JSON consumers.

The first slice should not attempt to fully freeze every JSON structure in the project. Instead, it should introduce a consistent machine-readable response envelope, document which outputs are considered stable, and add tests that protect the wrapper shape.

## Guiding Principles

- Keep JSON output machine-readable and predictable.
- Do not break existing plain text workflows.
- Prefer explicit schema boundaries over accidental stability.
- Add stability incrementally.
- Do not publish full JSON Schema documents before the wrapper pattern settles.
- Preserve the current core model/rendering separation.
- Keep serializers as renderers over shared core models.
- Avoid changing probe, candidate generation, ranking, execution, capture, validation, preset, or config behavior.

## Slice 1 — JSON Response Envelope

### Goal

Add a shared response envelope for selected JSON-producing commands.

The envelope should make JSON responses self-describing by including the output kind, schema version, tool version, and payload data.

### Proposed Envelope Shape

```json
{
  "kind": "device_profile",
  "schema_version": "1.0",
  "tool_version": "0.13.0",
  "data": {}
}
```

Field meanings:

- `kind`: stable identifier for the type of response.
- `schema_version`: version of the JSON response shape for that kind.
- `tool_version`: installed `gst-device-explorer` version.
- `data`: existing serialized payload.

### Initial Stable Kinds

Start with a small set of already well-formed outputs:

- `config_path`
- `config_show`
- `config_validate`
- `preset_list`
- `preset_show`
- `preset_command`

These are good first targets because Milestones 11 and 12 are recent, bounded, and less hardware-dependent than device probing outputs.

If implementation is straightforward, the following may also be included, but they are optional for Slice 1:

- `candidate_recommendation`
- `group_validation`
- `system_report`

Do not force all JSON outputs into the envelope in this milestone if it makes the change too broad.

### Expected Implementation Shape

Possible new or updated code:

- `src/gst_device_explorer/cli/serializers.py`
- `src/gst_device_explorer/core/schema.py` or similar small core module
- tests for envelope helper behavior
- tests for selected CLI JSON outputs

A simple helper may be enough:

```python
def wrap_json_response(kind: str, data: object) -> dict:
    return {
        "kind": kind,
        "schema_version": "1.0",
        "tool_version": __version__,
        "data": data,
    }
```

The exact module placement is up to the implementer, but the wrapper logic should be centralized rather than duplicated across commands.

## Slice 2 — CLI JSON Output Updates

### Goal

Update selected `--json` commands to emit the response envelope.

Initial target commands:

```sh
gst-device-explorer config path --json
gst-device-explorer config show --json
gst-device-explorer config validate --json

gst-device-explorer preset list --json
gst-device-explorer preset show <preset-id> --json
gst-device-explorer preset command <preset-id> <target-kind> <target> --json
```

### Behavior

Text output should remain unchanged unless a small wording clarification is needed.

JSON output should be wrapped consistently:

```json
{
  "schema_version": "1.0",
  "tool_version": "0.13.0",
  "kind": "preset_show",
  "data": {
    "id": "camera-preview",
    "label": "Camera Preview"
  }
}
```

Error output does not need full schema stabilization in this first slice unless it is already easy and low-risk. Clear non-zero behavior should be preserved.

## Slice 3 — Schema Documentation and Discovery

### Goal

Document the JSON stability boundary clearly and expose a small schema
discovery surface for the envelope contract.

Implemented schema discovery commands:

```sh
gst-device-explorer schema list
gst-device-explorer schema list --json
gst-device-explorer schema show json-envelope
gst-device-explorer schema show json-envelope --json
```

The only schema-like document in this milestone is `json-envelope`. It describes
the stable wrapper fields and current envelope schema version. Full JSON Schema
documents for every payload remain deferred.

Suggested documentation updates:

- `README.md`
- `docs/SETUP.md`
- `docs/ARCHITECTURE.md`
- `docs/DATA_MODEL.md`
- `docs/milestones/MILESTONE_13.md`

Documentation should explain:

- which commands currently emit stable JSON envelopes
- what the envelope fields mean
- that `schema_version` applies to the response kind, not necessarily the whole tool
- that unwrapped JSON outputs remain useful but are not yet part of the stabilized interface
- that full JSON Schema documents are deferred

Suggested wording:

```text
Some JSON outputs are now emitted in a stable response envelope. The envelope identifies the response kind, schema version, tool version, and serialized payload. This gives scripts and future front ends a predictable boundary while allowing the project to stabilize output shapes incrementally.
```

## Slice 4 — Tests and Version Bump

### Goal

Protect the wrapper shape and selected CLI JSON responses.

Tests should cover:

- wrapper includes `kind`
- wrapper includes `schema_version`
- wrapper includes `tool_version`
- wrapper includes `data`
- selected config JSON commands use the wrapper
- selected preset JSON commands use the wrapper
- data payload remains structured and usable
- text output still works
- schema discovery commands render the envelope contract
- unknown schema names return non-zero and suggest `schema list`

Version bump:

- `src/gst_device_explorer/__init__.py`: `0.12.0` → `0.13.0`
- `pyproject.toml`: `0.12.0` → `0.13.0`
- `uv.lock`: update with `uv lock` if needed

## Proposed Commands to Validate

```sh
/home/jim/.local/bin/uv run python -m pytest

/home/jim/.local/bin/uv run gst-device-explorer config path --json
/home/jim/.local/bin/uv run gst-device-explorer config show --json
/home/jim/.local/bin/uv run gst-device-explorer config validate --json

/home/jim/.local/bin/uv run gst-device-explorer preset list --json
/home/jim/.local/bin/uv run gst-device-explorer preset show camera-preview --json
/home/jim/.local/bin/uv run gst-device-explorer preset command camera-preview video /dev/video0 --json

/home/jim/.local/bin/uv run gst-device-explorer schema list
/home/jim/.local/bin/uv run gst-device-explorer schema show json-envelope
/home/jim/.local/bin/uv run gst-device-explorer schema show json-envelope --json
```

## Completion Criteria

Milestone 13 is complete when:

- A centralized JSON envelope helper exists.
- Selected JSON commands emit the envelope.
- Each wrapped response includes `kind`, `schema_version`, `tool_version`, and `data`.
- At least config and preset JSON outputs are covered.
- Existing text output remains usable.
- Documentation explains the stable JSON boundary.
- Schema discovery commands describe the JSON envelope contract.
- Synthetic tests cover the wrapper and selected CLI JSON output.
- Version is bumped to `0.13.0`.
- Full test suite passes.

## Explicit Non-Goals

Do not implement:

- full JSON Schema documents
- schema file installation
- automatic schema validation of every JSON output
- response-envelope migration for every command if it makes the milestone broad
- changes to probing behavior
- changes to candidate generation
- changes to ranking behavior
- changes to preset behavior
- changes to configuration behavior
- config-driven behavior changes
- new execution behavior
- new capture behavior
- user-authored pipelines
- plugin systems
- remote execution
- GUI, TUI, or MCP integration

## Deferred Ideas

Future milestones may add:

- installed JSON Schema files
- schema validation tests for every stable output kind
- stable error envelopes
- compatibility policy for breaking JSON changes
- command discovery metadata
- GUI/TUI/agent-oriented command descriptors

## Notes

This milestone should be treated as a boundary-setting milestone, not a large schema project.

The important step is to stop JSON stability from being accidental. A small stable envelope gives future tools something predictable to consume while leaving the project room to evolve internal models and unwrapped outputs.
