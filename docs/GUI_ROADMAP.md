# GUI Roadmap

This roadmap describes the proposed GUI-centered development path for `gst-device-explorer` after version 0.24.0.

The intent is to pause feature momentum and re-center the application around device exploration rather than report rendering. The existing discovery, probing, grouping, pipeline generation, diagnostics, execution, and reporting code remains valuable, but the GUI should present a cleaner workflow for selecting, understanding, and deliberately testing media devices.

## Product Direction

`gst-device-explorer` should be treated as a GUI-first media endpoint explorer for Jetson and Linux systems.

The application should help a user:

- discover connected cameras, microphones, speakers, and grouped physical devices
- select or inspect hardware capabilities through a GUI instead of manual command-line probing
- generate useful GStreamer commands from selected settings
- preview or test selected configurations only when explicitly supported
- inspect lower-level device information when needed
- reproduce the same investigation from the CLI when the workflow is mature enough to document

The primary GUI distinction should be:

- **Explore**: work with the selected endpoint or group
- **Device Information**: understand what the system discovered about the selected endpoint or group
- **Reports/Diagnostics**: produce full accounting for support, debugging, or documentation
- **Commands/Reproduce**: teach how to reproduce GUI-derived investigation from the CLI

Report-oriented data should not dominate the default view.

## Development Principles

Development should proceed from first principles rather than simply exposing whatever the backend already knows.

Each milestone should ask:

- What is the user trying to do?
- What device concept is being represented?
- What is the smallest useful interaction?
- What information must be visible now?
- What information belongs in a secondary view?
- What should remain internal, diagnostic, or support-only?
- What safety boundary is at risk if we proceed too quickly?

Python files should generally stay limited to about **250 to 300 lines**.

When a Python file grows beyond that range, it is usually a sign that the file is handling too many areas of concern. The implementation should be reviewed for clearer separation of responsibilities.

When a Python file exceeds **400 lines**, there should be an explicit review before continuing to add functionality to that file. The review should consider whether to split the file by responsibility, such as:

- UI widget construction
- application service logic
- model adaptation
- command generation
- formatting/rendering helpers
- process execution
- tests or fixtures

The goal is not to enforce an arbitrary line count. The goal is to keep the codebase understandable, testable, and easy to reshape as the product direction becomes clearer.

## Established Explore-Page Pattern

Milestones 29–33 established the current Explore-page pattern:

```text
Compact endpoint or group summary
Mode/capability selection or presentation
Generated command or pipeline
Compact read-only monospace code/copy surface
Future safe-action placeholder, only when useful
Read-only inspector semantics
Secondary/raw/detail material kept in Device Information or Reports
```

Current adaptations:

```text
Camera Explore:
Endpoint summary
Camera Mode
Generated video pipeline
Camera controls/properties

Audio Input Explore:
Endpoint summary
Audio Input Mode
Generated input pipeline
Future input test placeholder

Audio Output Explore:
Endpoint summary
Audio Output Mode
Generated output/test pipeline
Future speaker test placeholder

Group Explore:
Group summary
Evidence summary
Endpoint cards
Navigation to endpoint Explore pages
No group-based execution
```

This pattern should be preserved while the first hardware-interaction milestones are designed and implemented.

## Milestone 25 — Product and GUI Structure Reset

Define the application as a GUI-first media device explorer.

Establish:

- one-sentence product definition
- primary user
- main first-run workflow
- sidebar behavior
- selected-device tab structure
- group role
- what belongs in Explore views
- what belongs in Device Information views
- what remains report, diagnostic, or support infrastructure

This should be a design/spec milestone, not a feature milestone.

## Milestone 26 — Main Pane Tab Redesign

Refactor selected-device pages into a default **Explore** tab and a secondary **Device Information** tab.

The Explore tab should be the working surface for the selected device.

The Device Information tab should contain lower-level identity, metadata, capabilities, diagnostics, and command-reproduction information.

## Milestone 27 — Camera Explore Tab Cleanup

Make the camera page feel like a working control surface rather than rendered report output.

The page should prioritize:

- compact device summary
- pixel format selection
- image size selection
- frame duration / FPS selection
- generated GStreamer pipeline
- copy action
- dynamic read-only camera controls

The interaction model should follow the successful camera-caps direction while using cleaner layout and implementation practices.

## Milestone 28 — Camera Device Information Tab

Move report-style camera information into organized secondary sections.

