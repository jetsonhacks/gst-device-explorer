# Proposed Development Roadmap

This roadmap is a proposed path for `gst-device-explorer` development. It is not an absolute plan or a promise of future behavior. Each milestone should remain small, testable, and reversible.

The project should continue to follow these principles:

- Probe first, build later.
- Normalize raw system output into structured models before making decisions.
- Keep pipeline candidates as structured objects, not just strings.
- Treat CLI, JSON, future GUI, and future agent integrations as renderers over shared core models.
- Prefer capability detection over hard-coded platform checks.
- Avoid Reachy-specific behavior.
- Avoid arbitrary user-supplied pipeline execution.
- Keep grouping evidence-based and explainable.
- Use exploration sketches when a feature direction is uncertain.

## Completed Milestones

### Milestone 1 — Device Discovery and Video Candidate Generation

Implemented:

- GStreamer environment probing
- V4L2 video capability probing
- ALSA input/output discovery
- video pipeline candidate generation
- Jetson/NVIDIA MJPEG preview candidate generation
- text and JSON CLI output

Outcome:

`gst-device-explorer` can discover devices and generate useful video pipeline candidates.

---

### Milestone 2 — Safe Video Pipeline Execution

Implemented:

- stable `PipelineCandidate` IDs
- candidate selection by default, index, and ID
- `run video ... --dry-run`
- safe subprocess execution using generated argv
- no `shell=True`
- Ctrl+C cleanup
- no arbitrary user-supplied pipeline execution

Outcome:

The tool can safely run selected generated video candidates.

---

### Milestone 3 — Composite Device Grouping

Implemented:

- evidence-based grouping models
- exact ALSA card grouping
- exact USB parent-path grouping
- parent USB-family grouping
- V4L2 and ALSA sysfs metadata collection
- group CLI commands
- metadata diagnostic view

Outcome:

The tool can identify when multiple Linux endpoints likely belong to the same physical device.

---

### Milestone 4 — Audio Pipeline Candidates and Safe Audio Execution

Implemented:

- ALSA audio input pipeline candidates
- ALSA audio output pipeline candidates
- stable audio candidate IDs
- audio pipeline text and JSON inspection
- safe audio execution
- dry-run support
- candidate selection
- documentation and hardware validation flow

Outcome:

The tool can inspect and safely run bounded audio input/output tests.

---

### Milestone 5 — Pipeline Diagnostics and Explainability

Implemented:

- `PipelineDiagnostic` model
- shared diagnostic helpers
- audio diagnostics
- video diagnostics
- missing-element reporting
- `gst-inspect-1.0 <element>` suggested checks
- text and JSON diagnostics output

Outcome:

The tool can explain why pipeline candidates are available or unavailable.

---

### Milestone 6 — Device Profiles and Capability Summaries

Implemented:

- `DeviceProfile`
- `ProfileCandidateSummary`
- `ProfileGroupSummary`
- audio input profiles
- audio output profiles
- video profiles
- candidate summaries derived from diagnostics
- video capability summaries
- informational group membership summaries
- suggested next commands
- text and JSON profile output

Outcome:

The tool can summarize an endpoint as a practical field-debugging profile.

---

## Proposed Future Milestones

### Milestone 7 — Exportable System Reports

Theme:

Capture the whole media system state into one report.

Possible scope:

- system environment summary
- discovered video devices
- discovered audio devices
- composite groups
- endpoint profiles
- pipeline candidate summaries
- diagnostic summaries
- missing GStreamer elements
- suggested next checks
- JSON report output
- optional file output

Possible commands:

```sh
gst-device-explorer report
gst-device-explorer report --json
gst-device-explorer report --output report.json
```

Why this matters:

A report would be useful for GitHub issues, hardware validation, comparing Jetson systems, debugging remote machines, and documenting known-good setups.

Exploration sketch candidates:

- `sketches/report_json_shape.py`
- `sketches/report_text_layout.py`

Out of scope:

- running pipelines
- recording media
- changing system configuration
- package installation

---

### Milestone 8 — Candidate Ranking and Recommendations

Theme:

Choose the best candidate to try first.

Possible scope:

- recommended/default candidate marker
- ranking reasons
- safety ranking
- compatibility ranking
- Jetson acceleration preference
- simple text and JSON recommendation output

