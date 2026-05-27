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
Milestone 38 — Safe Audio Output Test Implementation
Milestone 39 — Safe Audio Input Activity Test Implementation
Milestone 40 — Hardware Interface / HIL Validation Pass
Milestone 41 — Audio Output Quality Test Policy and UX
Milestone 42 — Audio Output Quality Test Implementation
Milestone 43 — Camera Control Write Policy and UX
Milestone 44 — Camera Control Write Implementation and HIL Validation
Milestone 45 — Post-HIL Issue Resolution and Refactoring Pass
Milestone 46 — README and First-Run Documentation Rewrite
Milestone 47 — Commands and Reproduce Sections
Milestone 48 — Reports Area
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

Status: Implemented

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

Implemented as documentation-only policy:

- the first audio-input test should be a non-recording input activity or level-style test
- microphone recording and capture-to-file remain deferred
- the first audio-output test should be a short bounded generated tone test
- user-selected sound-file playback remains deferred
- future audio controls should appear only after the generated command/code-copy surface is visible
- audio tests must use generated structured argv data for the selected endpoint only
- Qt widgets should not own raw subprocess logic
- future audio tests should reuse/extract Milestone 36 process-runner behavior only where it keeps the implementation small
- process states reuse `Idle`, `Ready`, `Starting`, `Running`, `Stopping`, `Exited`, `Failed`, and `Unavailable`
- cleanup is required on Stop, endpoint change, mode change, refresh, close, partial start failure, unexpected exit, and endpoint unavailability
- no audio execution was added in this milestone

## Milestone 38 — Safe Audio Output Test Implementation

Status: Implemented

Add a bounded audio output speaker test using generated pipelines only.

Implemented:

- short bounded generated tone command
- structured argv execution through the existing GUI-facing runner/service
- Speaker Test controls after the generated output pipeline/code-copy surface
- cleanup through existing endpoint-change, refresh, and window-close runner paths
- no microphone/audio-input execution

This milestone should not introduce:

- arbitrary pipeline editing
- arbitrary user-authored pipeline execution
- mixer mutation
- volume changes
- route changes
- system audio configuration changes
- synchronized audio/video capture
- group-based execution

## Milestone 39 — Safe Audio Input Activity Test Implementation

Status: Implemented

Add a bounded, non-recording audio input activity test using generated pipelines only.

Implemented:

- Audio Input Activity Test controls after the generated input pipeline/code-copy surface
- bounded generated input command using the selected endpoint and `fakesink sync=false`
- structured argv execution through the existing GUI-facing runner/service
- explicit UI text that microphone audio is not recorded, saved, or retained
- Start Test and Stop Test state feedback using the shared process state vocabulary
- cleanup through existing endpoint-change, refresh, and window-close runner paths
- no recording, file capture, volume change, mixer mutation, route mutation, system audio mutation, or group-based execution

This milestone should not introduce:

- graphical level meter or waveform display
- audio recording
- file capture
- arbitrary pipeline editing
- arbitrary user-authored pipeline execution
- shell-string execution
- mixer, volume, route, ALSA, PulseAudio, or PipeWire mutation
- synchronized audio/video behavior
- group-based execution

## Milestone 40 — Hardware Interface / HIL Validation Pass

Status: Implemented

Validate the first GUI hardware-interaction behavior on Jetson and Reachy Mini-style hardware.

Validated on HIL host `jetsonhacks` (Linux 6.8.12-tegra, GStreamer 1.24.2):

- camera preview on `/dev/video0` (HD Pro Webcam C920)
- audio output tone test on `hw:0,0` (Reachy Mini Audio)
- audio input activity test on `hw:0,0` (Reachy Mini Audio)
- process cleanup under normal stop, failure, and window-close paths
- command provenance corrected for camera mode selection and MJPG candidate path
- safety boundaries confirmed intact

## Milestone 41 — Audio Output Quality Test Policy and UX

Status: Implemented

Define how Audio Output Explore should support a casual user's audio quality investigation.

This is a documentation-only policy milestone. Milestone 42 implements the approved design.

Implemented:

- distinguished Generated Tone Test (endpoint can produce sound) from Local File Playback Quality Test (user judges real-world fidelity)
- defined Test Level and Playback Level as pipeline-local controls that do not mutate system volume
- recommended level presets: Quiet, Normal, Loud
- defined local-file-only playback policy: no remote URLs, no playlists, no arbitrary pipelines, no shell strings
- recommended conservative initial file type handling
- defined bounded playback as the preferred first implementation
- defined command provenance requirements for file playback
- defined cleanup requirements matching Milestones 36, 38, and 39 patterns
- deferred `PreviewCommand` rename to the Milestone 45 post-HIL issue/refactoring pass
- confirmed all safety boundaries intact
- no implementation behavior added

## Milestone 42 — Audio Output Quality Test Implementation

Status: Implemented

Implement the local file playback quality test approved in Milestone 41.

Implemented:

