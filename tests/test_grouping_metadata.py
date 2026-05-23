from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.core.grouping import build_composite_devices
from gst_device_explorer.core.grouping_metadata import build_groupable_devices
from gst_device_explorer.core.models import Device


def test_alsa_input_device_becomes_groupable_audio_input() -> None:
    groupable = build_groupable_devices(
        [_alsa_input_device()],
    )[0]

    assert groupable.device_ref.role == "audio-input"
    assert groupable.device_ref.device_id == "hw:0,0"
    assert groupable.device_ref.path == "hw:0,0"
    assert groupable.device_ref.subsystem == "alsa"


def test_alsa_output_device_becomes_groupable_audio_output() -> None:
    groupable = build_groupable_devices(
        [_alsa_output_device()],
    )[0]

    assert groupable.device_ref.role == "audio-output"
    assert groupable.device_ref.device_id == "hw:0,0"
    assert groupable.device_ref.path == "hw:0,0"
    assert groupable.device_ref.subsystem == "alsa"


def test_alsa_card_and_device_numbers_are_parsed_from_hw_identifier() -> None:
    groupable = build_groupable_devices(
        [
            Device(
                id="hw:3,7",
                kind="audio_input",
                name="USB Audio: USB Audio",
                metadata={"backend": "alsa"},
            )
        ],
    )[0]

    assert groupable.metadata["alsa_card"] == "3"
    assert groupable.metadata["alsa_device"] == "hw:3,7"
    assert groupable.metadata["alsa_device_number"] == "7"


def test_alsa_card_name_is_preserved_when_available() -> None:
    groupable = build_groupable_devices(
        [_alsa_input_device(card_name="Reachy Mini Audio")],
    )[0]

    assert groupable.metadata["alsa_card_name"] == "Reachy Mini Audio"


def test_alsa_input_usb_metadata_is_read_from_pcm_capture_sysfs(tmp_path) -> None:
    sound_root = _fake_alsa_usb_sysfs(tmp_path, sound_node="pcmC0D0c")

    groupable = build_groupable_devices(
        [_alsa_input_device(card_name="USB Audio")],
        sysfs_sound_root=sound_root,
    )[0]

    assert groupable.metadata["usb_parent_path"] == "1-2.3"
    assert groupable.metadata["usb_vendor_id"] == "1234"
    assert groupable.metadata["usb_product_id"] == "5678"
    assert groupable.metadata["usb_product"] == "USB Composite Device"
    assert groupable.metadata["usb_manufacturer"] == "Example Devices"
    assert groupable.metadata["usb_serial"] == "ABC123"


def test_alsa_output_usb_metadata_is_read_from_pcm_playback_sysfs(tmp_path) -> None:
    sound_root = _fake_alsa_usb_sysfs(tmp_path, sound_node="pcmC0D0p")

    groupable = build_groupable_devices(
        [_alsa_output_device(card_name="USB Audio")],
        sysfs_sound_root=sound_root,
    )[0]

    assert groupable.metadata["usb_parent_path"] == "1-2.3"
    assert groupable.metadata["usb_vendor_id"] == "1234"
    assert groupable.metadata["usb_product_id"] == "5678"
    assert groupable.metadata["usb_product"] == "USB Composite Device"
    assert groupable.metadata["usb_manufacturer"] == "Example Devices"
    assert groupable.metadata["usb_serial"] == "ABC123"


def test_alsa_usb_metadata_falls_back_to_card_sysfs_path(tmp_path) -> None:
    sound_root = _fake_alsa_usb_sysfs(tmp_path, sound_node="card0")

    groupable = build_groupable_devices(
        [_alsa_input_device(card_name="USB Audio")],
        sysfs_sound_root=sound_root,
    )[0]

    assert groupable.metadata["usb_parent_path"] == "1-2.3"
    assert groupable.metadata["usb_product"] == "USB Composite Device"


