from pathlib import Path
import subprocess
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.probes.gst import (
    DEFAULT_GSTREAMER_ELEMENTS,
    inspect_gstreamer_environment,
)


def _fact_by_tool(facts, tool):
    return next(
        fact
        for fact in facts
        if fact.name == "gstreamer_tool_available" and fact.metadata["tool"] == tool
    )


def _fact_by_element(facts, element):
    return next(
        fact
        for fact in facts
        if fact.name == "gstreamer_element_available"
        and fact.metadata["element"] == element
    )


def _version_fact(facts):
    return next(fact for fact in facts if fact.name == "gstreamer_version")


def test_gstreamer_tools_available_and_version_is_normalized(monkeypatch) -> None:
    def fake_which(command):
        return f"/usr/bin/{command}"

    def fake_run(command, check, capture_output, text, timeout):
        assert check is False
        assert capture_output is True
        assert text is True
        assert timeout == 5
        if command == ["gst-launch-1.0", "--version"]:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout="gst-launch-1.0 version 1.22.8\nGStreamer 1.22.8\n",
                stderr="",
            )
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr("shutil.which", fake_which)
    monkeypatch.setattr("subprocess.run", fake_run)

    facts = inspect_gstreamer_environment(elements=[])

    assert _fact_by_tool(facts, "gst-launch-1.0").value is True
    assert _fact_by_tool(facts, "gst-inspect-1.0").value is True
    assert _fact_by_tool(facts, "gst-launch-1.0").metadata["path"] == (
        "/usr/bin/gst-launch-1.0"
    )

    version_fact = _version_fact(facts)
    assert version_fact.value == "1.22.8"
    assert version_fact.metadata["available"] is True


def test_missing_gstreamer_tools_return_unavailable_facts(monkeypatch) -> None:
    monkeypatch.setattr("shutil.which", lambda command: None)

    facts = inspect_gstreamer_environment(elements=["v4l2src"])

    assert _fact_by_tool(facts, "gst-launch-1.0").value is False
    assert _fact_by_tool(facts, "gst-inspect-1.0").value is False
    assert _fact_by_element(facts, "v4l2src").value is False

    version_fact = _version_fact(facts)
    assert version_fact.value is None
    assert version_fact.metadata["available"] is False


def test_version_fact_reports_unavailable_when_parsing_fails(monkeypatch) -> None:
    def fake_which(command):
        return f"/usr/bin/{command}"

    def fake_run(command, check, capture_output, text, timeout):
        if command == ["gst-launch-1.0", "--version"]:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout="gst-launch-1.0 custom output\n",
                stderr="",
            )
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr("shutil.which", fake_which)
    monkeypatch.setattr("subprocess.run", fake_run)

    facts = inspect_gstreamer_environment(elements=[])

    version_fact = _version_fact(facts)
    assert version_fact.value is None
    assert version_fact.metadata["available"] is False


def test_element_availability_is_reported_per_element(monkeypatch) -> None:
    def fake_which(command):
        return f"/usr/bin/{command}"

    def fake_run(command, check, capture_output, text, timeout):
        if command == ["gst-launch-1.0", "--version"]:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout="GStreamer 1.20.3\n",
                stderr="",
            )
        if command == ["gst-inspect-1.0", "v4l2src"]:
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        if command == ["gst-inspect-1.0", "nvjpegdec"]:
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="")
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr("shutil.which", fake_which)
    monkeypatch.setattr("subprocess.run", fake_run)

    facts = inspect_gstreamer_environment(elements=["v4l2src", "nvjpegdec"])

    assert _fact_by_element(facts, "v4l2src").value is True
    assert _fact_by_element(facts, "nvjpegdec").value is False


def test_default_elements_include_generic_video_preview_requirements() -> None:
    assert "v4l2src" in DEFAULT_GSTREAMER_ELEMENTS
    assert "videoconvert" in DEFAULT_GSTREAMER_ELEMENTS
    assert "autovideosink" in DEFAULT_GSTREAMER_ELEMENTS


def test_subprocess_failure_does_not_raise(monkeypatch) -> None:
    monkeypatch.setattr("shutil.which", lambda command: f"/usr/bin/{command}")

    def fake_run(command, check, capture_output, text, timeout):
        raise FileNotFoundError(command[0])

    monkeypatch.setattr("subprocess.run", fake_run)

    facts = inspect_gstreamer_environment(elements=["alsasrc"])

    version_fact = _version_fact(facts)
    assert version_fact.value is None
    assert version_fact.metadata["available"] is False
    assert _fact_by_element(facts, "alsasrc").value is False
