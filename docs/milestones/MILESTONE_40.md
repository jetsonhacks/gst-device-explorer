# Milestone 40 — Hardware Interface / HIL Validation Pass

Status: Implemented

## Theme

Validate the first complete GUI hardware-interaction loop on real Jetson/Linux media hardware and record any narrow fixes needed before expanding into Commands/Reproduce or Reports.

Milestones 36, 38, and 39 introduced the first endpoint-specific hardware interactions in the GUI:

- camera preview using a generated structured preview command
- audio output speaker test using a bounded generated tone command
- audio input activity test using a bounded non-recording generated command

Milestone 40 is the checkpoint that proves those interactions behave correctly outside automated fakes and test doubles.

This milestone should not add new product areas. It should validate the existing behavior, document results, and apply narrowly scoped fixes when real hardware exposes a bug, confusing state transition, cleanup problem, or unsafe edge case.

## Product Intent

A user should be able to select a discovered endpoint, inspect the generated command, and explicitly start or stop the scoped hardware test for that endpoint.

The validation pass should answer:

- Does camera preview start and stop correctly on real hardware?
- Does audio output speaker test play a short bounded generated tone and then stop?
- Does audio input activity test run as a bounded non-recording input test?
- Does the GUI communicate state clearly?
- Does cleanup happen on Stop, endpoint change, refresh, close, failure, and unavailable endpoints?
- Are generated commands still inspectable and copyable before execution?
- Are safety boundaries still intact?

## Scope

### In Scope

- Run hardware-in-the-loop validation for camera preview.
- Run hardware-in-the-loop validation for audio output speaker test.
- Run hardware-in-the-loop validation for audio input activity test.
- Validate the existing preview/test process lifecycle on real hardware.
- Validate UI state transitions:
  - Idle
  - Ready
  - Starting
  - Running
  - Stopping
  - Exited
  - Failed
  - Unavailable
- Validate cleanup behavior on:
  - Stop button
  - endpoint change
  - mode change, where applicable
  - refresh
  - window close
  - partial start failure
  - unexpected process exit
  - endpoint unavailability
- Document HIL results in this milestone file.
- Update `docs/GUI_ROADMAP.md` if the validation changes the next milestone ordering.
- Apply small, targeted fixes discovered during validation.
- Add or update regression tests for any bugs fixed during the validation pass.

### Out of Scope

- New camera preview features.
- Recording or capture workflows.
- Saved media files.
- Graphical microphone level meter.
- Arbitrary pipeline editing.
- Arbitrary command execution.
- User-authored pipeline execution.
- Shell-string execution.
- `shell=True`.
- Group-based execution.
- Synchronized audio/video behavior.
- V4L2 control writes.
- `v4l2-ctl --set-ctrl`.
- Volume, mixer, route, ALSA, PulseAudio, or PipeWire configuration mutation.
- Package installation.
- Remote behavior.
- Commands/Reproduce expansion.
- Reports/Diagnostics expansion.
- Broad service-layer rewrite unless a real HIL bug proves the existing seam is inadequate.

## Validation Targets

Use whatever real hardware is available, but prioritize Jetson/Linux systems and Reachy Mini-style composite devices where possible.

Suggested validation targets:

1. **USB camera or Reachy Mini camera endpoint**
   - Select a camera endpoint.
   - Confirm Camera Explore shows the generated preview command.
   - Start preview.
   - Confirm preview starts or fails with a clear error.
   - Stop preview.
   - Confirm process cleanup.

2. **Audio output endpoint / speaker**
   - Select an audio output endpoint.
   - Confirm Audio Output Explore shows the generated output command.
   - Start Speaker Test.
   - Confirm a short bounded generated tone plays.
   - Confirm it stops naturally or via Stop Test.
   - Confirm no volume, mixer, or route mutation occurs.

3. **Audio input endpoint / microphone**
   - Select an audio input endpoint.
   - Confirm Audio Input Explore shows the generated input command.
   - Start Activity Test.
   - Confirm the non-recording pipeline starts and exits or can be stopped.
   - Confirm no file is written and no microphone audio is retained.

4. **Composite group navigation**
   - Select a composite group, if available.
   - Navigate to camera, microphone, and speaker endpoints from group cards.
   - Confirm endpoint-specific tests remain endpoint-specific.
   - Confirm no group-level execution appears.

## HIL Checklist

Record validation results using concrete commands, endpoint identifiers, and observed behavior where practical.

### Camera Preview

- [ ] Generated preview command visible before Start.
- [ ] Preview controls appear after generated command/code-copy surface.
- [ ] Start Preview launches only structured generated argv.
- [ ] Stop Preview terminates the preview process.
- [ ] Endpoint change cleans up a running preview.
- [ ] Refresh cleans up a running preview.
- [ ] Window close cleans up a running preview.
- [ ] Failure state is understandable.
- [ ] No arbitrary command or shell-string execution is possible.