- Test Level presets (Quiet / Normal / Loud) on the existing Generated Tone speaker test; displayed pipeline text updates dynamically with level; runner argv and display text share the same generated source
- Local File Playback section: native file dialog, basename display, full path as tooltip, Playback Level presets, Start Playback / Stop Playback controls
- `filesrc location=<path>` pipeline (not URI) ensures remote URLs are structurally impossible
- Any locally selected file accepted; GStreamer failure surfaced through runner FAILED state
- Natural EOS ends playback; manual Stop available; cleanup on Stop, endpoint change, refresh, and close
- `is_safe_local_file()` rejects URLs, empty strings, and directories
- New module `qt_audio_output_file_playback.py` with injectable file selector for testing
- 9 new tests; 4 existing tests updated; 615 total passing

HIL validated on `jetsonhacks` with `hw:0,0`: `.wav`, `.flac`, `.mp3` play correctly; unsupported file reported as Failed; no system audio mutation observed.

## Roadmap Adjustment After Milestone 42

Milestone 42 completes the current audio output quality test path. Audio output is satisfactory for the current product stage, and audio input should remain intentionally minimal for now: endpoint discovery, capability display, generated safe command, bounded non-recording activity test, and external applications for deeper capture or audio quality testing.

The next product gap is camera controls. Camera preview without writable controls is not enough for useful HIL testing because a user needs to adjust brightness, exposure, white balance, and gain and visually confirm changes during preview.

Commands/Reproduce and Reports remain valuable, but they should stay deferred until after camera-control writes, post-HIL issue resolution/refactoring, and README/product framing cleanup.

## Milestone 43 — Camera Control Write Policy and UX

Status: Implemented

Define the policy and user experience for writing camera controls during testing.

This is a documentation/policy milestone, not an implementation milestone.

Earlier camera-control work intentionally preserved read-only inspector semantics and did not add V4L2 writes. Now that camera preview has been HIL validated, the project needs a scoped policy for changing camera controls during preview-oriented testing.

The policy should answer:

- which camera controls are writable
- which controls remain read-only
- how the UI distinguishes readable, writable, active, inactive, and unavailable controls
- whether writes apply live while preview is running
- whether writes also work when preview is stopped
- whether changes apply immediately or require an Apply action
- whether Reset to Default is available per control when default values are known
- whether original values are restored on close, or whether that remains deferred
- how auto/manual dependency controls are represented and updated
- what backend write mechanism is allowed
- how shell-string execution is avoided
- how stale or wrong-endpoint writes are prevented
- what HIL validation proves that controls affect the preview image

Safety boundaries that remain in force until Milestone 44 deliberately opens a scoped write path:

- no arbitrary command execution
- no shell-string execution
- no `shell=True`
- no group-based camera-control writes
- no arbitrary V4L2 command entry
- no hidden device mutation
- no broad system configuration changes

Implemented as documentation-only policy:

- distinguished readable, writable, active, inactive, and unavailable control states
- chose immediate writes for supported active writable controls
- allowed writes during preview and while preview is stopped, provided the selected endpoint remains valid
- kept preview execution separate from camera-control write requests
- scoped Reset/Default to per-control behavior only when a default value is known
- deferred global Reset All and automatic restore-on-close
- required structured camera-control write requests with selected-endpoint provenance
- required structured argv only if `v4l2-ctl` is used later
- scoped the first implementation to integer, boolean, and menu controls
- deferred compound, string, unknown/private, ambiguous button controls, and controls lacking safe metadata
- documented Milestone 44 HIL expectations
- confirmed no write behavior is added until Milestone 44

## Milestone 44 — Camera Control Write Implementation and HIL Validation

Status: Implementation complete; HIL validation blocked by unavailable camera device

Implement the camera-control write behavior approved in Milestone 43.

Expected implementation direction:

- structured camera-control write requests
- selected endpoint only
- active/writable controls only
- live update while preview is running
- read-only display for unsupported or inactive controls
- per-control Reset to Default only when default value is known
- no global restore-all unless explicitly approved
- no group-level writes
- no shell-string execution
- HIL validation with a real camera

Expected HIL validation:

- preview starts
- brightness, exposure, white balance, and gain changes affect the preview image when supported
- inactive controls stay disabled
- auto/manual control dependencies behave understandably
- reset/default behavior works where available
- endpoint changes prevent stale writes
- refresh and close cleanup are safe

Implementation status:

- added structured `CameraControlWriteRequest` and `CameraControlWriter`
- added a scoped `v4l2-ctl --set-ctrl` path using structured argv only
- enabled active writable integer, boolean, and menu controls in live camera Explore
- kept inactive, read-only, and unsupported controls non-editable
- added per-control Default writes where a default value is known
- blocked stale endpoint writes
- re-discovered selected-endpoint controls after successful boolean/menu writes so auto/manual dependencies can update dependent controls
- avoided rebuilding the scrolled control pane for integer slider/spin writes
- kept demo mode read-only for camera-control writes
- preserved preview, audio, group, Commands/Reproduce, and Reports boundaries
- full automated test suite passes

HIL status:

- HIL host `jetsonhacks` had `v4l2-ctl` installed but no `/dev/video*` device nodes
- real-camera preview/control validation could not be performed
- Milestone 44 is not complete by the HIL acceptance standard until a follow-up HIL pass validates at least one supported visual camera-control write on real hardware, when such a control is exposed

