"""Shared mapping and formatting primitives for GUI builders."""

from __future__ import annotations

from gst_device_explorer.core.models import CompositeDevice, Device


def _device_target(device: Device) -> str:
    value = device.metadata.get("path") if device.kind == "video_input" else None
    if isinstance(value, str) and value:
        return value
    return device.id


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


def _target_kind_for_node(node_kind: str) -> str:
    return {
        "video": "video",
        "audio_input": "audio-input",
        "audio_output": "audio-output",
    }.get(node_kind, node_kind)


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


def _group_node_id(group_id: str) -> str:
    return f"group:{group_id}"


def _endpoint_node_id(node_kind: str, target: str) -> str:
    return f"{node_kind}:{target}"


def _member_key(role: str, device_id: str) -> tuple[str, str]:
    return _node_kind_from_role(role), device_id


def _group_member_keys(group: CompositeDevice) -> set[tuple[str, str]]:
    return {_member_key(member.role, member.device_id) for member in group.members}


def _group_member_targets(group: CompositeDevice) -> str:
    return ", ".join(
        member.device_id
        for member in sorted(group.members, key=lambda m: (m.role, m.device_id))
    )


def _profile_kind(kind: str) -> str:
    return {
        "audio_input": "audio-input",
        "audio_output": "audio-output",
        "video_input": "video",
    }.get(kind, kind)