### Audio Output Speaker Test

- [ ] Generated output command visible before Start Test.
- [ ] Speaker Test controls appear after generated command/code-copy surface.
- [ ] Start Test launches only structured generated argv.
- [ ] Test is bounded and short.
- [ ] Stop Test terminates the process when needed.
- [ ] Natural exit returns to a clear state.
- [ ] Endpoint change cleans up a running test.
- [ ] Refresh cleans up a running test.
- [ ] Window close cleans up a running test.
- [ ] No mixer, volume, route, ALSA, PulseAudio, or PipeWire configuration mutation occurs.

### Audio Input Activity Test

- [ ] Generated input command visible before Start Test.
- [ ] Activity Test controls appear after generated command/code-copy surface.
- [ ] Start Test launches only structured generated argv.
- [ ] Test is bounded or explicitly stoppable.
- [ ] Pipeline uses a non-recording sink such as `fakesink`.
- [ ] No file is created.
- [ ] No microphone samples are saved or retained.
- [ ] Stop Test terminates the process when needed.
- [ ] Endpoint change cleans up a running test.
- [ ] Refresh cleans up a running test.
- [ ] Window close cleans up a running test.

### Composite Groups

- [ ] Group Explore remains navigation-only.
- [ ] Endpoint cards navigate to endpoint Explore pages.
- [ ] No group-level preview/test/capture action exists.

## Implementation Guidance

Prefer documentation and targeted fixes over feature work.

If real hardware validation exposes an issue, keep the fix small and specific. Examples of acceptable fixes:

- incorrect enabled/disabled state
- missing cleanup call on a lifecycle transition
- confusing status text
- generated command does not match the structured argv used by the runner
- process state does not update after natural exit
- endpoint change leaves a process running
- a test pipeline blocks unexpectedly and needs a bounded parameter correction
- a failure is swallowed without user-visible feedback

Examples of unacceptable expansion:

- adding arbitrary command entry
- adding capture-to-file
- adding a full microphone level meter
- adding audio recording
- adding synchronized media workflows
- adding report surfaces
- adding command catalog surfaces
- rewriting the GUI service architecture without a concrete HIL failure

## Suggested Test Commands

After any code changes, run focused tests first, then the full suite:

```sh
uv run python -m pytest tests/test_gui_preview_runner.py tests/test_gui_camera.py tests/test_gui_detail_pane.py tests/test_gui_shell.py
uv run python -m pytest tests/test_gui_model.py tests/test_gui_camera.py tests/test_gui_detail_pane.py tests/test_gui_shell.py
uv run python -m pytest
```

If validation adds or changes behavior, add tests near the affected area.

## Suggested Manual Validation Notes

Record:

- host system
- Jetson model, if applicable
- OS / JetPack version, if applicable
- display session type, if relevant
- camera endpoint id and device path
- audio input endpoint id and ALSA device
- audio output endpoint id and ALSA device
- generated command shown by the GUI
- observed process behavior
- cleanup behavior
- failures and exact messages
- follow-up fixes applied

## Validation Results

### Validation Environment

- Host: `jetsonhacks`
- Kernel/system: `Linux jetsonhacks 6.8.12-tegra #1 SMP PREEMPT Tue Dec 30 15:40:41 PST 2025 aarch64`
- GStreamer: `gst-launch-1.0 version 1.24.2`
- Direct shell device checks:
  - `/dev/video*`: no matching device nodes from `ls`
  - `v4l2-ctl --list-devices`: `Cannot open device /dev/video0`
  - `aplay -l`: `no soundcards found`
  - `arecord -l`: `no soundcards found`
- `gst-device-explorer devices` visible endpoints:
  - camera: `/dev/video0`, `/dev/video1`, `/dev/video2`, `/dev/video3`
  - audio input: `hw:0,0`, `hw:3,0`
  - audio output: `hw:0,0`, `hw:1,3`, `hw:1,7`, `hw:1,8`, `hw:1,9`
- `gst-device-explorer groups` visible groups:
  - `Reachy Mini Audio`
  - `Reachy Mini Camera`
  - `HD Pro Webcam C920`
  - `Reachy Mini`

Hardware discovery commands run:

```sh
uname -a
gst-launch-1.0 --version
ls -l /dev/video*
v4l2-ctl --list-devices
aplay -l
arecord -l
uv run gst-device-explorer devices
uv run gst-device-explorer groups
```

### Command Provenance Audit

