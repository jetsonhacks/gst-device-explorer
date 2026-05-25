# Milestone 31 — Group Device Information Tab

Status: Implemented

## Theme

Make composite-group evidence inspectable without turning the group Explore view into a report dump.

Milestone 30 made composite groups useful as physical-device dashboards. Milestone 31 adds the companion **Device Information** view for groups: a secondary, organized place to explain why endpoints were grouped, what evidence supports the grouping, and how the same investigation can be reproduced from the command line.

The intent is to preserve the GUI direction established in Milestones 29 and 30:

- **Explore** is the working surface.
- **Device Information** is the explanation and evidence surface.
- Groups are physical-device summaries, not execution targets.
- Endpoint-specific execution remains endpoint-specific.

## Product Goal

When a user selects a composite group such as a Reachy Mini-style physical device, the **Explore** tab should show a compact dashboard of endpoints. The **Device Information** tab should answer:

- Why does the application think these endpoints belong together?
- What evidence was used to form the group?
- Which endpoints are included directly?
- Which endpoints are represented by child groups?
- What lower-level metadata is available for debugging?
- How can the user reproduce the grouping investigation from the CLI?

## Scope

Implement a group-specific Device Information tab that is organized, readable, and secondary to the Group Explore dashboard.

### Required behavior

- Add or refine the group **Device Information** view.
- Show compact group identity information.
- Show grouping evidence in a readable form.
- Show endpoint membership information.
- Distinguish direct endpoints from endpoints represented by child groups, when the model supports this.
- Show relevant low-level metadata without overwhelming the default Explore tab.
- Include reproducible CLI commands where the existing command patterns support them.
- Preserve the Milestone 30 Group Explore dashboard.
- Preserve endpoint-card navigation behavior.
- Preserve existing camera Explore behavior from Milestone 29.

### Suggested sections

The exact labels may be adjusted to match the existing GUI vocabulary, but the view should remain organized around these concepts:

1. **Group Summary**
   - group display name
   - group id
   - group kind/type, if available
   - direct endpoint count
   - child group count, if applicable

2. **Grouping Evidence**
   - USB parent relationship evidence
   - ALSA card relationship evidence
   - shared sysfs path or parent-path evidence
   - any confidence/explanation fields already available in the model

3. **Endpoint Membership**
   - direct endpoint rows/cards
   - endpoint role labels where available, such as camera, microphone, speaker, video, audio input, audio output
   - endpoint ids and device paths
   - child group summaries where applicable

4. **Metadata / Diagnostics**
   - relevant sysfs, ALSA, V4L2, USB, or environment metadata already available to the GUI
   - missing or unavailable metadata should be explicit but not noisy

5. **Reproduce with CLI**
   - curated commands such as group inspection, metadata view, profile/report commands, or equivalent existing CLI entry points
   - commands should be displayed as read-only command/code surfaces where practical
   - copy affordances are acceptable if consistent with the existing GUI pattern

## Out of Scope

Do not implement:

- group-based pipeline execution
- group-based preview
- synchronized capture
- audio/video capture
- arbitrary pipeline editing
- arbitrary command execution
- V4L2 control writes
- package installation
- system configuration changes
- remote behavior
- new report-generation features beyond displaying already available group information
- audio Explore tabs
- preview or dry-run execution policy changes

## Safety Boundaries

This milestone must preserve all existing safety boundaries:

- generated pipelines only
- explicit user action for any future execution behavior
- no arbitrary user-authored pipelines
- no hidden command execution
- no group-based execution
- no system modification
- no V4L2 write/reset behavior

For this milestone, group views remain read-only inspection and navigation surfaces.

## Implementation Notes

- Prefer reusing existing GUI patterns from Milestones 29 and 30.
- Keep the group Explore tab compact and dashboard-oriented.
- Put evidence and lower-level details in Device Information.
- Avoid duplicating endpoint rows in parent groups when child groups already cover them, consistent with Milestone 30 behavior.
- Keep any new code small and focused.
- Avoid introducing new GUI modules unless the existing files would become difficult to maintain.
- Preserve the project guideline that Python files should generally remain around 250–300 lines when practical, with explicit review if a file grows too large.
- Do not weaken existing tests to make new behavior pass.

## Suggested Tests

Add or update tests that verify:

- group Device Information tab exists for composite groups
- group evidence text is visible and accessible
- endpoint membership is shown
- child group relationships are represented where available
- direct endpoint duplication is avoided where applicable
- CLI reproduction commands are shown when supported
- Group Explore remains a compact dashboard
- endpoint-card navigation still works
- camera Explore Milestone 29 behavior remains intact
- no execution behavior is introduced from group Device Information

Suggested commands:

```sh
uv run python -m pytest tests/test_gui_detail_pane.py tests/test_gui_shell.py
uv run python -m pytest tests/test_gui_model.py tests/test_gui_detail_pane.py tests/test_gui_camera.py tests/test_gui_shell.py
uv run python -m pytest
```

## Acceptance Criteria

Milestone 31 is complete when:

- selecting a composite group provides a useful Device Information tab
- the tab explains grouping evidence and membership clearly
- group Explore remains dashboard-like and uncluttered
- endpoint-specific navigation remains the path to endpoint-specific Explore pages
- no group-based execution exists
- relevant tests pass
- documentation is updated to mark the milestone implemented

## Implementation Notes

Implemented:

- Added richer group Device Information sections:
  - **Group Summary**
  - **Direct Endpoints**
  - **Child Groups**
  - **Grouping Evidence**
  - **Metadata / Diagnostics**
  - **Reproduce with CLI**
- Preserved the Milestone 30 Group Explore dashboard and endpoint-card navigation.
- Reused the Milestone 30 group containment logic so parent group Device Information can distinguish direct endpoints from endpoints represented by child groups.
- Avoided duplicating parent endpoint rows in Device Information when child groups cover those endpoints.
- Added read-only monospace command/copy rows for existing reproduction commands:
  - `gst-device-explorer groups`
  - `gst-device-explorer validate group <group-id>`
  - `gst-device-explorer report`
- Kept group views read-only and inspection-oriented.

Validation:

- Added tests for group summary, evidence, direct endpoint membership, child group summaries, endpoint de-duplication, and reproduce-with-CLI commands.
- Added widget tests for read-only code-style CLI command rows.
- Re-ran group Explore, shell navigation, and Milestone 29 camera Explore tests.

No group-based execution was added.

## Deferred Work

- group validation/report surfaces
- richer report/export integration
- audio input Explore tab
- audio output Explore tab
- preview policy and dry-run UX
- camera preview execution
- audio test policy and implementation
