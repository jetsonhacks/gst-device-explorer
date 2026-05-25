# GUI Product Scope

`gst-device-explorer` is pivoting back to its original product direction: a graphical media device explorer inspired by the earlier `camera-caps` project, but expanded beyond cameras to include audio input, audio output, and grouped composite devices.

The command-line interface and structured core models remain valuable, but they should now be treated primarily as the probe, diagnostic, and debug foundation for a GUI-first application.

## Product Statement

`gst-device-explorer` is a GUI-first Linux / Jetson media device explorer that discovers cameras, microphones, speakers, and composite USB devices, then lets the user inspect capabilities and safely try generated GStreamer actions.

A shorter framing:

```text
camera-caps for modern Jetson media devices.
```

## Target User

The primary user is a Linux / Jetson developer working with media devices attached to a local system.

Examples:

- A developer plugging in a USB camera and trying to understand supported formats.
- A Jetson user testing which GStreamer preview path works on a given platform.
- A developer examining USB audio input and output devices.
- A robotics developer working with a composite device that appears as multiple Linux endpoints.
- A Reachy Mini-style workflow where a single physical device may expose a camera, microphone, and speaker.

## Primary Use Cases

The GUI should help a user answer these questions:

1. What media devices are present?
2. Which endpoints appear to belong to the same physical device?
3. What capabilities does a selected camera, microphone, or speaker expose?
4. Which generated GStreamer test or preview action should I try first?
5. Why is a candidate unavailable?
6. Can I safely preview a camera, test audio output, test audio input, or create a short bounded capture?
7. What information should I collect if I need help debugging the system?

## Product Shape

The GUI should be organized around a sidebar and a main detail pane.

```text
┌────────────────────────────────────────────────────────────┐
│ gst-device-explorer                                       │
├───────────────────────┬────────────────────────────────────┤
│ Sidebar               │ Main Detail Pane                   │
│                       │                                    │
│ ▾ Composite Device    │ Selected: Camera /dev/video0       │
│   📷 Camera           │                                    │
│   🎙 Microphone        │ Capabilities                       │
│   🔊 Speaker           │ Candidate Pipelines                │
│                       │ Diagnostics                        │
│ ▸ USB Camera          │ Controls                           │
│ ▸ Built-in Audio      │                                    │
│                       │ [Preview] [Dry Run] [Copy]         │
└───────────────────────┴────────────────────────────────────┘
```

## Sidebar Model

The sidebar represents discovered devices and groups.

Groups should expand into their constituent endpoints.

Example:

```text
Devices
├── Composite Groups
│   ├── USB Device Group 1
│   │   ├── Camera /dev/video0
│   │   ├── Audio Input hw:2,0
│   │   └── Audio Output hw:2,0
│   └── USB Device Group 2
│       └── Camera /dev/video1
│
├── Cameras
│   ├── /dev/video0
│   └── /dev/video1
│
├── Audio Inputs
│   └── hw:2,0
│
└── Audio Outputs
    └── hw:2,0
```

The sidebar should support:

- refresh of discovered devices
- group expansion and collapse
- selection of a group
- selection of a camera endpoint
- selection of an audio input endpoint
- selection of an audio output endpoint
- clear status indicators where practical

A device may appear both under a composite group and under its endpoint category. The GUI model should make it clear whether these are two views of the same endpoint, not duplicate physical devices.

## Main Pane Model

The main pane details the currently selected sidebar item.

### Group Detail Pane

A group detail pane should show:

- group identity
- grouping evidence
- constituent endpoints
- endpoint status summary
- group validation status, when available
- missing elements aggregated across endpoints, when available
- suggested next actions

Possible controls:

- Refresh Group
- Validate Group
- Copy Summary
- Export Report or Support Bundle, if already supported by the backend

The group pane must not introduce group-based execution or synchronized capture.

### Camera Detail Pane

A camera detail pane should show:

- device path
- card, driver, bus, and sysfs metadata where available
- supported formats
- supported resolutions
- supported frame rates
- generated preview candidates
- recommended candidate
- candidate diagnostics
- missing GStreamer elements

Possible controls:

- Preview
- Dry Run
- Copy Pipeline
- Capture Short Sample
- Show Diagnostics

### Audio Input Detail Pane

An audio input detail pane should show:

- ALSA endpoint identifier
- card and device metadata where available
- generated audio input candidates
- recommended input test or capture candidate
- candidate diagnostics
- missing GStreamer elements

Possible controls:

- Test Input
- Record Short WAV
- Dry Run
- Copy Pipeline
- Show Diagnostics

### Audio Output Detail Pane

An audio output detail pane should show:

- ALSA endpoint identifier
- card and device metadata where available
- generated audio output candidates
- recommended speaker test candidate
- candidate diagnostics
- missing GStreamer elements

Possible controls:

- Test Speaker
- Dry Run
- Copy Pipeline
- Show Diagnostics

## Safe Action Model

The GUI must not accept arbitrary GStreamer pipeline strings from the user.

The GUI may expose actions only when they map to existing safe backend behavior:

```text
GUI button → generated candidate/action → existing bounded execution path
```

Allowed action categories:

- refresh discovery
- inspect endpoint details
- inspect group details
- dry-run a generated candidate
- run a generated safe preview/test candidate
- stop a running safe action
- bounded capture using generated candidates
- copy a generated command or pipeline
- export an existing report or support bundle