Possible commands:

```sh
gst-device-explorer recommend video /dev/video0
gst-device-explorer recommend audio-input hw:0,0
gst-device-explorer recommend audio-output hw:0,0
```

Possible output:

```text
Recommended: jetson-uvc-mjpeg-nvjpeg-nveglglessink
Reason: Device exposes MJPEG, NVIDIA JPEG decoder is available, and nveglglessink is present.
```

Why this matters:

The project can already list and explain candidates. Ranking helps users decide what to try first.

Exploration sketch candidates:

- `sketches/recommendation_rules.py`
- `sketches/candidate_ranking_matrix.md`

Out of scope:

- benchmarking
- automatically running recommended candidates
- user preference files
- arbitrary scoring plugins

---

### Milestone 9 — Bounded Capture Tests

Theme:

Generate short, controlled media samples.

Possible scope:

- short video capture
- short audio capture
- duration limit
- explicit output path
- dry-run support
- generated candidate argv only
- safe subprocess execution

Possible commands:

```sh
gst-device-explorer capture video /dev/video0 --duration 5 --output test.avi
gst-device-explorer capture audio-input hw:0,0 --duration 5 --output test.wav
gst-device-explorer capture video /dev/video0 --duration 5 --output test.avi --dry-run
```

Why this matters:

Preview tests are useful, but a bounded capture proves that the system can produce a usable file.

Exploration sketch candidates:

- `sketches/video_capture_candidates.py`
- `sketches/audio_capture_candidates.py`
- `sketches/capture_safety_rules.md`

Out of scope:

- long-running recording systems
- streaming
- synchronized audio/video capture
- arbitrary transcoding workflows
- file management beyond explicit output paths

---

### Milestone 10 — Composite Device Validation

Theme:

Validate a composite device without making group behavior magical.

Possible scope:

- group-level profile summary
- group-level report summary
- validate all endpoints in a group
- show camera/audio candidates together
- show missing dependencies across the group
- suggest per-endpoint next commands

Possible commands:

```sh
gst-device-explorer profile group <group-id>
gst-device-explorer report group <group-id>
gst-device-explorer validate group <group-id>
gst-device-explorer validate group <group-id> --json
```

Why this matters:

Devices such as Reachy Mini appear as multiple Linux endpoints. Composite validation helps users understand the whole attached device while keeping execution endpoint-based.

Exploration sketch candidates:

- `sketches/group_profile_shape.md`
- `sketches/group_validation_output.md`

Out of scope:

- group-based pipeline execution
- synchronized capture
- automatic endpoint selection for execution
- Reachy-specific hard-coding

---

### Milestone 11 — Presets and Named Workflows

Theme:

Turn repeated command patterns into named, explainable workflows.

Possible scope:

- built-in presets
- preset descriptions
- required device kind
- linked pipeline candidates
- dry-run-first workflow
- JSON preset descriptions

Possible commands:

```sh
gst-device-explorer preset list
gst-device-explorer preset show camera-preview
gst-device-explorer preset run camera-preview video /dev/video0 --dry-run
gst-device-explorer preset run audio-output-test audio-output hw:0,0 --dry-run
```

Possible presets:

- `camera-preview`
- `camera-diagnostics`
- `audio-input-level-test`
- `audio-output-sine-test`
- `short-video-capture`
- `short-audio-capture`
- `composite-device-validation`

Why this matters:

Presets make the tool easier to explain and easier to use repeatedly without introducing arbitrary pipeline execution.

Exploration sketch candidates:

- `sketches/preset_model.py`
- `sketches/preset_cli_layout.md`

Out of scope:

- user-authored arbitrary pipelines
- pipeline scripting
- plugin systems
- remote execution

---

### Milestone 12 — Configuration and Preferences

Theme:

Let users express bounded preferences safely.

Possible scope:

- configuration file discovery
- config validation
- read-only config display
- bounded preference values
- recommendation biasing
- preferred video sink
- preferred audio test frequency
- report verbosity preferences

Possible commands:

```sh
gst-device-explorer config path
gst-device-explorer config show
gst-device-explorer config validate
```

Possible configuration shape:

