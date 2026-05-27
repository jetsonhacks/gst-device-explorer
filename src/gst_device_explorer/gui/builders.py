"""Pure builders for toolkit-neutral GUI models."""

from __future__ import annotations

from collections.abc import Sequence

from gst_device_explorer.core.models import (
    CandidateRanking,
    CompositeDevice,
    Device,
    DeviceProfile,
    GroupValidation,
)
from gst_device_explorer.gui.builders_detail import (
    build_detail_pane_for_audio_input,
    build_detail_pane_for_audio_output,
    build_detail_pane_for_group,
    build_detail_pane_for_video,
    build_unknown_detail_pane,
)
from gst_device_explorer.gui.builders_sidebar import (
    build_sidebar_model,
    group_children_by_parent,
)
from gst_device_explorer.gui.builders_utils import (
    _device_target,
    _profile_kind,
    _target_kind_for_node,
)
from gst_device_explorer.gui.model import (
    DetailPaneModel,
    MediaExplorerSnapshot,
)

__all__ = [
    "build_detail_pane_for_audio_input",
    "build_detail_pane_for_audio_output",
    "build_detail_pane_for_group",
    "build_detail_pane_for_video",
    "build_media_explorer_snapshot",
    "build_sidebar_model",
    "build_unknown_detail_pane",
    "group_children_by_parent",
]


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
        summary=(sidebar_roots[0].summary,),
        generated_at=generated_at,
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
                child_groups=group_children_by_parent(groups).get(group.id, ()),
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


def _find_device(devices: Sequence[Device], target: str) -> Device | None:
    for device in devices:
        if device.id == target or _device_target(device) == target:
            return device
    return None