def test_missing_alsa_sysfs_metadata_does_not_raise(tmp_path) -> None:
    groupable = build_groupable_devices(
        [_alsa_input_device(card_name="USB Audio")],
        sysfs_sound_root=tmp_path / "missing",
    )[0]

    assert groupable.metadata["alsa_card"] == "0"
    assert groupable.metadata["alsa_device"] == "hw:0,0"
    assert groupable.metadata["alsa_device_number"] == "0"
    assert groupable.metadata["alsa_card_name"] == "USB Audio"
    assert "usb_parent_path" not in groupable.metadata


def test_partial_alsa_usb_metadata_returns_usable_groupable_device(tmp_path) -> None:
    sound_root = _fake_alsa_usb_sysfs(
        tmp_path,
        sound_node="pcmC0D0c",
        metadata={"idVendor": "1234"},
    )

    groupable = build_groupable_devices(
        [_alsa_input_device(card_name="USB Audio")],
        sysfs_sound_root=sound_root,
    )[0]

    assert groupable.metadata["alsa_card"] == "0"
    assert groupable.metadata["alsa_device"] == "hw:0,0"
    assert groupable.metadata["alsa_device_number"] == "0"
    assert groupable.metadata["alsa_card_name"] == "USB Audio"
    assert groupable.metadata["usb_parent_path"] == "1-2.3"
    assert groupable.metadata["usb_vendor_id"] == "1234"
    assert "usb_product_id" not in groupable.metadata


def test_v4l2_device_becomes_groupable_camera(tmp_path) -> None:
    groupable = build_groupable_devices(
        [_v4l2_device()],
        sysfs_video4linux_root=tmp_path,
    )[0]

    assert groupable.device_ref.role == "camera"
    assert groupable.device_ref.device_id == "/dev/video0"
    assert groupable.device_ref.path == "/dev/video0"
    assert groupable.device_ref.subsystem == "v4l2"


def test_v4l2_name_is_read_from_fake_sysfs(tmp_path) -> None:
    video0 = tmp_path / "video0"
    video0.mkdir()
    (video0 / "name").write_text("Reachy Mini Camera\n", encoding="utf-8")

    groupable = build_groupable_devices(
        [_v4l2_device(name="video0")],
        sysfs_video4linux_root=tmp_path,
    )[0]

    assert groupable.name == "Reachy Mini Camera"
    assert groupable.metadata["v4l2_name"] == "Reachy Mini Camera"


def test_v4l2_usb_metadata_is_read_from_fake_sysfs(tmp_path) -> None:
    sysfs_root = _fake_v4l2_usb_sysfs(tmp_path)

    groupable = build_groupable_devices(
        [_v4l2_device()],
        sysfs_video4linux_root=sysfs_root,
    )[0]

    assert groupable.metadata["usb_parent_path"] == "1-2.3"
    assert groupable.metadata["usb_vendor_id"] == "1234"
    assert groupable.metadata["usb_product_id"] == "5678"
    assert groupable.metadata["usb_product"] == "USB Composite Device"
    assert groupable.metadata["usb_manufacturer"] == "Example Devices"
    assert groupable.metadata["usb_serial"] == "ABC123"


def test_missing_v4l2_sysfs_metadata_does_not_raise(tmp_path) -> None:
    groupable = build_groupable_devices(
        [_v4l2_device()],
        sysfs_video4linux_root=tmp_path / "missing",
    )[0]

    assert groupable.name == "video0"
    assert groupable.metadata == {}


def test_partial_v4l2_sysfs_metadata_returns_usable_groupable_device(tmp_path) -> None:
    video0 = tmp_path / "video0"
    video0.mkdir()
    (video0 / "name").write_text("Partial Camera\n", encoding="utf-8")

    groupable = build_groupable_devices(
        [_v4l2_device()],
        sysfs_video4linux_root=tmp_path,
    )[0]

    assert groupable.device_ref.role == "camera"
    assert groupable.name == "Partial Camera"
    assert groupable.metadata == {"v4l2_name": "Partial Camera"}


