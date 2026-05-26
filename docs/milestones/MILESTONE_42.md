# Milestone 42 — Audio Output Quality Test Implementation

Status: Implemented

## Theme

Implement the audio output quality-test UX defined in Milestone 41.

Milestone 38 proved that a selected audio output endpoint can run a bounded generated tone. Milestone 41 clarified that a generated tone is useful for endpoint discovery, but it is not enough for judging real-world playback fidelity. Milestone 42 adds the first safe, local-file playback quality test while preserving the existing generated-command-only safety model.

The goal is not to build a media player, mixer, soundboard, playlist tool, or routing manager. The goal is to let a user select a local audio file, play it through the selected audio output endpoint at a conservative pipeline-local playback level, and judge whether the output sounds acceptable.

## Product Intent

A user exploring an audio output endpoint should be able to answer:

- Can this selected output endpoint make sound?
- Can I make the test comfortable for my environment?
- Can I play a familiar local audio file to judge playback fidelity?
- Can I stop playback safely?
- Is the displayed command the same command that will be run?
- Is the application avoiding system volume, mixer, routing, and audio configuration changes?

## Scope

Implement audio output quality testing in the Audio Output Explore page.

### Required user-visible behavior

The Audio Output Explore page should keep the existing structure:

```text
Endpoint summary
Audio Output Mode
Generated output pipeline / code-copy surface
Speaker Test / Audio Output Test
```

The test area should support two clearly distinct test modes:

```text
Generated Tone
Local File Playback
```

### Generated Tone refinement

The existing generated tone test should remain available and should gain a pipeline-local **Test Level** control.

Required behavior:

- Keep the generated tone short and bounded.
- Add conservative level presets:
  - Quiet
  - Normal
  - Loud
- Default to Quiet.
- Update generated tone command/argv when the selected Test Level changes.
- Start Test and Stop Test continue to delegate to the existing runner/service.
- Do not change system volume, mixer, route, ALSA, PulseAudio, or PipeWire configuration.

Suggested label:

```text
Test Level
```

Avoid:

```text
Volume
```

because the control must not imply system-volume mutation.

Suggested helper text:

```text
Test Level adjusts only this generated test pipeline. It does not change system volume, mixer settings, or audio routing.
```

### Local File Playback

Add a local file playback quality test.

Required behavior:

- Provide a way to select a local audio file.
- Show the selected file basename in the UI.
- Provide the full path as tooltip or secondary text.
- Add a pipeline-local **Playback Level** control with presets:
  - Quiet
  - Normal
  - Loud
- Default to Quiet.
- Provide Start Playback and Stop Playback controls.
- Playback must use the selected output endpoint.
- Playback must use structured argv only.
- Playback must not use shell strings.
- Playback must not use remote URLs, network streams, playlists, folders, or recursive playback.
- Playback must not mutate system volume, mixer, route, ALSA, PulseAudio, or PipeWire configuration.
- Unsupported or unplayable files should fail with a clear UI state/message.

Suggested helper text:

```text
Playback Level adjusts only this playback test. It does not change system volume, mixer settings, or audio routing.
```

## File Selection Policy

First implementation should be local-file-only.

Allowed:

- Explicitly selected local file path.
- Common audio files if supported by GStreamer on the system.

Disallowed:

- remote URLs
- network streams
- playlists
- directories
- recursive folder playback
- arbitrary command text
- arbitrary GStreamer pipeline text
- shell expansion
- glob expansion

Recommended initial extension handling:

Either:

1. Accept a conservative extension list and block unsupported extensions early:
   - `.wav`
   - `.flac`
   - `.ogg`
   - `.mp3`
   - `.m4a`
   - `.aac`

or:

2. Accept any local file selected by the user and let GStreamer fail cleanly if unsupported.

Prefer the simpler safe implementation. Record the choice in the milestone completion notes.

## Playback Duration Policy

Preferred behavior:

- File playback should be bounded by default if reasonably simple.
- A short preview duration is acceptable for quality testing.
- Manual Stop must always be available while playback is active.

Acceptable first implementation:

- Manual Start/Stop only, if process cleanup is robust and tested.

If bounded file playback is implemented, it should still expose Stop.

If bounded playback is not implemented, document why and ensure cleanup behavior is well tested.

## Command Provenance Requirements

This milestone must preserve the Milestone 40 command-provenance discipline.

Conceptual flow:

```text
selected output endpoint
+ selected/default output mode
+ selected test type
+ selected level preset
+ optional selected local file
    -> structured generated command / argv
    -> displayed read-only code/copy surface or test-command surface
    -> runner PreviewCommand argv
```

Required:

- The displayed command must be generated from the same source as the runner argv.
- The copied command must match the displayed generated command.
- The runner must receive structured argv only.
- The runner must not parse argv from display text.
- The runner must not receive a shell string.
- Switching endpoints must invalidate or regenerate stale playback commands.
- Switching files must update the displayed command and runner argv.
- Switching level presets must update the displayed command and runner argv.
- If no eligible local file is selected, Start Playback must be unavailable.

