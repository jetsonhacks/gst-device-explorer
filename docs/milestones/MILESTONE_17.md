# Milestone 17 — Stable Error Envelopes

Status: Complete (v0.17.0)

## Theme

Add structured JSON error envelopes for selected error paths.

Milestones 13 and 14 made successful JSON responses more consistent by introducing a shared envelope:

```json
{
  "schema_version": "1.0",
  "tool_version": "0.16.0",
  "kind": "<payload-kind>",
  "data": {}
}
```

Milestone 17 should extend that stability to selected JSON error responses.

The goal is not to redesign every error in the project. The goal is to define a small, stable error shape and apply it to the most obvious JSON-producing command failures, while preserving existing non-zero exit codes and human-readable text behavior.

## Current Context

The project is at version `0.16.0` after Milestone 16.

Implemented foundations include:

- device discovery
- video and audio pipeline candidate generation
- safe endpoint execution commands
- composite grouping
- diagnostics
- profiles
- system reports
- recommendations
- bounded capture tests
- group validation
- built-in presets
- bounded configuration inspection and validation
- JSON envelope coverage across major JSON outputs
- schema discovery for the shared JSON envelope and payload kinds
- read-only TUI review mode
- structured suggested commands and suggestion catalog

Several error paths already produce helpful text and recovery suggestions, but JSON error responses are not yet standardized.

Milestone 17 should use the existing JSON envelope and the new `SuggestedCommand` model to make selected JSON errors predictable for scripts, GUIs, TUI extensions, and future agent integrations.

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

- Preserve non-zero exit codes.
- Preserve human-readable text and stderr behavior where practical.
- JSON error output should be structured and stable for selected paths.
- Error envelopes should include enough information for a caller to recover or display a useful message.
- Suggested commands in errors are advisory only.
- Do not execute recovery commands.
- Do not add hidden retries or background behavior.
- Do not attempt to wrap every possible exception in this milestone.

## Desired Outcome

After this milestone, selected commands that support `--json` should produce structured error output on known, expected failures.

Example:

```sh
gst-device-explorer schema show unknown-schema --json
```

Possible JSON error output:

```json
{
  "schema_version": "1.0",
  "tool_version": "0.17.0",
  "kind": "error",
  "error": {
    "code": "unknown_schema",
    "message": "Unknown schema: unknown-schema",
    "details": {
      "schema_id": "unknown-schema"
    },
    "suggested_commands": [
      {
        "id": "schema-list",
        "title": "List available schemas",
        "argv": ["gst-device-explorer", "schema", "list"],
        "command": "gst-device-explorer schema list",
        "purpose": "Show available schema documents and payload kinds.",
        "source": "schema",
        "safety": "inspection",
        "target_kind": null,
        "target": null,
        "notes": []
      }
    ]
  }
}
```

The exact shape may differ, but it should be consistent and documented.

## Proposed Scope

### Slice 1 — Core Error Envelope Model

Add a small core model for structured JSON errors.

Possible file:

```text
src/gst_device_explorer/core/errors.py
```

Possible model:

```python
@dataclass(frozen=True)
class ErrorResponse:
    code: str
    message: str
    details: Mapping[str, object] = field(default_factory=dict)
    suggested_commands: tuple[SuggestedCommand, ...] = ()
```

Possible envelope helper:

```python
make_error_envelope(error: ErrorResponse) -> dict[str, object]
```

Or the error helper may live alongside the existing schema envelope helper if that better fits the current design.

The important pieces:

- stable `kind`, likely `"error"`
- stable `error.code`
- stable `error.message`
- optional `error.details`
- optional structured `error.suggested_commands`
- tool version
- schema version

Keep the model small.

### Slice 2 — Error Serialization

Add JSON serialization for error responses.

The serializer should reuse existing `SuggestedCommand` JSON serialization from Milestone 16.

Suggested JSON shape:

```json
{
  "schema_version": "1.0",
  "tool_version": "0.17.0",
  "kind": "error",
  "error": {
    "code": "unknown_preset",
    "message": "Unknown preset: not-a-preset",
    "details": {
      "preset_id": "not-a-preset"
    },
    "suggested_commands": []
  }
}
```

Decide whether error payload lives under top-level `error` or under `data.error`.

Recommendation for Milestone 17:

```json
{
  "kind": "error",
  "error": {}
}
```

This keeps errors distinct from successful `data` payloads.

Document the chosen shape clearly.

### Slice 3 — Wrap Selected Known Error Paths

Apply structured JSON error output to a narrow set of expected failures.

Good candidates:

1. Unknown schema:
   - `gst-device-explorer schema show <unknown> --json`

2. Unknown preset:
   - `gst-device-explorer preset show <unknown> --json`
   - `gst-device-explorer preset command <unknown> ... --json`

3. Wrong preset target kind:
   - `gst-device-explorer preset command <preset-id> <wrong-kind> <target> --json`

4. Missing preset command required arguments:
   - duration/output missing for capture-style presets, if currently validated

5. Config validation/load errors:
   - `gst-device-explorer config validate --config <bad-file> --json`
   - `gst-device-explorer config show --config <bad-file> --json`, if applicable

6. Group not found:
   - `gst-device-explorer group <group-id> --json`
   - `gst-device-explorer validate group <group-id> --json`

Do not try to capture every unexpected exception.

For non-JSON invocations, preserve existing text/stderr style.

### Slice 4 — Suggested Recovery Commands

For selected errors, include structured suggested commands where useful.

Examples:

- unknown schema:
  - `gst-device-explorer schema list`

