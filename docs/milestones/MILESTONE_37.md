# Milestone 37 — Audio Test Policy and UX

Status: Implemented

## Theme

Define the first safe audio-test policy and user experience before adding microphone capture, input monitoring, speaker playback, or any other audio execution behavior to the GUI.

Milestone 35 defined the preview policy and dry-run UX for camera preview. Milestone 36 implemented safe camera preview using a narrow GUI-facing runner/service that accepts structured command data instead of shell strings. Milestone 37 applies the same discipline to audio before implementation.

Audio testing has different risks than camera preview:

- microphone activity can raise privacy concerns
- speaker tests can produce unexpected sound
- feedback loops are easy to create
- ALSA devices can block or fail differently across hardware
- volume, mixer, route, and system audio state must not be mutated
- audio input and output tests may need different first versions

This milestone is intentionally policy/design-first. It should decide what the first safe audio test behaviors are and how they should appear in the GUI. It should not implement audio execution.

## Product Goal

The GUI should eventually let a user perform explicitly scoped, generated-command-only audio tests for a selected audio endpoint.

Before implementation, the project must define:

- what a safe microphone/input test means
- what a safe speaker/output test means
- which generated commands are eligible
- where controls appear in the Audio Input and Audio Output Explore pages
- what dry-run visibility means for audio
- what process states are shared with camera preview
- what cleanup is required
- what behavior remains out of scope

The result should be a clear implementation path for the next milestone without weakening the inspector-first model.

## Current Context

Recent GUI milestones established this pattern:

```text
Explore page pattern
- compact endpoint or group summary
- mode/capability selection or presentation
- generated command/pipeline
- compact read-only monospace code/copy surface
- future or scoped safe-action area
- read-only inspector semantics until an explicit policy milestone enables action
```

Milestone 36 added safe camera preview with this boundary:

```text
PreviewCommand -> PreviewRunner/service -> Camera Explore controls
```

Qt widgets should not own raw subprocess logic. Any future audio test behavior should follow the same architectural principle.

## Key Policy Questions

### Audio Input

Decide the first safe microphone/audio-input test shape.

Possible first versions:

1. **Input level monitor**
   - preferred first implementation candidate
   - no file recording
   - no long-running capture by default
   - visual indication that input is active
   - generated pipeline only
   - explicit Start/Stop

2. **Short bounded capture to discard/fakesink**
   - useful for proving the input pipeline starts
   - no saved media file
   - bounded by duration or explicit Stop

3. **Short capture to file**
   - likely defer
   - introduces file paths, storage, privacy, cleanup, and UX questions

Milestone 37 should decide whether the next implementation milestone should use option 1, option 2, or a hybrid.

Decision:

- The first audio-input implementation should use a non-recording input activity or level-style test.
- It may use a generated pipeline that proves input activity without writing audio to disk.
- It must show explicit active-state communication while the input endpoint is being tested.
- It must not expose recording, save-to-file, or capture-to-file workflow in the first implementation.

### Audio Output

Decide the first safe speaker/audio-output test shape.

Possible first versions:

1. **Short generated tone**
   - preferred first implementation candidate
   - bounded duration
   - explicit user action
   - no volume or mixer mutation
   - no route mutation
   - clear visible Running/Stopping state

2. **User-provided sound file playback**
   - likely defer
   - introduces file selection, format handling, duration, and loudness concerns

3. **Continuous tone until Stop**
   - possible but riskier than bounded duration
   - requires reliable stop/cleanup and clear UI state

Milestone 37 should decide the safest first speaker-test behavior.

Decision:

- The first audio-output implementation should use a short bounded generated tone test.
- It should have a conservative default duration and explicit Running/Stopping state.
- It must not play user-selected sound files.
- It must not modify volume, mixer, route, ALSA configuration, PulseAudio/PipeWire configuration, or system audio state.

### Shared Audio Test Policy

Define whether audio tests should:

