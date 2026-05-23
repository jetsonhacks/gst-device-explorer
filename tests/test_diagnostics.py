from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.core.diagnostics import (
    available_required_elements,
    missing_required_elements,
    suggest_gst_inspect_checks,
)
from gst_device_explorer.core.models import EnvironmentFact


def test_available_required_elements_preserves_required_order() -> None:
    environment = [
        _element_fact("autovideosink", True),
        _element_fact("v4l2src", True),
        _element_fact("videoconvert", False),
    ]

    available = available_required_elements(
        environment,
        ["v4l2src", "videoconvert", "autovideosink"],
    )

    assert available == ["v4l2src", "autovideosink"]


def test_missing_required_elements_preserves_required_order() -> None:
    missing = missing_required_elements(
        ["v4l2src", "videoconvert", "autovideosink"],
        ["v4l2src"],
    )

    assert missing == ["videoconvert", "autovideosink"]


def test_suggest_gst_inspect_checks_for_missing_elements() -> None:
    checks = suggest_gst_inspect_checks(["videoconvert", "autovideosink"])

    assert checks == [
        "gst-inspect-1.0 videoconvert",
        "gst-inspect-1.0 autovideosink",
    ]


def _element_fact(element: str, available: bool) -> EnvironmentFact:
    return EnvironmentFact(
        name="gstreamer_element_available",
        value=available,
        source="gst-inspect-1.0",
        metadata={"element": element},
    )
