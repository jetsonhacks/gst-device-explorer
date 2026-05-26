# Milestone 33 — Audio Output Explore Tab

Status: Implemented

## Theme

Create the first speaker/audio-output-oriented Explore surface for `gst-device-explorer`.

Milestone 29 established the camera Explore pane as the exemplar inspector pattern. Milestones 30 and 31 applied the Explore / Device Information split to composite groups. Milestone 32 created the Audio Input Explore tab and introduced the audio endpoint inspector pattern. Milestone 33 completes the first pair of audio endpoint Explore pages by adding an Audio Output Explore tab.

The goal is not to build a mixer, media player, soundboard, or speaker-test execution surface. The goal is to give the user a compact GUI surface for understanding an audio-output endpoint and deriving safe, generated GStreamer commands from selected or discovered capabilities.

## Product Intent

A user should be able to select a speaker or audio-output endpoint and quickly answer:

- What audio output endpoint is this?
- What card/device identifier does it use?
- What formats, sample rates, and channel counts are available?
- What selected/default audio mode would a generated output/test pipeline use?
- What GStreamer command can reproduce that selected output configuration?
- What can be copied safely for terminal use?
- What future speaker-test action could be added without changing the page structure?

## Scope

Implement an Audio Output Explore tab/page that follows the camera and audio-input inspector idioms where appropriate.

Required user-visible structure:

1. **Compact endpoint summary**
   - Endpoint kind: audio output / speaker
   - Display name or ALSA/device label when available
   - Stable endpoint identifier
   - Group membership summary when available

2. **Audio output mode/capability selection or presentation**
   - Supported sample formats, if available
   - Supported sample rates, if available
   - Supported channel counts, if available
   - The first version may use simple selectors, compact lists, or read-only capability rows.
   - The UI should stay compact and readable on smaller screens.

3. **Generated output/test pipeline**
   - Display a generated GStreamer audio-output pipeline for the selected/default mode.
   - Use the compact read-only monospace code/copy surface established in Milestone 29 and reused in Milestone 32.
   - Copy action must remain visible and provide transient copied feedback.
   - Long commands must remain contained within the command surface.

4. **Placeholder for future safe speaker testing**
   - Include a clearly non-executing placeholder area or disabled action slot for future audio output testing only if it helps establish the page structure.
   - Do not implement tone playback, sound-file playback, start/stop behavior, or pipeline execution in this milestone.

5. **Read-only inspector semantics**
   - The page inspects capabilities and generated commands.
   - It must not mutate ALSA, PulseAudio/PipeWire, system mixer state, volume, routing, or device settings.

## Out of Scope

- Speaker test execution
- Tone playback
- Sound-file playback
- Start/stop behavior
- Volume controls
- Mixer controls
- Audio output recording/loopback
- Audio output Device Information redesign
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
- No speaker playback execution in this milestone
- No ALSA/PulseAudio/PipeWire/system mixer mutation
- No volume or route changes
- No group-based execution
- No synchronized audio/video behavior

## Design Notes

The Audio Output Explore page should reuse the Audio Input Explore structure where useful, while using output-specific language.

Audio input pattern:

```text
Endpoint summary
Audio Input Mode
Generated input pipeline code/copy surface
Future input test placeholder
```

Audio output adaptation:

```text
Endpoint summary
Audio Output Mode
Generated output/test pipeline code/copy surface
Future speaker test placeholder
```

Suggested audio mode vocabulary:

- **Sample Format**
- **Sample Rate**
- **Channels**

Avoid overly technical labels when a clearer user-facing label exists.

If detailed audio output capability data is not available from existing backend models, the GUI should gracefully show what is known and avoid pretending unknown values are available. Use safe fallback text such as:

- `No detailed format list available`
- `Using default generated output candidate`
- `Inspect Device Information for lower-level details`

If GStreamer DeviceMonitor-derived audio capabilities are now available from the backend, use those normalized values rather than shelling out directly from the GUI.

## Implementation Guidance

Prefer small, focused changes.

Likely areas to inspect or modify:

- GUI model/builders for audio output selected-device pages
- Explore tab/page construction
- Detail pane routing
- Existing audio output candidate generation and profile data
- Existing audio input explorer implementation from Milestone 32
- Existing code/copy row helpers
- Tests for GUI model and detail pane behavior

Do not add new GUI modules unless the existing files would become too large or responsibilities become unclear. If a new audio-output-specific module is appropriate, mirror the rationale used for the audio input explorer module and keep the module small.

Reuse existing helper patterns from camera, group, and audio input pages where practical:

