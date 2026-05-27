"""Detail pane model builders for cameras, audio endpoints, and groups."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from gst_device_explorer.core.models import (
    CameraControlSet,
    CandidateRanking,
    CompositeDevice,
    Device,
    DeviceProfile,
    GroupValidation,
)
from gst_device_explorer.core.suggestions import (
    SAFETY_INSPECTION,
    suggest_group_list,
    suggest_group_validation,
    suggest_report,
)
from gst_device_explorer.gui.builders_actions import (
    _capture_action,
    _diagnostics_action,
    _dry_run_action,
    _export_report_action,
    _refresh_action,
    _run_action,
)
from gst_device_explorer.gui.builders_utils import (
    _device_target,
    _endpoint_node_id,
    _group_member_keys,
    _group_member_targets,
    _group_node_id,
    _member_key,
    _role_label,
)
from gst_device_explorer.gui.camera import (
    build_camera_explorer_state,
    camera_copy_actions,
    camera_explorer_sections,
)
from gst_device_explorer.gui.model import (
    DetailPaneModel,
    DetailSection,
    GuiAction,
)


def build_detail_pane_for_group(
    group: CompositeDevice,
    *,
    validation: GroupValidation | None = None,
    child_groups: Sequence[CompositeDevice] = (),
) -> DetailPaneModel:
    """Build a group detail pane from an existing composite-device model."""

    child_member_keys = {
        key
        for child_group in child_groups
        for key in _group_member_keys(child_group)
    }
    direct_members = tuple(
        member
        for member in sorted(group.members, key=lambda m: (m.role, m.device_id))
        if _member_key(member.role, member.device_id) not in child_member_keys
    )
    all_members = tuple(sorted(group.members, key=lambda m: (m.role, m.device_id)))
    validation_command = suggest_group_validation(group.id).command
    sections = [
        DetailSection(
            title="Group Summary",
            items=(
                f"Name: {group.name}",
                f"Group id: {group.id}",
                f"Kind: {group.kind}",
                f"Confidence: {group.confidence:.2f}",
                f"Direct endpoints: {len(direct_members) if child_groups else len(all_members)}",
                f"Child groups: {len(child_groups)}",
                f"Total endpoints: {len(all_members)}",
            ),
        ),
        DetailSection(
            title="Endpoints",
            items=tuple(
                f"{_role_label(member.role)}: {member.device_id}"
                for member in all_members
            ),
        ),
        DetailSection(
            title="Direct Endpoints",
            items=tuple(
                f"{_role_label(member.role)}: {member.device_id}"
                for member in direct_members
            )
            or ("No direct endpoints outside child groups.",),
        ),
        DetailSection(
            title="Child Groups",
            items=tuple(
                f"{child.name}: {child.id}, endpoints {_group_member_targets(child)}, confidence {child.confidence:.2f}"
                for child in child_groups
            )
            or ("No child groups inferred.",),
        ),
        DetailSection(
            title="Grouping Evidence",
            items=tuple(
                f"{evidence.description} ({evidence.source}, {evidence.strength:.2f})"
                for evidence in group.evidence
            )
            or ("No grouping evidence was provided.",),
        ),
        DetailSection(
            title="Metadata / Diagnostics",
            items=(
                "No additional group metadata is available."
                if validation is None
                else f"Validation status: {validation.status}",
            ),
        ),
        DetailSection(
            title="Reproduce with CLI",
            items=(
                suggest_group_list().command,
                validation_command,
                suggest_report().command,
            ),
        ),
        DetailSection(
            title="Notes / Limitations",
            items=(
                "Composite groups are informational in the GUI.",
                "Group-based execution and synchronized capture are not available.",
            ),
        ),
    ]
    if validation is not None:
        sections.append(
            DetailSection(
                title="Validation",
                items=(
                    f"Status: {validation.status}",
                    f"Video endpoints: {validation.endpoint_counts.video}",
                    f"Audio inputs: {validation.endpoint_counts.audio_inputs}",
                    f"Audio outputs: {validation.endpoint_counts.audio_outputs}",
                ),
            )
        )
        if validation.diagnostics.missing_elements:
            sections.append(
                DetailSection(
                    title="Missing Elements",
                    items=tuple(validation.diagnostics.missing_elements),
                )
            )

    return DetailPaneModel(
        selected_id=_group_node_id(group.id),
        title=group.name,
        kind="group",
        status=validation.status if validation is not None else "available",
        summary=(
            f"Group id: {group.id}",
            f"Kind: {group.kind}",
            f"Confidence: {group.confidence:.2f}",
            f"Members: {len(group.members)}",
        ),
        sections=tuple(sections),
        actions=(
            _refresh_action(),
            GuiAction(
                id=f"validate-group:{group.id}",
                label="Validate Group",
                kind="validate_group",
                enabled=True,
                safety=SAFETY_INSPECTION,
                target_kind="group",
                target=group.id,
                suggested_command=suggest_group_validation(group.id),
            ),
            _export_report_action(),
        ),
    )


def build_detail_pane_for_video(
    device: Device,
    *,
    profile: DeviceProfile | None = None,
    recommendation: CandidateRanking | None = None,
    control_set: CameraControlSet | None = None,
) -> DetailPaneModel:
    """Build a camera detail pane from already-built endpoint models."""

    target = _device_target(device)
    state = build_camera_explorer_state(device, control_set=control_set)
    return _endpoint_detail(
        selected_id=_endpoint_node_id("video", target),
        title=_display_name(device, profile, fallback=f"Camera {target}"),
        kind="video",
        status=_endpoint_status(profile, recommendation),
        target_kind="video",
        target=target,
        summary=_device_summary(device, profile),
        sections=(
            _raw_camera_capability_section(device),
            *camera_explorer_sections(state),
            *_endpoint_sections(device, profile, recommendation),
        ),
        actions=(
            *camera_copy_actions(state),
            _refresh_action(),
            _diagnostics_action("video", target),
            _dry_run_action("video", target),
            _run_action(
                action_id=f"preview:{target}",
                label="Preview",
                kind="preview",
                target_kind="video",
                target=target,
                enabled=_has_available_candidate(profile, recommendation),
            ),
            _capture_action("video", target),
        ),
    )


def build_detail_pane_for_audio_input(
    device: Device,
    *,
    profile: DeviceProfile | None = None,
    recommendation: CandidateRanking | None = None,
) -> DetailPaneModel:
    """Build an audio-input detail pane from already-built endpoint models."""

    target = _device_target(device)
    return _endpoint_detail(
        selected_id=_endpoint_node_id("audio_input", target),
        title=_display_name(device, profile, fallback=f"Audio Input {target}"),
        kind="audio_input",
        status=_endpoint_status(profile, recommendation),
        target_kind="audio-input",
        target=target,
        summary=_device_summary(device, profile),
        sections=_endpoint_sections(device, profile, recommendation),
        actions=(
            _refresh_action(),
            _diagnostics_action("audio-input", target),
            _dry_run_action("audio-input", target),
            _run_action(
                action_id=f"test-audio-input:{target}",
                label="Test Input",
                kind="test_audio_input",
                target_kind="audio-input",
                target=target,
                enabled=_has_available_candidate(profile, recommendation),
            ),
            _capture_action("audio-input", target),
        ),
    )


def build_detail_pane_for_audio_output(
    device: Device,
    *,
    profile: DeviceProfile | None = None,
    recommendation: CandidateRanking | None = None,
) -> DetailPaneModel:
    """Build an audio-output detail pane from already-built endpoint models."""

    target = _device_target(device)
    return _endpoint_detail(
        selected_id=_endpoint_node_id("audio_output", target),
        title=_display_name(device, profile, fallback=f"Audio Output {target}"),
        kind="audio_output",
        status=_endpoint_status(profile, recommendation),
        target_kind="audio-output",
        target=target,
        summary=_device_summary(device, profile),
        sections=_endpoint_sections(device, profile, recommendation),
        actions=(
            _refresh_action(),
            _diagnostics_action("audio-output", target),
            _dry_run_action("audio-output", target),
            _run_action(
                action_id=f"test-audio-output:{target}",
                label="Test Output",
                kind="test_audio_output",
                target_kind="audio-output",
                target=target,
                enabled=_has_available_candidate(profile, recommendation),
            ),
        ),
    )


def build_unknown_detail_pane(selected_id: str | None = None) -> DetailPaneModel:
    """Build a safe fallback pane for empty or unknown selections."""

    return DetailPaneModel(
        selected_id=selected_id or "selection:none",
        title="No Device Selected" if selected_id is None else "Selection Unavailable",
        kind="unknown",
        status="empty" if selected_id is None else "unavailable",
        summary=(
            "Select a camera, audio endpoint, or composite group to inspect it."
            if selected_id is None
            else f"No GUI model is available for {selected_id}.",
        ),
        sections=(
            DetailSection(
                title="Safe Actions",
                items=("Refresh discovery or inspect generated reports without running pipelines.",),
            ),
        ),
        actions=(_refresh_action(), _export_report_action()),
    )


def _endpoint_detail(
    *,
    selected_id: str,
    title: str,
    kind: str,
    status: str,
    target_kind: str,
    target: str,
    summary: tuple[str, ...],
    sections: tuple[DetailSection, ...],
    actions: tuple[GuiAction, ...],
) -> DetailPaneModel:
    return DetailPaneModel(
        selected_id=selected_id,
        title=title,
        kind=kind,
        status=status,
        summary=summary,
        sections=sections,
        actions=actions,
    )


def _endpoint_sections(
    device: Device,
    profile: DeviceProfile | None,
    recommendation: CandidateRanking | None,
) -> tuple[DetailSection, ...]:
    sections = [
        DetailSection(
            title="Metadata",
            items=tuple(_format_mapping(device.metadata)) or ("No metadata provided.",),
        ),
        DetailSection(
            title="Capabilities",
            items=tuple(_format_capabilities(device)) or ("No capabilities provided.",),
        ),
    ]
    if profile is not None:
        sections.append(
            DetailSection(
                title="Candidate Summary",
                items=tuple(_format_profile_candidates(profile)) or ("No candidate summary provided.",),
            )
        )
        if profile.groups:
            sections.append(
                DetailSection(
                    title="Groups",
                    items=tuple(f"{group.label} ({group.group_id})" for group in profile.groups),
                )
            )
    if recommendation is not None:
        sections.append(
            DetailSection(
                title="Recommendation",
                items=tuple(_format_recommendation(recommendation)),
            )
        )
    return tuple(sections)


def _raw_camera_capability_section(device: Device) -> DetailSection:
    items = []
    for capability in device.capabilities:
        if capability.name != "video_format":
            continue
        values = capability.values
        pixel_format = values.get("pixel_format") or values.get("raw_pixel_format")
        width = values.get("width")
        height = values.get("height")
        if not pixel_format or not isinstance(width, int) or not isinstance(height, int):
            continue
        fps_values = values.get("fps", ())
        if isinstance(fps_values, (int, float)):
            fps_items = (f"{float(fps_values):g}",)
        elif isinstance(fps_values, list):
            fps_items = tuple(f"{float(value):g}" for value in fps_values)
        else:
            fps_items = ()
        fields = [
            f"pixel_format={pixel_format}",
            f"width={width}",
            f"height={height}",
            f"fps={ '|'.join(fps_items) }",
        ]
        description = values.get("description")
        if description:
            fields.append(f"description={description}")
        media_type = values.get("media_type")
        if media_type:
            fields.append(f"media_type={media_type}")
        source = capability.source
        if source:
            fields.append(f"source={source}")
        items.append("; ".join(fields))
    return DetailSection(
        title="Raw Camera Capabilities",
        items=tuple(items) or ("No raw V4L2 camera capabilities discovered.",),
    )


def _format_mapping(mapping: dict[str, object]) -> Iterable[str]:
    for key in sorted(mapping):
        yield f"{key}: {mapping[key]}"


def _format_capabilities(device: Device) -> Iterable[str]:
    for capability in device.capabilities:
        if capability.values:
            values = ", ".join(f"{key}={capability.values[key]}" for key in sorted(capability.values))
            yield f"{capability.name}: {values}"
        else:
            yield capability.name


def _format_profile_candidates(profile: DeviceProfile) -> Iterable[str]:
    for status in ("available", "unavailable"):
        for candidate in profile.candidate_summary.get(status, []):
            yield f"{status}: {candidate.candidate_id} - {candidate.reason}"


def _format_recommendation(recommendation: CandidateRanking) -> Iterable[str]:
    if recommendation.recommended_candidate_id is not None:
        yield f"Recommended: {recommendation.recommended_candidate_id}"
    for candidate in recommendation.ranked_candidates:
        availability = "available" if candidate.available else "unavailable"
        yield f"#{candidate.rank} {candidate.candidate_id}: {availability}, score {candidate.score}"


def _endpoint_status(
    profile: DeviceProfile | None,
    recommendation: CandidateRanking | None,
) -> str:
    if _has_available_candidate(profile, recommendation):
        return "available"
    if profile is None and recommendation is None:
        return "unknown"
    return "limited"


def _has_available_candidate(
    profile: DeviceProfile | None,
    recommendation: CandidateRanking | None,
) -> bool:
    if recommendation is not None:
        return any(candidate.available for candidate in recommendation.ranked_candidates)
    if profile is not None:
        return bool(profile.candidate_summary.get("available"))
    return False


def _display_name(device: Device, profile: DeviceProfile | None, *, fallback: str) -> str:
    if device.kind == "video_input" and profile is not None and profile.groups:
        group_label = profile.groups[0].label
        if "camera" in group_label.lower():
            return group_label
        return f"{group_label} Camera"
    if profile is not None and profile.display_name:
        return profile.display_name
    if device.name:
        return device.name
    return fallback


def _device_summary(device: Device, profile: DeviceProfile | None) -> tuple[str, ...]:
    items = [
        f"Endpoint: {_device_target(device)}",
        f"Device kind: {device.kind}",
    ]
    if profile is not None:
        items.append(f"Profile kind: {profile.device_kind}")
    return tuple(items)
