# Milestone 18 — Support Bundle Export

Status: Complete

## Theme

Create a portable support/debug bundle from existing safe inspection surfaces.

The support bundle should make it easy to attach useful diagnostic information to
GitHub issues, compare Jetson systems, and capture a field-debugging snapshot
without running media pipelines, recording media, installing packages, or changing
system configuration.

## Core Idea

Add a command:

```sh
gst-device-explorer support bundle --output <path>
```

The command creates a new bundle directory at the explicit output path. The output
path must not already exist.

The first implementation should produce a directory, not a `.tar.gz` archive. A
compressed archive format can be added later as a separate, explicit slice.

## Design Principles

Preserve the existing project principles:

- Probe first, build later.
- Normalize raw system output into structured models before making decisions.
- CLI, JSON, TUI, future GUI, and future agent integrations are renderers over
  shared core models.
- Prefer capability detection over hard-coded JetPack version checks.
- Avoid Reachy-specific behavior.
- Avoid arbitrary user-supplied pipeline execution.
- Keep grouping evidence-based and explainable.
- Keep the milestone narrow.
- Use synthetic tests where possible.
- Preserve safety boundaries: suggestions are advisory, and execution remains
  explicit and bounded.

## Safety Boundaries

This milestone must not introduce:

- Arbitrary raw pipeline execution.
- Media capture.
- Pipeline preview execution.
- Preset execution.
- Remote execution.
- Background workflows.
- Package installation.
- System configuration changes.
- User-authored scripts.
- User-authored raw GStreamer pipelines.
- Plugin behavior.
- Reachy-specific hard-coding.
- JetPack-version-specific hard-coding.

The support bundle is an export of already-safe inspection information. It is not
a control surface.

## Proposed User Command

```sh
gst-device-explorer support bundle --output <path>
```

Required behavior:

- `--output` is required.
- Output path must be explicit.
- Existing output path is rejected.
- Parent directory must exist.
- Bundle is written as a directory.
- Command exits non-zero on validation or write failure.
- No hidden retries.
- No execution of generated suggested commands.

Possible future, out of scope for this milestone:

```sh
gst-device-explorer support bundle --output support-bundle.tar.gz --format tar.gz
gst-device-explorer support bundle --output bundle-dir --force
```

## Bundle Layout

Suggested initial directory layout:

```text
support-bundle/
├── manifest.json
├── report/
│   ├── system-report.json
│   └── system-report.txt
├── inventory/
│   ├── environment.json
│   ├── devices.json
│   ├── audio-inputs.json
│   ├── audio-outputs.json
│   ├── groups.json
│   └── grouping-metadata.json
├── config/
│   ├── config-path.json
│   ├── config-show.json
│   └── config-validate.json
├── schemas/
│   └── schema-list.json
├── suggestions/
│   └── suggestions-list.json
└── tui/
    └── snapshot.txt
```

The exact layout can change during implementation, but the bundle should remain
easy to inspect by humans and scripts.

## SupportBundleManifest Model

Add a frozen model, likely in a new core module:

```text
src/gst_device_explorer/core/support.py
```

Suggested model name:

```python
SupportBundleManifest
```

Suggested fields:

- `schema_version: str`
- `tool_version: str`
- `kind: str`
- `created_at: str`
- `bundle_format: str`
- `files: list[SupportBundleFile]`
- `warnings: list[str]`
- `notes: list[str]`

Suggested companion model:

```python
SupportBundleFile
```

Suggested fields:

- `path: str`
- `kind: str`
- `description: str`
- `required: bool`

The manifest should document what was written. It should not claim that a file
exists unless it was actually written.

## JSON Envelope Expectations

For JSON files generated from existing command surfaces, preserve the existing
success envelope shape where those surfaces already use it:

```json
{
  "schema_version": "1.0",
  "tool_version": "0.18.0",
  "kind": "...",
  "data": {}
}
```

`manifest.json` may either be:

1. a direct serialized manifest object, or
2. a success envelope with `kind: "support_bundle_manifest"`.

Prefer the envelope form if it fits the current serializer architecture cleanly.

## Implementation Shape

Prefer a pure core builder that can be tested without real hardware.

Possible structure:

```text
src/gst_device_explorer/core/support.py
src/gst_device_explorer/cli/support.py
```

The core layer should focus on manifest construction and bundle file descriptions.

The CLI layer may orchestrate existing probe/report/render paths and write files.

Avoid invoking the CLI recursively through subprocess. Use shared functions where
practical.

## Parser Additions

Add a new command group:

```sh
gst-device-explorer support bundle --output <path>
```

Expected parser shape:

```text
support
  bundle
    --output <path>
```

Do not add `--json` yet unless it is useful for returning the manifest after
successful creation. If added, it should use the existing success JSON envelope.

