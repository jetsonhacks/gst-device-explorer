# Milestone 24 — Camera Explorer HIL Validation and UX Alignment

Repository target path:

```text
docs/milestones/MILESTONE_24.md
```

Status: **Implemented**

## Theme

Validate the camera explorer against real hardware and align the GUI experience with the original `camera-caps` reference before adding new camera actions.

Milestone 23 corrected the GUI direction by making the selected camera pane a task-oriented camera explorer:

- camera identity
- pixel format selection
- resolution selection
- frame-rate / frame-duration selection
- prominent generated pipeline text
- copy pipeline affordance
- dynamically discovered V4L2 controls
- read-only control rendering
- diagnostics as secondary detail

Milestone 24 uses the available hardware-in-the-loop environment to check whether the new camera explorer is actually usable and aligned with the intended product direction.

## HIL Validation

### Environment

- Machine: Jetson (Linux 6.8.12-tegra)
- Display: X11 (:1)
- Camera hardware: Reachy Mini Camera (`usb-a80aa10000.usb-4.1.4`)
  - `/dev/video0` — Video Capture node (uvcvideo, MJPG + YUYV)
  - `/dev/video1` — Metadata Capture node (no video formats)

### Demo Mode

Command:

```sh
/home/jim/.local/bin/uv run gst-device-explorer gui --demo
```

Validated:

- GUI launches in demo mode.
- Sidebar shows demo composite group, two cameras, audio input, audio output.
- Selecting a camera opens the camera explorer pane.
- Camera Explorer section renders with mode selectors, pipeline text, and V4L2 controls.
- Copy Pipeline affordance is present.
- Preview Deferred button is visible and disabled.
- Safety boundaries confirmed: no pipeline execution, no subprocess on copy.

### Live Mode

Command:

```sh
/home/jim/.local/bin/uv run gst-device-explorer gui
```

Validated:

- GUI launches in live mode.
- Reachy Mini Camera appears in the sidebar at `/dev/video0`.
- `/dev/video1` (metadata-only node) also appears but has no video formats.
- Selecting `/dev/video0` opens camera explorer with 8 format/resolution combinations:
  - MJPG: 3840×2592 (30fps), 1920×1080 (60fps), 3840×2160 (30fps), 3264×2448 (30fps)
  - YUYV: 3840×2592 (1fps), 1920×1080 (5fps), 3840×2160 (1fps), 3264×2448 (1fps)
- 14 V4L2 controls discovered and rendered:
  - Integer controls: brightness, contrast, saturation, hue, gamma, gain, sharpness, backlight_compensation
  - Boolean controls: white_balance_automatic, exposure_dynamic_framerate
  - Menu controls: power_line_frequency, auto_exposure
  - Inactive (grayed out): white_balance_temperature, exposure_time_absolute
- Controls are read-only; no `--set-ctrl` is invoked.
- Pipeline text displays and updates when mode selectors are changed.
- Refresh does not crash; sidebar stable on re-query.

### Parser Observations

Real camera output includes annotated menu values (`value=2 (60 Hz)`). Parser correctly ignores the annotation and extracts the numeric value. Synthetic tests added for this pattern.

Inactive controls (`flags=inactive`) display as disabled widgets. Verified on `white_balance_temperature` and `exposure_time_absolute`.

## UX Comparison with camera-caps

The reference application (`~/camera-caps`) uses:

- A top-bar camera selector (`QComboBox`) with identity labels below.
- Three side-by-side **expanding QListWidget** panels for Pixel Format, Image Size, and Frame Duration.
- A pipeline text line edit + copy icon + preview icon button in a row below the lists.
- A scrollable V4L2 control area at the bottom.

The Milestone 23 camera pane used:

- Three `QComboBox` selectors inside `QGroupBox` containers in a horizontal row.
- This showed only one item at a time and required dropdown interaction to see all options.
- The `QGroupBox` wrappers added visual overhead without benefit.

## UX Corrections Made

### Mode Selectors: QComboBox → QListWidget

Replaced the three `QComboBox + QGroupBox` mode selectors with three labeled `QListWidget` column panels, directly aligned with the camera-caps interaction model.

