"""GStreamer environment inspection probes."""

from __future__ import annotations

import re
import shutil
import subprocess

from gst_device_explorer.core.models import EnvironmentFact


GST_LAUNCH = "gst-launch-1.0"
GST_INSPECT = "gst-inspect-1.0"

DEFAULT_GSTREAMER_ELEMENTS = [
    "v4l2src",
    "videoconvert",
    "autovideosink",
    "alsasrc",
    "alsasink",
    "audioconvert",
    "audioresample",
    "audiotestsrc",
    "autoaudiosrc",
    "autoaudiosink",
    "level",
    "fakesink",
    "jpegparse",
    "nvjpegdec",
    "nvv4l2decoder",
    "nvvidconv",
    "nveglglessink",
    "nv3dsink",
    "xvimagesink",
]


def inspect_gstreamer_environment(
    elements: list[str] | None = None,
) -> list[EnvironmentFact]:
    """Inspect local GStreamer tools and selected element availability."""

    selected_elements = elements if elements is not None else DEFAULT_GSTREAMER_ELEMENTS
    facts: list[EnvironmentFact] = []

    gst_launch_path = shutil.which(GST_LAUNCH)
    gst_inspect_path = shutil.which(GST_INSPECT)

    facts.append(
        EnvironmentFact(
            name="gstreamer_tool_available",
            value=gst_launch_path is not None,
            source=GST_LAUNCH,
            metadata={"tool": GST_LAUNCH, "path": gst_launch_path},
        )
    )
    facts.append(
        EnvironmentFact(
            name="gstreamer_tool_available",
            value=gst_inspect_path is not None,
            source=GST_INSPECT,
            metadata={"tool": GST_INSPECT, "path": gst_inspect_path},
        )
    )

    version = _get_gstreamer_version() if gst_launch_path is not None else None
    facts.append(
        EnvironmentFact(
            name="gstreamer_version",
            value=version,
            source=GST_LAUNCH,
            metadata={"available": version is not None},
        )
    )

    if gst_inspect_path is None:
        for element in selected_elements:
            facts.append(_element_fact(element=element, available=False))
        return facts

    for element in selected_elements:
        facts.append(
            _element_fact(
                element=element,
                available=_is_gstreamer_element_available(element),
            )
        )

    return facts


def _get_gstreamer_version() -> str | None:
    result = _run_command([GST_LAUNCH, "--version"])
    if result is None or result.returncode != 0:
        return None

    output = f"{result.stdout}\n{result.stderr}"
    match = re.search(r"GStreamer\s+(\d+(?:\.\d+)+)", output)
    if match is None:
        return None
    return match.group(1)


def _is_gstreamer_element_available(element: str) -> bool:
    result = _run_command([GST_INSPECT, element])
    return result is not None and result.returncode == 0


def _element_fact(element: str, available: bool) -> EnvironmentFact:
    return EnvironmentFact(
        name="gstreamer_element_available",
        value=available,
        source=GST_INSPECT,
        metadata={"element": element},
    )


def _run_command(command: list[str]) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.SubprocessError, OSError):
        return None