## Renderer / Serializer Additions

Add serializers for:

- `SupportBundleManifest`
- `SupportBundleFile`

Add text rendering for command success, for example:

```text
Support bundle written: /path/to/support-bundle

Files:
  manifest.json
  report/system-report.json
  report/system-report.txt
  ...
```

On expected JSON errors, use stable error envelope machinery if the command has a
JSON mode. Without JSON mode, preserve concise text errors.

## Error Handling

Expected errors:

- missing required `--output`
- parent directory does not exist
- output path already exists
- output path parent is not a directory
- file write failure

At minimum, text errors should be clear and actionable.

Possible future error envelope kind names:

- `missing_required_argument`
- `output_path_exists`
- `invalid_output_parent`
- `support_bundle_write_failed`

Only add new stable error kinds if they are covered by tests and docs.

## Tests

Use synthetic tests. Do not require real hardware.

Suggested test coverage:

- parser recognizes `support bundle --output <path>`
- parser rejects missing output argument
- existing output path is rejected
- missing parent path is rejected
- bundle directory is created
- expected files are written
- manifest lists written files
- manifest does not list failed/skipped files as written
- no media capture functions are called
- no pipeline execution functions are called
- no arbitrary subprocess command is used
- JSON files use expected envelope shapes where applicable
- text success output includes bundle path
- version metadata updated to `0.18.0`

Mock probe/build functions where needed.

## Documentation Updates

Update:

- `README.md`
- `docs/SETUP.md`
- `docs/ARCHITECTURE.md` if architecture boundaries need documenting
- `docs/milestones/MILESTONE_18.md`
- `pyproject.toml`
- `src/gst_device_explorer/__init__.py`
- `uv.lock`

Document that support bundles are safe inspection exports and do not run
pipelines or capture media.

## Completion Criteria

Milestone 18 is complete when:

- `gst-device-explorer support bundle --output <path>` creates a support bundle
  directory.
- The command rejects existing output paths.
- The bundle includes a manifest.
- The bundle includes system report JSON and text.
- The bundle includes selected inventory/config/schema/suggestion artifacts.
- The bundle includes a TUI snapshot text artifact if practical.
- Tests pass without real hardware.
- Documentation is updated.
- Version is bumped to `0.18.0`.

## Deferred

Explicitly defer:

- `.tar.gz` output.
- `--force`.
- media capture.
- running suggested commands.
- preset execution.
- bundle upload.
- remote support workflows.
- GUI integration.
- MCP/tool descriptor integration.
- payload-specific schema expansion.
- config changing runtime behavior.

## Implementation Notes

### Files added and modified

New files:
- `src/gst_device_explorer/core/support.py` — `SupportBundleFile`, `SupportBundleManifest`, `validate_bundle_output_path`
- `tests/test_support_bundle.py` — 33 synthetic tests

Modified files:
- `src/gst_device_explorer/__init__.py` — bumped version to `0.18.0`
- `pyproject.toml` — bumped version to `0.18.0`
- `src/gst_device_explorer/cli/parser.py` — added `support bundle --output` subcommand
- `src/gst_device_explorer/cli/commands.py` — added `run_support_bundle()` and `_write_bundle_json()`
- `src/gst_device_explorer/cli/renderer.py` — added `print_support_bundle_written()`
- `src/gst_device_explorer/cli/serializers.py` — added `support_bundle_file_to_json_dict()` and `support_bundle_manifest_to_json_dict()`
- `src/gst_device_explorer/cli/main.py` — added `support bundle` dispatch
- `src/gst_device_explorer/core/schema.py` — added `support_bundle_manifest` schema document
- `README.md`, `docs/SETUP.md`, `docs/ARCHITECTURE.md` — documentation updates

### Manifest envelope decision

The manifest file (`manifest.json`) uses the success envelope form:
```json
{
  "schema_version": "1.0",
  "tool_version": "0.18.0",
  "kind": "support_bundle_manifest",
  "data": { ... }
}
```
This matches the existing serializer architecture cleanly. All other JSON
artifacts in the bundle also use the standard success envelope.

### TUI snapshot approach

The TUI snapshot is rendered using `core.tui.build_tui_review_model` and
`render_overview_lines` imported directly from `core/tui.py` in `commands.py`.
This avoids importing `cli/tui.py` (which would create a circular dependency)
while reusing the pre-built system report to avoid duplicate probe calls.

### Safety boundaries preserved

- No pipeline execution in `run_support_bundle`
- No media capture in `run_support_bundle`
- No subprocess calls beyond existing probe tools
- No suggested command execution
- No user-authored pipelines accepted
- All data comes from existing safe inspection functions

## Outcome

`gst-device-explorer` can export a practical, portable support/debug bundle for
field diagnostics and GitHub issue triage while preserving the project’s safety
boundaries.
