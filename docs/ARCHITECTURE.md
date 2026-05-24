# Architecture

`gst-device-explorer` should be organized around separate layers that each own a
specific responsibility. The goal is to make probing, modeling, profile
selection, pipeline construction, and presentation evolve independently.

The first implementation domain is GStreamer-oriented media exploration. The
architecture should also leave room for future exploration plugins without
turning Milestone 1 into a generic hardware inventory system.

The core architecture should separate the exploration framework from the initial
media-specific probes. GStreamer video/audio support is the first domain, not
the only possible domain.

## Probes

Probes inspect the local system and collect raw information from tools and APIs
such as GStreamer, v4l2, ALSA, PulseAudio, PipeWire, and platform-specific
commands. They should avoid making final product decisions.

Initial probes should focus on video inputs, audio inputs, audio outputs, and
the local GStreamer environment.

## Normalized Models

Normalized models convert raw probe output into consistent representations of
devices, capabilities, formats, environment facts, warnings, and availability.
Later layers should depend on these models instead of parsing command output
directly.

## Profiles

The project uses two distinct concepts under the "profile" umbrella.

**Candidate profile labels** are string metadata attached to `PipelineCandidate`
objects. They identify the generation strategy or family used to construct the
candidate, for example `"generic-linux-video-preview"` or
`"jetson-video-preview"`. These labels are candidate metadata; they are not
policy objects consumed by builders.

**`DeviceProfile`** is an endpoint summary built after discovery and candidate
generation. It combines discovered device facts, a capability summary, pipeline
candidate summaries, group membership, and suggested next commands into a
structured view for CLI/JSON inspection and system reports. It does not control
pipeline generation.

A richer platform-policy Profile layer — where a named object expresses
preferences and known-good patterns consumed by pipeline builders — may be added
in a later milestone but is not part of the current implementation.

## Pipeline Builders

Pipeline builders consume normalized device models, capabilities, and
environment facts to produce structured pipeline candidates. They do not consume
Profile policy objects. Candidates carry a profile label identifying the
generation strategy. Builders should record assumptions, requirements, ranking
signals, and warnings alongside the rendered GStreamer pipeline string.

Pipeline builders are part of the initial media exploration domain. Other future
exploration plugins may have their own candidate builders or recommendation
objects.

## Grouping Engine

The grouping pipeline has two core-layer steps:

```text
discovery -> grouping metadata -> grouping engine -> composite devices
```

The grouping metadata step converts discovered `Device` objects into
`GroupableDevice` records. It may read directly available normalized metadata or
safe sysfs files, including V4L2 video device paths and ALSA sound device
paths, but it should not call shell commands or depend on optional external
tools.

The grouping engine consumes normalized grouping metadata and emits
`CompositeDevice` objects. It should not call shell commands, parse raw probe
output, or depend on live hardware directly.

Grouping is evidence-based. A group records member `DeviceRef` objects,
confidence, and `GroupingEvidence` so renderers can show uncertainty instead of
hiding it. The grouping layer enriches discovery; it does not replace raw
individual device views.

Milestone 3 emits exact USB-device groups for devices sharing the same USB
parent path. It can also emit a parent USB-family group above multiple exact
USB-device groups when they share a meaningful USB ancestor, USB vendor ID, and
non-generic product-family token. Devices without that evidence remain
independent; for example, a separate Orbbec Femto Bolt attached alongside a
robot is not folded into the robot's USB-family group.

The CLI renders computed groups through `groups`, `groups --json`, `group
<group-id>`, and `group <group-id> --json`. It can also render the normalized
metadata feeding the grouping engine through `groups --metadata` and
`groups --metadata --json`. Group rendering is presentation only; group-based
pipeline generation and execution are outside the current scope.

## Validation

Group validation is a core layer that summarizes an existing `CompositeDevice`
using already-built endpoint profiles. It preserves grouping evidence, derives
simple endpoint and group statuses, aggregates missing elements, and suggests
endpoint-level next commands.