Possible sections:

- identity
- hardware metadata
- raw V4L2 capabilities
- candidate pipelines
- recommended candidate
- diagnostics
- reproduce with CLI

This preserves the existing discovery work without making it the default user experience.

## Roadmap Adjustment After Milestone 28

Implementation learning from Milestones 27 and 28 intentionally paused the planned transition to group views.

Before building the remaining endpoint and group pages, the camera Explore pane needed one more refinement pass so it could become the exemplar inspector surface for future device-specific Explore tabs.

The corrected direction is inspector-first: a user plugs in a media-capable device, such as a 3D camera, multimedia device, or simple robot like Reachy Mini, and first understands available endpoints, modes, generated pipelines, controls, and diagnostics. Safe copy/run affordances come second and remain explicitly scoped.

This was an intentional design correction based on implementation learning, not accidental scope expansion.

## Milestone 29 — Camera Pane Inspector Refinement

Status: Implemented

Stabilize the camera Explore pane as the blueprint for future endpoint explorers.

Implemented:

- renamed **Camera Settings** to **Camera Mode**
- renamed **Frame Duration / FPS** to **Frame Rate**
- preserved frame-rate list behavior
- rendered the generated pipeline as a compact read-only monospace code/copy surface
- kept copy visible and provided transient `Copied` feedback
- added light non-collapsible camera-control grouping
- improved inactive camera-control row presentation
- bounded control rows to a compact left-aligned working width
- preserved read-only inspector semantics
- did not add V4L2 write/reset behavior

## Milestone 30 — Group Explore View

Status: Implemented

Make composite groups useful as physical-device dashboards.

Implemented:

- compact group dashboard
- group summary and evidence summary
- endpoint cards with role labels and concise summaries
- endpoint-card actions that navigate to endpoint-specific Explore pages
- nested child composite groups under parent groups when membership shows containment
- parent groups avoiding duplicated endpoint rows already covered by child groups
- no group-based execution

## Milestone 31 — Group Device Information Tab

Status: Implemented

Show why endpoints were grouped.

Implemented sections:

- **Group Summary**
- **Direct Endpoints**
- **Child Groups**
- **Grouping Evidence**
- **Metadata / Diagnostics**
- **Reproduce with CLI**

The implementation preserved the Milestone 30 Group Explore dashboard, endpoint-card navigation, group containment logic, and read-only inspection semantics.

No group-based execution was added.

## Milestone 32 — Audio Input Explore Tab

Status: Implemented

Create a microphone-oriented explorer.

Implemented:

- compact audio input endpoint summary
- **Audio Input Mode** section
- sample format, sample rate, and channel count rows
- generated audio-input GStreamer pipeline
- compact read-only monospace code/copy surface
- transient `Copied` feedback
- explicit fallback text when detailed capability data is unavailable
- non-executing **Future Input Test** placeholder
- no audio capture/execution, recording, mixer mutation, system audio mutation, or group-based execution

## Milestone 33 — Audio Output Explore Tab

Status: Implemented

Create a speaker-oriented explorer.

Implemented:

- compact audio output endpoint summary
- **Audio Output Mode** section
- sample format, sample rate, and channel count rows
- generated audio-output/test GStreamer pipeline
- compact read-only monospace code/copy surface
- transient `Copied` feedback
- explicit fallback text when detailed capability data is unavailable
- non-executing **Future Speaker Test** placeholder
- no speaker playback/execution, tone playback, sound-file playback, volume change, mixer mutation, system audio mutation, route change, or group-based execution

## Roadmap Adjustment After Milestone 33

The original roadmap placed **Commands and Reproduce Sections** and **Reports Area** immediately after the endpoint Explore surfaces. These remain valuable, but they should be deferred.

The reason is product maturity. Commands/Reproduce and Reports/Diagnostics are presentation layers over workflows that may change once hardware interaction is implemented. The GUI has established strong inspector surfaces, but camera preview, microphone testing, speaker testing, subprocess lifecycle, dry-run display, stop behavior, and HIL validation are not yet proven.

Expanding command/report presentation now would put emphasis on an immature area and could create churn after preview/audio-test implementation.

Therefore, the post-33 roadmap should shift toward safe hardware interaction:

