from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.core import Device, discover_devices
import gst_device_explorer.core.discovery as discovery


def test_discover_devices_combines_probe_output(monkeypatch) -> None:
    video = Device(id="/dev/video0", kind="video_input", name="video0")
    audio_input = Device(id="hw:2,0", kind="audio_input", name="USB Mic")
    audio_output = Device(id="hw:0,3", kind="audio_output", name="HDMI")

    monkeypatch.setattr(
        discovery,
        "discover_v4l2_video_devices",
        lambda: [video],
    )
    monkeypatch.setattr(
        discovery,
        "discover_alsa_audio_inputs",
        lambda: [audio_input],
    )
    monkeypatch.setattr(
        discovery,
        "discover_alsa_audio_outputs",
        lambda: [audio_output],
    )

    assert discover_devices() == [video, audio_input, audio_output]


def test_discover_devices_returns_empty_list_when_all_probes_are_empty(
    monkeypatch,
) -> None:
    monkeypatch.setattr(discovery, "discover_v4l2_video_devices", lambda: [])
    monkeypatch.setattr(discovery, "discover_alsa_audio_inputs", lambda: [])
    monkeypatch.setattr(discovery, "discover_alsa_audio_outputs", lambda: [])

    assert discover_devices() == []


def test_discover_devices_preserves_probe_order(monkeypatch) -> None:
    video1 = Device(id="/dev/video0", kind="video_input", name="video0")
    video2 = Device(id="/dev/video1", kind="video_input", name="video1")
    input1 = Device(id="hw:1,0", kind="audio_input", name="Mic 1")
    output1 = Device(id="hw:0,0", kind="audio_output", name="Speaker 1")
    output2 = Device(id="hw:0,3", kind="audio_output", name="HDMI")

    monkeypatch.setattr(
        discovery,
        "discover_v4l2_video_devices",
        lambda: [video1, video2],
    )
    monkeypatch.setattr(
        discovery,
        "discover_alsa_audio_inputs",
        lambda: [input1],
    )
    monkeypatch.setattr(
        discovery,
        "discover_alsa_audio_outputs",
        lambda: [output1, output2],
    )

    devices = discover_devices()

    assert [device.kind for device in devices] == [
        "video_input",
        "video_input",
        "audio_input",
        "audio_output",
        "audio_output",
    ]
    assert [device.id for device in devices] == [
        "/dev/video0",
        "/dev/video1",
        "hw:1,0",
        "hw:0,0",
        "hw:0,3",
    ]
