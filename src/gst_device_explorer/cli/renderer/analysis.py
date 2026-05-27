"""Renderers for pipeline analysis, profiles, diagnostics, and validation."""

from __future__ import annotations

from gst_device_explorer.cli.renderer._utils import _print_json, print_json_error
from gst_device_explorer.cli.serializers import (
    candidate_ranking_to_json_dict,
    device_profile_to_json_dict,
    group_validation_to_json_dict,
    pipeline_diagnostic_to_json_dict,
    system_report_to_json_dict,
    to_json_data,
)
from gst_device_explorer.core.errors import ErrorResponse
from gst_device_explorer.core.models import (
    CandidateRanking,
    DeviceProfile,
    GroupValidation,
    PipelineCandidate,
    PipelineDiagnostic,
    SystemReport,
)
from gst_device_explorer.core.suggestions import suggest_group_list


def print_pipeline_candidates(
    candidates: list[PipelineCandidate],
    device_path: str,
    heading: str,
    empty_message: str,
    as_json: bool,
    show_all: bool = False,
    limit: int | None = None,
    json_kind: str = "pipeline_candidates",
) -> None:
    rendered_candidates = _select_pipeline_candidates(
        candidates,
        as_json=as_json,
        show_all=show_all,
        limit=limit,
    )

    if as_json:
        _print_json(json_kind, to_json_data(rendered_candidates))
        return

    if not rendered_candidates:
        print(f"{empty_message} for {device_path}.")
        return

    print(f"{heading} for {device_path}:")
    for index, candidate in enumerate(rendered_candidates, start=1):
        print(f"{index}. {candidate.purpose}")
        if candidate.candidate_id:
            print(f"   id: {candidate.candidate_id}")
        print(f"   command: {candidate.command}")
        print(f"   confidence: {candidate.confidence}")
        if candidate.selected_profile is not None:
            print(f"   profile: {candidate.selected_profile}")
        if candidate.required_elements:
            print(
                "   required elements: "
                + ", ".join(candidate.required_elements)
            )
        if candidate.reasons:
            print("   reasons:")
            for reason in candidate.reasons:
                print(f"   - {reason}")
        if candidate.warnings:
            print("   warnings:")
            for warning in candidate.warnings:
                print(f"   - {warning}")


def print_device_profile(profile: DeviceProfile | None, as_json: bool) -> None:
    if profile is None:
        if as_json:
            _print_json("device_profile", None)
            return
        print("No device profile found.")
        return

    if as_json:
        _print_json("device_profile", device_profile_to_json_dict(profile))
        return

    print(f"Device profile for {profile.device_kind} {profile.device}")
    if profile.display_name is not None:
        print()
        print(f"Name: {profile.display_name}")
    if profile.metadata:
        print()
        print("Metadata:")
        for key in sorted(profile.metadata):
            print(f"  {key}: {profile.metadata[key]}")
    if profile.capabilities_summary:
        print()
        print("Capabilities:")
        _print_capabilities_summary(profile.capabilities_summary)
    print()
    print("Pipeline candidates:")
    for status in ("available", "unavailable"):
        for candidate in profile.candidate_summary.get(status, []):
            print(f"  {status:<11} {candidate.candidate_id}")
            if candidate.missing_elements:
                print("    missing: " + ", ".join(candidate.missing_elements))
    if profile.groups:
        print()
        print("Groups:")
        for group in profile.groups:
            print(f"  {group.label}    confidence {group.confidence:.2f}")
    print()
    print("Suggested next commands:")
    for cmd in profile.suggested_next_commands:
        print(f"  {cmd.command}")


def print_pipeline_diagnostics(
    diagnostics: list[PipelineDiagnostic],
    device_kind: str,
    device_path: str,
    as_json: bool,
) -> None:
    if as_json:
        _print_json(
            "pipeline_diagnostics",
            {
                "device_kind": device_kind,
                "device": device_path,
                "diagnostics": [
                    pipeline_diagnostic_to_json_dict(d)
                    for d in diagnostics
                ],
            },
        )
        return

    if not diagnostics:
        print(f"No pipeline diagnostics found for {device_kind} {device_path}.")
        return

    print(f"Pipeline diagnostics for {device_kind} {device_path}")
    for diagnostic in diagnostics:
        print()
        print(f"Candidate: {diagnostic.candidate_id}")
        print(f"Status: {diagnostic.status}")
        print(f"Reason: {diagnostic.reason}")
        print()
        print("Required elements:")
        for element in diagnostic.required_elements:
            marker = "ok" if element in diagnostic.available_elements else "missing"
            print(f"  {marker}: {element}")
        if diagnostic.suggested_next_checks:
            print()
            print("Suggested checks:")
            for check in diagnostic.suggested_next_checks:
                print(f"  {check}")
        elif diagnostic.status == "available":
            print()
            print("Suggested next step:")
            print(f"  gst-device-explorer run {device_kind} {device_path} --dry-run")