def test_grouping_metadata_feeds_composite_device_grouping(tmp_path) -> None:
    video_root = _fake_v4l2_usb_sysfs(tmp_path, node_name="video0")
    _fake_v4l2_usb_sysfs(tmp_path, node_name="video1")
    sound_root = tmp_path / "class" / "sound"
    _fake_alsa_usb_sysfs(
        tmp_path,
        sound_node="pcmC0D0c",
        sound_root=sound_root,
    )
    _fake_alsa_usb_sysfs(
        tmp_path,
        sound_node="pcmC0D0p",
        sound_root=sound_root,
    )
    devices = [
        _v4l2_device(name="video0", path="/dev/video0"),
        _v4l2_device(name="video1", path="/dev/video1"),
        _alsa_input_device(card_name="USB Audio"),
        _alsa_output_device(card_name="USB Audio"),
    ]

    groupable_devices = build_groupable_devices(
        devices,
        sysfs_video4linux_root=video_root,
        sysfs_sound_root=sound_root,
    )
    groups = build_composite_devices(groupable_devices)

    assert len(groups) == 1
    group = groups[0]
    assert group.id == "usb-device-1-2-3"
    assert [member.role for member in group.members] == [
        "audio-input",
        "audio-output",
        "camera",
        "camera",
    ]


def _alsa_input_device(
    card_name: str = "Reachy Mini Audio",
    extra_metadata: dict | None = None,
) -> Device:
    metadata = {
        "backend": "alsa",
        "alsa_device": "hw:0,0",
        "card_number": 0,
        "device_number": 0,
        "card_name": card_name,
    }
    metadata.update(extra_metadata or {})
    return Device(
        id="hw:0,0",
        kind="audio_input",
        name=f"{card_name}: USB Audio",
        metadata=metadata,
    )


def _alsa_output_device(
    card_name: str = "Reachy Mini Audio",
    extra_metadata: dict | None = None,
) -> Device:
    metadata = {
        "backend": "alsa",
        "alsa_device": "hw:0,0",
        "card_number": 0,
        "device_number": 0,
        "card_name": card_name,
    }
    metadata.update(extra_metadata or {})
    return Device(
        id="hw:0,0",
        kind="audio_output",
        name=f"{card_name}: USB Audio",
        metadata=metadata,
    )


def _v4l2_device(name: str = "video0", path: str = "/dev/video0") -> Device:
    return Device(
        id=path,
        kind="video_input",
        name=name,
        metadata={
            "backend": "v4l2",
            "path": path,
            "node_name": name,
        },
    )


def _fake_v4l2_usb_sysfs(tmp_path, node_name: str = "video0") -> Path:
    sysfs_root = tmp_path / "class" / "video4linux"
    video0 = sysfs_root / node_name
    video0.mkdir(parents=True)
    (video0 / "name").write_text("USB Camera\n", encoding="utf-8")

    usb_parent = tmp_path / "devices" / "pci0000:00" / "usb1" / "1-2.3"
    video_device = usb_parent / "1-2.3:1.0" / "video4linux" / node_name
    video_device.mkdir(parents=True)
    (usb_parent / "idVendor").write_text("1234\n", encoding="utf-8")
    (usb_parent / "idProduct").write_text("5678\n", encoding="utf-8")
    (usb_parent / "product").write_text(
        "USB Composite Device\n",
        encoding="utf-8",
    )
    (usb_parent / "manufacturer").write_text(
        "Example Devices\n",
        encoding="utf-8",
    )
    (usb_parent / "serial").write_text("ABC123\n", encoding="utf-8")
    (video0 / "device").symlink_to(video_device)
    return sysfs_root


def _fake_alsa_usb_sysfs(
    tmp_path,
    sound_node: str,
    sound_root: Path | None = None,
    metadata: dict[str, str] | None = None,
) -> Path:
    sound_root = sound_root or tmp_path / "class" / "sound"
    sound_root.mkdir(parents=True, exist_ok=True)

    usb_parent = tmp_path / "devices" / "pci0000:00" / "usb1" / "1-2.3"
    sound_device = usb_parent / "1-2.3:1.1" / "sound" / sound_node
    sound_device.mkdir(parents=True)

    files = metadata or {
        "idVendor": "1234",
        "idProduct": "5678",
        "product": "USB Composite Device",
        "manufacturer": "Example Devices",
        "serial": "ABC123",
    }
    for name, value in files.items():
        (usb_parent / name).write_text(f"{value}\n", encoding="utf-8")

    (sound_root / sound_node).symlink_to(sound_device)
    return sound_root
