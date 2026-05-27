"""Sidebar tree construction for the media explorer GUI."""

from __future__ import annotations

from collections.abc import Sequence

from gst_device_explorer.core.models import CompositeDevice, Device
from gst_device_explorer.gui.builders_utils import (
    _device_target,
    _endpoint_node_id,
    _group_node_id,
    _member_key,
    _node_kind_from_role,
    _role_label,
    _target_kind_for_node,
)
from gst_device_explorer.gui.model import SidebarNode


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
                children=_group_nodes(groups),
            ),
            _section_node(
                node_id="section:cameras",
                label="Cameras",
                children=tuple(
                    _endpoint_node("video", device)
                    for device in sorted(video_devices, key=lambda d: d.id)
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


def group_children_by_parent(
    groups: Sequence[CompositeDevice],
) -> dict[str, tuple[CompositeDevice, ...]]:
    result: dict[str, tuple[CompositeDevice, ...]] = {}
    for parent in groups:
        candidates = [
            child
            for child in groups
            if child.id != parent.id
            and _group_member_keys(child) < _group_member_keys(parent)
        ]
        direct_children = [
            child
            for child in candidates
            if not any(
                child.id != other.id
                and _group_member_keys(child) < _group_member_keys(other)
                and _group_member_keys(other) < _group_member_keys(parent)
                for other in candidates
            )
        ]
        if direct_children:
            result[parent.id] = tuple(sorted(direct_children, key=lambda g: g.id))
    return result


def _section_node(node_id: str, label: str, children: tuple[SidebarNode, ...]) -> SidebarNode:
    return SidebarNode(
        id=node_id,
        label=label,
        kind="section",
        status="available" if children else "empty",
        children=children,
        summary=f"{len(children)} item(s)",
    )


def _group_nodes(groups: Sequence[CompositeDevice]) -> tuple[SidebarNode, ...]:
    children_by_group = group_children_by_parent(groups)
    child_ids = {child.id for children in children_by_group.values() for child in children}
    return tuple(
        _group_node(group, children_by_group=children_by_group)
        for group in sorted(groups, key=lambda g: g.id)
        if group.id not in child_ids
    )


def _group_node(
    group: CompositeDevice,
    *,
    children_by_group: dict[str, tuple[CompositeDevice, ...]] | None = None,
) -> SidebarNode:
    group_children = () if children_by_group is None else children_by_group.get(group.id, ())
    child_member_keys = {
        key
        for child in group_children
        for key in _group_member_keys(child)
    }
    return SidebarNode(
        id=_group_node_id(group.id),
        label=group.name,
        kind="group",
        status="available",
        target_kind="group",
        target=group.id,
        summary=f"{len(group.members)} endpoint(s), confidence {group.confidence:.2f}",
        children=(
            *(
                _group_node(child, children_by_group=children_by_group)
                for child in group_children
            ),
            *(
                _group_member_node(group.id, member.role, member.device_id)
                for member in sorted(group.members, key=lambda m: (m.role, m.device_id))
                if _member_key(member.role, member.device_id) not in child_member_keys
            ),
        ),
    )


def _group_member_keys(group: CompositeDevice) -> set[tuple[str, str]]:
    return {_member_key(member.role, member.device_id) for member in group.members}


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


def _endpoint_label(node_kind: str, device: Device) -> str:
    prefix = {
        "video": "Camera",
        "audio_input": "Audio Input",
        "audio_output": "Audio Output",
    }[node_kind]
    return f"{prefix} {_device_target(device)}"


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
