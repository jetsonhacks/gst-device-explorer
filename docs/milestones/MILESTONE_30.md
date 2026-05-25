# Milestone 30 — Group Explore View

## Status

Implemented

## Theme

Make composite groups useful as physical-device dashboards without implying group-based execution.

`gst-device-explorer` is an inspector-first GUI. A user may plug in a device such as a 3D camera, a multimedia USB device, or a simple robot like Reachy Mini and want to understand the endpoints exposed by that physical device. The Group Explore view should help the user see the physical device as a whole while still preserving endpoint-based exploration and execution boundaries.

Milestone 29 established the camera Explore pane as the exemplar inspector surface. Milestone 30 applies that product direction to composite groups.

## Product Intent

The Group Explore view should answer these user questions:

- What physical or composite device did the tool infer?
- Which Linux/media endpoints appear to belong to it?
- What kind of endpoint is each one: camera, microphone, speaker, or other?
- Which endpoint should I explore next?
- Is this grouping based on explainable evidence?

The Group Explore view is a dashboard and navigation surface. It should not become a group-level execution surface.

## Primary User Flow

1. User opens `gst-device-explorer`.
2. User selects a composite group in the sidebar.
3. The main pane opens the group Explore tab.
4. The user sees a compact group summary and endpoint cards.
5. The user chooses an endpoint card action such as **Explore Camera**, **Explore Microphone**, or **Explore Speaker**.
6. The application navigates to the endpoint-specific Explore tab.

## Scope

### In Scope

- Add or refine a group Explore tab/view.
- Show a compact group summary.
- Show endpoint cards for discovered group members.
- Nest child composite groups under their physical/composite parent in the sidebar when group membership shows a containment relationship.
- Include endpoint kinds such as:
  - camera / video input
  - microphone / audio input
  - speaker / audio output
  - unknown or other endpoint types, when applicable
- Each endpoint card should include a concise summary.
- Each endpoint card should include a clear action to explore that endpoint directly.
- Preserve a clear distinction between:
  - group-level overview
  - endpoint-level exploration
  - Device Information / diagnostics
- Preserve evidence-based grouping language without overloading the Explore view with raw metadata.
- Add or update GUI tests covering the group Explore behavior.
- Update milestone documentation.

### Out of Scope

- Group-based pipeline execution.
- Synchronized camera/audio capture.
- Automatic endpoint selection for execution.
- Reachy-specific hard-coding.
- Arbitrary pipeline execution.
- Arbitrary user-authored pipeline scripts.
- V4L2 control writes.
- Audio test implementation.
- Camera preview implementation unless already existing behavior is being preserved.
- Deep grouping evidence views; those belong in the Group Device Information tab.
- Major service-layer redesign unless a small extraction is necessary to keep files maintainable.

## Design Principles

### Inspector first

The group view should expose what the system discovered, not hide uncertainty behind a polished product metaphor.

### Endpoint actions only

A group can summarize endpoints and route the user to them, but execution remains endpoint-based.

### Explainable but compact

The Explore tab may include a short grouping confidence/evidence summary, but detailed evidence belongs in Device Information.

### No Reachy-specific behavior

Reachy Mini is an important validation example, but the implementation should stay generic. The same group view should work for any composite USB/media device.

### Follow the camera-pane blueprint

Use Milestone 29 as the design reference:

- compact summary first
- clear inspector surface
- generated commands only where endpoint-specific and scoped
- copy/run affordances only when deliberately supported
- secondary details kept out of the default Explore flow

## Suggested UI Shape

```text
Group Explore

[Compact Group Summary]
Name / inferred label
Group kind or grouping basis
Endpoint count
Short evidence summary

[Endpoints]
┌─────────────────────────────┐
│ Camera                      │
│ /dev/video0                 │
│ 1920x1080, MJPG/YUYV, ...   │
│ [Explore Camera]            │
└─────────────────────────────┘

┌─────────────────────────────┐
│ Microphone                  │
│ hw:2,0                      │
│ Input device, ALSA card ... │
│ [Explore Microphone]        │
└─────────────────────────────┘

┌─────────────────────────────┐
│ Speaker                     │
│ hw:2,0                      │
│ Output device, ALSA card ...│
│ [Explore Speaker]           │
└─────────────────────────────┘
```

