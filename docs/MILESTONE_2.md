# Milestone 2 — Safe Pipeline Execution

## Goal

Add a controlled way to execute generated GStreamer pipeline candidates.

Milestone 1 generates and ranks pipeline candidates, but does not execute them.
Milestone 2 introduces safe execution while preserving the separation between:

- probing
- normalized device and capability models
- pipeline candidate generation
- rendering
- execution

The tool still generates structured candidates first. Execution is a separate
step that consumes a selected candidate through an argv-style execution plan.

## Current Status

Milestone 2 is implemented.

Completed pieces:

- Stable candidate IDs on `PipelineCandidate`
- Candidate selection by default top-ranked candidate
- Candidate selection by zero-based index
- Candidate selection by stable candidate ID
- `run video <device> --dry-run`
- Real subprocess execution for `run video <device>`
- argv-based execution through `subprocess.Popen(argv)`
- No `shell=True`
- Rendered display command strings are not executed
- Ctrl+C cleanup with terminate, wait, and kill fallback
- Child subprocess return-code propagation
- Existing `pipeline` command behavior preserved
- Existing pipeline JSON behavior preserved
- Test suite passing: `95 passed`

## Why This Milestone

At the end of Milestone 1, `gst-device-explorer` can discover media devices, inspect their capabilities, and produce ranked GStreamer pipeline candidates.

That is useful, but the user still has to copy a generated command and run it manually.

Milestone 2 closes that loop by allowing the tool to run a selected candidate safely and predictably.

The important design point is that execution should not weaken the current architecture. A pipeline candidate is still a structured object. A shell command is only one rendered form of that object. The execution path should use an argv-style representation, not a shell string.

## Non-Goals

This milestone does not add:

- arbitrary user-supplied pipeline execution
- preview window management
- audio pipelines
- GStreamer pipeline editing
- GUI support
- composite device grouping
- PulseAudio support
- PipeWire support
- GStreamer-native device discovery
- motor, sensor, or actuator support

Those are valid future directions, but they should not be pulled into this milestone.

## User-Facing Commands

Milestone 2 adds a `run` command for video pipeline candidates.

```sh
gst-device-explorer run video /dev/video0
gst-device-explorer run video /dev/video0 --candidate 0
gst-device-explorer run video /dev/video0 --candidate jetson-uvc-mjpeg-nvjpeg-nveglglessink
gst-device-explorer run video /dev/video0 --dry-run
```

Real execution runs only one selected candidate.

## Behavior

Default behavior:

- Generate pipeline candidates for the requested device.
- Select the top-ranked candidate.
- Print the selected command.
- Execute the selected candidate.

Candidate selection:

- `--candidate 0` selects by displayed index.
- `--candidate <candidate-id>` selects by stable candidate ID.
- Invalid selections produce a clear error.
- If no candidate can be generated, print a useful message and exit nonzero.

Dry run behavior:

- `--dry-run` prints the command that would be executed.
- `--dry-run` does not start GStreamer.
- `--dry-run` should be safe to use in tests.

Execution behavior:

- Use `subprocess.Popen(argv)`.
- Do not use `shell=True`.
- Do not execute rendered shell strings.
- Forward stdout and stderr by default.
- Ctrl+C should terminate the child process cleanly.
- If the child exits with a nonzero status, the CLI should return a nonzero status.

## Data Model Additions

### Candidate IDs

`PipelineCandidate` has a stable candidate ID.

Candidate IDs should be descriptive enough for documentation, testing, and future GUI use.

Example IDs:

```text
jetson-uvc-mjpeg-nvjpeg-nveglglessink
generic-v4l2-mjpeg-jpegdec-autovideosink
generic-v4l2-yuyv-videoconvert-autovideosink
```

Candidate IDs do not need to encode every caps detail. They should identify the pipeline family or strategy.

### ExecutionPlan

Milestone 2 adds an `ExecutionPlan` model.

Possible shape:

```python
@dataclass
class ExecutionPlan:
    candidate_id: str
    argv: list[str]
    display_command: str
    warnings: list[str]
```

The `display_command` is for humans.

The `argv` list is for execution.

These should be derived from the same structured pipeline candidate, but they should not be treated as interchangeable.

## Design Rules

