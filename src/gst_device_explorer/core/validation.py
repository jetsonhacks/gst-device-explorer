"""Composite device validation builders."""

from __future__ import annotations

from gst_device_explorer.core.models import (
    CompositeDevice,
    DeviceProfile,
    DeviceRef,
    EndpointValidationSummary,
    GroupValidation,
    GroupValidationDiagnostics,
    GroupValidationEndpointCounts,
)
from gst_device_explorer.core.suggestions import SuggestedCommand, suggest_profile


def build_group_validation(
    group: CompositeDevice,
    endpoint_profiles: list[DeviceProfile],
) -> GroupValidation:
    """Build a group validation summary from already-gathered profile data."""

    endpoint_summaries = [
        _endpoint_summary(member, _find_profile(member, endpoint_profiles))
        for member in group.members
    ]
    missing_elements = _aggregate_missing_elements(endpoint_summaries)
    suggested_next_commands = _deduplicate_commands(endpoint_summaries)

    return GroupValidation(
        kind="group_validation",
        group_id=group.id,
        group_label=group.name,
        grouping_method=group.kind,
        status=_group_status(endpoint_summaries),
        evidence=list(group.evidence),
        endpoint_counts=_endpoint_counts(endpoint_summaries),
        endpoint_summaries=endpoint_summaries,
        diagnostics=GroupValidationDiagnostics(missing_elements=missing_elements),
        suggested_next_commands=suggested_next_commands,
        warnings=[],
    )


def _endpoint_summary(
    member: DeviceRef,
    profile: DeviceProfile | None,
) -> EndpointValidationSummary:
    endpoint_kind = _endpoint_kind(member.role)
    endpoint = member.path or member.device_id

    if profile is None:
        return EndpointValidationSummary(
            endpoint_kind=endpoint_kind,
            endpoint=endpoint,
            status="unknown",
            suggested_next_commands=_default_suggested_commands(endpoint_kind, endpoint),
        )

    available = profile.candidate_summary.get("available", [])
    unavailable = profile.candidate_summary.get("unavailable", [])
    missing_elements = _missing_elements_from_profile(profile)

    return EndpointValidationSummary(
        endpoint_kind=endpoint_kind,
        endpoint=endpoint,
        status=_endpoint_status(len(available), len(unavailable)),
        available_candidate_count=len(available),
        unavailable_candidate_count=len(unavailable),
        recommended_candidate_id=available[0].candidate_id if available else None,
        missing_elements=missing_elements,
        suggested_next_commands=list(profile.suggested_next_commands),
    )


def _find_profile(
    member: DeviceRef,
    profiles: list[DeviceProfile],
) -> DeviceProfile | None:
    endpoint_kind = _endpoint_kind(member.role)
    endpoint = member.path or member.device_id
    return next(
        (
            profile
            for profile in profiles
            if profile.device_kind == endpoint_kind
            and (profile.device == endpoint or profile.device == member.device_id)
        ),
        None,
    )


def _endpoint_kind(role: str) -> str:
    if role == "camera":
        return "video"
    return role


def _endpoint_status(available_count: int, unavailable_count: int) -> str:
    if available_count > 0:
        return "ok"
    if unavailable_count > 0:
        return "candidates_unavailable"
    return "no_candidates"


def _group_status(endpoint_summaries: list[EndpointValidationSummary]) -> str:
    if not endpoint_summaries:
        return "unknown"

    statuses = [summary.status for summary in endpoint_summaries]
    if all(status == "ok" for status in statuses):
        return "ok"
    if any(status == "ok" for status in statuses):
        return "partial"
    if all(status in {"no_candidates", "candidates_unavailable"} for status in statuses):
        return "unavailable"
    return "unknown"


def _endpoint_counts(
    endpoint_summaries: list[EndpointValidationSummary],
) -> GroupValidationEndpointCounts:
    return GroupValidationEndpointCounts(
        video=sum(1 for summary in endpoint_summaries if summary.endpoint_kind == "video"),
        audio_inputs=sum(
            1 for summary in endpoint_summaries if summary.endpoint_kind == "audio-input"
        ),
        audio_outputs=sum(
            1 for summary in endpoint_summaries if summary.endpoint_kind == "audio-output"
        ),
        unknown=sum(
            1
            for summary in endpoint_summaries
            if summary.endpoint_kind not in {"video", "audio-input", "audio-output"}
        ),
    )


def _missing_elements_from_profile(profile: DeviceProfile) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for candidate in profile.candidate_summary.get("unavailable", []):
        for element in candidate.missing_elements:
            if element not in seen:
                seen.add(element)
                result.append(element)
    return result


def _aggregate_missing_elements(
    endpoint_summaries: list[EndpointValidationSummary],
) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for summary in endpoint_summaries:
        for element in summary.missing_elements:
            if element not in seen:
                seen.add(element)
                result.append(element)
    return result


def _deduplicate_commands(
    endpoint_summaries: list[EndpointValidationSummary],
) -> list[SuggestedCommand]:
    seen: set[str] = set()
    result: list[SuggestedCommand] = []
    for summary in endpoint_summaries:
        for cmd in summary.suggested_next_commands:
            if cmd.id not in seen:
                seen.add(cmd.id)
                result.append(cmd)
    return result


def _default_suggested_commands(
    endpoint_kind: str,
    endpoint: str,
) -> list[SuggestedCommand]:
    if endpoint_kind in {"video", "audio-input", "audio-output"}:
        return [suggest_profile(endpoint_kind, endpoint)]
    return []
