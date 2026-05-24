# Milestone 6 — Device Profiles and Capability Summaries

Status: Complete

Target version: `v0.6.0`

## Theme

Milestone 6 adds structured device profiles.

The tool can already discover media devices, inspect raw capabilities, generate pipeline candidates, safely run selected bounded tests, group related endpoints, and explain candidate availability through diagnostics.

The next step is to provide a compact, structured summary of what a device is, what it can do, which pipeline candidates apply, and what is missing.

Milestone 6 should make `gst-device-explorer` more useful as a field-debugging tool.

A user should be able to ask:

- What is this device?
- What capabilities did the tool discover?
- Which pipeline candidates are available?
- Which candidates are blocked, and why?
- Is this endpoint part of a larger composite device?
- What should I try next?

The goal is not to add new media behavior. The goal is to summarize existing discovery, grouping, candidate, and diagnostic information in one place.

## Slice 1 Status

Implemented in the first slice:

- small `DeviceProfile` and `ProfileCandidateSummary` models
- audio input endpoint profiles
- audio output endpoint profiles
- candidate summaries derived from existing audio diagnostics
- available/unavailable candidate buckets
- missing element summaries
- suggested next commands
- text and JSON CLI output for audio endpoint profiles
- tests using synthetic ALSA devices and synthetic GStreamer environment facts

Commands added:

```sh
gst-device-explorer profile audio-input hw:0,0
gst-device-explorer profile audio-input hw:0,0 --json
gst-device-explorer profile audio-output hw:0,0
gst-device-explorer profile audio-output hw:0,0 --json
```

Still deferred after the first slice:

- video endpoint profiles
- group profiles
- group membership summaries
- new media behavior or pipeline families

## Slice 2 Status

Implemented in the second slice:

- video endpoint profiles
- compact V4L2 capability summaries
- video candidate summaries derived from existing video diagnostics
- available/unavailable candidate buckets
- missing element summaries
- suggested next commands
- text and JSON CLI output for video endpoint profiles
- tests using synthetic V4L2 capabilities and synthetic GStreamer environment facts

Commands added:

```sh
gst-device-explorer profile video /dev/video0
gst-device-explorer profile video /dev/video0 --json
```

Capabilities summary shape:

```json
{
  "formats": ["MJPG", "YUYV"],
  "max_resolution": "1920x1080",
  "frame_rates": ["30/1"],
  "mode_count": 2
}
```

Audio and video endpoint profiles are now covered.

## Slice 3 Status

Implemented in the third slice:

- compact `ProfileGroupSummary` model
- informational group membership summaries in endpoint profiles
- matching against existing `CompositeDevice` members
- audio input group membership summaries
- audio output group membership summaries
- video group membership summaries
- JSON profile `groups` entries with:
  - group ID
  - label
  - confidence
  - kind
  - member count
- text profile `Groups` section when matching groups are available
- tests using synthetic composite groups

Group membership in profiles is informational only. It does not add
group-based pipeline generation, group-based execution, or group-based
candidate selection.

Group profiles remain deferred.

## Goals

Add a structured device profile layer that summarizes discovered device information.

Profiles should be useful for:

- CLI users
- JSON consumers
- future GUI renderers
- debugging Jetson / Linux media setups
- documenting real hardware behavior
- comparing devices across systems

A profile should combine existing information rather than inventing new probing paths.

## Non-goals

Milestone 6 should not add:

- new video pipeline families
- new audio pipeline families
- audio loopback
- synchronized audio/video capture
- group-based pipeline execution
- group-based pipeline generation
- ASR
- TTS
- WebRTC
- PulseAudio
- PipeWire
- effects
- echo cancellation
- recording workflows
- Reachy-specific hard-coding
- JetPack-version-specific hard-coding
- arbitrary user-supplied GStreamer execution
- GUI implementation

## Design Principles