## Milestone 45 — Post-HIL Issue Resolution and Refactoring Pass

Collect and resolve issues discovered during Milestones 36–44, then refactor only where the HIL-proven implementation reveals real seams.

Scope:

- collect issues raised during camera preview, audio output, audio input, HIL, and camera-control work
- fix stale/provenance/eligibility bugs
- review shared process-runner naming such as `PreviewCommand`
- reduce duplicate camera/audio test code where practical
- review GUI module size and responsibility boundaries
- review test fixtures that may look like real hardware data
- keep safety boundaries intact
- avoid adding new product features

This is the right place to consider renaming `PreviewCommand` or introducing a more generic media-test/process-runner name.

## Milestone 46 — README and First-Run Documentation Rewrite

Rewrite the repository README so it reflects what the project actually is now.

This is a user-facing documentation milestone after the refactoring pass.

Scope:

- explain `gst-device-explorer` as a GUI-first media endpoint explorer
- explain first-run workflow
- describe camera preview and camera controls
- describe audio output generated tone and local file playback quality test
- describe audio input's current scope honestly
- explain composite group behavior
- explain safety boundaries
- provide Jetson/Linux setup notes
- include minimal CLI examples only where useful
- remove stale report-first or CLI-first framing
- avoid overpromising unsupported behavior

## Milestone 47 — Commands and Reproduce Sections

Add curated command sections in Device Information views after camera preview, audio output quality testing, minimal audio input activity testing, camera-control writes, issue/refactoring cleanup, and README/product framing cleanup have matured.

Commands may include:

- `gst-device-explorer` commands
- `v4l2-ctl` commands for camera inspection
- ALSA commands for audio inspection
- GStreamer commands for generated pipeline testing
- commands that reproduce the proven preview/test investigation flow

These commands should teach the user how to reproduce GUI-derived discovery from the command line without cluttering the Explore tab.

The goal remains curated, read-only, copyable commands that reproduce mature GUI-derived investigations.

## Milestone 48 — Reports Area

Add a dedicated Reports or Diagnostics area after Commands/Reproduce.

This area should contain:

- full device reports
- support bundles
- raw JSON
- schema-related output
- diagnostic summaries
- development/debug information
- hardware-interaction diagnostics that proved useful during preview, audio-test, and camera-control validation

This keeps report functions available while removing them from the main exploration workflow.

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
- V4L2 control writes are limited to supported active camera controls for the currently selected camera endpoint
- `v4l2-ctl --set-ctrl` is allowed only through structured camera-control requests and structured argv
- no new GUI preview/capture/test behavior unless deliberately scoped
- no new audio capture/playback execution unless deliberately scoped
- no mixer, volume, route, or system audio mutation

Milestone 44 opens only this scoped boundary:

```text
Write supported active camera controls for the currently selected camera endpoint using structured control requests.
```

All other camera-control write behavior remains prohibited:

- no arbitrary user-authored V4L2 commands
- no shell-string execution
- no `shell=True`
- no group-based camera-control writes
- no writes to unrelated endpoints

## Working Summary

The GUI should be organized around exploration first.

The camera, audio input, audio output, and group Explore pages now share an inspector-first pattern: compact summary, capability selection or presentation, generated code/copy output, scoped safe-action placeholders, and read-only semantics. Lower-level reports and diagnostics stay out of the primary working surface.

A useful distinction:

- **Explore** means selecting settings, inspecting modes, and eventually trying explicitly scoped generated behavior.
- **Device Information** means understanding what the system discovered.
- **Reports** means creating a full accounting for support, debugging, or documentation.
- **Commands** means teaching how to reproduce a mature investigation outside the GUI.

Through Milestone 41, the GUI established:

- inspector-first Explore pages for camera, audio input, audio output, and groups
- safe camera preview, audio output speaker tone, and audio input activity test on real HIL hardware
- a policy for audio output quality testing that distinguishes generated tone verification from local file playback fidelity

Through Milestone 42, Audio Output Explore supports both Generated Tone testing and Local File Playback:

- Generated Tone test exists
- Test Level presets exist: Quiet / Normal / Loud
- Local File Playback exists
- Playback Level presets exist
- local selected files play through the selected output endpoint
- `filesrc location=<path>` is used instead of URI/network playback
- remote URLs are structurally impossible in the playback path
- unsupported files fail cleanly
- HIL validation was performed on `jetsonhacks` with `hw:0,0`
- `.wav`, `.flac`, and `.mp3` were validated
- safety boundaries remain intact

Audio input is intentionally minimal for now: endpoint discovery, capability display, generated safe command, bounded non-recording activity test, and recommendation to use an external application for deeper capture or audio quality testing.

Camera controls are the next product gap. Camera preview without writable controls is not enough for useful HIL testing because a user needs to adjust brightness, exposure, white balance, and gain and visually confirm changes during preview.

Commands/Reproduce and Reports remain deferred until after camera-control writes, issue/refactoring cleanup, and README/product framing cleanup. The app remains exploration-first, with hardware actions explicitly scoped and safety bounded.
