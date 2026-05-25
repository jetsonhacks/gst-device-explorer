from pathlib import Path
import subprocess
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.probes import (
    discover_alsa_audio_inputs,
    discover_alsa_audio_outputs,
)


def test_no_capture_devices_found(monkeypatch) -> None:
    _mock_alsa_command(monkeypatch, expected_command="arecord", output="")

    devices = discover_alsa_audio_inputs()

    assert devices == []


def test_one_capture_device(monkeypatch) -> None:
    output = """
**** List of CAPTURE Hardware Devices ****
card 2: Camera [USB Camera], device 0: USB Audio [USB Audio]
  Subdevices: 1/1
  Subdevice #0: subdevice #0
"""
    _mock_alsa_command(monkeypatch, expected_command="arecord", output=output)

    devices = discover_alsa_audio_inputs()

    assert len(devices) == 1
    device = devices[0]
    assert device.id == "hw:2,0"
    assert device.kind == "audio_input"
    assert device.name == "USB Camera: USB Audio"
    assert device.metadata["backend"] == "alsa"
    assert device.metadata["source"] == "arecord"
    assert device.metadata["card_number"] == 2
    assert device.metadata["device_number"] == 0
    assert device.metadata["card_id"] == "Camera"
    assert device.metadata["device_id"] == "USB Audio"
    assert device.metadata["card_name"] == "USB Camera"
    assert device.metadata["device_name"] == "USB Audio"
    assert device.metadata["alsa_device"] == "hw:2,0"


def test_capture_device_includes_audio_hw_params(monkeypatch) -> None:
    output = """
**** List of CAPTURE Hardware Devices ****
card 2: Camera [USB Camera], device 0: USB Audio [USB Audio]
"""
    hw_params = """
ACCESS:  MMAP_INTERLEAVED RW_INTERLEAVED
FORMAT:  S16_LE S24_LE
CHANNELS: [1 2]
RATE: [8000 48000]
"""
    _mock_alsa_command(
        monkeypatch,
        expected_command="arecord",
        output=output,
        hw_params={"hw:2,0": hw_params},
    )

    devices = discover_alsa_audio_inputs()

    assert len(devices) == 1
    capability = devices[0].capabilities[0]
    assert capability.name == "audio_format"
    assert capability.source == "arecord --dump-hw-params"
    assert capability.values == {
        "channels": "1-2",
        "format": "S16LE, S24LE",
        "rate": "8000-48000",
    }


def test_one_playback_device(monkeypatch) -> None:
    output = """
**** List of PLAYBACK Hardware Devices ****
card 0: PCH [HDA Intel PCH], device 3: HDMI 0 [HDMI 0]
  Subdevices: 1/1
  Subdevice #0: subdevice #0
"""
    _mock_alsa_command(monkeypatch, expected_command="aplay", output=output)

    devices = discover_alsa_audio_outputs()

    assert len(devices) == 1
    assert devices[0].id == "hw:0,3"
    assert devices[0].kind == "audio_output"
    assert devices[0].name == "HDA Intel PCH: HDMI 0"
    assert devices[0].metadata["source"] == "aplay"


def test_multiple_devices(monkeypatch) -> None:
    output = """
card 1: Device [USB Audio Device], device 0: USB Audio [USB Audio]
card 2: Camera [USB Camera], device 0: USB Audio [USB Audio]
"""
    _mock_alsa_command(monkeypatch, expected_command="arecord", output=output)

    devices = discover_alsa_audio_inputs()

    assert [device.id for device in devices] == ["hw:1,0", "hw:2,0"]
    assert [device.metadata["card_name"] for device in devices] == [
        "USB Audio Device",
        "USB Camera",
    ]


def test_missing_arecord_returns_empty_list(monkeypatch) -> None:
    monkeypatch.setattr("shutil.which", lambda command: None)

    devices = discover_alsa_audio_inputs()

    assert devices == []


def test_missing_aplay_returns_empty_list(monkeypatch) -> None:
    monkeypatch.setattr("shutil.which", lambda command: None)

    devices = discover_alsa_audio_outputs()

    assert devices == []


def test_command_failure_returns_empty_list(monkeypatch) -> None:
    _mock_alsa_command(
        monkeypatch,
        expected_command="arecord",
        output="",
        returncode=1,
    )

    devices = discover_alsa_audio_inputs()

    assert devices == []


def test_unrecognized_output_returns_empty_list(monkeypatch) -> None:
    _mock_alsa_command(
        monkeypatch,
        expected_command="aplay",
        output="this is not an ALSA device listing",
    )

    devices = discover_alsa_audio_outputs()

    assert devices == []


def _mock_alsa_command(
    monkeypatch,
    expected_command: str,
    output: str,
    returncode: int = 0,
    hw_params: dict[str, str] | None = None,
) -> None:
    monkeypatch.setattr("shutil.which", lambda command: f"/usr/bin/{command}")
    hw_params = hw_params or {}

    def fake_run(command, check, capture_output, text, timeout):
        assert check is False
        assert capture_output is True
        assert text is True
        assert timeout == 5
        if command == [expected_command, "-l"]:
            return subprocess.CompletedProcess(
                command,
                returncode,
                stdout=output,
                stderr="",
            )
        if len(command) == 4 and command[:3] == [expected_command, "--dump-hw-params", "-D"]:
            device = command[3]
            if device in hw_params:
                return subprocess.CompletedProcess(command, 0, stdout=hw_params[device], stderr="")
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="")
        raise AssertionError(f"Unexpected ALSA command: {command!r}")

    monkeypatch.setattr("subprocess.run", fake_run)
