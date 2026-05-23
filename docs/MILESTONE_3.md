# Milestone 3 — Composite Device Grouping

## Goal

Group related Linux devices into higher-level composite devices.

Linux exposes hardware through separate subsystems. A single physical device may appear as several unrelated entries:

- a V4L2 camera device
- an ALSA audio input
- an ALSA audio output
- a serial device
- a USB HID device
- a control bus

For a robot or embedded peripheral, those pieces often belong together.

Milestone 3 adds a grouping layer so `gst-device-explorer` can present related devices as one composite device while still preserving access to the raw individual devices.

## Final Status

Milestone 3 is complete. It adds evidence-backed composite device grouping and
CLI presentation while preserving the existing raw device views and Milestone 2
individual-device pipeline execution behavior.

Implemented:

- `DeviceRef`
- `GroupingEvidence`
- `CompositeDevice`
- `GroupableDevice`
- Synthetic grouping engine
- ALSA capture/playback same-card grouping
- Synthetic USB parent path grouping
- Grouping metadata collection from discovered V4L2 and ALSA devices
- ALSA card/device metadata extraction
- V4L2 sysfs name and USB metadata extraction when available
- ALSA sysfs USB metadata extraction when available
- Parent USB-family grouping from shared USB ancestor, shared vendor ID, and
  shared non-generic product-family metadata
- Parent USB-family names derived from shared non-generic product-family tokens
- `groups`
- `groups --json`
- `groups --metadata`
- `groups --metadata --json`
- `group <group-id>`
- `group <group-id> --json`
- Synthetic model tests
- Synthetic grouping tests
- Synthetic metadata collection tests
- CLI group rendering tests
- CLI grouping metadata rendering tests

Remaining Out Of Scope:

- Group-based pipeline generation or execution
- Reachy-specific grouping logic

These are intentional non-goals for Milestone 3.

## Why This Milestone

Milestone 1 establishes device discovery, capability probing, and pipeline candidate generation.

Milestone 2 adds safe execution of selected pipeline candidates.

Milestone 3 moves the project from a list of unrelated Linux devices toward a more useful embedded-system inventory.

For example, a Reachy Mini may expose:

- a camera
- an audio input
- an audio output

The useful user-facing concept is not just:

```text
/dev/video0
ALSA capture device
ALSA playback device
```

It is:

```text
Reachy Mini
  camera:
    /dev/video0
  audio input:
    hw:2,0
  audio output:
    hw:2,0
```

This helps the tool evolve from a media-device explorer into a broader device-exploration foundation for Jetson and robotics work.

## Non-Goals

This milestone does not add:

- motor control
- Dynamixel protocol support
- non-media control APIs
- audio pipeline generation
- pipeline execution changes
- GStreamer pipeline editing
- GUI support
- hard-coded Reachy-only behavior
- device claiming or exclusive access
- live health monitoring
- automatic driver installation

The goal is grouping and presentation, not control.

## Core Concept

A composite device is a higher-level object that contains one or more discovered devices.

A composite device should be created from evidence, not assumptions.

For example:

```text
Composite device:
  Reachy Mini

Members:
  camera        -> /dev/video0
  audio-input   -> hw:2,0
  audio-output  -> hw:2,0

Evidence:
  shared USB parent path
  matching vendor/product information
  matching device names
```

The grouping layer should enrich discovery. It should not replace the existing individual device views.

## Data Model Additions

### CompositeDevice

Add a model representing a grouped physical or logical device.

Possible shape:

```python
@dataclass
class CompositeDevice:
    id: str
    name: str
    kind: str
    confidence: float
    members: list[DeviceRef]
    evidence: list[GroupingEvidence]
```

Suggested fields:

- `id`: stable identifier suitable for CLI use
- `name`: human-readable name
- `kind`: broad category such as `robot`, `camera-system`, `audio-device`, or `unknown`
- `confidence`: numeric confidence from 0.0 to 1.0
- `members`: related discovered devices
- `evidence`: reasons why the devices were grouped

### DeviceRef

Add a model for a member device reference.

Possible shape:

```python
@dataclass
class DeviceRef:
    role: str
    device_id: str
    path: str | None
    subsystem: str
```

Suggested roles:

```text
camera
audio-input
audio-output
control
sensor
actuator-bus
hid
serial
unknown
```

