# Milestone 29 — Camera Pane Inspector Refinement

Status: Implemented

## Theme

Refine the camera Explore pane so it becomes the reference blueprint for future endpoint inspector pages.

The project direction is **inspector first, with safe copy/run affordances second**. A user plugs in a media-capable device — for example a 3D camera, a USB multimedia device, or a simple robot such as Reachy Mini — and wants to understand what Linux, GStreamer, V4L2, and ALSA expose. The GUI should help the user inspect valid modes, see the generated safe command, and perform bounded experiments such as previewing, playing, recording, or capturing.

This milestone is intentionally split into two slices. Slice 1 establishes the top-level camera-mode and generated-pipeline blueprint. Slice 2 refines the camera-control area after the higher-value structural pattern is in place.

## Guiding Principles

- Preserve the inspector model: show what the device exposes before suggesting actions.
- Keep generated commands derived from structured selections, not free-form user input.
- Keep the GUI compact enough for smaller laptop and embedded screens.
- Treat the camera pane as the pattern language for later audio, capture, group, and device pages.
- Avoid broad redesign, arbitrary pipeline editing, and Reachy-specific behavior.
- Keep changes small, testable, and reversible.

## Slice 1 — Camera Mode and Generated Pipeline Blueprint

### Goal

Clarify the top half of the camera Explore pane and establish the generated-command presentation pattern that future panes can reuse.

### Scope

1. Rename the third mode-selection column from **Frame Duration / FPS** to **Frame Rate**.
   - The UI displays values such as `30 fps`, so the user-facing label should be frame-rate oriented.
   - Internal models may continue to preserve frame duration, fractions, and derived FPS as appropriate.
   - Do not change frame-rate list behavior; testing with a more capable camera confirmed the current list correctly shows multiple rates when the device exposes them.

2. Rename the camera mode section from **Camera Settings** to a mode-oriented label.
   - Preferred: **Camera Mode**.
   - Acceptable alternative if the implementation already uses video-oriented terminology: **Video Mode**.
   - The section contains pixel format, image size, and frame-rate selection; it is not the same kind of setting as brightness, exposure, white balance, or gain.

3. Convert the generated pipeline field into a compact code/copy surface.
   - Present the generated GStreamer command as read-only code, not as an editable form field.
   - Use a monospace font.
   - Keep the surface compact in height.
   - Preserve long-command usability with horizontal scrolling or clean clipping.
   - Keep the copy affordance visible and easy to use.
   - Provide copy feedback such as a transient `Copied` state or tooltip.
   - Avoid making the command panel so large that it harms smaller-screen usability.

### Expected User-Facing Flow

The top half of the pane should communicate:

```text
Pixel Format -> Image Size -> Frame Rate -> Generated Pipeline
```

The generated pipeline should read as a derived artifact from the selected camera mode.

### Out of Scope for Slice 1

- Changing the mode-list data model.
- Replacing the three-column selector with a table.
- Adding arbitrary pipeline editing.
- Adding new run/capture workflows beyond existing bounded behavior.
- Reworking camera controls.
- Adding broad tooltip/help infrastructure.

### Suggested Tests / Smoke Checks

- Existing GUI camera tests continue to pass.
- The mode selector still displays all available frame rates for a selected pixel format and image size.
- A camera that exposes only one frame rate still shows one frame rate.
- A camera that exposes multiple frame rates still shows multiple frame rates.
- The third column label is exactly `Frame Rate`.
- The mode section label is `Camera Mode` or the chosen equivalent.
- The generated pipeline text remains copyable.
- The generated pipeline text is read-only.
- The generated pipeline uses a monospace font or an identifiable code-style widget/object.
- Long pipelines do not push the copy button off the visible layout.

## Slice 2 — Camera Controls Ergonomics

### Goal

Improve the lower camera-control area so exposed V4L2 controls remain inspectable, easier to scan, and visually accurate in active/inactive states.

### Scope

