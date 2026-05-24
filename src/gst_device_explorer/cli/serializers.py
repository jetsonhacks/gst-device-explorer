"""JSON serialization helpers for gst-device-explorer CLI output."""

from __future__ import annotations

import json
from dataclasses import asdict

from gst_device_explorer.core.grouping import GroupableDevice
from gst_device_explorer.core.models import (
    CandidateRanking,
    CandidateRecommendation,
    Capability,
    CompositeDevice,
    Device,
    DeviceProfile,
    EndpointValidationSummary,
    EnvironmentFact,
    GroupValidation,
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


def candidate_ranking_to_json_dict(ranking: CandidateRanking) -> dict:
    return {
        "endpoint": ranking.endpoint,
        "endpoint_kind": ranking.endpoint_kind,
        "kind": ranking.kind,
        "ranked_candidates": [
            candidate_recommendation_to_json_dict(item)
            for item in ranking.ranked_candidates
        ],
        "recommended_candidate_id": ranking.recommended_candidate_id,
    }


def candidate_recommendation_to_json_dict(item: CandidateRecommendation) -> dict:
    return {
        "available": item.available,
        "candidate_id": item.candidate_id,
        "missing_elements": list(item.missing_elements),
        "rank": item.rank,
        "reasons": list(item.reasons),
        "score": item.score,
        "selected_profile": item.selected_profile,
        "warnings": list(item.warnings),
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


def group_validation_to_json_dict(validation: GroupValidation) -> dict:
    return {
        "diagnostics": {
            "missing_elements": list(validation.diagnostics.missing_elements),
        },
        "endpoint_counts": {
            "audio_inputs": validation.endpoint_counts.audio_inputs,
            "audio_outputs": validation.endpoint_counts.audio_outputs,
            "unknown": validation.endpoint_counts.unknown,
            "video": validation.endpoint_counts.video,
        },
        "endpoint_summaries": [
            endpoint_validation_summary_to_json_dict(summary)
            for summary in validation.endpoint_summaries
        ],
        "evidence": [asdict(evidence) for evidence in validation.evidence],
        "group_id": validation.group_id,
        "group_label": validation.group_label,
        "grouping_method": validation.grouping_method,
        "kind": validation.kind,
        "status": validation.status,
        "suggested_next_commands": list(validation.suggested_next_commands),
        "warnings": list(validation.warnings),
    }


def endpoint_validation_summary_to_json_dict(
    summary: EndpointValidationSummary,
) -> dict:
    return {
        "available_candidate_count": summary.available_candidate_count,
        "endpoint": summary.endpoint,
        "endpoint_kind": summary.endpoint_kind,
        "missing_elements": list(summary.missing_elements),
        "recommended_candidate_id": summary.recommended_candidate_id,
        "status": summary.status,
        "suggested_next_commands": list(summary.suggested_next_commands),
        "unavailable_candidate_count": summary.unavailable_candidate_count,
    }