- Pipeline candidates remain structured objects.
- CLI output is rendering.
- Execution is a separate step.
- Do not execute rendered shell strings.
- Do not use shell-specific quoting as part of runtime correctness.
- Do not accept arbitrary user-supplied pipeline strings in this milestone.
- Keep execution narrow, predictable, and testable.
- Preserve existing `pipeline` command behavior.
- Preserve existing JSON behavior.
- Do not add preview-window lifecycle abstractions yet.

## Suggested Internal Flow

```text
probe device
  -> normalize capabilities
  -> build ranked PipelineCandidate objects
  -> select candidate
  -> create ExecutionPlan
  -> render display command
  -> execute argv, unless --dry-run was requested
```

This keeps command rendering and command execution as separate concerns.

## CLI Output

Example dry run:

```text
Selected pipeline candidate: jetson-uvc-mjpeg-nvjpeg-nveglglessink

gst-launch-1.0 v4l2src device=/dev/video0 io-mode=2 do-timestamp=true ! image/jpeg, width=1920, height=1080, framerate=60/1 ! jpegparse ! nvjpegdec ! 'video/x-raw(memory:NVMM), format=Y42B' ! nvvidconv ! 'video/x-raw(memory:NVMM), format=NV12' ! nveglglessink sync=false

Dry run only. Pipeline was not executed.
```

Example execution:

```text
Selected pipeline candidate: jetson-uvc-mjpeg-nvjpeg-nveglglessink

gst-launch-1.0 v4l2src device=/dev/video0 io-mode=2 do-timestamp=true ! image/jpeg, width=1920, height=1080, framerate=60/1 ! jpegparse ! nvjpegdec ! 'video/x-raw(memory:NVMM), format=Y42B' ! nvvidconv ! 'video/x-raw(memory:NVMM), format=NV12' ! nveglglessink sync=false

Running pipeline. Press Ctrl+C to stop.
```

## Error Handling

The command should fail clearly when:

- the requested device does not exist
- no pipeline candidates are available
- the candidate index is out of range
- the candidate ID does not exist
- `gst-launch-1.0` is unavailable
- the subprocess cannot be started
- GStreamer exits with an error

Errors should explain what happened and, where practical, suggest the next diagnostic command.

Example:

```text
No pipeline candidates were generated for /dev/video3.

Try:
  gst-device-explorer video /dev/video3
  gst-device-explorer env
```

## Testing Plan

Add tests for:

- candidate IDs are present
- candidate selection by index
- candidate selection by ID
- invalid candidate index
- invalid candidate ID
- dry-run does not invoke subprocess
- execution uses argv form
- execution does not use `shell=True`
- subprocess nonzero exit propagates to CLI
- existing `pipeline` behavior remains unchanged

Where signal handling is difficult to test directly, isolate the subprocess management logic so it can be unit tested with a fake process object.

## Acceptance Criteria

Milestone 2 is complete when:

- `gst-device-explorer run video /dev/video0 --dry-run` prints the top candidate command.
- `gst-device-explorer run video /dev/video0 --candidate 0 --dry-run` selects by index.
- `gst-device-explorer run video /dev/video0 --candidate <id> --dry-run` selects by ID.
- Invalid candidate selection gives a useful error.
- Real execution uses `subprocess.Popen(argv)`.
- Real execution does not use `shell=True`.
- Ctrl+C terminates the running GStreamer process cleanly.
- Existing `pipeline` commands continue to work.
- Existing JSON behavior remains unchanged.
- All tests pass.

## Implementation Order

1. Mark Milestone 1 complete.
2. Add candidate IDs to `PipelineCandidate`.
3. Update pipeline builders to assign IDs.
4. Add candidate selection helpers.
5. Add `ExecutionPlan`.
6. Add dry-run support.
7. Add subprocess execution.
8. Add Ctrl+C cleanup.
9. Add tests.
10. Update README and setup documentation with the new `run` command.

## Future Work

The following should remain outside Milestone 2:

- composite device grouping
- audio pipeline generation
- GStreamer device monitor integration
- explicit profile files or profile classes
- GUI rendering
- preview window management
- pipeline execution history
- recording pipelines
- latency measurement
- robot peripheral grouping

Composite device grouping is likely a good Milestone 3 candidate.