```toml
[video]
preferred_sink = "nveglglessink"
prefer_jetson_acceleration = true
max_preview_resolution = "1920x1080"

[audio]
output_test_frequency = 440
prefer_silent_input_tests = true

[report]
include_metadata = true
include_diagnostics = true
```

Why this matters:

Once recommendations and presets exist, users need a safe way to express preferences without editing code.

Exploration sketch candidates:

- `sketches/config_schema.toml`
- `sketches/config_validation.py`

Out of scope:

- arbitrary command execution
- user-defined raw pipelines
- modifying system audio/video settings
- auto-installing packages

---

### Milestone 13 — Machine-Readable Schema Stability

Theme:

Treat JSON output as a stable external interface.

Possible scope:

- schema version field
- tool version field
- JSON schema documents
- compatibility notes
- schema validation tests
- breaking-change policy

Possible commands:

```sh
gst-device-explorer schema list
gst-device-explorer schema show device-profile
gst-device-explorer schema show report
```

Possible JSON wrapper:

```json
{
  "schema_version": "1.0",
  "tool_version": "0.13.0",
  "kind": "device_profile",
  "data": {}
}
```

Why this matters:

The project already emits structured JSON. Schema stability makes it safer for GUI tools, agents, scripts, and external integrations to consume.

Exploration sketch candidates:

- `sketches/schema_wrappers.md`
- `sketches/json_schema_device_profile.json`

Out of scope:

- network API
- server mode
- GUI implementation

---

### Milestone 14 — Interactive TUI Review Mode

Theme:

Make field debugging easier without building a full GUI.

Possible scope:

- browse devices
- browse groups
- inspect profiles
- inspect diagnostics
- inspect reports
- copy suggested commands
- possibly dry-run selected commands, if safe and explicit

Possible command:

```sh
gst-device-explorer tui
```

Why this matters:

A terminal UI could make the tool much easier to use on Jetson systems over SSH while avoiding the complexity of a full graphical application.

Exploration sketch candidates:

- `sketches/tui_navigation.md`
- `sketches/tui_data_model.py`

Out of scope:

- full GUI
- media preview windows
- arbitrary pipeline editor
- long-running dashboard

---

### Milestone 15 — GUI and Agent Integration Boundary

Theme:

Prepare the project for front ends without baking one in.

Possible scope:

- consolidated JSON command set
- command discovery metadata
- capability metadata
- stable schemas
- possible MCP/tool descriptor generation
- examples for GUI or agent use

Possible commands:

```sh
gst-device-explorer capabilities --json
gst-device-explorer commands --json
gst-device-explorer mcp-descriptor
```

Why this matters:

At this point, `gst-device-explorer` becomes more than a CLI utility. It becomes a structured media-system introspection layer that other tools can drive.

Exploration sketch candidates:

- `sketches/agent_tool_descriptor.json`
- `sketches/gui_boundary.md`
- `sketches/mcp_descriptor.md`

Out of scope:

- actually building the GUI
- running a web server
- remote execution
- arbitrary pipeline control

---

## Exploration Sketches

Some future milestones may benefit from small sketches before implementation.

Sketches should be:

- clearly marked experimental
- isolated from production code
- easy to delete
- focused on shape and behavior, not completeness
- used to answer design questions before committing to core models

Possible location:

```text
sketches/
```

Possible sketch types:

- JSON shape examples
- CLI output mockups
- ranking rule experiments
- schema drafts
- small one-file Python prototypes
- TUI navigation notes
- report layout examples

Sketches should not become hidden production dependencies.

## Roadmap Summary

```text
Milestone 1: Discover devices and generate video candidates.
Milestone 2: Safely run selected video candidates.
Milestone 3: Group related physical device endpoints.
Milestone 4: Generate and safely run bounded audio test candidates.
Milestone 5: Explain pipeline candidate availability.
Milestone 6: Summarize individual endpoints with device profiles.
Milestone 7: Export whole-system reports.
Milestone 8: Rank and recommend candidates.
Milestone 9: Capture bounded media samples.
Milestone 10: Validate composite devices.
Milestone 11: Add named safe workflows.
Milestone 12: Add bounded configuration and preferences.
Milestone 13: Stabilize JSON schemas.
Milestone 14: Add interactive terminal review mode.
Milestone 15: Define GUI and agent integration boundaries.
```