- reuse the existing preview runner/service under a more generic media-process abstraction
- use a separate audio-test runner facade backed by the same process-management core
- share the camera preview state vocabulary
- use structured argv command objects similar to `PreviewCommand`
- expose the same dry-run/code-copy command surface already present in Audio Input and Audio Output Explore pages

The current expected state vocabulary is:

```text
Idle
Ready
Starting
Running
Stopping
Exited
Failed
Unavailable
```

Decision:

- Future audio tests should reuse the camera preview state vocabulary where practical.
- The next implementation may reuse or extract common process-management behavior from the Milestone 36 preview runner.
- If reuse is awkward, introduce a small audio-test facade backed by the same structured-argv principle.
- Do not perform broad service-layer cleanup as part of Milestone 37 or Milestone 38.

## Proposed Decisions

Unless implementation discovery shows a better path, use these decisions as the default outcome of this milestone:

### Audio Input first test

The first audio-input implementation should be a non-recording input activity or level-style test, started explicitly by the user and stopped explicitly by the user or by cleanup events.

It should not write audio to disk.

It should not expose a microphone recording workflow.

The UI must make the active microphone state visible while the test is running.

### Audio Output first test

The first audio-output implementation should be a short generated tone test with a bounded default duration.

It should not modify volume, mixer, route, PulseAudio/PipeWire, ALSA configuration, or system audio settings.

It should not play user-selected media files.

The UI must make the active speaker-test state visible while the test is running.

### Shared architecture

The audio implementation should not put raw subprocess ownership inside Qt widgets.

A small GUI-facing audio test service or generalized media process service should accept structured command data only. It may reuse or extract common behavior from the Milestone 36 preview runner if doing so keeps the code simpler and clearer.

Do not perform broad service-layer cleanup unless it is necessary to avoid duplicating process-management logic.

## Required Documentation Output

Milestone 37 should update or create documentation that captures:

- audio input test policy
- audio output test policy
- audio dry-run UX
- eligibility rules for generated commands
- process states and cleanup events
- GUI placement rules for future controls
- explicit deferred work
- safety boundaries
- next milestone scope

Likely files:

- `docs/milestones/MILESTONE_37.md`
- `docs/GUI_ROADMAP.md`

## GUI UX Policy

Future audio test controls should appear only after the generated command/code-copy surface is visible.

Audio Input Explore should continue to read as:

```text
Endpoint summary
Audio Input Mode
Generated input pipeline
Future/Scoped Input Test area
```

Audio Output Explore should continue to read as:

```text
Endpoint summary
Audio Output Mode
Generated output/test pipeline
Future/Scoped Speaker Test area
```

When audio execution is later implemented, controls should be visually subordinate to the generated command. The user should understand that the test is derived from the selected/generated command, not from arbitrary hidden behavior.

## Eligibility Rules

Audio tests must be limited to generated, structured commands for the selected endpoint.

Eligible commands must:

- come from the application’s structured candidate/model layer
- target the currently selected audio endpoint
- use structured argv data, not shell strings
- be displayed or represented by the existing generated command surface
- avoid user-authored raw pipeline text
- avoid shell interpretation
- avoid system configuration mutation

Ineligible commands include:

- arbitrary user-entered pipelines
- copied display text parsed back into execution
- shell strings
- commands that change volume, mixer, route, or system audio state
- commands that write files unless a future milestone explicitly scopes capture-to-file
- group-level commands
- synchronized audio/video commands

## Cleanup Policy

Future audio tests must clean up on:

- explicit Stop
- endpoint change
- selected mode change when the generated command changes
- refresh
- application/window close
- process start failure
- unexpected process exit
- transition to an unavailable endpoint
- endpoint becoming unavailable

Cleanup should be visible in the GUI state where practical.

## In Scope

- Define audio input test policy.
- Define audio output test policy.
- Define audio test dry-run UX.
- Define audio test process state vocabulary.
- Define cleanup requirements.
- Define generated-command eligibility rules.
- Decide whether the next implementation should reuse/extract the camera preview runner process-management layer.
- Update `GUI_ROADMAP.md` to reflect the policy and the next implementation milestone.
- Preserve the existing Audio Input and Audio Output Explore surfaces.