- Camera Explore now derives the displayed command from the selected endpoint and selected/default mode via `camera_pipeline_argv_for_selection`.
- Camera Explore now uses available candidate evidence to choose the Jetson MJPEG preview argv when `jetson-uvc-mjpeg-nvjpeg-nveglglessink` is available.
- Camera selected/default mode and displayed command now agree. The HIL default for `/dev/video0` is `MJPG`, `1920x1080`, `60 fps`.
- Audio Output Explore derives display text and runner argv from the same `_generated_output_pipeline_argv(target, caps)` helper.
- Audio Input Explore derives display text and runner argv from the same `_generated_input_pipeline_argv(target, caps)` helper.
- Copy surfaces read from the generated command widgets; runner commands are constructed from structured argv helpers, not parsed from display text.
- No runner command is a shell string.
- Detail-pane endpoint changes still call runner cleanup, preventing stale endpoint commands from remaining active.
- Automated tests now cover selected endpoint command provenance, copy/runner consistency, unavailable controls, and the Jetson MJPEG candidate path.

### Camera Preview

HIL status: validated.

- Camera endpoint tested: `/dev/video0` (`Reachy Mini Camera`)
- GUI-generated command after fix:

```sh
gst-launch-1.0 v4l2src device=/dev/video0 io-mode=2 do-timestamp=true ! image/jpeg,width=1920,height=1080,framerate=60/1 ! jpegparse ! nvjpegdec ! video/x-raw(memory:NVMM), format=Y42B ! nvvidconv ! video/x-raw(memory:NVMM), format=NV12 ! nveglglessink sync=false
```

- The command references the selected endpoint `/dev/video0`.
- The selected/default mode influences the command:
  - `MJPG`, `1920x1080`, `60 fps` produces the Jetson MJPEG preview command.
  - `YUYV`, `1920x1080`, `5 fps` produces a `video/x-raw,format=YUYV` command.
- Start was validated through the shared structured-argv `PreviewRunner`.
- Observed start state after two seconds: `Running`.
- Stop/cleanup returned state: `Exited`.
- Initial failure observed before the fix:
  - generic GUI MJPG command failed with `not-negotiated`
  - runner failure text: `Preview exited with code 1.`
- Fix applied:
  - camera GUI command generation now prefers the available Jetson MJPEG candidate path when the candidate summary marks it available.
  - generic MJPEG candidate generation now includes `jpegparse ! jpegdec`.
  - generic MJPEG diagnostics now require `jpegparse` and `jpegdec`.
  - candidate generation no longer suppresses Jetson MJPEG candidates when generic `jpegdec` is missing.
- Endpoint-change, refresh, and window-close cleanup are covered by automated GUI shell/detail tests.

### Audio Output Speaker Test

HIL status: validated.

- Audio output endpoint tested: `hw:0,0` (`Reachy Mini Audio: USB Audio`)
- GUI-generated command:

```sh
gst-launch-1.0 audiotestsrc wave=sine freq=440 samplesperbuffer=2400 num-buffers=20 ! audio/x-raw,format=S16LE,rate=16000,channels=2 ! audioconvert ! audioresample ! alsasink device=hw:0,0
```

- The command references the selected endpoint `hw:0,0`.
- The command is bounded with `num-buffers=20`.
- Start was validated through the shared structured-argv `PreviewRunner`.
- Stop cleanup was validated while the tone was running:
  - observed state after one second: `Running`
  - cleanup state: `Exited`
- Natural exit was validated:
  - GStreamer reached EOS after about three seconds
  - runner state: `Exited`
  - exit code: `0`
- No volume, mixer, route, ALSA, PulseAudio, or PipeWire configuration mutation was added or attempted by the app.
- Endpoint-change, refresh, and window-close cleanup are covered by automated GUI shell/detail tests.

### Audio Input Activity Test

HIL status: validated.

- Audio input endpoint tested: `hw:0,0` (`Reachy Mini Audio: USB Audio`)
- GUI-generated command:

```sh
gst-launch-1.0 alsasrc device=hw:0,0 num-buffers=20 ! audio/x-raw,format=S16LE,rate=16000,channels=2 ! audioconvert ! audioresample ! level interval=1000000000 ! fakesink sync=false
```

- The command references the selected endpoint `hw:0,0`.
- The command is bounded with `num-buffers=20`.
- The command is non-recording and uses `fakesink sync=false`.
- Start was validated through the shared structured-argv `PreviewRunner`.
- Natural exit was validated:
  - GStreamer reached EOS after about 0.2 seconds
  - runner state: `Exited`
  - exit code: `0`
- No file output path exists in the generated command.
- No microphone audio was recorded, saved, retained, or written to disk by the app.
- No mixer, volume, route, ALSA, PulseAudio, or PipeWire configuration mutation was added or attempted by the app.
- Endpoint-change, refresh, and window-close cleanup are covered by automated GUI shell/detail tests.

### Composite Group Behavior

HIL status: validated by discovery plus automated GUI navigation tests.

- Real composite groups were visible through `gst-device-explorer groups`.
- Existing GUI tests validate that Group Explore remains navigation-only, endpoint cards navigate to endpoint-specific Explore pages, and group-level execution controls are not exposed.