def print_candidate_ranking(ranking: CandidateRanking, as_json: bool) -> None:
    if as_json:
        _print_json("candidate_recommendation", candidate_ranking_to_json_dict(ranking))
        return

    print(f"Recommendations for {ranking.endpoint_kind} {ranking.endpoint}")
    print()

    if ranking.recommended_candidate_id is not None:
        print(f"Recommended: {ranking.recommended_candidate_id}")
    else:
        print("No available candidate.")

    if not ranking.ranked_candidates:
        return

    print()
    for item in ranking.ranked_candidates:
        status = "available" if item.available else "unavailable"
        print(f"{item.rank}. {item.candidate_id}  [{status}]")
        if item.selected_profile is not None:
            print(f"   Profile label: {item.selected_profile}")
        for reason in item.reasons:
            print(f"   Reason: {reason}")
        if item.warnings:
            for warning in item.warnings:
                print(f"   Warning: {warning}")
        if item.missing_elements:
            print(f"   Missing elements: {', '.join(item.missing_elements)}")
            print("   Suggested checks:")
            for element in item.missing_elements:
                print(f"     gst-inspect-1.0 {element}")


def print_system_report(report: SystemReport, as_json: bool) -> None:
    if as_json:
        _print_json("system_report", system_report_to_json_dict(report))
        return

    video_count = len(report.devices.video)
    audio_in_count = len(report.devices.audio_inputs)
    audio_out_count = len(report.devices.audio_outputs)
    group_count = len(report.groups)

    print(f"System report  tool version {report.tool_version}")
    print()
    print(f"Video devices:    {video_count}")
    print(f"Audio inputs:     {audio_in_count}")
    print(f"Audio outputs:    {audio_out_count}")
    print(f"Composite groups: {group_count}")

    if report.diagnostics.missing_elements:
        print()
        print("Missing GStreamer elements:")
        for element in report.diagnostics.missing_elements:
            print(f"  {element}")

    if report.suggested_next_commands:
        print()
        print("Suggested next commands:")
        for cmd in report.suggested_next_commands:
            print(f"  {cmd.command}")


def print_group_validation(validation: GroupValidation, as_json: bool) -> None:
    if as_json:
        _print_json("group_validation", group_validation_to_json_dict(validation))
        return

    print(f"Composite group validation: {validation.group_id}")
    print(f"Status: {validation.status}")
    print(f"Grouping method: {validation.grouping_method}")
    if validation.group_label:
        print(f"Label: {validation.group_label}")

    if validation.evidence:
        print()
        print("Evidence:")
        for evidence in validation.evidence:
            print(f"- {evidence.source}: {evidence.description}")

    print()
    print("Endpoints:")
    if not validation.endpoint_summaries:
        print("- none")
    for summary in validation.endpoint_summaries:
        print(f"- {_endpoint_label(summary.endpoint_kind)}: {summary.endpoint}")
        print(f"  Status: {summary.status}")
        print(f"  Available candidates: {summary.available_candidate_count}")
        print(f"  Unavailable candidates: {summary.unavailable_candidate_count}")
        if summary.recommended_candidate_id is not None:
            print(f"  Recommended: {summary.recommended_candidate_id}")
        if summary.missing_elements:
            print(f"  Missing elements: {', '.join(summary.missing_elements)}")

    if validation.diagnostics.missing_elements:
        print()
        print("Missing elements:")
        for element in validation.diagnostics.missing_elements:
            print(f"- {element}")

    if validation.suggested_next_commands:
        print()
        print("Suggested next commands:")
        for cmd in validation.suggested_next_commands:
            print(f"- {cmd.command}")


def print_group_not_found(group_id: str, as_json: bool) -> None:
    if as_json:
        print_json_error(ErrorResponse(
            code="group_not_found",
            message=f"Group not found: {group_id}",
            details={"group_id": group_id},
            suggested_commands=(suggest_group_list(),),
        ))
        return

    print(f"Group not found: {group_id}")
    print()
    print("Run:")
    print("gst-device-explorer groups")


def _print_capabilities_summary(summary: dict) -> None:
    labels = {
        "formats": "Formats",
        "max_resolution": "Max resolution",
        "frame_rates": "Frame rates",
        "mode_count": "Mode count",
    }
    for key in ("formats", "max_resolution", "frame_rates", "mode_count"):
        if key not in summary:
            continue
        value = summary[key]
        if isinstance(value, list):
            rendered = ", ".join(str(item) for item in value)
        else:
            rendered = str(value)
        print(f"  {labels[key]}: {rendered}")


def _select_pipeline_candidates(
    candidates: list[PipelineCandidate],
    as_json: bool,
    show_all: bool,
    limit: int | None,
) -> list[PipelineCandidate]:
    if limit is not None:
        return candidates[: max(limit, 0)]
    if as_json or show_all:
        return candidates
    return candidates[:3]


def _endpoint_label(endpoint_kind: str) -> str:
    labels = {
        "video": "Video",
        "audio-input": "Audio input",
        "audio-output": "Audio output",
    }
    return labels.get(endpoint_kind, endpoint_kind.replace("-", " ").title())
