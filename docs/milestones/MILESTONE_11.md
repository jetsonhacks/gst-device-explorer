# Milestone 11 — Presets and Named Workflows

Status: Implemented

## Theme

Turn repeated `gst-device-explorer` command patterns into named, explainable workflows without adding a second execution system.

Milestone 11 should make common usage paths easier to discover and repeat while preserving the project's existing safety model:

- Probe first, build later.
- Keep pipeline candidates as structured objects, not raw command strings.
- Keep execution endpoint-based.
- Delegate real execution to existing safe commands.
- Avoid arbitrary user-authored pipelines.
- Avoid Reachy-specific behavior.
- Avoid JetPack-version-specific behavior.

## Recommended First Slice

The narrowest useful first slice is:

**Built-in preset catalog + preset inspection + safe command suggestions.**

This milestone should not introduce direct preset execution yet. Instead, presets should describe known workflows and generate suggested existing `gst-device-explorer` commands, preferably dry-run-first.

This keeps presets as an explainability and workflow layer rather than a new pipeline builder or execution framework.

## Goals

- Provide a small built-in catalog of named presets.
- Make presets inspectable from the CLI.
- Describe each preset's purpose, endpoint requirements, and safety behavior.
- Generate safe suggested commands using existing CLI flows.
- Prefer dry-run-first command suggestions.
- Provide text and JSON output.
- Keep behavior deterministic and testable with synthetic tests.

## Non-Goals

Milestone 11 should not implement:

- Arbitrary raw GStreamer pipeline execution.
- User-authored pipeline scripts.
- User-authored preset files.
- Plugin systems.
- Remote execution.
- Background workflows.
- Group-based execution.
- Synchronized audio/video capture.
- New capture formats.
- Package installation.
- System configuration changes.
- Reachy-specific hard-coding.
- JetPack-version-specific hard-coding.
- A replacement for existing `run`, `capture`, `profile`, `diagnostics`, `recommend`, or `validate` commands.

## Proposed Commands

```sh
gst-device-explorer preset list
gst-device-explorer preset list --json

gst-device-explorer preset show camera-preview
gst-device-explorer preset show camera-preview --json

gst-device-explorer preset command camera-preview video /dev/video0
gst-device-explorer preset command camera-preview video /dev/video0 --json

gst-device-explorer preset command audio-input-test audio-input hw:0,0
gst-device-explorer preset command audio-output-test audio-output hw:0,0

gst-device-explorer preset command short-video-capture video /dev/video0 --duration 5 --output sample.avi
gst-device-explorer preset command short-audio-capture audio-input hw:0,0 --duration 5 --output sample.wav
```

The `preset command` subcommand should print a suggested existing command. It should not run the command.

## Possible Built-in Presets

Start with a small catalog. Presets should map to capabilities already implemented by earlier milestones.

### `camera-preview`

Purpose:

Preview a video endpoint using the existing safe video run flow.

Required endpoint kind:

- `video`

Suggested command shape:

```sh
gst-device-explorer run video /dev/video0 --dry-run
```

Follow-up command shape:

```sh
gst-device-explorer run video /dev/video0
```

Notes:

- The preset should not choose arbitrary pipeline text.
- Candidate selection should remain delegated to the existing run command.
- Future versions may add `--candidate`, but the first slice can omit it unless already easy to pass through safely.

### `video-diagnostics`

Purpose:

Explain available and unavailable video pipeline candidates for a video endpoint.

Required endpoint kind:

- `video`

Suggested command shape:

```sh
gst-device-explorer diagnostics video /dev/video0
```

### `audio-input-test`

Purpose:

Exercise an ALSA audio input endpoint using the existing safe audio input run flow.

Required endpoint kind:

- `audio-input`

Suggested command shape:

```sh
gst-device-explorer run audio-input hw:0,0 --dry-run
```

Follow-up command shape:

```sh
gst-device-explorer run audio-input hw:0,0
```

### `audio-output-test`

Purpose:

Exercise an ALSA audio output endpoint using the existing safe audio output run flow.

Required endpoint kind:

- `audio-output`

Suggested command shape:

```sh
gst-device-explorer run audio-output hw:0,0 --dry-run
```

Follow-up command shape:

```sh
gst-device-explorer run audio-output hw:0,0
```

### `short-video-capture`

Purpose:

Generate a bounded video capture command using the existing capture flow.

Required endpoint kind:

- `video`

Required arguments:

- `--duration <seconds>`
- `--output <path>`

Suggested command shape:

```sh
gst-device-explorer capture video /dev/video0 --duration 5 --output sample.avi --dry-run
```

Follow-up command shape:

```sh
gst-device-explorer capture video /dev/video0 --duration 5 --output sample.avi
```

### `short-audio-capture`

Purpose:

Generate a bounded audio input capture command using the existing capture flow.

Required endpoint kind:

- `audio-input`

Required arguments:

- `--duration <seconds>`
- `--output <path>`

Suggested command shape:

```sh
gst-device-explorer capture audio-input hw:0,0 --duration 5 --output sample.wav --dry-run
```

Follow-up command shape:

```sh
gst-device-explorer capture audio-input hw:0,0 --duration 5 --output sample.wav
```

### `composite-device-validation`

Purpose:

Validate a discovered composite device group using the existing group validation flow.

Required target kind:

- `group`

Suggested command shape:

```sh
gst-device-explorer validate group <group-id>
```

Notes:

- This preset should not introduce group execution.
- It should only point to the existing validation command.

## Suggested Data Model

Add a small core model for presets.

Possible file:

```text
src/gst_device_explorer/core/presets.py
```

Possible models:

```python
@dataclass(frozen=True)
class PresetArgument:
    name: str
    description: str
    required: bool = False


@dataclass(frozen=True)
class PresetCommandSuggestion:
    argv: tuple[str, ...]
    dry_run: bool
    description: str


@dataclass(frozen=True)
class PresetDefinition:
    preset_id: str
    title: str
    description: str
    target_kind: str
    safety_notes: tuple[str, ...]
    arguments: tuple[PresetArgument, ...]
```

The exact shape can be adjusted to match the existing model style in the repository.

Important distinction:

- A preset is not a pipeline candidate.
- A preset is not a device profile.
- A preset is not a platform policy object.
- A preset is a named workflow description that can suggest existing safe commands.

## Suggested Core Functions

Possible pure functions:

```python
list_presets() -> list[PresetDefinition]
get_preset(preset_id: str) -> PresetDefinition | None
build_preset_command_suggestion(...) -> PresetCommandSuggestion
```

The command suggestion builder should return structured argv, not shell strings.

Rendering layers may display the argv as a shell-style command for human readability, but the core object should remain structured.

## CLI Behavior

### `preset list`

Text output should be compact:

```text
Available presets:
  camera-preview              Preview a video endpoint.
  video-diagnostics           Explain video candidate availability.
  audio-input-test            Test an ALSA audio input endpoint.
  audio-output-test           Test an ALSA audio output endpoint.
  short-video-capture         Suggest a bounded video capture command.
  short-audio-capture         Suggest a bounded audio capture command.
  composite-device-validation Validate a composite device group.
```

JSON output should include preset IDs, titles, target kinds, and short descriptions.

### `preset show <preset-id>`

Text output should explain:

- preset ID
- title
- description
- required target kind
- required arguments
- safety notes
- related existing command family

Example:

```text
Preset: camera-preview
Title: Camera Preview
Target kind: video

Description:
  Preview a video endpoint using the existing safe video run flow.

Safety:
  - Uses generated candidates only.
  - Suggests dry-run first.
  - Delegates execution to `gst-device-explorer run video`.
```

### `preset command <preset-id> ...`

Text output should provide a suggested command and explain that the command is not being run.

Example:

```text
Preset: camera-preview
Target: video /dev/video0

Suggested command:
  gst-device-explorer run video /dev/video0 --dry-run

This command was not executed.
Review the dry-run output before running a non-dry-run command.
```

JSON output should provide structured data:

```json
{
  "preset_id": "camera-preview",
  "target_kind": "video",
  "target": "/dev/video0",
  "suggestions": [
    {
      "description": "Inspect the generated video preview command before execution.",
      "dry_run": true,
      "argv": [
        "gst-device-explorer",
        "run",
        "video",
        "/dev/video0",
        "--dry-run"
      ]
    }
  ]
}
```

## Error Handling

Unknown preset:

```text
Preset not found: foo

Try:
  gst-device-explorer preset list
```

Wrong target kind:

```text
Preset `camera-preview` requires target kind `video`.
Received: audio-input
```

Missing required argument:

```text
Preset `short-video-capture` requires --duration and --output.
```

Duration and output validation should match the existing capture command expectations where practical, but this milestone should avoid duplicating too much capture validation logic in presets.

## Documentation Updates

Update:

- `README.md`
- `docs/SETUP.md`
- `docs/milestones/MILESTONE_11.md` or `docs/MILESTONE_11.md`, depending on the repository's current docs layout
- `docs/ARCHITECTURE.md`, if a new core preset module is added

The README should emphasize that presets are named safe workflows that suggest existing commands. They do not enable arbitrary pipelines.

## Tests

Add synthetic tests for:

- built-in preset registry contains expected IDs
- `get_preset()` returns known presets and rejects unknown presets
- `preset list` text output
- `preset list --json`
- `preset show <preset>` text output
- `preset show <preset> --json`
- `preset command camera-preview video /dev/video0`
- `preset command short-video-capture video /dev/video0 --duration 5 --output sample.avi`
- wrong target kind error
- missing required argument error
- unknown preset error

Tests should not require real hardware.

## Acceptance Criteria

Milestone 11 is complete when:

- Built-in presets can be listed.
- A single preset can be inspected.
- Presets can generate safe suggested commands as structured argv.
- Text and JSON output are available.
- The first slice does not execute preset commands directly.
- No raw user-authored GStreamer pipelines are accepted.
- No group execution is introduced.
- Synthetic tests pass.
- Documentation explains presets as safe named workflows over existing commands.
- Version metadata is bumped to `0.11.0`.

## Implemented First Slice

The implemented first slice adds:

- `gst-device-explorer preset list`
- `gst-device-explorer preset list --json`
- `gst-device-explorer preset show <preset-id>`
- `gst-device-explorer preset show <preset-id> --json`
- `gst-device-explorer preset command <preset-id> <target-kind> <target>`
- structured preset definitions, arguments, command requests, and command suggestions
- a deterministic built-in preset registry
- text and JSON rendering for preset lists, preset inspection, and command suggestions
- validation for unknown presets, wrong target kinds, and missing required capture arguments
- synthetic tests for the core registry, structured argv suggestions, CLI output, and error paths

Presets only suggest existing safe commands. They do not execute commands,
accept arbitrary GStreamer pipelines, add group execution, or replace existing
endpoint commands.

## Deferred Work

Potential future slices:

- `preset run` that delegates only to existing safe endpoint commands.
- Passing through explicit `--candidate` selections where appropriate.
- Integration with future bounded configuration/preferences.
- Preset recommendations based on endpoint profile or candidate ranking.
- Schema versioning for preset JSON output.
- TUI support for browsing and copying preset command suggestions.

These should remain deferred until the first slice proves useful.
