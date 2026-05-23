from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.core.grouping import (
    GroupableDevice,
    build_composite_devices,
)
from gst_device_explorer.core.models import DeviceRef


def test_build_composite_devices_with_no_input_returns_no_groups() -> None:
    assert build_composite_devices([]) == []


def test_build_composite_devices_with_single_device_returns_no_groups() -> None:
    groups = build_composite_devices(
        [
            _groupable_device(
                role="camera",
                device_id="/dev/video0",
                subsystem="v4l2",
                path="/dev/video0",
                name="USB Camera",
            )
        ]
    )

    assert groups == []


def test_alsa_input_and_output_same_card_create_audio_device_group() -> None:
    groups = build_composite_devices(
        [
            _alsa_audio_input("hw:2,0", card="0"),
            _alsa_audio_output("hw:2,0", card="0"),
        ]
    )

    assert len(groups) == 1
    group = groups[0]
    assert group.id == "audio-device-alsa-card-0"
    assert group.name == "Reachy Mini Audio"
    assert group.kind == "audio-device"
    assert group.confidence == 0.9
    assert [member.role for member in group.members] == [
        "audio-input",
        "audio-output",
    ]
    assert group.evidence[0].source == "alsa-card"
    assert group.evidence[0].description == "audio devices share ALSA card 0"
    assert group.evidence[0].strength == 0.9


def test_alsa_input_and_output_different_cards_do_not_group() -> None:
    groups = build_composite_devices(
        [
            _alsa_audio_input("hw:2,0", card="0"),
            _alsa_audio_output("hw:3,0", card="1"),
        ]
    )

    assert groups == []


def test_usb_parent_path_groups_camera_audio_input_and_audio_output() -> None:
    groups = build_composite_devices(
        [
            _usb_camera("/dev/video0", parent_path="1-2.3"),
            _usb_audio_input("hw:2,0", parent_path="1-2.3"),
            _usb_audio_output("hw:2,0", parent_path="1-2.3"),
        ]
    )

    assert len(groups) == 1
    group = groups[0]
    assert group.id == "usb-device-1-2-3"
    assert group.name == "Reachy Mini"
    assert group.kind == "unknown"
    assert group.confidence == 0.9
    assert [member.role for member in group.members] == [
        "audio-input",
        "audio-output",
        "camera",
    ]
    assert group.evidence[0].source == "usb-topology"
    assert group.evidence[0].description == (
        "devices share USB parent path 1-2.3"
    )
    assert group.evidence[0].strength == 0.9


def test_usb_ancestor_groups_related_composite_groups() -> None:
    groups = build_composite_devices(
        [
            _usb_family_camera(
                "/dev/video0",
                parent_path="1-4.1.4",
                product="Reachy Mini Camera",
            ),
            _usb_family_audio_input(
                "hw:2,0",
                parent_path="1-4.1.1",
                product="Reachy Mini Audio",
            ),
            _usb_family_camera(
                "/dev/video1",
                parent_path="1-4.1.4",
                product="Reachy Mini Camera",
            ),
            _usb_family_audio_output(
                "hw:2,0",
                parent_path="1-4.1.1",
                product="Reachy Mini Audio",
            ),
        ]
    )

    assert [group.id for group in groups] == [
        "usb-device-1-4-1-1",
        "usb-device-1-4-1-4",
        "usb-family-1-4-1",
    ]
    parent = groups[2]
    assert parent.name == "Reachy Mini"
    assert parent.kind == "unknown"
    assert parent.confidence == 0.8
    assert [member.device_id for member in parent.members] == [
        "hw:2,0",
        "hw:2,0",
        "/dev/video0",
        "/dev/video1",
    ]
    assert [member.role for member in parent.members] == [
        "audio-input",
        "audio-output",
        "camera",
        "camera",
    ]
    assert [evidence.source for evidence in parent.evidence] == [
        "usb-topology",
        "usb-metadata",
    ]
    assert parent.evidence[0].description == (
        "composite groups share USB ancestor 1-4.1"
    )


def test_usb_ancestor_does_not_group_generic_product_names() -> None:
    groups = build_composite_devices(
        [
            _usb_family_camera(
                "/dev/video0",
                parent_path="1-2.3",
                product="USB Camera",
            ),
            _usb_family_audio_input(
                "hw:2,0",
                parent_path="1-2.3",
                product="USB Camera",
            ),
            _usb_family_camera(
                "/dev/video1",
                parent_path="1-2.4",
                product="USB Audio Device",
            ),
            _usb_family_audio_output(
                "hw:3,0",
                parent_path="1-2.4",
                product="USB Audio Device",
            ),
        ]
    )

    assert [group.id for group in groups] == [
        "usb-device-1-2-3",
        "usb-device-1-2-4",
    ]


def test_usb_ancestor_does_not_group_different_vendor_ids() -> None:
    groups = build_composite_devices(
        [
            _usb_family_camera(
                "/dev/video0",
                parent_path="1-2.3",
                product="Reachy Mini Camera",
                vendor_id="1234",
            ),
            _usb_family_audio_input(
                "hw:2,0",
                parent_path="1-2.3",
                product="Reachy Mini Camera",
                vendor_id="1234",
            ),
            _usb_family_camera(
                "/dev/video1",
                parent_path="1-2.4",
                product="Reachy Mini Display Camera",
                vendor_id="abcd",
            ),
            _usb_family_audio_output(
                "hw:3,0",
                parent_path="1-2.4",
                product="Reachy Mini Display Camera",
                vendor_id="abcd",
            ),
        ]
    )

    assert [group.id for group in groups] == [
        "usb-device-1-2-3",
        "usb-device-1-2-4",
    ]