Invalid flows:

```text
display text -> parsed argv -> runner
file path -> shell string -> runner
hard-coded demo command -> runner
previous selected file -> current endpoint runner
previous selected endpoint -> current playback command
```

## Implementation Guidance

Prefer small, focused changes.

Likely files to inspect or modify:

- `src/gst_device_explorer/gui/qt_audio_output_explorer.py`
- `src/gst_device_explorer/gui/qt_audio_output_test.py`
- `src/gst_device_explorer/gui/qt_explore.py`
- `src/gst_device_explorer/gui/preview_runner.py`
- audio pipeline/candidate builders in `src/gst_device_explorer/core/`
- GUI tests in `tests/test_gui_detail_pane.py`
- GUI shell/runner tests in `tests/test_gui_shell.py`
- pipeline/provenance tests if command construction moves into core helpers

Prefer adding focused helpers rather than growing existing files past the roadmap line-count guidance.

Do not perform broad service-layer cleanup in this milestone unless a very small extraction is necessary to keep command generation testable.

Do not rename `PreviewCommand` in this milestone. Milestone 41 explicitly deferred the name cleanup to a later service-layer cleanup milestone.

## HIL Validation

A HIL environment should be used for this milestone.

Validate:

### Generated tone

- Audio output endpoint is visible.
- Generated tone still starts and stops.
- Quiet / Normal / Loud affect only pipeline-local amplitude.
- Tone remains bounded.
- Stop works.
- Endpoint change, refresh, and close cleanup work.

### Local file playback

- Select a local audio file.
- UI shows basename and preserves full path access.
- Generated playback command includes the selected file path and selected output endpoint.
- Playback starts through the selected output endpoint.
- Playback level affects only pipeline-local amplitude.
- Stop Playback works.
- Endpoint change, refresh, and close cleanup work.
- Unsupported/unplayable file failure is understandable.
- No system volume, mixer, route, ALSA, PulseAudio, or PipeWire configuration is mutated.

Record HIL hardware, selected file type(s), command examples, and observations in the completion notes.

## Tests

Add or update automated tests to verify:

- Generated tone level presets are visible.
- Generated tone defaults to Quiet.
- Changing tone level updates generated argv.
- Tone runner argv remains structured.
- Local file playback controls are visible.
- Start Playback is unavailable until a local file is selected.
- Remote URLs are rejected or cannot be selected.
- Directories/playlists are rejected or unavailable.
- Selected file basename appears in UI.
- Full path is retained for generated argv.
- Playback Level defaults to Quiet.
- Changing Playback Level updates generated argv.
- Displayed command, copied command, and runner argv share the same generated source.
- Switching endpoints invalidates or regenerates file playback commands.
- Stop/cleanup behavior uses the runner/service.
- Existing camera preview, audio input activity, and group navigation tests still pass.

Suggested commands:

```sh
uv run python -m pytest tests/test_gui_preview_runner.py tests/test_gui_detail_pane.py tests/test_gui_shell.py
uv run python -m pytest tests/test_gui_model.py tests/test_gui_camera.py tests/test_gui_detail_pane.py tests/test_gui_shell.py
uv run python -m pytest
```

Add more focused tests if new modules are introduced.

## Safety Boundaries

Preserve all existing safety boundaries:

- No arbitrary pipeline execution.
- No arbitrary user-authored pipeline scripts.
- No shell-string execution.
- No `shell=True`.
- No hidden command execution.
- No package installation.
- No system configuration changes.
- No remote behavior.
- No remote URL/network-stream playback.
- No playlists.
- No recursive folder playback.
- No group-based execution.
- No synchronized audio/video behavior.
- No recording.
- No file capture.
- No microphone input behavior in this milestone.
- No arbitrary file playback beyond an explicitly selected local audio file.
- No mixer mutation.
- No system volume mutation.
- No route mutation.
- No ALSA/PulseAudio/PipeWire configuration mutation.
- No Commands/Reproduce expansion.
- No Reports expansion.

## Out of Scope

Do not implement:

- audio input level meters
- audio recording
- arbitrary media player features
- playlists
- network playback
- folder playback
- audio routing selection
- system volume control
- mixer controls
- user-authored pipelines
- synchronized audio/video behavior
- Reports
- Commands/Reproduce sections
- broad service-layer cleanup

## Acceptance Criteria

Milestone 42 is complete when:

- Audio Output Explore has clear Generated Tone and Local File Playback test modes.
- Generated Tone supports pipeline-local Test Level presets.
- Local File Playback supports selecting a local audio file.
- Local File Playback supports pipeline-local Playback Level presets.
- Test/playback level controls do not mutate system volume or mixer state.
- Generated commands are structured and derived from the selected endpoint, selected file, and level preset.
- Displayed command, copied command, and runner argv remain aligned.
- Remote URLs, playlists, directories, and arbitrary pipeline text are not supported.
- Start Playback is unavailable until a valid local file is selected.
- Stop/cleanup behavior is implemented through the runner/service.
- HIL validation is performed and recorded.
- Automated tests pass.
- Existing camera preview, audio output tone, audio input activity, group navigation, and safety behavior remain intact.
- Commands/Reproduce and Reports remain deferred.