- Summarize existing facts; do not re-probe unnecessarily.
- Keep profiles structured, not just formatted text.
- CLI and future GUI are renderers.
- Preserve the distinction between observed facts and inferred summaries.
- Do not change candidate generation behavior.
- Do not change diagnostic behavior.
- Keep group membership evidence-based.
- Prefer capability detection over platform assumptions.
- Avoid Reachy-specific behavior.
- Keep the milestone narrow.

## Proposed Model Concepts

Milestone 6 may add one or more lightweight profile models.

Possible names:

- `DeviceProfile`
- `VideoDeviceProfile`
- `AudioDeviceProfile`
- `ProfileSummary`
- `ProfileCandidateSummary`
- `ProfileGroupSummary`

The exact names should follow the style of the existing codebase.

A profile may include:

- device kind
- device identifier
- display name, if known
- subsystem-specific metadata
- key capabilities
- pipeline candidate summaries
- diagnostic summaries
- group membership
- suggested next commands

Example high-level shape:

```json
{
  "device_kind": "video",
  "device": "/dev/video0",
  "display_name": "Reachy Mini Camera",
  "metadata": {
    "bus": "usb",
    "vendor_id": "2e8a",
    "product_id": "000a",
    "driver": "uvcvideo"
  },
  "capabilities_summary": {
    "formats": ["MJPG", "YUYV"],
    "max_resolution": "3840x2592",
    "frame_rates": ["30/1"]
  },
  "candidate_summary": {
    "available": [
      "generic-v4l2-mjpeg-jpegdec-autovideosink",
      "jetson-uvc-mjpeg-nvjpeg-nveglglessink"
    ],
    "unavailable": []
  },
  "groups": [
    {
      "group_id": "reachy-mini-camera",
      "label": "Reachy Mini Camera",
      "confidence": 0.9
    }
  ],
  "suggested_next_commands": [
    "gst-device-explorer pipeline video /dev/video0",
    "gst-device-explorer pipeline video /dev/video0 --diagnostics",
    "gst-device-explorer run video /dev/video0 --dry-run"
  ]
}
```

## Profile Scope

Milestone 6 should cover existing endpoint types:

- video devices
- audio input devices
- audio output devices

Endpoint profiles now include informational composite group membership when
existing grouping data contains the endpoint. Composite/group profiles remain
deferred and may be considered only if they remain summary-only and do not
introduce group-based execution behavior.

## Candidate and Diagnostic Summaries

Device profiles should include a concise summary of existing pipeline candidates and diagnostics.

For each applicable candidate, include:

- candidate ID
- label/name, if available
- status
- reason
- missing elements, if any

The profile should not duplicate every detail of `--diagnostics` unless JSON consumers need it. The CLI text output should remain compact.

A profile should point users to diagnostics for deeper detail.

## Group Membership

Milestone 6 should connect individual device profiles to existing composite device grouping information.

For example:

- `/dev/video0` may report membership in `Reachy Mini Camera`
- `hw:0,0` may report membership in `Reachy Mini Audio`
- both may report membership in the parent `Reachy Mini` USB-family group, if available

Group information should remain evidence-based and should not imply group-based pipeline execution.

Profile output should make clear that group membership is informational.

## CLI Shape

Possible command shape:

```sh
gst-device-explorer profile video /dev/video0
gst-device-explorer profile video /dev/video0 --json

gst-device-explorer profile audio-input hw:0,0
gst-device-explorer profile audio-input hw:0,0 --json

gst-device-explorer profile audio-output hw:0,0
gst-device-explorer profile audio-output hw:0,0 --json
```

Optional later shape, only if it remains clean:

```sh
gst-device-explorer profile group <group-id>
gst-device-explorer profile group <group-id> --json
```

The first implementation should prefer endpoint profiles over group profiles.

## Text Output

Text output should be concise and field-oriented.

Example:

```text
Device profile for video /dev/video0

Name: Reachy Mini Camera
Driver: uvcvideo
Bus: usb

Capabilities:
  Formats: MJPG, YUYV
  Max resolution: 3840x2592
  Frame rates: 30/1

Pipeline candidates:
  available    generic-v4l2-mjpeg-jpegdec-autovideosink
  available    jetson-uvc-mjpeg-nvjpeg-nveglglessink

Groups:
  Reachy Mini Camera       confidence 0.90
  Reachy Mini              confidence 0.80

Suggested next commands:
  gst-device-explorer pipeline video /dev/video0
  gst-device-explorer pipeline video /dev/video0 --diagnostics
  gst-device-explorer run video /dev/video0 --dry-run
```

Audio output example:

```text
Device profile for audio-output hw:0,0

Name: Reachy Mini Audio
Bus: usb

Pipeline candidates:
  available    generic-alsa-audio-output-sine-alsasink

Groups:
  Reachy Mini Audio        confidence 0.90
  Reachy Mini              confidence 0.80

Suggested next commands:
  gst-device-explorer pipeline audio-output hw:0,0
  gst-device-explorer pipeline audio-output hw:0,0 --diagnostics
  gst-device-explorer run audio-output hw:0,0 --dry-run
```

## JSON Output

JSON output should be structured and stable enough for tests and future GUI use.

Possible shape:

```json
{
  "device_kind": "audio-output",
  "device": "hw:0,0",
  "display_name": "Reachy Mini Audio",
  "metadata": {
    "bus": "usb"
  },
  "capabilities_summary": {},
  "candidate_summary": {
    "available": [
      {
        "candidate_id": "generic-alsa-audio-output-sine-alsasink",
        "status": "available",
        "reason": "ALSA playback device and required GStreamer elements are available.",
        "missing_elements": []
      }
    ],
    "unavailable": []
  },
  "groups": [
    {
      "group_id": "audio-device-alsa-card-0",
      "label": "Reachy Mini Audio",
      "confidence": 0.9,
      "kind": "audio-device",
      "member_count": 2
    }
  ],
  "suggested_next_commands": [
    "gst-device-explorer pipeline audio-output hw:0,0",
    "gst-device-explorer pipeline audio-output hw:0,0 --diagnostics",
    "gst-device-explorer run audio-output hw:0,0 --dry-run"
  ]
}
```

## First Implementation Slice

The first slice focuses on audio endpoint profiles without group profiles.

Implemented first slice:

- add core profile model
- add audio input profile
- add audio output profile
- include candidate/diagnostic summary
- include suggested next commands
- add CLI:
  - `gst-device-explorer profile audio-input hw:0,0`
  - `gst-device-explorer profile audio-input hw:0,0 --json`
  - `gst-device-explorer profile audio-output hw:0,0`
  - `gst-device-explorer profile audio-output hw:0,0 --json`
- add tests using synthetic devices and synthetic environment facts

Video profiles remain deferred after the first slice.

## Second Implementation Slice

The second slice adds video endpoint profiles.

Video profiles summarize:

- device identifier
- display name, if known
- V4L2 metadata, if available
- supported formats
- notable resolutions/frame rates where already available
- existing video candidate diagnostics
- suggested next commands

Do not add new video pipeline candidates.

## Third Implementation Slice

The third slice adds informational group membership summaries to endpoint
profiles.

Implemented third slice:

- use existing grouping logic and `CompositeDevice` data
- summarize matching composite groups in endpoint profiles
- keep `groups: []` when no group data is available or no groups match
- keep group profiles deferred
- do not add group-based execution or group-based pipeline generation

## Testing

Tests should use synthetic devices, synthetic metadata, synthetic capabilities, and synthetic environment facts.

Tests should not require real hardware.

Test coverage should include:

- audio input profile JSON shape
- audio output profile JSON shape
- audio input profile text output
- audio output profile text output
- video profile JSON shape
- video profile text output
- candidate summary available status
- candidate summary unavailable status
- missing element summary
- suggested next commands
- group membership summary, if implemented
- no change to existing discovery behavior
- no change to existing candidate generation behavior
- no change to existing diagnostics behavior
- all existing tests continue to pass

## Documentation

Update:

- `README.md`
- `docs/SETUP.md`
- `docs/MILESTONE_6.md`

Documentation should show:

- how to generate a device profile
- how profile output fits into the workflow
- how profiles differ from raw discovery, pipeline inspection, and diagnostics
- how profiles summarize rather than execute
- JSON profile examples or command examples

## Suggested Workflow

Milestone 6 should support this user workflow:

```sh
gst-device-explorer devices
gst-device-explorer groups

gst-device-explorer profile video /dev/video0
gst-device-explorer profile video /dev/video0 --json

gst-device-explorer pipeline video /dev/video0
gst-device-explorer pipeline video /dev/video0 --diagnostics
gst-device-explorer run video /dev/video0 --dry-run
```

For audio:

```sh
gst-device-explorer audio-inputs
gst-device-explorer audio-outputs

gst-device-explorer profile audio-input hw:0,0
gst-device-explorer profile audio-output hw:0,0

gst-device-explorer pipeline audio-input hw:0,0 --diagnostics
gst-device-explorer pipeline audio-output hw:0,0 --diagnostics
```

## Validation Commands

Run:

```sh
/home/jim/.local/bin/uv run python -m pytest
```

Optional manual checks:

```sh
/home/jim/.local/bin/uv run gst-device-explorer profile audio-input hw:0,0
/home/jim/.local/bin/uv run gst-device-explorer profile audio-input hw:0,0 --json

/home/jim/.local/bin/uv run gst-device-explorer profile audio-output hw:0,0
/home/jim/.local/bin/uv run gst-device-explorer profile audio-output hw:0,0 --json

/home/jim/.local/bin/uv run gst-device-explorer profile video /dev/video0
/home/jim/.local/bin/uv run gst-device-explorer profile video /dev/video0 --json

/home/jim/.local/bin/uv run gst-device-explorer groups
/home/jim/.local/bin/uv run gst-device-explorer groups --json
```

## Completion Criteria

All criteria are met as of `v0.6.0`:

- [x] endpoint device profiles are represented as structured data
- [x] profiles cover audio input devices
- [x] profiles cover audio output devices
- [x] profiles cover video devices
- [x] profiles include candidate/diagnostic summaries
- [x] profiles include informational group membership summaries when available
- [x] profiles include suggested next commands
- [x] JSON output is stable and test-covered
- [x] text output is concise and useful
- [x] docs explain the profile workflow
- [x] all tests pass
- [x] project version bumped to `0.6.0`

## Implemented in Milestone 6

- `DeviceProfile`, `ProfileCandidateSummary`, `ProfileGroupSummary` models
- Audio input endpoint profiles
- Audio output endpoint profiles
- Video endpoint profiles with V4L2 capabilities summary
- Candidate/diagnostic summaries (available and unavailable buckets, missing elements)
- Informational group membership summaries in endpoint profiles
- Suggested next commands in all profiles
- Text and JSON CLI output for all profile types
- Commands:
  - `gst-device-explorer profile audio-input <device>`
  - `gst-device-explorer profile audio-input <device> --json`
  - `gst-device-explorer profile audio-output <device>`
  - `gst-device-explorer profile audio-output <device> --json`
  - `gst-device-explorer profile video <device>`
  - `gst-device-explorer profile video <device> --json`

## Deferred Beyond Milestone 6

The following remain out of scope:

- group profiles
- group-based pipeline generation
- group-based pipeline execution
- new video pipeline families
- new audio pipeline families
- audio loopback
- ASR / TTS / WebRTC
- PulseAudio / PipeWire
- effects / echo cancellation
- recording workflows
- synchronized audio/video workflows
- GUI implementation
