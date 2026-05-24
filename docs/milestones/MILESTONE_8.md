# Milestone 8 — Candidate Ranking and Recommendations

Status: Complete

Target version: v0.8.0

## Theme

Choose the best candidate to try first.

## Goal

Add recommendation behavior that ranks existing pipeline candidates and explains why one candidate is suggested before another.

The goal is not to create new pipelines. The goal is to help users decide which existing generated candidate is the best first thing to inspect, dry-run, or run.

Milestone 8 should build on the existing candidate, diagnostic, profile, and report work without changing the safety model.

## Why This Matters

By Milestone 7, `gst-device-explorer` can:

- discover audio and video endpoints
- generate structured pipeline candidates
- safely run selected bounded candidates
- explain candidate availability
- summarize endpoint profiles
- export a whole-system report

The next practical step is helping the user answer:

```text
Which candidate should I try first?
```

Ranking makes the tool more useful for field debugging without making it magical.

## Guiding Principles

Milestone 8 should continue the existing project principles:

- Probe first, build later.
- Normalize raw system output into structured models before making decisions.
- Treat pipeline candidates as structured objects, not just strings.
- Treat CLI, JSON, future GUI, and future agent integrations as renderers over shared core models.
- Prefer capability detection over hard-coded JetPack version checks.
- Avoid Reachy-specific behavior.
- Avoid arbitrary user-supplied pipeline execution.
- Keep grouping evidence-based and explainable.
- Keep each milestone narrow and testable.
- Use synthetic tests that do not require real hardware.

Milestone 8 should also follow these recommendation-specific principles:

- Rank only existing generated candidates.
- Explain every recommendation.
- Prefer available candidates over unavailable candidates.
- Prefer safer, simpler, more broadly compatible candidates when appropriate.
- Prefer platform-accelerated candidates only when the required elements and capabilities are present.
- Do not hide lower-ranked candidates.
- Do not make group-level execution decisions.
- Do not automatically run the recommended candidate.

## Terminology

Milestone 8 should use the clarified profile terminology.

### Candidate Profile Label

A candidate profile label is a string stored on a pipeline candidate, such as:

```text
generic-linux-video-preview
jetson-video-preview
generic-alsa-audio-input-test
generic-alsa-audio-output-test
```

These labels identify the candidate generation strategy. They are metadata on candidates. They are not policy objects consumed by pipeline builders.

### DeviceProfile

A `DeviceProfile` is an endpoint summary built after discovery and candidate generation. It summarizes device facts, capabilities, candidate summaries, diagnostics, group membership, and suggested commands.

A `DeviceProfile` does not control pipeline generation.

### Future Platform-Policy Profile

A richer platform-policy Profile layer may be added later, where named objects express preferences for particular platforms or workflows and are consumed by pipeline builders.

That is not part of Milestone 8.

## First Implementation Slice

The first slice should add a small recommendation model and ranking function for already-generated candidates.

Recommended scope:

- Add a structured recommendation model, perhaps named `CandidateRecommendation`.
- Add a ranking result model, perhaps named `CandidateRanking`.
- Add a pure ranking helper that accepts existing candidate summaries or diagnostics.
- Rank candidates for a single endpoint.
- Include recommendation reasons.
- Include warning or limitation reasons when a candidate is not recommended.
- Add JSON output.
- Add compact text output.
- Add CLI commands for video, audio input, and audio output recommendations.

Possible commands:

```sh
gst-device-explorer recommend video /dev/video0
gst-device-explorer recommend video /dev/video0 --json

gst-device-explorer recommend audio-input hw:0,0
gst-device-explorer recommend audio-input hw:0,0 --json

gst-device-explorer recommend audio-output hw:0,0
gst-device-explorer recommend audio-output hw:0,0 --json
```

The first slice should not add group-level recommendation behavior.

## Recommendation Contents

A recommendation result should include:

- endpoint kind
- endpoint identifier
- recommended candidate ID, if one is available
- recommended candidate description or label
- selected candidate profile label
- rank position
- score or priority value, if useful
- recommendation reasons
- unavailable or skipped reasons
- all ranked candidates, not just the winner

A JSON shape might look like this:

```json
{
  "kind": "candidate_ranking",
  "endpoint_kind": "video",
  "endpoint": "/dev/video0",
  "recommended_candidate_id": "video-preview-jetson-mjpeg",
  "ranked_candidates": [
    {
      "candidate_id": "video-preview-jetson-mjpeg",
      "rank": 1,
      "selected_profile": "jetson-video-preview",
      "available": true,
      "score": 90,
      "reasons": [
        "Device exposes MJPEG capability",
        "NVIDIA decoder element is available",
        "NVIDIA display sink is available"
      ],
      "warnings": []
    }
  ]
}
```

This is only a starting point. The implementation should follow existing project model and JSON conventions.

## Ranking Rules