## Out of Scope

Do not implement:

- microphone capture execution
- input level meter execution
- speaker tone playback
- sound-file playback
- audio recording
- capture-to-file workflow
- arbitrary pipeline editing
- arbitrary command execution
- shell-string execution
- mixer control
- volume control
- route changes
- PulseAudio/PipeWire configuration changes
- ALSA configuration changes
- group-based execution
- synchronized audio/video behavior
- reports area
- commands/reproduce expansion
- broad service-layer cleanup

## Safety Boundaries

Preserve these boundaries:

- no arbitrary pipeline execution
- no arbitrary user-authored pipeline scripts
- no hidden command execution
- no shell-string execution
- no package installation
- no system configuration changes
- no remote behavior
- no group-based execution
- no synchronized capture
- no V4L2 control writes
- no mixer mutation
- no system audio mutation
- no volume mutation
- no route mutation
- no ALSA configuration mutation
- no PulseAudio/PipeWire configuration mutation
- no audio recording or playback execution in this milestone

## Suggested Next Milestone

The likely next milestone should be:

```text
Milestone 38 — Safe Audio Test Implementation
```

Expected scope for Milestone 38, depending on Milestone 37 decisions:

- implement a small audio test runner/facade or generalized media process runner
- add Audio Input Explore test controls for the chosen non-recording input test
- add Audio Output Explore controls for the chosen bounded speaker test
- use structured generated argv only
- preserve generated command dry-run visibility
- add cleanup on endpoint change, refresh, close, failure, and stop
- add tests with fakes/test doubles rather than requiring real audio hardware

## Acceptance Criteria

Milestone 37 is complete when:

- `MILESTONE_37.md` records the audio input and output test policy.
- `GUI_ROADMAP.md` reflects that Milestone 37 is policy/design-first.
- The next implementation milestone has a clear scoped target.
- The roadmap still defers Commands/Reproduce and Reports until after preview/audio-test behavior is proven.
- Safety boundaries are explicit and unchanged.
- No audio execution or system audio mutation has been added.
- If tests are not run, the milestone notes explain that the change is documentation-only.

## Suggested Validation

Because this milestone is documentation/policy-only, tests are not required unless implementation files are touched.

If any code is changed while updating roadmap references, run the relevant tests.

Suggested optional check:

```sh
git diff -- docs/milestones/MILESTONE_37.md docs/GUI_ROADMAP.md
```

## Implementation Notes

Implemented as documentation and policy only:

- Defined the first audio-input test as a non-recording input activity or level-style test.
- Deferred microphone recording, capture-to-file, and file-writing workflows.
- Defined the first audio-output test as a short bounded generated tone test.
- Deferred user-selected sound-file playback.
- Required future audio test controls to appear after generated command/code-copy surfaces.
- Required structured argv data and generated endpoint/mode candidates only.
- Required future audio tests to target only the selected endpoint.
- Reused the camera preview state vocabulary:
  - `Idle`
  - `Ready`
  - `Starting`
  - `Running`
  - `Stopping`
  - `Exited`
  - `Failed`
  - `Unavailable`
- Required cleanup on explicit Stop, endpoint change, selected mode change, refresh, window/application close, partial start failure, unexpected process exit, and endpoint unavailability.
- Defined the next implementation milestone as **Milestone 38 — Safe Audio Test Implementation**.
- Preserved Commands/Reproduce and Reports deferral.

Files changed:

- `docs/milestones/MILESTONE_37.md`
- `docs/GUI_ROADMAP.md`

Validation:

- No code was changed.
- No automated tests were run because this milestone is documentation-only.

No audio execution, speaker playback, microphone capture, recording, file capture, arbitrary command execution, shell-string execution, mixer mutation, volume mutation, route mutation, ALSA/PulseAudio/PipeWire configuration mutation, system audio mutation, synchronized audio/video behavior, or group-based execution was added.