def test_different_usb_parent_paths_do_not_group() -> None:
    groups = build_composite_devices(
        [
            _usb_camera("/dev/video0", parent_path="1-2.3"),
            _usb_audio_input("hw:2,0", parent_path="1-2.4"),
            _usb_audio_output("hw:2,0", parent_path="1-2.5"),
        ]
    )

    assert groups == []


def test_group_ids_are_stable_and_deterministic() -> None:
    devices = [
        _usb_audio_output("hw:2,0", parent_path="1-2.3"),
        _usb_camera("/dev/video0", parent_path="1-2.3"),
        _usb_audio_input("hw:2,0", parent_path="1-2.3"),
        _alsa_audio_output("hw:3,0", card="1"),
        _alsa_audio_input("hw:3,0", card="1"),
    ]

    first = build_composite_devices(devices)
    second = build_composite_devices(list(reversed(devices)))

    assert [group.id for group in first] == [
        "audio-device-alsa-card-1",
        "usb-device-1-2-3",
    ]
    assert [group.id for group in second] == [
        "audio-device-alsa-card-1",
        "usb-device-1-2-3",
    ]


def test_name_only_similarity_does_not_create_group() -> None:
    groups = build_composite_devices(
        [
            _groupable_device(
                role="camera",
                device_id="/dev/video0",
                subsystem="v4l2",
                path="/dev/video0",
                name="Reachy Mini",
            ),
            _groupable_device(
                role="audio-input",
                device_id="hw:2,0",
                subsystem="alsa",
                path=None,
                name="Reachy Mini",
            ),
        ]
    )

    assert groups == []


def _alsa_audio_input(device_id: str, card: str) -> GroupableDevice:
    return _groupable_device(
        role="audio-input",
        device_id=device_id,
        subsystem="alsa",
        path=None,
        name="Reachy Mini Audio Capture",
        metadata={"alsa_card": card, "alsa_card_name": "Reachy Mini Audio"},
    )


def _alsa_audio_output(device_id: str, card: str) -> GroupableDevice:
    return _groupable_device(
        role="audio-output",
        device_id=device_id,
        subsystem="alsa",
        path=None,
        name="Reachy Mini Audio Playback",
        metadata={"alsa_card": card, "alsa_card_name": "Reachy Mini Audio"},
    )


def _usb_camera(device_id: str, parent_path: str) -> GroupableDevice:
    return _groupable_device(
        role="camera",
        device_id=device_id,
        subsystem="v4l2",
        path=device_id,
        name="Camera",
        metadata={
            "usb_parent_path": parent_path,
            "usb_vendor_id": "1234",
            "usb_product_id": "5678",
            "usb_product": "Reachy Mini",
        },
    )


def _usb_audio_input(device_id: str, parent_path: str) -> GroupableDevice:
    return _groupable_device(
        role="audio-input",
        device_id=device_id,
        subsystem="alsa",
        path=None,
        name="Audio Capture",
        metadata={
            "usb_parent_path": parent_path,
            "usb_vendor_id": "1234",
            "usb_product_id": "5678",
            "usb_product": "Reachy Mini",
        },
    )


def _usb_audio_output(device_id: str, parent_path: str) -> GroupableDevice:
    return _groupable_device(
        role="audio-output",
        device_id=device_id,
        subsystem="alsa",
        path=None,
        name="Audio Playback",
        metadata={
            "usb_parent_path": parent_path,
            "usb_vendor_id": "1234",
            "usb_product_id": "5678",
            "usb_product": "Reachy Mini",
        },
    )


def _usb_family_camera(
    device_id: str,
    parent_path: str,
    product: str,
    vendor_id: str = "1234",
) -> GroupableDevice:
    return _usb_family_device(
        role="camera",
        device_id=device_id,
        path=device_id,
        name="Camera",
        parent_path=parent_path,
        product=product,
        vendor_id=vendor_id,
    )


def _usb_family_audio_input(
    device_id: str,
    parent_path: str,
    product: str,
    vendor_id: str = "1234",
) -> GroupableDevice:
    return _usb_family_device(
        role="audio-input",
        device_id=device_id,
        path=None,
        name="Audio Capture",
        parent_path=parent_path,
        product=product,
        vendor_id=vendor_id,
    )


def _usb_family_audio_output(
    device_id: str,
    parent_path: str,
    product: str,
    vendor_id: str = "1234",
) -> GroupableDevice:
    return _usb_family_device(
        role="audio-output",
        device_id=device_id,
        path=None,
        name="Audio Playback",
        parent_path=parent_path,
        product=product,
        vendor_id=vendor_id,
    )


def _usb_family_device(
    role: str,
    device_id: str,
    path: str | None,
    name: str,
    parent_path: str,
    product: str,
    vendor_id: str,
) -> GroupableDevice:
    return _groupable_device(
        role=role,
        device_id=device_id,
        subsystem="v4l2" if role == "camera" else "alsa",
        path=path,
        name=name,
        metadata={
            "usb_parent_path": parent_path,
            "usb_vendor_id": vendor_id,
            "usb_product_id": "5678",
            "usb_product": product,
        },
    )


def _groupable_device(
    role: str,
    device_id: str,
    subsystem: str,
    path: str | None,
    name: str,
    metadata: dict[str, str] | None = None,
) -> GroupableDevice:
    return GroupableDevice(
        device_ref=DeviceRef(
            role=role,
            device_id=device_id,
            path=path,
            subsystem=subsystem,
        ),
        name=name,
        metadata=metadata or {},
    )