### Failures Observed

- Direct shell tools and the app discovery path disagreed: `ls`, `v4l2-ctl`, `aplay`, and `arecord` did not see endpoints, while `gst-device-explorer devices` did.
- Camera GUI MJPG preview initially failed on `/dev/video0` with `not-negotiated` because the GUI-generated command sent `image/jpeg` directly to `autovideosink`.
- The generic MJPG candidate ID already referred to `jpegdec`, but the command omitted `jpegparse ! jpegdec`.
- Generic MJPG candidate filtering initially suppressed Jetson candidates when generic `jpegdec` was missing; this was corrected.

### Fixes Applied

- Camera GUI command provenance now uses the selected/default mode and available candidate evidence instead of the stale generated-pipeline section.
- Camera mode list initialization now selects the model's selected/default mode instead of always selecting the first raw capability row.
- MJPG GUI commands now use either:
  - Jetson path: `jpegparse ! nvjpegdec ! nvvidconv ! nveglglessink`
  - generic path: `jpegparse ! jpegdec ! videoconvert ! autovideosink sync=false`
- Core generic MJPG candidate generation now includes `jpegparse ! jpegdec`.
- Core generic MJPG diagnostics now require `jpegparse` and `jpegdec`.
- Regression tests were updated for the corrected command shapes and selected-mode provenance.
- No `docs/GUI_ROADMAP.md` change was needed because validation did not change milestone ordering or introduce an intermediate milestone.

### Tests Run

Focused GUI/runner regression:

```sh
uv run python -m pytest tests/test_gui_preview_runner.py tests/test_gui_detail_pane.py tests/test_gui_shell.py
```

Result before the HIL fix: `63 passed`.

Required focused GUI/runner regression after the HIL fix:

```sh
uv run python -m pytest tests/test_gui_preview_runner.py tests/test_gui_camera.py tests/test_gui_detail_pane.py tests/test_gui_shell.py
```

Result: `74 passed`.

Broader GUI regression:

```sh
uv run python -m pytest tests/test_gui_model.py tests/test_gui_camera.py tests/test_gui_detail_pane.py tests/test_gui_shell.py
```

Result after the HIL fix: `79 passed`.

Full suite:

```sh
uv run python -m pytest
```

Result after the HIL fix: `606 passed`.

Additional focused tests for the HIL fixes:

```sh
uv run python -m pytest tests/test_gui_camera.py tests/test_gui_detail_pane.py tests/test_pipelines.py tests/test_video_diagnostics.py
```

Result: `75 passed`.

### Safety Confirmation

- No arbitrary pipeline execution was added.
- No arbitrary user-authored pipeline execution was added.
- No shell-string execution or `shell=True` path was added.
- No package installation, remote behavior, or system configuration change was attempted.
- No group-based execution was added.
- No synchronized capture was added.
- No recording, saved capture workflow, or retained microphone samples were added.
- No V4L2 control writes or `v4l2-ctl --set-ctrl` path was added.
- No mixer, volume, route, ALSA, PulseAudio, or PipeWire mutation was added.
- Commands/Reproduce and Reports/Diagnostics remain deferred.

## Acceptance Criteria

Milestone 40 is complete when:

- Camera preview has been manually validated on at least one real camera endpoint, or the inability to do so is documented.
- Audio output speaker test has been manually validated on at least one real output endpoint, or the inability to do so is documented.
- Audio input activity test has been manually validated on at least one real input endpoint, or the inability to do so is documented.
- Stop, endpoint-change, refresh, and close cleanup behavior has been checked where practical.
- Any discovered defects are either fixed with focused regression coverage or explicitly deferred.
- Safety boundaries remain intact.
- `docs/milestones/MILESTONE_40.md` records the validation results.
- `docs/GUI_ROADMAP.md` is updated if the validation results change the next milestone direction.
- Automated tests pass after any code changes.

## Safety Boundaries

Preserve these boundaries:

- no arbitrary pipeline execution
- no arbitrary user-authored pipeline scripts
- no hidden command execution
- no shell-string execution
- no `shell=True`
- no package installation
- no system configuration changes
- no remote behavior
- no group-based execution
- no synchronized capture
- no recording or saved capture workflow
- no retained microphone samples
- no V4L2 control writes
- no `v4l2-ctl --set-ctrl`
- no mixer, volume, route, ALSA, PulseAudio, or PipeWire configuration mutation
- no Commands/Reproduce expansion
- no Reports/Diagnostics expansion

## Deferred Work

- Commands and Reproduce Sections
- Reports Area
- Richer microphone level visualization
- Capture-to-file workflows
- Synchronized audio/video workflows
- Service-layer cleanup, unless required by a specific HIL finding
- Broader polish pass
