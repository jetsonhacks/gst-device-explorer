# Milestone 32 — Audio Input Explore Tab

Status: Implemented

## Theme

Create the first microphone-oriented Explore surface for `gst-device-explorer`.

Milestone 29 established the camera Explore pane as the exemplar inspector pattern. Milestones 30 and 31 applied the Explore / Device Information split to composite groups. Milestone 32 extends the same inspector-first direction to audio input endpoints.

The goal is not to build a recorder, mixer, level meter, or audio workstation. The goal is to give the user a compact GUI surface for understanding a microphone/audio-input endpoint and deriving safe, generated GStreamer commands from selected capabilities.

## Product Intent

A user should be able to select a microphone or audio-input endpoint and quickly answer:

- What audio input endpoint is this?
- What card/device identifier does it use?
- What formats, sample rates, and channel counts are available?
- What selected audio mode would a generated pipeline use?
- What GStreamer command can reproduce that selected input configuration?
- What can be copied safely for terminal use?
- What future test action could be added without changing the page structure?

## Scope

Implement an Audio Input Explore tab/page that follows the camera Explore idiom where appropriate.

Required user-visible structure:

1. **Compact endpoint summary**
   - Endpoint kind: audio input / microphone
   - Display name or ALSA/device label when available
   - Stable endpoint identifier
   - Group membership summary when available

2. **Audio input mode/capability selection**
   - Supported sample formats, if available
   - Supported sample rates, if available
   - Supported channel counts, if available
   - The first version may use simple selectors/lists rather than advanced controls.
   - The UI should stay compact and readable on smaller screens.

3. **Generated input pipeline**
   - Display a generated GStreamer audio-input pipeline for the selected/default mode.
   - Use the compact read-only monospace code/copy surface established in Milestone 29.
   - Copy action must remain visible and provide transient copied feedback.
   - Long commands must remain contained within the command surface.

4. **Placeholder for future safe input testing**
   - Include a clearly non-executing placeholder area or disabled action slot for future audio input testing only if it helps establish the page structure.
   - Do not implement recording, level display, capture, or start/stop behavior in this milestone.

5. **Read-only inspector semantics**
   - The page inspects capabilities and generated commands.
   - It must not mutate ALSA, PulseAudio/PipeWire, system mixer state, or device settings.

## Out of Scope

- Audio recording
- Audio level meters
- Microphone capture execution
- Preview/test execution
- Speaker/output behavior
- Full audio Device Information redesign
- Arbitrary GStreamer pipeline editing
- Arbitrary user-authored pipeline execution
- System audio configuration changes
- Package installation
- Group-based execution
- Synchronized audio/video capture

## Safety Boundaries

Preserve existing safety boundaries:

- Generated pipelines only
- No arbitrary pipeline execution
- No hidden command execution
- No system configuration changes
- No group-based execution
- No audio capture execution in this milestone
- No GUI write behavior to ALSA or other system audio controls

## Design Notes

The Audio Input Explore page should reuse the camera pane lessons without copying camera-specific concepts too literally.

Camera pattern:

```text
Endpoint summary
Camera Mode selector
Generated pipeline code/copy surface
Read-only controls/properties
Secondary details in Device Information
```

Audio input adaptation:

```text
Endpoint summary
Audio Input Mode selector
Generated input pipeline code/copy surface
Future bounded test placeholder
Secondary details in Device Information
```

Suggested audio mode vocabulary:

- **Sample Format**
- **Sample Rate**
- **Channels**

Avoid overly technical labels when a clearer user-facing label exists.

If the backend currently has limited audio capability detail, the GUI should gracefully show what is known and avoid pretending unknown values are available. Use safe fallback text such as:

- `No detailed format list available`
- `Inspect Device Information for lower-level details`

## Implementation Guidance

Prefer small, focused changes.

Likely areas to inspect or modify:

- GUI model/builders for audio input selected-device pages
- Explore tab/page construction
- Detail pane routing
- Existing audio candidate generation and profile data
- Existing code/copy row helpers, if available
- Tests for GUI model and detail pane behavior

Do not add new GUI modules unless the existing files would become too large or responsibilities become unclear. If a file approaches or exceeds the GUI roadmap line-count guidance, note the concern and keep the implementation minimal.

Reuse existing helper patterns from camera/group pages where practical:

- read-only code/copy command rows
- compact section headings
- endpoint summary cards/labels
- selected-device Explore vs Device Information split

## Acceptance Criteria

