"""Normalized data models for gst-device-explorer.

These models are intentionally small. They describe discovered data and
recommendations without performing probing, pipeline selection, or rendering.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Capability:
    """Something a device can do, produce, or report."""

    name: str
    values: dict[str, Any] = field(default_factory=dict)
    source: str | None = None


@dataclass(frozen=True)
class Device:
    """A discovered thing attached to or exposed by the system."""

    id: str
    kind: str
    name: str
    capabilities: list[Capability] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EnvironmentFact:
    """A fact about the host system or media stack."""

    name: str
    value: Any
    source: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Profile:
    """A named set of preferences or known-good patterns."""

    name: str
    description: str = ""
    preferences: list[str] = field(default_factory=list)
    known_good_patterns: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PipelineCandidate:
    """A structured recommendation for a GStreamer pipeline."""

    purpose: str
    command: str
    confidence: float
    candidate_id: str = ""
    argv: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    required_elements: list[str] = field(default_factory=list)
    selected_profile: str | None = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")


@dataclass(frozen=True)
class ExecutionPlan:
    """A selected pipeline candidate prepared for safe execution."""

    candidate_id: str
    argv: list[str]
    display_command: str
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RendererOutput:
    """A presentation of model data for a user or tool."""

    kind: str
    content: Any
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
