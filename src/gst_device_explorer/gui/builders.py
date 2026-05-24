"""Pure builders for toolkit-neutral GUI models."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from gst_device_explorer.core.models import (
    CandidateRanking,
    CompositeDevice,
    Device,
    DeviceProfile,
    GroupValidation,
)
from gst_device_explorer.core.suggestions import (
    SAFETY_BOUNDED_CAPTURE,
    SAFETY_DRY_RUN,
    SAFETY_INSPECTION,
    SAFETY_SAFE_EXECUTION,
    SuggestedCommand,
    suggest_audio_input_pipeline_diagnostics,
    suggest_audio_input_run_dry_run,
    suggest_audio_output_pipeline_diagnostics,
    suggest_audio_output_run_dry_run,
    suggest_devices_command,
    suggest_group_validation,
    suggest_report,
    suggest_video_pipeline_diagnostics,
    suggest_video_run_dry_run,
)
from gst_device_explorer.gui.model import (
    DetailPaneModel,
    DetailSection,
    GuiAction,
    MediaExplorerSnapshot,
    SidebarNode,
)


def build_sidebar_model(
    *,
    video_devices: Sequence[Device] = (),
    audio_inputs: Sequence[Device] = (),
    audio_outputs: Sequence[Device] = (),
    groups: Sequence[CompositeDevice] = (),
) -> tuple[SidebarNode, ...]:
    """Build the root sidebar tree without probing or executing anything."""

    root = SidebarNode(
        id="root:devices",
        label="Devices",
        kind="root",
        status=_overall_sidebar_status(video_devices, audio_inputs, audio_outputs, groups),
        children=(
            _section_node(
                node_id="section:composite-groups",
                label="Composite Groups",
                children=tuple(_group_node(group) for group in sorted(groups, key=lambda g: g.id)),
            ),
            _section_node(
                node_id="section:cameras",
                label="Cameras",
                children=tuple(
                    _endpoint_node("video", device) for device in sorted(video_devices, key=lambda d: d.id)
                ),
            ),
            _section_node(
                node_id="section:audio-inputs",
                label="Audio Inputs",
                children=tuple(
                    _endpoint_node("audio_input", device)
                    for device in sorted(audio_inputs, key=lambda d: d.id)
                ),
            ),
            _section_node(
                node_id="section:audio-outputs",
                label="Audio Outputs",
                children=tuple(
                    _endpoint_node("audio_output", device)
                    for device in sorted(audio_outputs, key=lambda d: d.id)
                ),
            ),
        ),
        summary=_sidebar_summary(video_devices, audio_inputs, audio_outputs, groups),
    )
    return (root,)


def build_media_explorer_snapshot(
    *,
    video_devices: Sequence[Device] = (),
    audio_inputs: Sequence[Device] = (),
    audio_outputs: Sequence[Device] = (),
    groups: Sequence[CompositeDevice] = (),
    profiles: Sequence[DeviceProfile] = (),
    validations: Sequence[GroupValidation] = (),
    recommendations: Sequence[CandidateRanking] = (),
    selected_id: str | None = None,
    generated_at: str | None = None,
) -> MediaExplorerSnapshot:
    """Build a renderable GUI snapshot from already-discovered core models."""

    sidebar_roots = build_sidebar_model(
        video_devices=video_devices,
        audio_inputs=audio_inputs,
        audio_outputs=audio_outputs,
        groups=groups,
    )
    detail = _detail_for_selection(
        selected_id=selected_id,
        video_devices=video_devices,
        audio_inputs=audio_inputs,
        audio_outputs=audio_outputs,
        groups=groups,
        profiles=profiles,
        validations=validations,
        recommendations=recommendations,
    )
    return MediaExplorerSnapshot(
        sidebar_roots=sidebar_roots,
        selected_node_id=selected_id,
        detail_pane=detail,
        status=detail.status,
        summary=(
            _sidebar_summary(video_devices, audio_inputs, audio_outputs, groups),
        ),
        generated_at=generated_at,
    )


def build_detail_pane_for_group(
    group: CompositeDevice,
    *,
    validation: GroupValidation | None = None,
) -> DetailPaneModel:
    """Build a group detail pane from an existing composite-device model."""

    sections = [
        DetailSection(
            title="Endpoints",
            items=tuple(
                f"{_role_label(member.role)}: {member.device_id}"
                for member in sorted(group.members, key=lambda m: (m.role, m.device_id))
            ),
        ),
        DetailSection(
            title="Grouping Evidence",
            items=tuple(
                f"{evidence.description} ({evidence.source}, {evidence.strength:.2f})"
                for evidence in group.evidence
            )
            or ("No grouping evidence was provided.",),
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
) -> DetailPaneModel:
    """Build a camera detail pane from already-built endpoint models."""

    target = _device_target(device)
    return _endpoint_detail(
        selected_id=_endpoint_node_id("video", target),
        title=_display_name(device, profile, fallback=f"Camera {target}"),
        kind="video",
        status=_endpoint_status(profile, recommendation),
        target_kind="video",
        target=target,
        summary=_device_summary(device, profile),
        sections=_endpoint_sections(device, profile, recommendation),
        actions=(
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


def _detail_for_selection(
    *,
    selected_id: str | None,
    video_devices: Sequence[Device],
    audio_inputs: Sequence[Device],
    audio_outputs: Sequence[Device],
    groups: Sequence[CompositeDevice],
    profiles: Sequence[DeviceProfile],
    validations: Sequence[GroupValidation],
    recommendations: Sequence[CandidateRanking],
) -> DetailPaneModel:
    if selected_id is None:
        return build_unknown_detail_pane(None)

    group_by_id = {group.id: group for group in groups}
    validation_by_group = {validation.group_id: validation for validation in validations}
    profiles_by_key = {(_profile_kind(profile.device_kind), profile.device): profile for profile in profiles}
    rankings_by_key = {
        (_profile_kind(ranking.endpoint_kind), ranking.endpoint): ranking
        for ranking in recommendations
    }

    if selected_id.startswith("group:"):
        group_id = selected_id.removeprefix("group:")
        group = group_by_id.get(group_id)
        if group is not None:
            return build_detail_pane_for_group(
                group,
                validation=validation_by_group.get(group.id),
            )

    for node_kind, devices, builder in (
        ("video", video_devices, build_detail_pane_for_video),
        ("audio_input", audio_inputs, build_detail_pane_for_audio_input),
        ("audio_output", audio_outputs, build_detail_pane_for_audio_output),
    ):
        prefix = f"{node_kind}:"
        if selected_id.startswith(prefix):
            target = selected_id.removeprefix(prefix)
            device = _find_device(devices, target)
            if device is not None:
                profile_key = (_target_kind_for_node(node_kind), target)
                return builder(
                    device,
                    profile=profiles_by_key.get(profile_key),
                    recommendation=rankings_by_key.get(profile_key),
                )

    return build_unknown_detail_pane(selected_id)


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


def _section_node(node_id: str, label: str, children: tuple[SidebarNode, ...]) -> SidebarNode:
    return SidebarNode(
        id=node_id,
        label=label,
        kind="section",
        status="available" if children else "empty",
        children=children,
        summary=f"{len(children)} item(s)",
    )


def _group_node(group: CompositeDevice) -> SidebarNode:
    return SidebarNode(
        id=_group_node_id(group.id),
        label=group.name,
        kind="group",
        status="available",
        target_kind="group",
        target=group.id,
        summary=f"{len(group.members)} endpoint(s), confidence {group.confidence:.2f}",
        children=tuple(
            _group_member_node(group.id, member.role, member.device_id)
            for member in sorted(group.members, key=lambda m: (m.role, m.device_id))
        ),
    )


def _group_member_node(group_id: str, role: str, device_id: str) -> SidebarNode:
    node_kind = _node_kind_from_role(role)
    return SidebarNode(
        id=f"{_group_node_id(group_id)}:{node_kind}:{device_id}",
        label=f"{_role_label(role)} {device_id}",
        kind=node_kind,
        status="available",
        target_kind=_target_kind_for_node(node_kind),
        target=device_id,
        summary=f"Member of {group_id}",
    )


def _endpoint_node(node_kind: str, device: Device) -> SidebarNode:
    target = _device_target(device)
    return SidebarNode(
        id=_endpoint_node_id(node_kind, target),
        label=_endpoint_label(node_kind, device),
        kind=node_kind,
        status=str(device.metadata.get("status", "available")),
        target_kind=_target_kind_for_node(node_kind),
        target=target,
        summary=device.name,
    )


def _group_node_id(group_id: str) -> str:
    return f"group:{group_id}"


def _endpoint_node_id(node_kind: str, target: str) -> str:
    return f"{node_kind}:{target}"


def _node_kind_from_role(role: str) -> str:
    return {
        "camera": "video",
        "video": "video",
        "video_input": "video",
        "audio-input": "audio_input",
        "audio_input": "audio_input",
        "audio-output": "audio_output",
        "audio_output": "audio_output",
    }.get(role, "section")


def _target_kind_for_node(node_kind: str) -> str:
    return {
        "video": "video",
        "audio_input": "audio-input",
        "audio_output": "audio-output",
    }.get(node_kind, node_kind)


def _profile_kind(kind: str) -> str:
    return {
        "audio_input": "audio-input",
        "audio_output": "audio-output",
        "video_input": "video",
    }.get(kind, kind)


def _role_label(role: str) -> str:
    return {
        "camera": "Camera",
        "video": "Camera",
        "video_input": "Camera",
        "audio-input": "Audio Input",
        "audio_input": "Audio Input",
        "audio-output": "Audio Output",
        "audio_output": "Audio Output",
    }.get(role, role.replace("_", " ").replace("-", " ").title())


def _endpoint_label(node_kind: str, device: Device) -> str:
    prefix = {
        "video": "Camera",
        "audio_input": "Audio Input",
        "audio_output": "Audio Output",
    }[node_kind]
    return f"{prefix} {_device_target(device)}"


def _device_target(device: Device) -> str:
    value = device.metadata.get("path") if device.kind == "video_input" else None
    if isinstance(value, str) and value:
        return value
    return device.id


def _display_name(device: Device, profile: DeviceProfile | None, *, fallback: str) -> str:
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


def _find_device(devices: Sequence[Device], target: str) -> Device | None:
    for device in devices:
        if device.id == target or _device_target(device) == target:
            return device
    return None


def _refresh_action() -> GuiAction:
    return GuiAction(
        id="refresh:devices",
        label="Refresh",
        kind="refresh",
        enabled=True,
        safety=SAFETY_INSPECTION,
        suggested_command=suggest_devices_command(),
    )


def _export_report_action() -> GuiAction:
    return GuiAction(
        id="export:report",
        label="Export Report",
        kind="export_report",
        enabled=True,
        safety=SAFETY_INSPECTION,
        suggested_command=suggest_report(),
    )


def _diagnostics_action(target_kind: str, target: str) -> GuiAction:
    suggestion = {
        "video": suggest_video_pipeline_diagnostics,
        "audio-input": suggest_audio_input_pipeline_diagnostics,
        "audio-output": suggest_audio_output_pipeline_diagnostics,
    }[target_kind](target)
    return GuiAction(
        id=f"diagnostics:{target_kind}:{target}",
        label="Show Diagnostics",
        kind="show_diagnostics",
        enabled=True,
        safety=SAFETY_INSPECTION,
        target_kind=target_kind,
        target=target,
        suggested_command=suggestion,
    )


def _dry_run_action(target_kind: str, target: str) -> GuiAction:
    suggestion = {
        "video": suggest_video_run_dry_run,
        "audio-input": suggest_audio_input_run_dry_run,
        "audio-output": suggest_audio_output_run_dry_run,
    }[target_kind](target)
    return GuiAction(
        id=f"dry-run:{target_kind}:{target}",
        label="Dry Run",
        kind="dry_run",
        enabled=True,
        safety=SAFETY_DRY_RUN,
        target_kind=target_kind,
        target=target,
        suggested_command=suggestion,
    )


def _run_action(
    *,
    action_id: str,
    label: str,
    kind: str,
    target_kind: str,
    target: str,
    enabled: bool,
) -> GuiAction:
    return GuiAction(
        id=action_id,
        label=label,
        kind=kind,
        enabled=enabled,
        safety=SAFETY_SAFE_EXECUTION,
        target_kind=target_kind,
        target=target,
        suggested_command=None,
        disabled_reason=None if enabled else "No available generated candidate is known yet.",
    )


def _capture_action(target_kind: str, target: str) -> GuiAction:
    return GuiAction(
        id=f"capture:{target_kind}:{target}",
        label="Capture",
        kind="capture",
        enabled=False,
        safety=SAFETY_BOUNDED_CAPTURE,
        target_kind=target_kind,
        target=target,
        suggested_command=None,
        disabled_reason="Choose an explicit output path before capture.",
    )


def _overall_sidebar_status(
    video_devices: Sequence[Device],
    audio_inputs: Sequence[Device],
    audio_outputs: Sequence[Device],
    groups: Sequence[CompositeDevice],
) -> str:
    if video_devices or audio_inputs or audio_outputs or groups:
        return "available"
    return "empty"


def _sidebar_summary(
    video_devices: Sequence[Device],
    audio_inputs: Sequence[Device],
    audio_outputs: Sequence[Device],
    groups: Sequence[CompositeDevice],
) -> str:
    return (
        f"{len(video_devices)} camera(s), {len(audio_inputs)} audio input(s), "
        f"{len(audio_outputs)} audio output(s), {len(groups)} group(s)"
    )