```text
Milestone 34 — GUI Roadmap Consolidation and Hardware Interaction Readiness
Milestone 35 — Preview Policy and Dry-Run UX
Milestone 36 — Camera Preview Implementation
Milestone 37 — Audio Test Policy and UX
Milestone 38 — Audio Test Implementation
Milestone 39 — Hardware Interface / HIL Validation Pass
Milestone 40 — Commands and Reproduce Sections
Milestone 41 — Reports Area
Milestone 42 — Service-Layer Cleanup
Milestone 43 — Polish and HIL Validation
```

A small process-boundary milestone may be inserted before camera preview if Milestone 35 shows that subprocess handling should not live directly in Qt widgets.

Possible inserted milestone:

```text
Milestone 36A — Minimal GUI Process Runner
```

Only add this if the policy/design work reveals a concrete need.

## Milestone 34 — GUI Roadmap Consolidation and Hardware Interaction Readiness

Re-center the roadmap after Milestones 29–33 and prepare the project for deliberately scoped hardware interaction.

This is a design/spec/documentation milestone, not a feature milestone.

Scope:

- update `docs/GUI_ROADMAP.md` to reflect completed work through Milestone 33
- record that the original Commands/Reproduce and Reports milestones are deferred
- name the established Explore-page pattern explicitly
- reorder the next roadmap sequence around preview and audio-test readiness
- distinguish policy/design milestones from implementation milestones
- preserve the Explore / Device Information / Reports / Commands separation
- define the next milestone as Preview Policy and Dry-Run UX
- restate safety boundaries before hardware interaction work begins

Out of scope:

- camera preview implementation
- audio capture implementation
- speaker playback implementation
- new Reports UI
- broad command/reproduce expansion
- arbitrary pipeline editing
- arbitrary user-authored pipeline execution
- group-based execution
- V4L2 control writes
- mixer, volume, route, or system audio mutation

## Milestone 35 — Preview Policy and Dry-Run UX

Status: Implemented

Define the first safe GUI execution policy for camera preview behavior before implementation.

The policy should answer:

- what exact user action starts preview
- what generated pipelines are eligible for preview
- how dry-run information is shown before or during execution
- how the user stops preview
- how subprocess lifecycle and cleanup are guaranteed
- where process management belongs architecturally
- what is displayed when preview cannot run
- how failure is reported without turning Explore into a report dump
- what remains out of scope

The policy should preserve existing safety boundaries:

- generated pipelines only
- explicit user action
- no arbitrary user-authored pipelines
- dry-run visibility
- safe subprocess handling
- clear stop behavior
- process cleanup

This milestone should remain policy/design-focused unless the project explicitly decides to combine policy and implementation.

Implemented as documentation-only policy:

- preview eligibility is limited to structured generated camera preview candidates for the currently selected endpoint and mode
- the generated pipeline/code-copy surface is the preferred persistent dry-run representation
- preview controls should appear only after the generated command is visible
- process states are defined as `Idle`, `Ready`, `Starting`, `Running`, `Stopping`, `Exited`, `Failed`, and `Unavailable`
- stop and cleanup are required for user stop, endpoint change, window/application close, partial start failure, and unexpected process exit
- Qt widgets should not directly own raw subprocess logic
- a small GUI-facing preview runner/service should accept structured command data or argv, not shell strings
- preview execution remains deferred to Milestone 36

## Milestone 36 — Camera Preview Implementation

Status: Implemented

Allow the camera Explore tab to launch and stop a selected generated preview pipeline safely.

This milestone should focus on camera preview only.

It should not introduce:

- arbitrary pipeline editing
- arbitrary user-authored pipeline execution
- synchronized capture
- recording workflows
- audio tests
- group-based execution
- V4L2 control writes

If Milestone 35 identifies the need for a small GUI process runner or service seam, introduce only the minimal boundary needed for safe preview lifecycle management.

Implemented:

- added a small GUI-facing preview runner/service that accepts structured argv data only
- added Camera Explore preview controls after the generated pipeline/code-copy surface
- limited preview to eligible generated camera preview commands for the selected endpoint/mode
- delegated Start Preview and Stop Preview to the runner/service
- added cleanup on endpoint change, refresh, and window close
- preserved audio input/output and group views as non-executing inspector/navigation surfaces
- kept Commands/Reproduce and Reports deferred

## Milestone 37 — Audio Test Policy and UX

Define safe GUI behavior for audio input and output tests before implementing them.

The design should answer:

