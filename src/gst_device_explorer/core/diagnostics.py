"""Shared pipeline diagnostic helpers."""

from __future__ import annotations

from gst_device_explorer.core.models import EnvironmentFact, PipelineDiagnostic


MISSING_ELEMENTS_REASON = "Required GStreamer elements are missing."


def build_requirement_diagnostic(
    candidate_id: str,
    device_kind: str,
    device_id: str,
    required_elements: list[str],
    environment: list[EnvironmentFact],
    available_reason: str,
) -> PipelineDiagnostic:
    """Build an available/unavailable diagnostic from required elements."""

    available_elements = available_required_elements(environment, required_elements)
    missing_elements = missing_required_elements(required_elements, available_elements)

    if missing_elements:
        return PipelineDiagnostic(
            candidate_id=candidate_id,
            device_kind=device_kind,
            device=device_id,
            status="unavailable",
            reason=MISSING_ELEMENTS_REASON,
            required_elements=list(required_elements),
            available_elements=available_elements,
            missing_elements=missing_elements,
            suggested_next_checks=suggest_gst_inspect_checks(missing_elements),
        )

    return PipelineDiagnostic(
        candidate_id=candidate_id,
        device_kind=device_kind,
        device=device_id,
        status="available",
        reason=available_reason,
        required_elements=list(required_elements),
        available_elements=available_elements,
        missing_elements=[],
        suggested_next_checks=[],
    )


def available_required_elements(
    environment: list[EnvironmentFact],
    required_elements: list[str],
) -> list[str]:
    """Return available required elements in required-element order."""

    available = {
        fact.metadata.get("element")
        for fact in environment
        if fact.name == "gstreamer_element_available" and fact.value is True
    }
    return [element for element in required_elements if element in available]


def missing_required_elements(
    required_elements: list[str],
    available_elements: list[str],
) -> list[str]:
    """Return missing required elements in required-element order."""

    return [element for element in required_elements if element not in available_elements]


def find_missing_elements(
    environment: list[EnvironmentFact],
    required_elements: list[str],
) -> list[str]:
    """Return required elements not available in the environment."""

    available = available_required_elements(environment, required_elements)
    return missing_required_elements(required_elements, available)


def suggest_gst_inspect_checks(missing_elements: list[str]) -> list[str]:
    """Return gst-inspect checks for missing GStreamer elements."""

    return [f"gst-inspect-1.0 {element}" for element in missing_elements]