Disallowed action categories:

- arbitrary raw pipeline execution
- user-authored pipeline scripts
- plugin execution
- remote execution
- background workflows
- hidden retries
- package installation
- system configuration changes
- group-based execution unless explicitly scoped in a future milestone
- synchronized multi-endpoint capture unless explicitly scoped in a future milestone

## Relationship to Existing CLI and Core

The existing CLI remains important, but it is no longer the product north star.

The existing core work should be reused as the GUI backend:

- discovery
- capability probing
- pipeline candidate generation
- diagnostics
- recommendations
- grouping
- validation
- bounded capture
- safe execution
- reports
- support bundle export

The GUI should not expose backend implementation concepts such as JSON envelopes, schema names, or serializer internals as primary user-facing concepts.

Instead, the GUI should translate them into direct user-facing information:

```text
Camera detected.
This endpoint appears to belong to the same USB device as this microphone.
This preview candidate is recommended.
This test is unavailable because a required GStreamer element is missing.
```

## GUI Application Model Direction

Before committing deeply to a toolkit, the project should define a GUI-facing application model.

Possible plain dataclasses:

```python
@dataclass(frozen=True)
class MediaExplorerSnapshot:
    sidebar_roots: list[SidebarNode]
    selected_node_id: str | None
    generated_at: str
```

```python
@dataclass(frozen=True)
class SidebarNode:
    id: str
    label: str
    kind: str
    status: str
    children: list[SidebarNode]
    target_kind: str | None = None
    target: str | None = None
```

```python
@dataclass(frozen=True)
class DetailPaneModel:
    selected_id: str
    title: str
    kind: str
    summary: list[str]
    sections: list[DetailSection]
    actions: list[GuiAction]
```

```python
@dataclass(frozen=True)
class GuiAction:
    id: str
    label: str
    kind: str
    enabled: bool
    safety: str
    suggested_command: SuggestedCommand | None
    disabled_reason: str | None = None
```

The GUI toolkit should render this model. It should not become the place where probing, grouping, ranking, or diagnostics logic is reinvented.

Milestone 19 implements the first version of this model in
`src/gst_device_explorer/gui/`. The package is toolkit-neutral and contains:

- frozen dataclasses for sidebar nodes, detail panes, sections, GUI actions,
  action results, and full media explorer snapshots
- pure builders that adapt existing core models into GUI-facing state
- synthetic tests for grouped devices, endpoint details, safe action metadata,
  unknown selections, and empty system state

This milestone does not implement a GUI window, event loop, preview widget,
web server, subprocess controller, capture workflow, or toolkit dependency.

## Toolkit Direction

PySide6 / Qt is the initial concrete GUI toolkit. It provides a straightforward
desktop application model, tree widgets, detail panes, process integration, and
a traditional local utility feel.

Milestone 20 adds a minimal PySide6 shell that renders the toolkit-neutral GUI
model from Milestone 19. The shell has a sidebar, expandable group nodes, a
detail pane, and non-executing action controls. It also includes a deterministic
demo snapshot for early screenshots and HIL manual validation.

Milestone 21 connects the shell to live read-only discovery when launched
without `--demo`:

```sh
gst-device-explorer gui
```

Demo mode remains deterministic and hardware-free:

```sh
gst-device-explorer gui --demo
```

The GUI Refresh control rebuilds the read-only live snapshot and updates the
sidebar/detail panes. It does not run GUI actions, execute suggested commands,
start media pipelines, capture media, install packages, or change system
configuration.

Milestone 22 improves the selected-item detail pane with clearer identity,
summary, capability, candidate, diagnostic, safe-action, and notes sections.
Copy buttons are allowed only for already-displayed text such as endpoint IDs,
group IDs, and suggested command strings. Copying text does not run commands.

Milestone 23 makes the camera detail pane task-oriented. When a camera is
selected, the first visible content should be camera exploration: pixel format,
resolution, frame-rate choices, generated pipeline text, copy pipeline controls,
and dynamically discovered V4L2 controls. Controls are discovered per camera
from advertised V4L2 metadata and rendered read-only; applying values, resetting
values, previewing, dry-running, and capture remain deferred.

PySide6 is kept out of core probe/discovery modules. CLI-only behavior should
continue to work without importing Qt unless the GUI command is launched.

## Explicitly Deferred

The following are deferred until the GUI becomes tangible:

- MCP integration
- agent descriptors
- command discovery metadata
- additional schema expansion
- support bundle polish beyond basic usefulness
- advanced TUI drill-downs
- config-driven behavior changes
- preset expansion
- GUI plugin systems
- server mode
- remote operation

## Near-Term GUI Roadmap

```text
19. GUI Product Scope and Application Model
20. Minimal GUI Shell
21. Sidebar Device/Group Tree
22. Endpoint Detail Panes
23. Camera Explorer Pane and Dynamic V4L2 Controls
24. Safe GUI Actions
25. Camera Preview and Audio Test UX
26. Reachy Mini-Style Composite Device Validation
27. Packaging and Demo Documentation
```

## Success Criteria

The GUI direction is successful when a user can plug in a camera, microphone, speaker, or composite media device and immediately see:

- what was discovered
- how endpoints are grouped
- what each endpoint can do
- which safe action to try first
- why unavailable actions are unavailable
- how to copy or run a generated safe test

The north star is a useful screenshot, not another schema document.
