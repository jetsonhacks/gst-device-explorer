"""JSON serialization helpers for gst-device-explorer CLI output."""

from __future__ import annotations

import json
from dataclasses import asdict

from gst_device_explorer.core.grouping import GroupableDevice
from gst_device_explorer.core.models import (
    Capability,
    CompositeDevice,
    Device,
    DeviceProfile,
    EnvironmentFact,
    PipelineCandidate,
    PipelineDiagnostic,
    ProfileGroupSummary,
    SystemReport,
)


def to_json(
    items: list[Device]
    | list[EnvironmentFact]
    | list[Capability]
    | list[PipelineCandidate]
    | list[CompositeDevice]
    | list[GroupableDevice],
) -> str:
    if items and isinstance(items[0], PipelineCandidate):
        return json.dumps(
            [pipeline_candidate_to_json_dict(item) for item in items],
            indent=2,
            sort_keys=True,
        )
    return json.dumps([asdict(item) for item in items], indent=2, sort_keys=True)


def pipeline_candidate_to_json_dict(candidate: PipelineCandidate) -> dict:
    return {
        "argv": candidate.argv,
        "candidate_id": candidate.candidate_id,
        "command": candidate.command,
        "confidence": candidate.confidence,
        "purpose": candidate.purpose,
        "reasons": candidate.reasons,
        "required_elements": candidate.required_elements,
        "selected_profile": candidate.selected_profile,
        "warnings": candidate.warnings,
    }


def pipeline_diagnostic_to_json_dict(diagnostic: PipelineDiagnostic) -> dict:
    return {
        "available_elements": diagnostic.available_elements,
        "candidate_id": diagnostic.candidate_id,
        "missing_elements": diagnostic.missing_elements,
        "reason": diagnostic.reason,
        "required_elements": diagnostic.required_elements,
        "status": diagnostic.status,
        "suggested_next_checks": diagnostic.suggested_next_checks,
    }


def device_profile_to_json_dict(profile: DeviceProfile) -> dict:
    return {
        "candidate_summary": {
            "available": [
                profile_candidate_summary_to_json_dict(c)
                for c in profile.candidate_summary.get("available", [])
            ],
            "unavailable": [
                profile_candidate_summary_to_json_dict(c)
                for c in profile.candidate_summary.get("unavailable", [])
            ],
        },
        "capabilities_summary": profile.capabilities_summary,
        "device": profile.device,
        "device_kind": profile.device_kind,
        "display_name": profile.display_name,
        "groups": [profile_group_summary_to_json_dict(g) for g in profile.groups],
        "metadata": profile.metadata,
        "suggested_next_commands": profile.suggested_next_commands,
    }


def profile_candidate_summary_to_json_dict(candidate) -> dict:
    return {
        "candidate_id": candidate.candidate_id,
        "missing_elements": candidate.missing_elements,
        "reason": candidate.reason,
        "status": candidate.status,
    }


def profile_group_summary_to_json_dict(group: ProfileGroupSummary) -> dict:
    return {
        "confidence": group.confidence,
        "group_id": group.group_id,
        "kind": group.kind,
        "label": group.label,
        "member_count": group.member_count,
    }


def system_report_to_json_dict(report: SystemReport) -> dict:
    return {
        "kind": report.kind,
        "tool_version": report.tool_version,
        "environment": [asdict(f) for f in report.environment],
        "devices": {
            "audio_inputs": [asdict(d) for d in report.devices.audio_inputs],
            "audio_outputs": [asdict(d) for d in report.devices.audio_outputs],
            "video": [asdict(d) for d in report.devices.video],
        },
        "groups": [asdict(g) for g in report.groups],
        "profiles": {
            "audio_inputs": [
                device_profile_to_json_dict(p) for p in report.profiles.audio_inputs
            ],
            "audio_outputs": [
                device_profile_to_json_dict(p) for p in report.profiles.audio_outputs
            ],
            "video": [
                device_profile_to_json_dict(p) for p in report.profiles.video
            ],
        },
        "diagnostics": {
            "missing_elements": list(report.diagnostics.missing_elements),
        },
        "suggested_next_commands": list(report.suggested_next_commands),
    }
