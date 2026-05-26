# Milestone 34 — GUI Roadmap Consolidation and Hardware Interaction Readiness

Status: Proposed

## Theme

Re-center the GUI roadmap after Milestones 29–33 and prepare the project for the first deliberately scoped hardware-interaction work.

Milestones 29–33 established the inspector-first GUI pattern across camera, group, audio-input, and audio-output surfaces. The next useful step is not to expand command/report presentation. The next useful step is to decide how the GUI should safely interact with hardware for preview and audio tests.

The original roadmap placed **Commands and Reproduce Sections** and **Reports Area** immediately after the endpoint Explore surfaces. Those areas remain important, but they are downstream presentation layers over workflows that are still immature. They should be deferred until after camera preview and audio test behavior have been designed, implemented, and validated on real hardware.

## Product Intent

`gst-device-explorer` should continue to behave as a GUI-first media endpoint explorer.

The current product path is:

1. Show what the system discovered.
2. Let the user inspect endpoint or group capabilities.
3. Generate safe commands and pipelines from structured selections.
4. Add explicitly scoped hardware interactions only when the policy is clear.
5. Keep lower-level accounting, reports, and reproduction material secondary.

Milestone 34 is a consolidation milestone. It should update the roadmap, preserve the design lessons from recent work, and define the next safe implementation path.

## Established Explore-Page Pattern

The Explore page pattern is now:

```text
Compact endpoint or group summary
Mode/capability selection or presentation
Generated command or pipeline
Compact read-only monospace code/copy surface
Future safe-action placeholder, only when useful
Read-only inspector semantics
Secondary/raw/detail material kept in Device Information or Reports
```

Endpoint-specific adaptations:

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

## Why Commands and Reports Are Deferred

The original next milestones emphasized command reproduction and report organization. Those are valuable, but they depend on stable workflows.

At this point, the GUI has good inspector surfaces, but the hardware interaction model is not proven. Camera preview, microphone tests, speaker tests, subprocess lifecycle, dry-run display, stop behavior, and HIL validation may change the shape of generated commands and diagnostics.

If command/reproduce and report surfaces are expanded now, they risk documenting immature behavior and increasing maintenance churn after preview/audio-test implementation.

Therefore:

- **Commands and Reproduce Sections** should move after preview and audio-test implementation.
- **Reports Area** should move after preview and audio-test implementation.
- Any command rows already present in Device Information may remain, but broad expansion should wait.
- The next roadmap emphasis should be safe hardware interaction.

## Scope

### In Scope

- Update `docs/GUI_ROADMAP.md` to reflect completed work through Milestone 33.
- Record that the original Milestones 34 and 35 are deferred.
- Name the established Explore-page pattern explicitly.
- Reorder the next roadmap sequence around preview and audio-test readiness.
- Distinguish policy/design milestones from implementation milestones.
- Preserve the Explore / Device Information / Reports / Commands separation.
- Define the next milestone as Preview Policy and Dry-Run UX.
- Re-state safety boundaries before hardware interaction work begins.
- Identify when a small service/process boundary may be needed before implementation.

### Out of Scope

- Camera preview implementation.
- Audio capture implementation.
- Speaker playback implementation.
- New Reports UI.
- Broad command/reproduce expansion.
- Arbitrary pipeline editing.
- Arbitrary user-authored pipeline execution.
- Group-based execution.
- V4L2 control writes.
- Mixer, volume, route, or system audio mutation.
- Major service-layer rewrite unless a small boundary is required to keep preview policy clear.

## Proposed Roadmap Sequence

Replace the old post-33 sequence with:

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

## Next Milestone Preview

Milestone 35 should answer the policy and UX questions for camera preview before implementation.

Questions to answer:

- What exact user action starts a preview?
- What generated pipeline is eligible for preview?
- How is dry-run information shown before or during execution?
- How does the user stop preview?
- How does the GUI guarantee process cleanup?
- Where does subprocess lifecycle management live?
- What is displayed when preview cannot run?
- How is failure reported without turning Explore into a report dump?
- What remains strictly out of scope?

Milestone 35 should still avoid implementing preview unless the project intentionally combines policy and implementation in a later decision.

## Safety Boundaries

Preserve these boundaries until deliberately changed by a scoped milestone:

- No arbitrary pipeline execution.
- No arbitrary user-authored pipeline scripts.
- No hidden command execution.
- No package installation.
- No system configuration changes.
- No remote behavior.
- No group-based execution.
- No synchronized capture.
- No V4L2 control writes.
- No `v4l2-ctl --set-ctrl`.
- No GUI preview/capture/test behavior except through explicitly scoped generated pipelines.
- No audio capture/playback execution until the audio test policy milestone.
- No mixer, volume, route, or system audio mutation.

## Implementation Guidance

Keep this milestone documentation-focused and small.

Likely files changed:

- `docs/milestones/MILESTONE_34.md`
- `docs/GUI_ROADMAP.md`

Optional updates only if the repository uses milestone indexes or README links:

- milestone index document
- README roadmap reference

Do not touch GUI implementation files for this milestone unless the project already has a milestone index or status surface that must be updated.

## Suggested Validation

Because this milestone is documentation-focused, validation should be lightweight:

```sh
grep -n "Milestone 34" docs/GUI_ROADMAP.md docs/milestones/MILESTONE_34.md
grep -n "Commands and Reproduce" docs/GUI_ROADMAP.md
grep -n "Reports Area" docs/GUI_ROADMAP.md
grep -n "Preview Policy" docs/GUI_ROADMAP.md
```

If documentation checks are part of the test suite, run them. Full GUI tests are not required unless code changes are introduced.

## Acceptance Criteria

Milestone 34 is complete when:

- `docs/milestones/MILESTONE_34.md` exists.
- `docs/GUI_ROADMAP.md` reflects the actual state after Milestones 29–33.
- The established Explore-page pattern is explicitly named.
- The old Commands/Reproduce and Reports milestones are clearly deferred until after preview/audio-test work.
- The next implementation sequence is centered on safe hardware interaction.
- Policy/design milestones are distinguished from implementation milestones.
- Safety boundaries are preserved and restated.
- The next milestone, Preview Policy and Dry-Run UX, has clear purpose and scope.

## Deferred Work

Deferred until after hardware interaction behavior is proven:

- Expanded Commands and Reproduce Sections.
- Dedicated Reports or Diagnostics area.
- Broad report/export GUI integration.
- Service-layer cleanup not directly required by preview/audio-test work.
- Polish pass beyond roadmap clarity.