- read-only code/copy command rows
- compact section headings
- endpoint summary cards/labels
- selected-device Explore vs Device Information split
- honest fallback text for sparse capability data

## Acceptance Criteria

Milestone 33 is complete when:

- Selecting an audio output endpoint opens a useful Audio Output Explore page instead of a generic placeholder/report surface.
- The page shows a compact audio output endpoint summary.
- The page exposes available/known audio output mode information in a compact selector or equivalent read-only presentation.
- The page shows a generated audio-output GStreamer command/pipeline using the established read-only monospace code/copy surface.
- Copy behavior works and provides feedback.
- The page stays read-only and does not execute speaker playback or mutate system audio configuration.
- Existing camera Explore behavior remains unchanged.
- Existing group Explore and group Device Information behavior remains unchanged.
- Existing audio input Explore behavior remains unchanged.
- Tests cover the audio output Explore page structure and code/copy command surface.
- Full test suite passes.

## Suggested Tests

Add or update tests to verify:

- Audio output endpoints route to the new Audio Output Explore surface.
- The page contains expected labels such as `Audio Output`, `Sample Format`, `Sample Rate`, and/or `Channels` when data is available.
- The generated output/test pipeline is displayed in a read-only code/copy surface.
- Copy action remains visible.
- The page does not expose start/play/test execution behavior.
- Audio Input Explore tests from Milestone 32 still pass.
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

If `docs/GUI_ROADMAP.md` needs a small consistency note, keep it minimal. It should already identify Milestone 33 as Audio Output Explore Tab.

## Implementation Notes

Implemented:

- Added an Audio Output Explore surface for audio output endpoints.
- The page shows a compact endpoint summary with audio-output kind and stable endpoint id.
- The page shows an **Audio Output Mode** section with sample format, sample rate, and channel count rows.
- ALSA audio output discovery now carries read-only hardware-parameter capability details when available, so the Explore pane can show discovered sample formats, sample rates, and channel counts.
- ALSA hardware-parameter probing uses a short bounded timeout and preserves partial timeout output when ALSA prints useful capability data before returning.
- Playback hardware-parameter probing uses `aplay --dump-hw-params` with a raw zero-length `/dev/null` input, which avoids the blocking/read-error form and does not play speaker audio.
- When detailed audio output capability lists are not available, the page shows safe fallback text rather than fabricating capabilities.
- The page shows generated ALSA/GStreamer output pipeline text in a compact read-only monospace code/copy surface.
- Generated output pipeline text includes exact GStreamer caps values when they are known; broader ranges remain visible in the mode rows without being forced into an invalid caps filter.
- Copy feedback uses the same transient `Copied` behavior established for camera and audio input generated pipelines.
- Added a non-executing **Future Speaker Test** placeholder.
- Preserved Milestone 29 camera Explore behavior.
- Preserved Milestone 30 Group Explore behavior.
- Preserved Milestone 31 Group Device Information behavior.
- Preserved Milestone 32 Audio Input Explore behavior.

Files changed:

- `src/gst_device_explorer/gui/qt_audio_output_explorer.py`
- `src/gst_device_explorer/probes/alsa.py`
- `src/gst_device_explorer/gui/qt_explore.py`
- `tests/test_alsa_probe.py`
- `tests/test_gui_detail_pane.py`
- `docs/milestones/MILESTONE_33.md`

Structure note:

- A small audio-output-specific Qt module was added to mirror the Milestone 32 audio input module and keep `qt_explore.py` focused on routing and group Explore behavior.

Tests added or updated:

- Audio output Explore accessible-text coverage.
- ALSA output capability parsing from hardware-parameter output.
- ALSA hardware-parameter timeout handling that preserves partial capability output.
- Audio output generated-pipeline read-only code/copy widget coverage.
- Audio output capability-to-caps coverage for exact values.
- Audio output range fallback coverage that avoids forcing broad ranges into exact caps.
- Existing audio input, camera, group Explore, group Device Information, model, and shell tests were rerun.

Tests run:

- `uv run python -m pytest tests/test_gui_detail_pane.py tests/test_gui_shell.py`
- `uv run python -m pytest tests/test_gui_model.py tests/test_gui_detail_pane.py tests/test_gui_camera.py tests/test_gui_shell.py`
- `uv run python -m pytest`

No speaker playback/execution, tone playback, sound-file playback, volume change, mixer mutation, system audio mutation, route change, or group-based execution was added.

## Deferred Work

Likely follow-up work:

- Audio input/output Device Information refinements
- Audio test policy and UX
- Bounded microphone capture or level display
- Bounded speaker test tone or sound-file playback
- Shared audio endpoint explorer service cleanup
- Reports/diagnostics integration