The layout should work on smaller screens. Prefer a wrapping card layout or compact vertical card stack over a wide fixed layout.

## Endpoint Card Guidance

Each endpoint card should include:

- endpoint role/kind label
- device path or stable identifier
- concise human-readable summary
- optional small diagnostic/status cue, if already available
- one primary navigation action

Endpoint cards should not include:

- raw JSON
- full sysfs metadata
- long candidate pipeline lists
- detailed grouping evidence
- execution buttons that imply group-level behavior

## Possible Labels

Use clear user-facing labels:

- **Camera** for video input endpoints
- **Microphone** for audio input endpoints
- **Speaker** for audio output endpoints
- **Endpoint** or **Other Endpoint** for unknown kinds

Avoid overfitting labels to Reachy Mini or any specific hardware vendor.

## Testing Expectations

Add or update tests that verify:

- selecting a group shows a group Explore view
- the group view includes a compact group summary
- endpoint cards are rendered for group members
- endpoint cards expose appropriate role labels
- endpoint cards include navigation/explore actions
- group view does not expose group-level run/preview/capture actions
- existing camera Explore behavior from Milestone 29 remains intact
- no new GUI modules are introduced unless explicitly justified

Suggested test commands:

```sh
uv run python -m pytest tests/test_gui_detail_pane.py tests/test_gui_camera.py
uv run python -m pytest tests/test_gui_shell.py
uv run python -m pytest
```

Adjust the specific test list based on the existing test organization.

## Documentation Updates

- Add this milestone file under `docs/milestones/MILESTONE_30.md`.
- Link the milestone from the appropriate milestone index or GUI roadmap if the project uses one.
- Keep `docs/GUI_ROADMAP.md` consistent with the shifted numbering where Milestone 30 is Group Explore View.

## Completion Criteria

Milestone 30 is complete when:

- group selection opens a useful Group Explore view
- group-level content is compact and inspector-oriented
- endpoint cards are visible and understandable
- endpoint cards navigate to endpoint-specific Explore pages
- composite group hierarchy is represented in the sidebar, such as child audio/camera groups under a physical parent group
- no group-based execution is introduced
- Reachy Mini-style groups are handled generically
- tests pass
- documentation is updated

## Implementation Notes

Implemented:

- Composite groups in the sidebar now infer parent/child hierarchy from endpoint membership containment.
- A physical parent group, such as `Reachy Mini`, can contain child groups such as `Reachy Mini Audio` and `Reachy Mini Camera` instead of listing all groups as siblings.
- Parent groups avoid duplicating endpoint rows already covered by child groups.
- Selecting a group opens a Group Explore dashboard with compact summary information and endpoint cards.
- Endpoint cards show role labels, endpoint identifiers, concise summaries, and navigation-only actions such as **Explore Camera**, **Explore Microphone**, and **Explore Speaker**.
- Endpoint card actions navigate to endpoint-specific Explore pages.
- Group Explore does not show group-level run, preview, capture, or test controls.
- No group-based execution was added.

Validation:

- Added GUI model tests for nested composite group hierarchy.
- Added Explore text and widget tests for group summary, endpoint cards, role labels, and navigation-only endpoint actions.
- Added a Qt shell smoke test that clicks a group endpoint action and verifies sidebar navigation to the grouped endpoint.

## Deferred Work

The following should remain deferred unless explicitly scoped later:

- Group Device Information tab with detailed grouping evidence.
- Group-level validation reports.
- Synchronized media capture.
- Audio input/output Explore tabs.
- Safe preview/test execution policies.
- Service-layer cleanup.