Changes in `src/gst_device_explorer/gui/qt_detail.py`:

- Added `QListWidget` import.
- Replaced `_combo_group()` helper with `_list_column()` inline factory.
- Format, Image Size, and Frame Duration are now expanding `QListWidget` panels side-by-side.
- Each list shows all available options at once without dropdown interaction.
- Clicking an item in Pixel Format repopulates Image Size; clicking Image Size repopulates Frame Duration.
- Pipeline text updates on each selection change.
- Device path shown at the top of the Camera Explorer box for identity.

### Copy Pipeline Button

- Copy Pipeline button is always rendered.
- Button is enabled when a valid pipeline exists; disabled otherwise.
- Button state updates dynamically as selection changes.

### No-Controls Message

- Improved the "no controls" message to `"No V4L2 controls advertised for this device."` in the Qt widget rendering, distinguishing the display from the serialized section text.

### Pipeline Row

- Preview Deferred button remains visible and disabled, positioned after Copy Pipeline.

## Parser and Display Fixes

No parser bugs were found. The V4L2 control parser correctly handles:

- Menu current value with label annotation (`value=2 (60 Hz)` → parses `"2"`).
- Inactive flag on integer controls (`flags=inactive` → `flags=('inactive',)`).
- Multi-section v4l2-ctl output (User Controls, Camera Controls).

## Tests Added

### `tests/test_v4l2_probe.py`

- `test_menu_control_with_current_value_annotation` — verifies `value=N (label)` annotation handling.
- `test_inactive_int_control_flags_from_real_format` — verifies `flags=inactive` on integer control.
- `test_real_camera_style_full_control_block` — smoke test matching the Reachy Mini Camera v4l2-ctl output.

### `tests/test_gui_camera.py`

- `test_pipeline_text_updates_when_format_changes` — verifies MJPG uses `image/jpeg`, YUYV uses `video/x-raw`.
- `test_pipeline_text_fractional_frame_rate` — verifies 29.97 fps → `framerate=29970/1000`.
- `test_no_controls_section_shows_unavailable_message` — verifies no-controls state text.
- `test_camera_explorer_state_with_real_camera_format` — state built from high-resolution MJPG modes.
- `test_pipeline_text_without_frame_rate_is_valid` — verifies pipeline without frame rate omits `framerate=`.

## Versioning

Version bumped from `0.23.0` to `0.24.0` in:

- `pyproject.toml`
- `src/gst_device_explorer/__init__.py`
- `tests/test_support_bundle.py`
- `README.md`

## Safety Boundaries Confirmed

- No camera preview.
- No audio input test.
- No audio output test.
- No media capture.
- No pipeline execution.
- No dry-run subprocess from GUI buttons.
- No suggested-command execution.
- No arbitrary subprocess execution (only existing safe read-only probes).
- No V4L2 control writes.
- No `v4l2-ctl --set-ctrl`.
- No reset-to-default control mutation.
- No system configuration changes.
- No package installation.
- No remote behavior.
- No group-based execution.
- No synchronized capture.

Copy-to-clipboard and read-only probe subprocesses remain allowed.

## Deferred

- Applying V4L2 control changes.
- Reset-to-default control actions.
- Camera preview and embedded video preview widgets.
- Dry-run process execution from GUI.
- Media capture dialogs.
- Audio input explorer redesign.
- Audio output explorer redesign.
- Audio test controls.
- Process lifecycle controls.
- Support bundle GUI.
- Screenshots and demo docs beyond validation notes.
- Packaging and installers.

## Completion Criteria

All completion criteria met:

- HIL validation performed on Reachy Mini Camera (demo and live modes).
- GUI compared against `~/camera-caps` reference.
- Targeted UX correction made: QListWidget mode selectors replacing QComboBox.
- Real-device parser behavior confirmed correct; synthetic tests added for observed patterns.
- Dynamic V4L2 controls remain read-only.
- Generated pipeline text remains copyable.
- Diagnostics remain secondary.
- Tests pass (549 + 11 new = 560 total).
- No preview, capture, pipeline execution, dry-run subprocess, or V4L2 control-write behavior introduced.
- Documentation updated.
- Version bumped to `0.24.0`.
