# Milestone 12 — Configuration and Preferences

## Status

Implemented.

## Theme

Introduce a bounded configuration surface for `gst-device-explorer` without changing runtime behavior yet.

This milestone should let users see where configuration would live, inspect the effective configuration, and validate a configuration file. It should not yet allow configuration values to alter candidate generation, ranking, presets, capture behavior, or execution behavior.

The purpose is to establish the shape, safety rules, and user-facing commands for configuration before connecting configuration to tool behavior.

## Motivation

By Milestone 11, the tool has endpoint discovery, candidates, diagnostics, profiles, reports, ranking, bounded capture, composite validation, and named preset command suggestions.

The next useful step is to give users a safe place to express preferences such as:

- preferred video sink
- whether to prefer Jetson/NVIDIA accelerated candidates
- preferred audio output test frequency
- default report verbosity
- whether to include metadata in reports

However, configuration can easily become a hidden policy layer. This milestone should avoid that. The first slice should be read-only from the perspective of behavior: configuration can be discovered, loaded, displayed, and validated, but it does not yet influence commands.

## Guiding Principles

- Keep configuration bounded and explicit.
- Prefer validation over implicit fallback behavior.
- Do not introduce arbitrary command execution.
- Do not allow user-authored raw pipelines.
- Do not change system audio/video settings.
- Do not install packages or modify the host system.
- Do not make configuration silently change execution behavior in this milestone.
- Keep configuration models structured and serializable.
- Keep text and JSON output consistent with the rest of the project.
- Preserve the existing project principle: CLI, JSON, future GUI, and future agent integrations are renderers over shared core models.

## Proposed First Slice

### Slice 1 — Configuration Model, Discovery, Show, and Validate

Implement a bounded configuration model and CLI commands to inspect and validate it.

This slice should include:

- A core configuration module.
- Structured configuration dataclasses or models.
- Default configuration values.
- Configuration path discovery.
- Loading configuration from an explicit file path.
- Loading configuration from the default path, if present.
- Validation of known sections and known fields.
- Clear diagnostics for unknown sections, unknown fields, and invalid values.
- Text rendering.
- JSON serialization.
- Synthetic tests.

This slice should not include:

- Changing candidate generation.
- Changing candidate ranking.
- Changing preset suggestions.
- Changing execution behavior.
- Writing configuration files.
- Editing configuration files.
- User-defined raw pipelines.
- Plugin systems.

## Possible Commands

```sh
gst-device-explorer config path
gst-device-explorer config show
gst-device-explorer config show --json
gst-device-explorer config validate
gst-device-explorer config validate --json
gst-device-explorer config validate --config ./gst-device-explorer.toml
gst-device-explorer config validate --config ./gst-device-explorer.toml --json
```

Optional, if it stays simple:

```sh
gst-device-explorer config defaults
gst-device-explorer config defaults --json
```

If `config defaults` adds too much CLI surface, defer it. `config show` can show the effective default configuration when no config file exists.

## Suggested Default Config Path

Use an XDG-style default path on Linux:

```text
~/.config/gst-device-explorer/config.toml
```

The command should report the path even if the file does not exist:

```sh
gst-device-explorer config path
```

Example text output:

```text
Configuration path:
  /home/jim/.config/gst-device-explorer/config.toml

Status:
  not found

The default configuration will be used.
```

## Possible Configuration Shape

Initial TOML shape:

```toml
[video]
preferred_sink = "auto"
prefer_jetson_acceleration = true
max_preview_width = 1920
max_preview_height = 1080

[audio]
output_test_frequency = 440
input_test_duration = 5
output_test_duration = 5

[report]
include_metadata = true
include_diagnostics = true
include_suggested_commands = true
```

This shape is intentionally small. All values should be bounded and typed.

## Proposed Fields

### `[video]`

#### `preferred_sink`

Allowed values:

```text
auto
nveglglessink
xvimagesink
autovideosink
fakesink
```

Initial behavior:

- Validate and display only.
- Do not alter generated candidates yet.

#### `prefer_jetson_acceleration`

Allowed values:

```text
true
false
```

Initial behavior:

- Validate and display only.
- Do not alter ranking yet.

#### `max_preview_width`

Allowed values:

- positive integer
- suggested range: 1 to 7680

Initial behavior:

- Validate and display only.

#### `max_preview_height`

Allowed values:

- positive integer
- suggested range: 1 to 4320

Initial behavior:

- Validate and display only.

### `[audio]`

#### `output_test_frequency`

Allowed values:

- positive integer or float
- suggested range: 20 to 20000

Initial behavior:

- Validate and display only.
- Do not alter audio-output preset suggestions yet.

#### `input_test_duration`

Allowed values:

- positive integer or float
- suggested range: greater than 0 and less than or equal to 60

Initial behavior:

- Validate and display only.

#### `output_test_duration`

Allowed values:

- positive integer or float
- suggested range: greater than 0 and less than or equal to 60

Initial behavior:

- Validate and display only.

### `[report]`

#### `include_metadata`

Allowed values:

```text
true
false
```

Initial behavior:

- Validate and display only.
- Do not alter report generation yet.

#### `include_diagnostics`

Allowed values:

```text
true
false
```

Initial behavior:

- Validate and display only.

#### `include_suggested_commands`

Allowed values:

```text
true
false
```

Initial behavior:

- Validate and display only.

## Suggested Core Models

Names are suggestions only. Match the existing project style.

```text
ConfigStatus
ConfigSource
ConfigDiagnostic
VideoPreferences
AudioPreferences
ReportPreferences
ExplorerConfig
ConfigValidation
```

Possible status values:

```text
ok
not_found
invalid
```

Possible diagnostic severities:

```text
error
warning
info
```

Possible diagnostic codes:

```text
config_not_found
parse_error
unknown_section
unknown_field
invalid_type
invalid_value
```

## Suggested Core Module

```text
src/gst_device_explorer/core/config.py
```

Possible pure functions:

```python
def default_config_path() -> Path: ...
def default_config() -> ExplorerConfig: ...
def load_config(path: Path | None = None) -> ConfigValidation: ...
def validate_config_data(data: Mapping[str, Any], source: ConfigSource) -> ConfigValidation: ...
```

Keep parsing and validation in core code. The CLI should call core functions and render the resulting structured models.

## CLI Behavior

### `config path`

Shows the default config path and whether it exists.

JSON output is optional. If added, keep it simple:

```json
{
  "path": "/home/jim/.config/gst-device-explorer/config.toml",
  "exists": false
}
```

### `config show`

Shows the effective configuration.

If no config file exists:

- Status should be `not_found` or equivalent.
- Output should explain that defaults are being used.
- This should not be treated as an error.

Example:

```text
Configuration

Source:
  /home/jim/.config/gst-device-explorer/config.toml

Status:
  not found

Effective values:
  video.preferred_sink: auto
  video.prefer_jetson_acceleration: true
  video.max_preview_width: 1920
  video.max_preview_height: 1080
  audio.output_test_frequency: 440
  audio.input_test_duration: 5
  audio.output_test_duration: 5
  report.include_metadata: true
  report.include_diagnostics: true
  report.include_suggested_commands: true
```

### `config validate`

Validates either the default config path or an explicit file.

If the file does not exist at the default path, this should probably be a successful validation with a `not_found` status and an informational diagnostic, because default configuration is valid.

If an explicit `--config` path is supplied and it does not exist, that should be an error.

Example text output for valid config:

```text
Configuration validation

Source:
  ./gst-device-explorer.toml

Status:
  ok

Diagnostics:
  none
```

Example text output for invalid config:

```text
Configuration validation

Source:
  ./gst-device-explorer.toml

Status:
  invalid

Diagnostics:
  error unknown_field: video.preview_sink
  error invalid_value: audio.output_test_frequency must be between 20 and 20000
```

## JSON Output

JSON should expose structured values, not text-only messages.

Possible shape:

```json
{
  "source": {
    "path": "/home/jim/.config/gst-device-explorer/config.toml",
    "exists": false,
    "explicit": false
  },
  "status": "not_found",
  "effective_config": {
    "video": {
      "preferred_sink": "auto",
      "prefer_jetson_acceleration": true,
      "max_preview_width": 1920,
      "max_preview_height": 1080
    },
    "audio": {
      "output_test_frequency": 440,
      "input_test_duration": 5,
      "output_test_duration": 5
    },
    "report": {
      "include_metadata": true,
      "include_diagnostics": true,
      "include_suggested_commands": true
    }
  },
  "diagnostics": [
    {
      "severity": "info",
      "code": "config_not_found",
      "message": "Configuration file was not found; using defaults."
    }
  ]
}
```