Suggested subsystems:

```text
v4l2
alsa
gstreamer
usb
udev
serial
hid
unknown
```

### GroupingEvidence

Add a model for evidence used during grouping.

Possible shape:

```python
@dataclass
class GroupingEvidence:
    source: str
    description: str
    strength: float
```

Example evidence:

```text
source: usb-topology
description: camera and audio devices share the same USB parent path
strength: 0.9
```

## Evidence Sources

Grouping should use evidence that can be inspected and explained.

Possible evidence sources:

- same USB parent path
- same USB vendor ID
- same USB product ID
- same USB serial number
- matching manufacturer string
- matching product string
- matching ALSA card name
- matching V4L2 card name
- matching udev properties
- known profile hints
- physical bus topology

The strongest generic signal is usually shared USB topology.

Name matching alone should be treated as weaker evidence because device names can be inconsistent, generic, or duplicated.

## Grouping Strategy

Use a staged approach.

### Stage 1 — Collect Metadata

Extend probes or add a metadata collector to gather grouping-relevant information.

Useful metadata may include:

- subsystem
- device path
- card index
- device index
- vendor ID
- product ID
- manufacturer
- product name
- serial number
- USB bus path
- parent device path
- udev properties when available

### Stage 2 — Build Candidate Groups

Create possible groups using strong evidence first.

Implemented grouping rules:

- devices sharing the same USB parent path
- ALSA capture and playback devices from the same card
- parent USB-family groups when child exact USB-device groups share a meaningful
  USB ancestor, USB vendor ID, and non-generic product-family token

Name matching alone is not grouping evidence. Generic USB product names such as
`USB Audio Device` or `USB Camera` do not create parent groups by themselves.

### Stage 3 — Score Groups

Assign confidence based on evidence strength.

Example scoring:

```text
shared USB parent path       strong
shared serial number         strong
shared vendor/product        medium
matching product names       medium
matching generic names       weak
same ALSA card               strong for audio input/output pairing
```

### Stage 4 — Render Groups

Expose groups in CLI and JSON output.

The CLI should make uncertainty visible rather than pretending every grouping is definitive.

## User-Facing Commands

Milestone 3 group-oriented commands:

```sh
gst-device-explorer groups
gst-device-explorer groups --json
gst-device-explorer groups --metadata
gst-device-explorer groups --metadata --json
gst-device-explorer group <group-id>
gst-device-explorer group <group-id> --json
```

Possible future commands, not required for this milestone:

```sh
gst-device-explorer pipeline group <group-id> camera
gst-device-explorer run group <group-id> camera
```

Those should wait until the group model is proven.

## CLI Output

Example with exact USB-device groups and a parent USB-family group:

```text
Composite devices:
- Reachy Mini Audio
  id: usb-device-1-4-1-1
  kind: unknown
  confidence: 0.90
  members:
    - audio-input: hw:0,0
    - audio-output: hw:0,0
  evidence:
    - usb-topology: devices share USB parent path 1-4.1.1

- Reachy Mini Camera
  id: usb-device-1-4-1-4
  kind: unknown
  confidence: 0.90
  members:
    - camera: /dev/video0
    - camera: /dev/video1
  evidence:
    - usb-topology: devices share USB parent path 1-4.1.4

- Reachy Mini
  id: usb-family-1-4-1
  kind: unknown
  confidence: 0.80
  members:
    - audio-input: hw:0,0
    - audio-output: hw:0,0
    - camera: /dev/video0
    - camera: /dev/video1
  evidence:
    - usb-topology: composite groups share USB ancestor 1-4.1
    - usb-metadata: composite group metadata suggests the same attached product family
```

Separate attached devices that do not share the grouping evidence, such as an
Orbbec Femto Bolt on another USB branch or vendor/product family, remain
independent rather than being folded into the parent USB-family group.

Use `groups --metadata` and `groups --metadata --json` as the diagnostic views
for the normalized records feeding the grouping engine.

Example with no or insufficient group evidence:

```text
No composite device groups found.
```

## JSON Output

Example shape:

```json
{
  "groups": [
    {
      "id": "reachy-mini",
      "name": "Reachy Mini",
      "kind": "robot",
      "confidence": 0.92,
      "members": [
        {
          "role": "camera",
          "device_id": "video:/dev/video0",
          "path": "/dev/video0",
          "subsystem": "v4l2"
        },
        {
          "role": "audio-input",
          "device_id": "alsa:capture:2,0",
          "path": "hw:2,0",
          "subsystem": "alsa"
        },
        {
          "role": "audio-output",
          "device_id": "alsa:playback:2,0",
          "path": "hw:2,0",
          "subsystem": "alsa"
        }
      ],
      "evidence": [
        {
          "source": "usb-topology",
          "description": "camera and audio devices share the same USB parent path",
          "strength": 0.9
        }
      ]
    }
  ]
}
```

## Design Rules

- Group by evidence.
- Preserve raw individual device listings.
- Do not hide uncertainty.
- Do not hard-code Reachy behavior into the generic grouping engine.
- Known devices may be recognized through profile hints, but the grouping engine should remain general.
- Device grouping should enrich discovery, not replace discovery.
- CLI and future GUI remain renderers.
- Grouping should not execute pipelines.
- Grouping should not claim exclusive access to devices.
- Grouping should not require GStreamer to be present.

## Relationship to Profiles

Profiles may eventually help identify known composite devices.

For example, a future Reachy Mini profile might know that a matching camera, microphone, and speaker are expected.

However, the core grouping engine should not require a Reachy-specific profile.

A good split is:

```text
grouping engine:
  finds probable relationships from system evidence

profile hints:
  improve names, roles, and confidence for known devices
```

This avoids hard-coding one robot into the generic discovery path.

## Relationship to Existing Commands

Existing commands should continue to show individual devices:

```sh
gst-device-explorer devices
gst-device-explorer audio-inputs
gst-device-explorer audio-outputs
gst-device-explorer video /dev/video0
```

Milestone 3 adds additional group views:

```sh
gst-device-explorer groups
gst-device-explorer groups --json
gst-device-explorer groups --metadata
gst-device-explorer groups --metadata --json
gst-device-explorer group <group-id>
gst-device-explorer group <group-id> --json
```

The same device may appear both individually and as a member of a group.
Group-based pipeline generation and execution are not part of Milestone 3.

## Testing Status

Implemented tests cover:

- no groups found
- one camera, one audio input, and one audio output grouped
- ALSA capture and playback from the same card grouped
- devices with weak name-only evidence not grouped too aggressively
- exact USB-device groups
- parent USB-family groups
- parent USB-family naming from shared non-generic product-family tokens
- vendor mismatch not producing a parent USB-family group
- generic USB product names not producing parent groups
- stable group IDs
- JSON output structure
- existing device commands remain unchanged

Use fixtures with synthetic device metadata rather than depending on a specific attached robot.

## Acceptance Criteria

Milestone 3 is complete:

- The tool can report zero or more composite device groups.
- Individual devices still appear in existing commands.
- `gst-device-explorer groups` displays grouped devices.
- `gst-device-explorer groups --json` emits structured group data.
- `gst-device-explorer group <group-id>` displays one group.
- Group members include roles such as `camera`, `audio-input`, and `audio-output`.
- Group output includes confidence or evidence.
- Ambiguous grouping is represented honestly.
- Tests cover grouped, ungrouped, and ambiguous cases.
- All existing tests pass.

## Implementation Record

1. Added grouping metadata fields where needed.
2. Added `DeviceRef` model.
3. Added `GroupingEvidence` model.
4. Added `CompositeDevice` model.
5. Added grouping engine using synthetic metadata fixtures.
6. Added ALSA capture/playback same-card grouping.
7. Added USB-topology grouping where metadata is available.
8. Added parent USB-family grouping.
9. Added CLI command: `groups`.
10. Added CLI command: `group <group-id>`.
11. Added JSON output.
12. Added metadata diagnostic views.
13. Added tests.
14. Updated README, setup, architecture, and milestone documentation.

## Future Work

The following should remain outside Milestone 3:

- audio pipeline generation
- group-based pipeline generation
- group-based pipeline execution
- Reachy-specific control APIs
- Dynamixel bus exploration
- serial device probing
- HID controller grouping
- GUI representation of composite devices
- device health monitoring
- latency tests
- recording pipelines

A future milestone can use composite device groups as the foundation for robot-oriented exploration.