- unknown preset:
  - `gst-device-explorer preset list`

- group not found:
  - `gst-device-explorer groups`

- config validation failure:
  - `gst-device-explorer config path`
  - `gst-device-explorer config show`
  - possibly `gst-device-explorer config validate`

Use the structured `SuggestedCommand` builders from Milestone 16 where possible.

Do not invent arbitrary recovery commands.

### Slice 5 — Text Behavior Preservation

Preserve current text behavior for non-JSON errors where practical.

For example:

```sh
gst-device-explorer schema show unknown-schema
```

should still produce a clear human-readable error and a suggestion such as:

```text
Unknown schema: unknown-schema
Try:
  gst-device-explorer schema list
```

Milestone 17 is not primarily a text-output redesign.

### Slice 6 — Tests

Add tests for:

- `ErrorResponse` creation
- error envelope serialization
- suggested command serialization inside errors
- unknown schema JSON error
- unknown preset JSON error
- wrong preset target JSON error
- config validation JSON error
- group-not-found JSON error, if easy to test synthetically
- non-zero exit code preservation
- non-JSON text behavior preservation
- no command execution side effects

Tests should be synthetic and should not require:

- real V4L2 devices
- real ALSA devices
- real USB devices
- real GStreamer devices
- NVIDIA hardware
- Reachy Mini hardware
- interactive TUI sessions

### Slice 7 — Schema Discovery and Documentation

Update schema discovery to document the error envelope.

Add or extend schema discovery so this works:

```sh
gst-device-explorer schema show error-envelope
gst-device-explorer schema show error-envelope --json
```

Alternatively, if the project prefers a single schema document, extend `json-envelope` documentation to include the error form.

Preferred for clarity:

```text
json-envelope
error-envelope
```

Document:

- success envelopes use `kind` plus `data`
- error envelopes use `kind: error` plus `error`
- `error.code` is intended for programmatic handling
- `error.message` is intended for human display
- `error.details` is optional and command-specific
- `error.suggested_commands` is advisory

Update:

- `README.md`
- `docs/SETUP.md`
- `docs/ARCHITECTURE.md`
- `docs/DATA_MODEL.md`
- `docs/milestones/MILESTONE_17.md`

### Slice 8 — Version Bump

Bump version to `0.17.0` in:

- `src/gst_device_explorer/__init__.py`
- `pyproject.toml`
- `uv.lock`

Use `uv lock` as appropriate.

## Error Codes

Use stable, simple, snake_case error codes.

Possible codes:

```text
unknown_schema
unknown_preset
wrong_preset_target_kind
missing_required_argument
invalid_config
config_not_found
group_not_found
invalid_candidate_selection
unsupported_json_error
```

Only add codes that are actually used.

Do not create a large speculative taxonomy.

## Expected JSON Error Shape

Recommended shape:

```json
{
  "schema_version": "1.0",
  "tool_version": "0.17.0",
  "kind": "error",
  "error": {
    "code": "group_not_found",
    "message": "Group not found: usb-1-2",
    "details": {
      "group_id": "usb-1-2"
    },
    "suggested_commands": [
      {
        "id": "list-groups",
        "title": "List composite groups",
        "argv": ["gst-device-explorer", "groups"],
        "command": "gst-device-explorer groups",
        "purpose": "Show discovered composite device groups.",
        "source": "group_validation",
        "safety": "inspection",
        "target_kind": null,
        "target": null,
        "notes": []
      }
    ]
  }
}
```

## Suggested Commands

Existing command examples that should continue to work:

```sh
gst-device-explorer schema list
gst-device-explorer schema show json-envelope
gst-device-explorer schema show error-envelope
gst-device-explorer preset list
gst-device-explorer config validate --json
gst-device-explorer groups --json
```

Representative JSON error examples:

```sh
gst-device-explorer schema show not-a-schema --json
gst-device-explorer preset show not-a-preset --json
gst-device-explorer validate group not-a-group --json
```

## Completion Criteria

Milestone 17 is complete when:

- a structured error response model exists
- a JSON error envelope helper/serializer exists
- selected known JSON error paths return structured error envelopes
- selected errors include structured suggested recovery commands
- non-zero exit codes are preserved
- non-JSON text behavior is preserved where practical
- schema discovery documents the error envelope
- synthetic tests cover error model, serialization, and selected CLI error paths
- documentation is updated
- version is bumped to `0.17.0`
- full test suite passes

## Non-Goals

Do not implement:

- wrapping every unexpected exception
- replacing all text/stderr errors
- changing success-envelope shape
- changing successful payload internals
- automatic retries
- executing recovery suggestions
- TUI execution controls
- config editing
- package installation
- system configuration changes
- arbitrary command execution
- raw pipeline execution
- raw pipeline editing
- user-authored command templates
- plugin systems
- remote execution
- GUI mode
- web server mode
- MCP/tool descriptor generation
- full payload-specific JSON Schema documents
- Reachy-specific errors
- JetPack-version-specific errors

## Deferred Items

Possible future work:

- broader error envelope coverage
- stable error envelopes for all command families
- error code compatibility policy
- full error-envelope JSON Schema
- stable machine-readable validation diagnostics
- TUI display of structured errors
- GUI/agent recovery workflows
- support bundle generation

## Design Note

A stable success envelope lets a caller understand what worked.

A stable error envelope lets a caller understand what failed and what safe thing to inspect next.

The project should be able to say:

```text
This failed.
Here is the stable error code.
Here is the human-readable message.
Here are the details.
Here are safe commands you may run next.
```

But it should not run those recovery commands automatically.