Do not add formal JSON schema versioning in this milestone unless it is already trivial and consistent with the project. Schema versioning remains a better fit for a later milestone.

## TOML Parsing Note

Python 3.11+ includes `tomllib` for reading TOML.

If the project currently supports Python versions older than 3.11, avoid adding a dependency casually. Consider one of these approaches:

- confirm the project already requires Python 3.11+
- use `tomllib` if available
- defer TOML file parsing and start with model/default display only
- add a small dependency only if it is consistent with current project policy

Do not introduce a large configuration framework.

## Tests

Add synthetic tests. Do not require real hardware.

Suggested test coverage:

- default config path returns a stable expected suffix
- default config contains expected sections and fields
- `config show` works when no config file exists
- `config validate` works when no default config file exists
- explicit missing `--config` produces an error
- valid TOML config validates successfully
- unknown section is reported
- unknown field is reported
- invalid type is reported
- invalid value is reported
- text output includes status and effective values
- JSON output includes source, status, effective config, and diagnostics
- configuration does not affect existing preset/candidate/ranking behavior in this milestone

## Documentation Updates

Update:

```text
README.md
docs/SETUP.md
docs/ARCHITECTURE.md
docs/DATA_MODEL.md
docs/milestones/MILESTONE_12.md
```

Documentation should make clear:

- configuration is currently inspectable and validateable
- configuration does not yet affect pipeline generation, ranking, presets, capture, or execution
- values are bounded and validated
- no raw pipelines are accepted through configuration
- no system settings are modified

## Version Update

When complete, bump the project version to:

```text
0.12.0
```

Update the usual version locations:

```text
src/gst_device_explorer/__init__.py
pyproject.toml
uv.lock
```

## Completion Criteria

Milestone 12 is complete when:

- A bounded configuration model exists in core code.
- Default preferences are represented as structured data.
- The default configuration path can be displayed.
- The effective configuration can be displayed as text.
- The effective configuration can be displayed as JSON.
- Configuration validation reports structured diagnostics.
- Unknown sections and fields are rejected or clearly reported.
- Invalid types and invalid values are rejected or clearly reported.
- Default missing config is handled gracefully.
- Explicit missing config file is handled as an error.
- Tests cover the behavior without real hardware.
- Documentation is updated.
- Version is bumped to `0.12.0`.
- Full test suite passes.

## Implemented First Slice

The implemented first slice adds:

- `gst-device-explorer config path [--json]`
- `gst-device-explorer config show [--config <path>] [--json]`
- `gst-device-explorer config validate [--config <path>] [--json]`
- structured `VideoPreferences`, `AudioPreferences`, `ReportPreferences`, and
  `ExplorerConfig` models
- structured `ConfigIssue` and `ConfigValidationResult` models
- deterministic default configuration and search paths
- TOML loading with standard-library `tomllib` when a file is present
- strict validation for wrong types and non-positive numeric values
- warnings for unknown sections and keys
- JSON serialization and compact text rendering
- synthetic tests for defaults, search paths, TOML loading, validation,
  rendering, JSON, and CLI behavior

Milestone 12 only validates and displays configuration. It does not apply
preferences to candidate generation, ranking, presets, reports, capture,
validation, or execution.

## Explicit Non-Goals

Do not implement:

- configuration-controlled candidate generation
- configuration-controlled ranking
- configuration-controlled preset behavior
- configuration-controlled capture behavior
- configuration-controlled execution behavior
- arbitrary raw pipelines in config
- user-authored pipeline templates
- plugin systems
- package installation
- system configuration changes
- audio/video device configuration changes
- remote execution
- background services
- GUI integration
- MCP/tool descriptor generation
- formal JSON schema stabilization

## Deferred Ideas

These may be considered in later milestones:

- Let configuration bias candidate ranking.
- Let configuration influence preset command suggestions.
- Let configuration choose preferred preview sinks.
- Add `config init` to write a starter config file.
- Add JSON schema documents.
- Add stable schema version wrappers.
- Add GUI/agent command metadata.

## Design Summary

Milestone 12 should create the safe configuration boundary, not consume it broadly.

The key distinction is:

```text
Milestone 12 defines, discovers, displays, and validates preferences.
Later milestones may decide how selected preferences affect behavior.
```

That keeps the project explainable and avoids turning configuration into hidden policy.