The first implementation should keep ranking simple and explainable.

Possible ranking factors:

- candidate is available
- candidate has no missing required GStreamer elements
- candidate matches device capabilities
- candidate uses a broadly available generic path
- candidate uses Jetson/NVIDIA acceleration when required elements are present
- candidate is a bounded test candidate
- candidate has a clear safe dry-run/run command
- candidate has fewer warnings

Ranking should not depend on hard-coded JetPack versions.

Ranking should not require benchmarking.

Ranking should not inspect live media output.

Ranking should not require real hardware in tests.

## Text Output Direction

Text output should be compact and useful.

Possible text output:

```text
Recommended candidate for video /dev/video0

1. jetson-video-preview-mjpeg
   Status: available
   Profile label: jetson-video-preview
   Reason: Device exposes MJPEG; NVIDIA decoder and display sink are available.

Other candidates:
2. generic-linux-video-preview
   Status: available
   Reason: Generic fallback preview path is available.
```

If no candidate is available, the command should explain why:

```text
No available candidate found for video /dev/video0.

Missing elements:
- nvv4l2decoder
- nveglglessink

Suggested checks:
- gst-inspect-1.0 nvv4l2decoder
- gst-inspect-1.0 nveglglessink
```

## JSON-First Direction

Milestone 8 should provide machine-readable recommendation output because recommendations will be useful for:

- scripts
- reports
- future GUI tools
- future TUI tools
- future agent integrations
- documentation examples

The JSON does not need to be declared stable yet. Formal schema versioning is deferred to the later schema-stability milestone.

## Documentation

Update documentation to describe:

- what recommendation does
- what recommendation does not do
- how recommendation relates to existing candidates
- how recommendation relates to diagnostics
- how candidate profile labels are used as metadata
- how to inspect all candidates if the user disagrees with the recommendation
- how to dry-run or run a selected candidate explicitly

Likely documentation targets:

- `README.md`
- `docs/SETUP.md`
- `docs/milestones/MILESTONE_8.md`
- `docs/PIPELINE_CANDIDATES.md`, if recommendation needs to be mentioned there

## Tests

Use synthetic tests.

Tests should verify:

- available candidates rank above unavailable candidates
- missing elements lower candidate rank
- recommendation reasons are included
- warnings or unavailable reasons are included
- candidate profile labels are preserved as metadata
- JSON output has the expected top-level shape
- text output includes the recommended candidate and reasons
- video recommendation CLI works with mocked discovery/probe functions
- audio input recommendation CLI works with mocked discovery/probe functions
- audio output recommendation CLI works with mocked discovery/probe functions
- recommendation does not execute pipelines
- existing pipeline, profile, diagnostic, report, and execution behavior remains unchanged

Tests should not require:

- a real camera
- a real microphone
- a real speaker
- GStreamer hardware access
- ALSA hardware access
- Jetson-specific hardware
- Reachy Mini hardware

## Non-Goals

Milestone 8 should not add:

- new video pipeline families
- new audio pipeline families
- arbitrary user-supplied pipelines
- automatic pipeline execution
- benchmark-based ranking
- recording media
- capture tests
- synchronized audio/video behavior
- group-based execution
- group-based pipeline generation
- group-level recommendation
- user preference files
- configuration files
- platform-policy Profile objects
- package installation
- system configuration changes
- PulseAudio support
- PipeWire support
- ASR
- TTS
- WebRTC
- GUI behavior
- TUI behavior
- MCP or agent descriptor generation
- Reachy-specific hard-coding
- JetPack-version-specific hard-coding

## Deferred Work

Possible follow-on work after the first slice:

- group-level recommendations
- recommendation summaries inside `SystemReport`
- recommendation-aware `DeviceProfile` output
- configurable ranking preferences
- preferred sink preferences
- preferred acceleration preferences
- formal recommendation schema
- report comparison workflow
- integration with presets
- integration with future capture tests
- GUI/TUI recommendation display
- agent-facing recommendation consumption

## Completion Criteria

Milestone 8 can be considered complete when:

- a structured recommendation/ranking model exists
- a pure ranking helper ranks existing candidates without probing or execution
- recommendation reasons are included
- unavailable candidates are explained
- `gst-device-explorer recommend video <device>` works
- `gst-device-explorer recommend audio-input <device>` works
- `gst-device-explorer recommend audio-output <device>` works
- `--json` output works for recommendation commands
- compact text output works for recommendation commands
- synthetic tests cover ranking and CLI behavior
- recommendation does not execute pipelines
- documentation describes scope and non-goals
- the full test suite passes

## Validation Command

Run:

```sh
/home/jim/.local/bin/uv run python -m pytest
```

Expected final Codex report should include:

- files changed
- recommendation model added
- ranking behavior added
- CLI behavior added
- JSON shape chosen
- text output behavior
- tests added
- test result
- deferred work
