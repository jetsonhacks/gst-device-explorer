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
class PipelineDiagnostic:
    """A structured explanation of one pipeline candidate decision."""

    candidate_id: str
    device_kind: str
    device: str
    status: str
    reason: str
    required_elements: list[str] = field(default_factory=list)
    available_elements: list[str] = field(default_factory=list)
    missing_elements: list[str] = field(default_factory=list)
    suggested_next_checks: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ProfileCandidateSummary:
    """A concise profile summary of one pipeline candidate diagnostic."""

    candidate_id: str
    status: str
    reason: str
    missing_elements: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ProfileGroupSummary:
    """A concise profile summary of one composite group membership."""

    group_id: str
    label: str
    confidence: float
    kind: str
    member_count: int


@dataclass(frozen=True)
class DeviceProfile:
    """A structured endpoint summary built from discovered facts."""

    device_kind: str
    device: str
    display_name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    capabilities_summary: dict[str, Any] = field(default_factory=dict)
    candidate_summary: dict[str, list[ProfileCandidateSummary]] = field(
        default_factory=lambda: {"available": [], "unavailable": []}
    )
    groups: list[ProfileGroupSummary] = field(default_factory=list)
    suggested_next_commands: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ReportDevices:
    """Device lists for a system report, grouped by kind."""

    video: list[Device] = field(default_factory=list)
    audio_inputs: list[Device] = field(default_factory=list)
    audio_outputs: list[Device] = field(default_factory=list)


@dataclass(frozen=True)
class ReportProfiles:
    """Endpoint profile lists for a system report, grouped by kind."""

    video: list[DeviceProfile] = field(default_factory=list)
    audio_inputs: list[DeviceProfile] = field(default_factory=list)
    audio_outputs: list[DeviceProfile] = field(default_factory=list)


@dataclass(frozen=True)
class ReportDiagnostics:
    """Aggregated diagnostic summary for a system report."""

    missing_elements: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SystemReport:
    """A structured snapshot of the full media system state."""

    kind: str
    tool_version: str
    environment: list[EnvironmentFact] = field(default_factory=list)
    devices: ReportDevices = field(default_factory=ReportDevices)
    groups: list[CompositeDevice] = field(default_factory=list)
    profiles: ReportProfiles = field(default_factory=ReportProfiles)
    diagnostics: ReportDiagnostics = field(default_factory=ReportDiagnostics)
    suggested_next_commands: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CandidateRecommendation:
    """One ranked pipeline candidate in a recommendation result."""

    candidate_id: str
    rank: int
    selected_profile: str | None
    available: bool
    score: int
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    missing_elements: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CandidateRanking:
    """Ranked pipeline candidates for one endpoint."""

    kind: str
    endpoint_kind: str
    endpoint: str
    recommended_candidate_id: str | None
    ranked_candidates: list[CandidateRecommendation] = field(default_factory=list)


@dataclass(frozen=True)
class ExecutionPlan:
    """A selected pipeline candidate prepared for safe execution."""

    candidate_id: str
    argv: list[str]
    display_command: str
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DeviceRef:
    """A reference to a discovered device inside a composite device."""

    role: str
    device_id: str
    path: str | None
    subsystem: str


@dataclass(frozen=True)
class GroupingEvidence:
    """Evidence used to group devices into a composite device."""

    source: str
    description: str
    strength: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.strength <= 1.0:
            raise ValueError("strength must be between 0.0 and 1.0")


@dataclass(frozen=True)
class CompositeDevice:
    """A grouped physical or logical device with evidence-backed members."""

    id: str
    name: str
    kind: str
    confidence: float
    members: list[DeviceRef] = field(default_factory=list)
    evidence: list[GroupingEvidence] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")