1. Improve inactive control-row presentation.
   - Inactive rows should be visually muted as a whole row, not merely labeled with `Inactive`.
   - Labels, sliders, value fields, combo boxes, checkboxes, and default buttons should all communicate the inactive/disabled state.
   - Disabled controls should not invite interaction.
   - The inactive reason/status should remain readable.

2. Add light grouping to camera controls.
   - Use simple section headers or subtle separators rather than heavy accordions at first.
   - Suggested groups:
     - **Image Adjustment**: Brightness, Contrast, Saturation, Hue, Sharpness, Gamma.
     - **Exposure & Gain**: Auto Exposure, Exposure Time Absolute, Gain, Backlight Compensation.
     - **White Balance**: White Balance Automatic, White Balance Temperature.
     - **Advanced**: Power Line Frequency, Exposure Dynamic Framerate, and other controls that do not clearly fit above.
   - Grouping should reduce scan fatigue without hiding inspector information.

3. Tighten and bound the camera-control row layout.
   - Avoid stretching labels, sliders, values, status labels, and Default buttons across excessive horizontal distance.
   - Keep related widgets visually close enough to read as a single control.
   - Prefer a bounded left-aligned working width over full-width sprawl.
   - Preserve responsiveness on narrower screens.

### Out of Scope for Slice 2

- Collapsible accordion behavior unless it is clearly simpler than expected.
- Per-control documentation popovers.
- A large visual redesign of the entire application.
- Changing V4L2 control semantics.
- Device-specific control ordering.
- Reachy-specific grouping.

### Suggested Tests / Smoke Checks

- Existing camera-control tests continue to pass.
- Inactive controls remain non-interactive.
- Active controls remain interactive.
- Default buttons still work for active controls.
- Inactive rows expose their inactive state in widget enabled/disabled state, styling, or object properties that can be smoke-tested.
- Control grouping appears without losing controls.
- The control area remains usable at reduced window widths.

## Milestone Completion Criteria

- Slice 1 is complete and committed independently before Slice 2 begins.
- Slice 2 is complete and committed independently after Slice 1.
- No generated GUI module sprawl is introduced.
- Existing tests pass.
- New or updated tests cover label changes, generated-pipeline presentation, and inactive-control behavior where practical.
- Documentation or milestone notes record the camera pane as the current blueprint for future endpoint inspector pages.

## Notes

The earlier suspicion that frame rates were not all visible was disproven by testing with a more capable camera. The original camera exposed only one frame rate for each selected resolution. Therefore, do not implement a frame-rate data fix in this milestone. Only rename the column to match the displayed data.

## Slice 1 Implementation Notes

Implemented:

- Renamed the mode selector section to **Camera Mode**.
- Renamed the third selector column to **Frame Rate**.
- Kept frame-rate selection behavior unchanged.
- Kept the generated pipeline as a read-only compact command surface.
- Made the generated pipeline field explicitly code-styled with a monospace font.
- Preserved the copy affordance and added transient `Copied` button feedback.
- Added focused GUI tests for the new labels, read-only code presentation, copyability, and long-pipeline layout behavior.

Deferred to Slice 2:

- Inactive camera-control row presentation.
- Camera-control grouping.
- Bounded camera-control row layout.

## Slice 2 Implementation Notes

Implemented:

- Added light camera-control grouping in the existing camera-control module:
  - **Image Adjustment**
  - **Exposure & Gain**
  - **White Balance**
  - **Advanced**
- Kept grouping generic and capability-name based; no Reachy-specific checks were added.
- Muted inactive rows as a whole row with row/object properties, disabled labels, disabled value widgets, disabled status labels, and disabled default buttons.
- Preserved the existing read-only inspector semantics for active controls; active rows remain visually readable and are not marked inactive.
- Bounded control rows to a compact left-aligned working width so labels, values, status, and Default buttons stay visually related.
- Added focused tests for grouping order, preserved controls, inactive row state, and reduced-width row bounds.

No new GUI modules were introduced.