Validation does not probe hardware directly and does not execute pipelines or
capture commands. The CLI assembles current groups and endpoint profiles, then
delegates to the pure validation builder. Individual endpoint commands remain
responsible for detailed inspection, recommendation, execution, and capture.

## Presets

Presets are a small built-in workflow catalog over existing commands. A preset
describes a common task, its target kind, required arguments, safety notes, and
one or more structured argv command suggestions.

Presets do not probe hardware, build pipelines, execute commands, accept raw
GStreamer strings, or replace endpoint commands. They are an explainability and
repeatability layer that points users back to the existing `run`, `capture`,
`pipeline --diagnostics`, and `validate group` flows.

## Configuration

Configuration is a bounded preference model with pure parsing and validation in
the core layer. The CLI can show search paths, display the effective/default
configuration, and validate TOML files.

Milestone 12 configuration is display and validation only. It does not alter
candidate generation, ranking, presets, reports, capture, validation, or
execution. Configuration files cannot define raw pipelines, shell commands,
scripts, hooks, plugins, or remote behavior.

## Suggested Command Catalog

`SuggestedCommand` is a frozen, hashable dataclass in the core layer. It
represents a displayable, advisory command — something the user can copy and
run manually. It is never executed automatically by this tool.

The model carries: `id` (slug derived from argv), `title`, `argv` (tuple),
`purpose`, `source`, `safety`, optional `target_kind`, `target`, and `notes`.
A `command` property renders the argv via `shlex.join` for shell-safe display.

Builder functions in `core/suggestions.py` construct named suggestions for
all endpoint kinds and tool commands. Builders are pure functions with no
side effects. The `list_generic_suggestions()` function returns a static catalog
of broad starting-point commands for the `suggestions list` CLI command.

Four model fields changed from `list[str]` to `list[SuggestedCommand]` in
Milestone 16: `DeviceProfile.suggested_next_commands`,
`SystemReport.suggested_next_commands`,
`EndpointValidationSummary.suggested_next_commands`, and
`GroupValidation.suggested_next_commands`. Serializers expose the full
`SuggestedCommand` shape under these keys. Renderers extract `.command` for
text display.

Safety vocabulary: `inspection`, `dry_run`, `bounded_capture`,
`safe_execution`, `external_check`.

## Schema Stability

Selected JSON outputs are wrapped in a small stable envelope. The core schema
helper supplies `schema_version`, `tool_version`, `kind`, and `data` fields so
scripts and future UI layers can identify the response family before reading
the command-specific payload.

Milestone 13 applied the envelope to bounded config and preset JSON outputs and
added schema discovery commands for the envelope contract. Milestone 14 extends
that same wrapper to older hardware-oriented JSON outputs at the renderer
boundary. Command-specific payloads are preserved under `data`.

## Error Envelopes

Selected known JSON error paths use a companion error envelope form:

```json
{
  "schema_version": "1.0",
  "tool_version": "0.17.0",
  "kind": "error",
  "error": {
    "code": "unknown_schema",
    "message": "...",
    "details": {},
    "suggested_commands": []
  }
}
```

Error envelopes differ from success envelopes: they use `kind: "error"` and put
the payload under `error` instead of `data`. The `error.code` is a stable
snake_case identifier for programmatic handling. The `error.message` is
human-readable. The `error.details` map carries command-specific context.
`error.suggested_commands` is advisory — it is never executed automatically.

`ErrorResponse` is a frozen dataclass in `core/errors.py`. `make_error_envelope`
in `cli/serializers.py` wraps it with the schema/tool version fields.
`print_json_error` in `cli/renderer.py` serializes and prints it.

Milestone 17 wraps: unknown schema, unknown preset, wrong preset target kind,
missing required preset arguments, and group-not-found error paths.

Non-JSON error paths preserve existing human-readable text behavior.
Non-zero exit codes are preserved for all error paths.

The schema layer does not generate full JSON Schema files and does not change
probing, candidate generation, ranking, execution, capture, validation, preset,
or configuration behavior.

## Renderers

Renderers turn normalized models and pipeline candidates into user-facing
representations. The first renderer is expected to be a CLI. A future GUI should
use the same underlying models and builders rather than duplicating discovery or
pipeline logic.