Milestone 32 is complete when:

- Selecting an audio input endpoint opens a useful Audio Input Explore page instead of a generic placeholder/report surface.
- The page shows a compact audio input endpoint summary.
- The page exposes available/known audio input mode information in a compact selector or equivalent read-only presentation.
- The page shows a generated audio-input GStreamer command/pipeline using the established read-only monospace code/copy surface.
- Copy behavior works and provides feedback.
- The page stays read-only and does not execute audio capture or mutate system audio configuration.
- Existing camera Explore behavior remains unchanged.
- Existing group Explore and group Device Information behavior remains unchanged.
- Tests cover the audio input Explore page structure and code/copy command surface.
- Full test suite passes.

## Implementation Notes

Implemented:

- Added an Audio Input Explore surface for audio input endpoints.
- The page shows a compact endpoint summary with audio-input kind and stable endpoint id.
- The page shows an **Audio Input Mode** section with sample format, sample rate, and channel count rows.
- ALSA audio input discovery now carries read-only hardware-parameter capability details when available, so the Explore pane can show discovered sample formats, sample rates, and channel counts.
- When detailed audio capability lists are not available, the page shows safe fallback text rather than fabricating capabilities.
- The page shows generated ALSA/GStreamer input pipeline text in a compact read-only monospace code/copy surface.
- Generated input pipeline text includes exact GStreamer caps values when they are known; broader ranges remain visible in the mode rows without being forced into an invalid caps filter.
- Copy feedback uses the same transient `Copied` behavior established for camera generated pipelines.
- Added a non-executing **Future Input Test** placeholder.
- Preserved Milestone 29 camera Explore behavior.
- Preserved Milestone 30 Group Explore behavior.
- Preserved Milestone 31 Group Device Information behavior.

Files changed:

- `src/gst_device_explorer/probes/alsa.py`
- `src/gst_device_explorer/gui/qt_audio_input_explorer.py`
- `src/gst_device_explorer/gui/qt_explore.py`
- `tests/test_alsa_probe.py`
- `tests/test_gui_detail_pane.py`
- `docs/milestones/MILESTONE_32.md`

Structure note:

- A small audio-input-specific Qt module was added because `qt_explore.py` was already near the GUI roadmap line-count guidance and group Explore logic was already present there. The new module keeps the audio input surface focused and avoids turning the Explore router into a mixed widget implementation file.

Tests added or updated:

- ALSA input capability parsing from hardware-parameter output.
- Audio input Explore accessible-text coverage.
- Audio input generated-pipeline read-only code/copy widget coverage.
- Existing camera, group Explore, group Device Information, and shell tests were rerun.

Tests run:

- `uv run python -m pytest tests/test_gui_detail_pane.py tests/test_gui_shell.py`
- `uv run python -m pytest tests/test_gui_model.py tests/test_gui_detail_pane.py tests/test_gui_camera.py tests/test_gui_shell.py`
- `uv run python -m pytest`

No audio capture/execution, recording, mixer mutation, system audio mutation, or group-based execution was added.

## Suggested Tests

Add or update tests to verify:

- Audio input endpoints route to an Audio Input Explore surface.
- The page contains expected labels such as `Audio Input`, `Sample Format`, `Sample Rate`, and/or `Channels` when data is available.
- The generated input pipeline/command is displayed in a read-only monospace code/copy row.
- Copy action remains visible.
- The page does not expose start/record/capture execution behavior.
- Camera Explore tests from Milestone 29 still pass.
- Group Explore and Group Device Information tests from Milestones 30 and 31 still pass.

Suggested commands:

```sh
uv run python -m pytest tests/test_gui_detail_pane.py tests/test_gui_shell.py
uv run python -m pytest tests/test_gui_model.py tests/test_gui_detail_pane.py tests/test_gui_camera.py tests/test_gui_shell.py
uv run python -m pytest
```

## Documentation Updates

Update this file when implemented:

- Mark status as `Implemented`.
- Record files changed.
- Record behavior implemented.
- Record tests run and results.
- Record deferred work.

If `docs/GUI_ROADMAP.md` needs a small consistency note, keep it minimal. It should already identify Milestone 32 as Audio Input Explore Tab.

## Deferred Work

Likely follow-up work:

- Audio Output Explore Tab
- Audio input Device Information refinements
- Audio test policy and UX
- Bounded microphone capture or level display
- Shared audio mode model/service cleanup
- Reports/diagnostics integration