## Completion Notes

### Files changed

- `src/gst_device_explorer/gui/qt_audio_output_file_playback.py` — new module (185 lines)
- `src/gst_device_explorer/gui/qt_audio_output_test.py` — Test Level combo added (114 lines)
- `src/gst_device_explorer/gui/qt_audio_output_explorer.py` — level state, dynamic pipeline text, file playback integration (249 lines)
- `tests/test_gui_detail_pane.py` — 4 tests updated, 9 new tests added
- `docs/milestones/MILESTONE_42.md` — this file

### UI behavior implemented

**Generated Tone Test Level:**

- `QComboBox` with "Quiet", "Normal", "Loud" inside the Speaker Test group box
- Default: Quiet
- Label: "Test Level:" (not "Volume")
- Changing level updates the "Generated Output Pipeline" `QLineEdit` immediately
- `" ".join(command.argv) == pipeline_edit.text()` invariant maintained at all times
- Safety note: "Test Level adjusts only this generated pipeline and does not change system volume, mixer settings, or audio routing."

**Local File Playback:**

- "Local File Playback" group box below the Speaker Test group box
- "Select Audio File" button opens native `QFileDialog`; file name is shown in a label; full path stored as tooltip
- `QComboBox` with "Quiet", "Normal", "Loud" for Playback Level (default: Quiet)
- Start Playback disabled until a valid local file is selected
- Start Playback and Stop Playback delegate to an injected or self-owned `PreviewRunner`
- Safety note: "Playback Level adjusts only this playback pipeline and does not change system volume, mixer settings, or audio routing."

### File selection policy chosen

**Option B:** accept any locally selected file; let GStreamer fail cleanly if the format is unsupported. The file dialog offers a suggested filter ("Audio Files *.wav *.flac *.ogg *.mp3 *.m4a *.aac") but allows "All Files" as a fallback. `is_safe_local_file()` rejects URLs, empty strings, and directories.

### Playback duration policy

Natural EOS (file plays to end, runner detects exit code 0 → EXITED). Manual Stop always available. This is effectively bounded by the file length without additional complexity.

### Command provenance

Tone: `selected endpoint + level → _generated_tone_argv() → pipeline_edit.text() == " ".join(command.argv)`. The pipeline edit updates dynamically; copy surface and runner argv share the same generated source.

File playback: `selected endpoint + file_path + level → file_playback_argv() → runner argv`. The full file path appears in argv as `location=<path>`. No shell string is constructed. `filesrc` is used instead of `uridecodebin` to make remote URLs structurally impossible.

### HIL hardware

- Host: `jetsonhacks`
- Kernel: `Linux jetsonhacks 6.8.12-tegra #1 SMP PREEMPT Tue Dec 30 15:40:41 PST 2025 aarch64`
- GStreamer: `gst-launch-1.0 1.24.2`
- Audio output endpoint validated: `hw:0,0` (Reachy Mini Audio)

### HIL results

**Generated tone with level:**

- Quiet (volume=0.2): audible, conservative
- Normal (volume=0.5): comfortable
- Loud (volume=0.8): clearly louder, no distortion
- Pipeline text updates immediately when level combo changes
- Tone remains bounded; runner transitions to EXITED after automatic completion
- Cleanup on endpoint change, Refresh, and window close confirmed

**Local file playback:**

- `.wav` (PCM 16-bit, 48 kHz stereo): plays correctly, EOS detected as EXITED
- `.flac`: plays correctly
- `.mp3` (128 kbps): plays correctly via decodebin
- `.txt` (unsupported): GStreamer exits with non-zero code; runner enters FAILED state; message shown
- Quiet/Normal/Loud level control works as expected
- Stop Playback stops cleanly
- Cleanup on endpoint change, Refresh, and window close confirmed
- No system volume, mixer, route, ALSA, PulseAudio, or PipeWire mutation observed

### Tests run

```sh
uv run python -m pytest tests/test_gui_detail_pane.py
```

Result: `54 passed`.

```sh
uv run python -m pytest
```

Result: `615 passed`.

### Safety confirmation

- No arbitrary pipeline execution.
- No shell-string execution. No `shell=True`.
- No remote URL or network stream playback (`is_safe_local_file()` rejects all URL schemes).
- No playlists or recursive folder playback.
- No system volume, mixer, route, ALSA, PulseAudio, or PipeWire configuration mutation.
- No microphone input behavior.
- No recording or file capture.
- No group-based execution.
- No synchronized audio/video behavior.
- No Commands/Reproduce expansion.
- No Reports expansion.
- `PreviewCommand` raises `TypeError` on shell strings.

### Deferred work

- Audio input level meter / waveform display (deferred in Milestone 37)
- Commands/Reproduce sections (Milestone 43)
- Reports area (Milestone 44)
- Service-layer cleanup / `PreviewCommand` rename (Milestone 45)
- Richer failure diagnostics for unsupported file types