## GUI Application Model

Milestone 19 resets the product direction around a GUI-first media explorer:
camera-caps for modern Jetson media devices. The CLI remains a backend, debug
surface, and testable probe layer, but future work should be judged by whether
it improves the GUI media exploration experience.

`gst_device_explorer.gui.model` defines frozen, toolkit-neutral dataclasses for
a future sidebar/main-pane application:

- `MediaExplorerSnapshot`
- `SidebarNode`
- `DetailPaneModel`
- `DetailSection`
- `GuiAction`
- `GuiActionResult`

`gst_device_explorer.gui.builders` maps existing core models such as `Device`,
`CompositeDevice`, `DeviceProfile`, `GroupValidation`, and `CandidateRanking`
into renderable GUI state. These builders are pure: they do not probe hardware,
run subprocesses, execute GStreamer pipelines, capture media, start background
workflows, or import Qt, GTK, Tkinter, Textual, web frameworks, or any other GUI
toolkit.

GUI actions are advisory metadata only. Where possible they reference existing
`SuggestedCommand` objects so a future GUI can show or copy generated commands
without opening an arbitrary execution surface.

## TUI Review Mode

The TUI is a read-only renderer over existing report, preset, configuration, and
schema data. Its core review model and navigation state are pure and testable
without opening a terminal. The curses runner is intentionally thin: it maps key
presses to state transitions and draws rendered lines.

Milestone 15 TUI mode displays suggested CLI commands but does not execute them.
It does not run pipelines, run capture, execute presets, edit configuration,
install packages, or change system settings.

## Support Bundle Export

The support bundle is a safe export of existing inspection surfaces, written as
a new directory at an explicit output path. It does not execute pipelines, does
not capture media, does not run suggested commands, does not install packages,
and does not change system configuration.

`core/support.py` defines two frozen dataclasses:

- `SupportBundleFile` — describes one written file (path, kind, description, required)
- `SupportBundleManifest` — bundle metadata including file list, creation timestamp,
  warnings, and notes

`validate_bundle_output_path()` enforces the pre-write invariants: the output
path must not already exist and its parent must be an existing directory. This
function raises before any writes begin.

The bundle-writing logic in `cli/commands.py` gathers data from existing shared
functions (report builder, config, schema, suggestions, discovery), writes each
artifact using the standard JSON envelope format, captures the system report as
both JSON and text, renders the TUI snapshot using `core.tui.build_tui_review_model`
and `render_overview_lines`, and writes the manifest as the final step. The
manifest only lists files that were actually written.

Milestone 18 defers: `.tar.gz` format, `--force`, bundle upload, media capture,
running suggested commands, preset execution, and MCP/tool descriptor integration.

## Execution Flow

Safe execution is a separate layer that consumes structured pipeline candidates.
The CLI acts as a renderer/controller: it asks probes and builders for data,
renders the selected plan for the user, and delegates subprocess handling to the
execution helper.

```text
probe device
  -> normalize capabilities
  -> build ranked PipelineCandidate objects
  -> select candidate
  -> create ExecutionPlan
  -> render display command
  -> execute argv
```

Pipeline generation and pipeline execution remain separate. A
`PipelineCandidate` contains both a display command and an argv representation.
The display command is for humans; the argv list is what execution passes to
`subprocess.Popen(argv)`.

## Exploration Plugins

The core architecture should allow future exploration plugins to add new probe
families, normalized models, profiles, builders, and renderers. A later plugin
might inspect robot hardware such as actuators, Dynamixel servos, sensors, or
other device classes.

This extensibility should remain secondary to the first domain. Milestone 1
should establish GStreamer-oriented device exploration first and leave clean
extension points for hardware exploration later.

## Separation of Concerns

Each layer should communicate through explicit data structures. Probes should not
format CLI output. Renderers should not inspect hardware directly. Pipeline
builders should accept normalized models and produce structured candidates.
This separation keeps Milestone 1 small while leaving room for richer interfaces
and future exploration plugins later.
