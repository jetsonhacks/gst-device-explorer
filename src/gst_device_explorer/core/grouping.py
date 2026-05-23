"""Composite device grouping from normalized metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
import re

from gst_device_explorer.core.models import (
    CompositeDevice,
    DeviceRef,
    GroupingEvidence,
)


@dataclass(frozen=True)
class GroupableDevice:
    """A discovered device plus normalized metadata for grouping."""

    device_ref: DeviceRef
    name: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class _UsbParentGroup:
    usb_parent_path: str
    members: list[GroupableDevice]
    composite: CompositeDevice


def build_composite_devices(
    devices: list[GroupableDevice],
) -> list[CompositeDevice]:
    """Build conservative composite device groups from normalized metadata."""

    if len(devices) < 2:
        return []

    groups: list[CompositeDevice] = []
    usb_groups: list[_UsbParentGroup] = []
    grouped_device_ids: set[str] = set()

    for usb_parent_path in _sorted_metadata_values(devices, "usb_parent_path"):
        members = [
            device
            for device in devices
            if device.metadata.get("usb_parent_path") == usb_parent_path
        ]
        if len(members) < 2:
            continue

        group = _usb_parent_group(usb_parent_path, members)
        groups.append(group)
        usb_groups.append(
            _UsbParentGroup(
                usb_parent_path=usb_parent_path,
                members=members,
                composite=group,
            )
        )
        grouped_device_ids.update(member.device_ref.device_id for member in members)

    groups.extend(_usb_ancestor_groups(usb_groups))

    for alsa_card in _sorted_metadata_values(devices, "alsa_card"):
        members = [
            device
            for device in devices
            if device.metadata.get("alsa_card") == alsa_card
            and device.device_ref.device_id not in grouped_device_ids
        ]
        if not _has_audio_input_and_output(members):
            continue

        groups.append(_alsa_card_group(alsa_card, members))

    return sorted(groups, key=lambda group: group.id)


def _usb_ancestor_groups(
    usb_groups: list[_UsbParentGroup],
) -> list[CompositeDevice]:
    ancestor_groups: list[CompositeDevice] = []
    used_group_ids: set[str] = set()

    for ancestor in _sorted_meaningful_usb_ancestors(usb_groups):
        related_groups = [
            group
            for group in usb_groups
            if group.composite.id not in used_group_ids
            and _is_usb_descendant(group.usb_parent_path, ancestor)
        ]
        family_groups = _largest_product_family(related_groups)
        if len(family_groups) < 2:
            continue

        ancestor_groups.append(_usb_ancestor_group(ancestor, family_groups))
        used_group_ids.update(group.composite.id for group in family_groups)

    return ancestor_groups


def _sorted_meaningful_usb_ancestors(
    usb_groups: list[_UsbParentGroup],
) -> list[str]:
    ancestors: set[str] = set()
    for group in usb_groups:
        ancestors.update(_usb_ancestors(group.usb_parent_path))

    return sorted(
        (
            ancestor
            for ancestor in ancestors
            if sum(
                1
                for group in usb_groups
                if _is_usb_descendant(group.usb_parent_path, ancestor)
            )
            >= 2
        ),
        key=lambda ancestor: (-_usb_path_depth(ancestor), ancestor),
    )


def _usb_ancestors(usb_parent_path: str) -> list[str]:
    parts = usb_parent_path.split(".")
    return [".".join(parts[:index]) for index in range(1, len(parts))]


def _is_usb_descendant(usb_parent_path: str, ancestor: str) -> bool:
    return usb_parent_path != ancestor and usb_parent_path.startswith(f"{ancestor}.")


def _usb_path_depth(usb_parent_path: str) -> int:
    return len(usb_parent_path.split("."))


def _largest_product_family(
    usb_groups: list[_UsbParentGroup],
) -> list[_UsbParentGroup]:
    grouped: dict[tuple[str, ...], list[_UsbParentGroup]] = {}
    for group in usb_groups:
        family_key = _product_family_key(group.members)
        if family_key is None:
            continue
        grouped.setdefault(family_key, []).append(group)

    if not grouped:
        return []

    return max(
        grouped.values(),
        key=lambda family_groups: (
            len(family_groups),
            _product_family_sort_key(family_groups),
        ),
    )


def _product_family_key(
    members: list[GroupableDevice],
) -> tuple[str, ...] | None:
    vendor_id = _first_metadata_value(members, "usb_vendor_id")
    product = _first_metadata_value(members, "usb_product")
    product_family_token = _product_family_token(product)

    if vendor_id and product_family_token:
        return ("product-family", _normalize_value(vendor_id), product_family_token)

    return None


def _product_family_token(product: str | None) -> str | None:
    tokens = _product_family_tokens(product)
    if not tokens:
        return None

    return tokens[0][1]


def _product_family_tokens(product: str | None) -> list[tuple[str, str]]:
    if product is None:
        return []

    ignored_tokens = {
        "audio",
        "camera",
        "capture",
        "composite",
        "device",
        "input",
        "microphone",
        "output",
        "playback",
        "speaker",
        "usb",
        "video",
        "webcam",
    }
    return [
        (token, token.lower())
        for token in re.findall(r"[A-Za-z0-9]+", product)
        if token.lower() not in ignored_tokens
    ]


def _normalize_value(value: str) -> str:
    return "-".join(re.findall(r"[a-z0-9]+", value.lower()))


def _product_family_sort_key(usb_groups: list[_UsbParentGroup]) -> tuple[str, ...]:
    return tuple(group.composite.id for group in usb_groups)


def _usb_parent_group(
    usb_parent_path: str,
    members: list[GroupableDevice],
) -> CompositeDevice:
    ordered_members = _sort_members(members)
    return CompositeDevice(
        id=f"usb-device-{_stable_id_part(usb_parent_path)}",
        name=_first_metadata_value(ordered_members, "usb_product")
        or f"USB Device {usb_parent_path}",
        kind="unknown",
        confidence=0.9,
        members=[member.device_ref for member in ordered_members],
        evidence=[
            GroupingEvidence(
                source="usb-topology",
                description=(
                    "devices share USB parent path "
                    f"{usb_parent_path}"
                ),
                strength=0.9,
            )
        ],
    )


def _alsa_card_group(
    alsa_card: str,
    members: list[GroupableDevice],
) -> CompositeDevice:
    ordered_members = _sort_members(members)
    return CompositeDevice(
        id=f"audio-device-alsa-card-{_stable_id_part(alsa_card)}",
        name=_first_metadata_value(ordered_members, "alsa_card_name")
        or f"ALSA Card {alsa_card}",
        kind="audio-device",
        confidence=0.9,
        members=[member.device_ref for member in ordered_members],
        evidence=[
            GroupingEvidence(
                source="alsa-card",
                description=f"audio devices share ALSA card {alsa_card}",
                strength=0.9,
            )
        ],
    )


def _usb_ancestor_group(
    ancestor: str,
    usb_groups: list[_UsbParentGroup],
) -> CompositeDevice:
    members = [
        member
        for group in sorted(usb_groups, key=lambda group: group.usb_parent_path)
        for member in group.members
    ]
    ordered_members = _sort_members(members)
    return CompositeDevice(
        id=f"usb-family-{_stable_id_part(ancestor)}",
        name=_usb_family_group_name(ordered_members),
        kind="unknown",
        confidence=0.8,
        members=[member.device_ref for member in ordered_members],
        evidence=[
            GroupingEvidence(
                source="usb-topology",
                description=(
                    "composite groups share USB ancestor "
                    f"{ancestor}"
                ),
                strength=0.8,
            ),
            GroupingEvidence(
                source="usb-metadata",
                description=(
                    "composite group metadata suggests the same attached "
                    "product family"
                ),
                strength=0.7,
            ),
        ],
    )


def _usb_family_group_name(members: list[GroupableDevice]) -> str:
    product_names = _unique_metadata_values(members, "usb_product")
    token_lists = [
        tokens
        for product in product_names
        if (tokens := _product_family_tokens(product))
    ]
    if not token_lists:
        return "USB Family Device"

    common_tokens = list(token_lists[0])
    for tokens in token_lists[1:]:
        prefix: list[tuple[str, str]] = []
        for left, right in zip(common_tokens, tokens, strict=False):
            if left[1] != right[1]:
                break
            prefix.append(left)
        common_tokens = prefix
        if not common_tokens:
            return "USB Family Device"

    return " ".join(token for token, _normalized in common_tokens)


def _unique_metadata_values(
    devices: list[GroupableDevice],
    key: str,
) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for device in devices:
        value = device.metadata.get(key)
        if not value or value in seen:
            continue
        values.append(value)
        seen.add(value)

    return values


def _sorted_metadata_values(
    devices: list[GroupableDevice],
    key: str,
) -> list[str]:
    return sorted(
        {
            value
            for device in devices
            if (value := device.metadata.get(key))
        }
    )


def _has_audio_input_and_output(devices: list[GroupableDevice]) -> bool:
    roles = {device.device_ref.role for device in devices}
    return "audio-input" in roles and "audio-output" in roles


def _first_metadata_value(
    devices: list[GroupableDevice],
    key: str,
) -> str | None:
    for device in devices:
        value = device.metadata.get(key)
        if value:
            return value
    return None


def _sort_members(devices: list[GroupableDevice]) -> list[GroupableDevice]:
    return sorted(
        devices,
        key=lambda device: (
            device.device_ref.role,
            device.device_ref.subsystem,
            device.device_ref.device_id,
        ),
    )


def _stable_id_part(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "unknown"