- what constitutes a safe microphone test
- what constitutes a safe speaker test
- whether the first version should use level display, bounded capture, test tone playback, or command generation only
- how the user starts and stops tests
- what generated pipelines are allowed
- how dry-run information is shown
- how to avoid mixer, route, volume, or system audio mutation
- how failures are reported clearly

This should be a policy/design milestone.

## Milestone 38 — Audio Test Implementation

Add bounded audio input and output tests using generated pipelines only.

Possible scope:

- short microphone capture
- input level test
- speaker test tone
- explicit start/stop behavior
- dry-run visibility
- safe process cleanup

This milestone should not introduce:

- arbitrary pipeline editing
- arbitrary user-authored pipeline execution
- mixer mutation
- volume changes
- route changes
- system audio configuration changes
- synchronized audio/video capture
- group-based execution

## Milestone 39 — Hardware Interface / HIL Validation Pass

Validate the first GUI hardware-interaction behavior on Jetson and Reachy Mini-style hardware.

This milestone should test the hardware interaction model before expanding command/report surfaces.

Possible scope:

- camera preview on Jetson
- camera preview on Reachy Mini-style USB camera endpoint
- audio input test behavior on real microphone endpoints
- audio output test behavior on real speaker endpoints
- process cleanup under normal stop, failure, and window-close paths
- fallback behavior when required GStreamer elements are missing
- layout and usability on embedded/laptop displays
- confirmation that safety boundaries remain intact

## Milestone 40 — Commands and Reproduce Sections

Add curated command sections in Device Information views after preview/audio-test workflows have matured.

Commands may include:

- `gst-device-explorer` commands
- `v4l2-ctl` commands for camera inspection
- ALSA commands for audio inspection
- GStreamer commands for generated pipeline testing
- commands that reproduce the proven preview/test investigation flow

These commands should teach the user how to reproduce GUI-derived discovery from the command line without cluttering the Explore tab.

## Milestone 41 — Reports Area

Add a dedicated Reports or Diagnostics area after hardware interaction workflows have been validated.

This area should contain:

- full device reports
- support bundles
- raw JSON
- schema-related output
- diagnostic summaries
- development/debug information
- hardware-interaction diagnostics that proved useful during preview/audio-test validation

This keeps report functions available while removing them from the main exploration workflow.

## Milestone 42 — Service-Layer Cleanup

Introduce purpose-built GUI-facing services so widgets consume exploration models instead of raw CLI/report structures.

Possible services:

- `MediaExplorerService`
- `CameraExplorerService`
- `AudioExplorerService`
- `GroupExplorerService`
- `GuiProcessRunner` or equivalent, if preview/audio-test implementation demonstrated the need

The goal is to prevent the GUI from becoming a rendered version of CLI output or a collection of widgets that directly own hardware/process behavior.

This milestone may move earlier if preview/audio-test work exposes a concrete architectural seam that must be addressed before safe implementation can continue.

## Milestone 43 — Polish and HIL Validation

Validate the redesigned GUI on Jetson and Reachy Mini-style hardware.

This milestone should include:

- hardware-in-the-loop validation
- layout refinement
- removal of development remnants from the main UI
- documentation updates
- regression tests
- confirmation that safety boundaries remain intact

## Safety Boundaries

Until deliberately changed by a scoped milestone, preserve these boundaries:

- no arbitrary pipeline execution
- no arbitrary user-authored pipeline scripts
- no hidden command execution
- no package installation
- no system configuration changes
- no remote behavior
- no group-based execution
- no synchronized capture
- no V4L2 control writes
- no `v4l2-ctl --set-ctrl`
- no GUI preview/capture/test behavior unless deliberately scoped
- no audio capture/playback execution unless deliberately scoped
- no mixer, volume, route, or system audio mutation

## Working Summary

The GUI should be organized around exploration first.

The camera, audio input, audio output, and group Explore pages now share an inspector-first pattern: compact summary, capability selection or presentation, generated code/copy output, scoped safe-action placeholders, and read-only semantics. Lower-level reports and diagnostics stay out of the primary working surface.

A useful distinction:

- **Explore** means selecting settings, inspecting modes, and eventually trying explicitly scoped generated behavior.
- **Device Information** means understanding what the system discovered.
- **Reports** means creating a full accounting for support, debugging, or documentation.
- **Commands** means teaching how to reproduce a mature investigation outside the GUI.

The next development path should prove safe hardware interaction before expanding command/reproduction or report presentation.
