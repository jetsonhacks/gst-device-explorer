# Milestone 43 — Camera Control Write Policy and UX

Status: Implemented

## Theme

Define the policy and user experience for safely moving camera controls from read-only inspection to scoped, endpoint-specific write behavior.

Milestone 29 intentionally preserved read-only inspector semantics for camera controls. That was correct before preview existed. Milestone 36 added safe camera preview, and Milestone 40 validated preview on real hardware. Now the product has crossed from pure inspection into deliberately scoped hardware interaction. For useful camera HIL testing, preview alone is not sufficient: users need to adjust brightness, exposure, gain, white balance, and similar controls while observing the live preview.

This milestone is a documentation-only policy milestone. It should decide what camera-control writes are allowed and how the GUI should present them before implementation begins.

Milestone 44 will implement the approved design and perform HIL validation.

## Product Intent

A user exploring a camera should be able to answer:

- Can I preview the selected camera endpoint?
- Which controls does the camera expose?
- Which controls are readable?
- Which controls are writable?
- Which controls are active right now?
- Can I adjust common image controls and see the effect during preview?
- Can I reset a control to its reported default?
- Can I trust that writes target only the selected camera endpoint?
- Can I trust that the app is not running arbitrary commands or mutating unrelated devices?

The GUI should support practical camera testing without becoming a general-purpose V4L2 control editor.

## Background

Current camera behavior:

- Camera Explore shows endpoint summary.
- Camera Mode selection drives generated preview command.
- Generated preview command is displayed in a read-only code/copy surface.
- Start/Stop Preview runs structured generated argv through the GUI-facing runner/service.
- Camera controls are grouped and inspectable.
- Inactive controls are muted/disabled.
- Camera-control write behavior is not implemented.
- Existing safety boundaries still prohibit V4L2 writes and `v4l2-ctl --set-ctrl`.

Milestone 43 should define the policy for deliberately opening a narrow write path in Milestone 44.

## Policy Decision: Controls Are No Longer Purely Read-Only After Milestone 44

Camera controls should remain inspector-first, but the GUI should eventually allow scoped writes for active, writable controls on the currently selected camera endpoint.

The user-facing model should distinguish:

```text
Readable
Writable
Active
Inactive
Unavailable
```

These states are not the same.

Definitions:

- **Readable** means the application can display the control's current value or known metadata.
- **Writable** means the device reports that the control can be changed in principle.
- **Active** means the control is currently effective and eligible for interaction in the device's present state.
- **Inactive** means the control is present but currently disabled or not effective, often because another auto/manual control owns that behavior.
- **Unavailable** means the control cannot be used because discovery did not provide enough safe metadata or the endpoint/control is no longer valid.

Examples:

- A control may be readable but not writable.
- A control may be writable in principle but inactive because an automatic control is enabled.
- A control may be unavailable because the backend did not discover enough metadata.
- A control may be active but still not safe to write if the value type is unsupported by the first implementation.

## UX Policy

### Placement

Camera controls should remain in Camera Explore below the generated pipeline and preview controls.

The control area should continue to use the grouping established earlier:

- Image Adjustment
- Exposure & Gain
- White Balance
- Advanced

### Write behavior

Recommended first policy:

- Writes apply immediately when the user changes a writable control.
- Writes are allowed while preview is running.
- Writes are also allowed while preview is stopped, as long as the selected endpoint is valid.
- Only active, writable controls are user-editable.
- Inactive controls remain visibly muted/disabled.
- Read-only controls remain visible but non-editable.
- Unsupported control types remain visible but non-editable.
- Controls must write only to the selected camera endpoint.
- Endpoint changes must invalidate stale write targets before any write can be attempted.
- Refresh must rebuild control state and invalidate stale write targets.

Rationale:

The main HIL use case is:

```text
Start preview -> adjust camera control -> see effect immediately
```

An Apply button would add friction and state complexity. The first implementation should prefer immediate writes for supported control types.

### Reset behavior

Recommended first policy:

- Provide per-control **Reset** or **Default** only when the device reports a default value.
- Reset writes the reported default to that one control.
- Do not implement global Reset All in the first implementation.
- Do not implement automatic restore-on-close in the first implementation unless the implementation is clearly simple and reliable.

Rationale:

Global restore sounds useful, but it can be misleading or unsafe because some controls are auto-managed, interdependent, inactive, or not reliably round-trippable. Per-control reset is more explicit and easier to validate.

### Preview interaction

Camera-control writes should work while preview is running.

The preview runner and control writer should remain separate concerns:

```text
Preview:
selected endpoint + selected mode -> generated preview argv -> runner

Control write:
selected endpoint + control id + typed value -> camera control write service/helper
```

Camera-control writes should not be implemented by modifying the running preview pipeline.

### Auto/manual dependencies

Some controls affect whether other controls are active. Examples:

- Auto Exposure may enable/disable manual exposure time.
- Auto White Balance may enable/disable white balance temperature.
- Power line frequency may affect exposure behavior.

Recommended first policy:

- If a write changes a control that may affect other controls, refresh control values/states for the selected endpoint.
- The GUI should not assume dependencies from names alone except for display grouping.
- The backend/device-reported active/inactive state should be the source of truth.
- If refreshing after every write is expensive, debounce or refresh only the affected group in a later milestone; do not invent stale states.

## Backend Write Policy

Milestone 44 should implement camera-control writes through a structured helper/service, not through UI strings.

Required conceptual flow:

```text
selected camera endpoint
+ control id/name from discovered model
+ typed value from widget
    -> structured camera-control write request
    -> camera-control writer/helper
    -> V4L2 write mechanism
```

Invalid flows:

```text
UI label -> shell command string -> execution
display text -> parsed command
arbitrary user-entered control name -> write
group selection -> write to multiple endpoints
stale endpoint path -> write after selection changed
```

Allowed write mechanisms should be chosen in Milestone 44, but policy constraints are:

- no shell-string execution
- no `shell=True`
- no arbitrary user-authored `v4l2-ctl` command entry
- no group-based writes
- no hidden writes to unrelated endpoints
- no remote behavior
- no package installation
- no system configuration changes outside the selected camera endpoint control

If the implementation uses `v4l2-ctl`, it must use structured argv only. Prefer a direct Python/V4L2 helper if one already exists and is reliable, but do not expand scope into a large new V4L2 library.

## Supported Control Types for First Implementation

Recommended first implementation should support only common scalar/menu control types already represented by the current GUI model:

- integer controls with min/max/step
- boolean controls
- menu controls

Defer complex or ambiguous control types:

- compound controls
- string controls
- unknown types
- device-specific private controls that lack safe metadata
- button controls unless safety semantics are clear
- controls without a stable id/name/value representation

## HIL Validation Policy

Milestone 44 must include HIL validation with at least one real camera exposing writable controls.

Validation should record:

- camera endpoint used
- controls discovered
- controls identified as writable
- controls left read-only and why
- preview behavior before writes
- brightness or equivalent image-control write effect
- exposure or equivalent control write effect, if supported
- white-balance or equivalent control write effect, if supported
- gain or equivalent control write effect, if supported
- inactive control behavior
- reset/default behavior where supported
- endpoint-change stale-write protection
- refresh behavior after writes
- tests run
- safety confirmation

HIL should not be considered successful merely because preview opens. At least one visible camera-control write should be validated if the camera exposes any writable visual controls.

## Safety Boundaries

Until Milestone 44 deliberately opens the scoped write path, preserve:

- No V4L2 control writes.
- No `v4l2-ctl --set-ctrl`.

Milestone 44 may open only this scoped boundary:

```text
Write supported active camera controls for the currently selected camera endpoint using structured control requests.
```

All other safety boundaries remain:

- No arbitrary command execution.
- No arbitrary user-authored V4L2 commands.
- No shell-string execution.
- No `shell=True`.
- No hidden command execution.
- No package installation.
- No system configuration changes.
- No remote behavior.
- No group-based camera-control writes.
- No synchronized capture.
- No recording/capture workflow.
- No mixer, volume, route, ALSA, PulseAudio, or PipeWire mutation.
- No Commands/Reproduce expansion.
- No Reports expansion.

## Out of Scope

This milestone does not implement:

- camera-control writes
- V4L2 write helpers
- enabling control widgets for write behavior
- reset/default behavior
- automatic restore-on-close
- camera preset profiles
- user-authored V4L2 commands
- arbitrary command execution
- Commands/Reproduce sections
- Reports area
- README rewrite

Those belong to later milestones.

## Documentation Updates

Update `docs/GUI_ROADMAP.md` only if needed to keep the roadmap consistent with this milestone.

Milestone 44 should remain:

```text
Milestone 44 — Camera Control Write Implementation and HIL Validation
```

## Acceptance Criteria

Milestone 43 is complete when:

- Camera-control write policy is documented.
- Readable/writable/active/inactive/unavailable states are distinguished.
- Immediate-write versus Apply-button behavior is decided.
- Preview interaction behavior is decided.
- Reset/default behavior is decided.
- Auto/manual dependency policy is documented.
- Backend write constraints are documented.
- First implementation control types are scoped.
- HIL validation expectations for Milestone 44 are documented.
- Safety boundaries are updated without claiming writes already exist.
- No implementation behavior is added.

## Completion Notes

Milestone 43 is implemented as a documentation-only policy and UX milestone.

Policy decisions captured:

- readable, writable, active, inactive, and unavailable are distinct states
- writes should apply immediately for supported active writable controls
- writes should work both while preview is running and while preview is stopped, provided the selected endpoint remains valid
- preview execution and control writes remain separate flows
- reset/default behavior is per-control only and only when the device reports a default value
- global Reset All and automatic restore-on-close are deferred
- device-reported active/inactive state is the source of truth for auto/manual dependencies
- camera-control writes must use structured requests and selected-endpoint provenance
- `v4l2-ctl`, if used in Milestone 44, must be invoked with structured argv only
- first implementation should support integer, boolean, and menu controls
- compound, string, unknown/private, ambiguous button controls, and controls without safe metadata are deferred

Files changed:

- `docs/milestones/MILESTONE_43.md`
- `docs/GUI_ROADMAP.md`

Roadmap updates:

- Milestone 43 is marked as implemented as a documentation-only policy milestone.
- Milestone 44 remains the implementation and HIL validation milestone.

Tests/checks:

- Documentation-only; no automated pytest run is required.

Safety confirmation:

- No camera-control writes were implemented.
- No V4L2 write helpers were added.
- No control widgets were enabled for write behavior.
- Until Milestone 44 deliberately scopes the write path, V4L2 control writes and `v4l2-ctl --set-ctrl` remain prohibited.

Deferred work:

- Milestone 44 implements the approved scoped camera-control write path and validates it on real hardware.
