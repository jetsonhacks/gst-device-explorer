"""Machine-readable schema envelope helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from gst_device_explorer import __version__


JSON_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class JsonEnvelope:
    """Stable envelope used by selected JSON command outputs."""

    schema_version: str
    tool_version: str
    kind: str
    data: Any


@dataclass(frozen=True)
class SchemaField:
    """One documented field in a schema discovery entry."""

    name: str
    value_type: str
    description: str


@dataclass(frozen=True)
class SchemaDocument:
    """Small schema discovery document exposed by the CLI."""

    schema_id: str
    title: str
    purpose: str
    fields: tuple[SchemaField, ...]
    current_schema_version: str | None = None


_SCHEMA_DOCUMENTS = (
    SchemaDocument(
        schema_id="json-envelope",
        title="JSON Envelope",
        purpose="Stable wrapper for selected machine-readable JSON success outputs.",
        current_schema_version=JSON_SCHEMA_VERSION,
        fields=(
            SchemaField(
                name="schema_version",
                value_type="string",
                description="Envelope compatibility version.",
            ),
            SchemaField(
                name="tool_version",
                value_type="string",
                description="gst-device-explorer package version.",
            ),
            SchemaField(
                name="kind",
                value_type="string",
                description="Stable response kind identifier.",
            ),
            SchemaField(
                name="data",
                value_type="any",
                description="Command-specific response payload.",
            ),
        ),
    ),
    SchemaDocument(
        schema_id="error-envelope",
        title="Error Envelope",
        purpose="Stable wrapper for selected machine-readable JSON error responses.",
        current_schema_version=JSON_SCHEMA_VERSION,
        fields=(
            SchemaField(
                name="schema_version",
                value_type="string",
                description="Envelope compatibility version.",
            ),
            SchemaField(
                name="tool_version",
                value_type="string",
                description="gst-device-explorer package version.",
            ),
            SchemaField(
                name="kind",
                value_type="string",
                description='Always \"error\" for error responses.',
            ),
            SchemaField(
                name="error.code",
                value_type="string",
                description="Stable snake_case machine-readable error code.",
            ),
            SchemaField(
                name="error.message",
                value_type="string",
                description="Human-readable error message.",
            ),
            SchemaField(
                name="error.details",
                value_type="object",
                description="Optional command-specific detail fields.",
            ),
            SchemaField(
                name="error.suggested_commands",
                value_type="array",
                description="Advisory suggested commands for recovery. Never executed automatically.",
            ),
        ),
    ),
    SchemaDocument(
        schema_id="audio_input_candidates",
        title="Audio Input Candidates",
        purpose="Envelope kind for ALSA audio input pipeline candidate JSON.",
        fields=(),
    ),
    SchemaDocument(
        schema_id="audio_inputs",
        title="Audio Inputs",
        purpose="Envelope kind for ALSA audio input discovery JSON.",
        fields=(),
    ),
    SchemaDocument(
        schema_id="audio_output_candidates",
        title="Audio Output Candidates",
        purpose="Envelope kind for ALSA audio output pipeline candidate JSON.",
        fields=(),
    ),
    SchemaDocument(
        schema_id="audio_outputs",
        title="Audio Outputs",
        purpose="Envelope kind for ALSA audio output discovery JSON.",
        fields=(),
    ),
    SchemaDocument(
        schema_id="candidate_recommendation",
        title="Candidate Recommendation",
        purpose="Envelope kind for endpoint recommendation JSON.",
        fields=(),
    ),
    SchemaDocument(
        schema_id="composite_group",
        title="Composite Group",
        purpose="Envelope kind for one composite device group JSON.",
        fields=(),
    ),
    SchemaDocument(
        schema_id="composite_groups",
        title="Composite Groups",
        purpose="Envelope kind for composite device group listing JSON.",
        fields=(),
    ),
    SchemaDocument(
        schema_id="device_profile",
        title="Device Profile",
        purpose="Envelope kind for endpoint profile JSON.",
        fields=(),
    ),
    SchemaDocument(
        schema_id="devices",
        title="Devices",
        purpose="Envelope kind for combined device discovery JSON.",
        fields=(),
    ),
    SchemaDocument(
        schema_id="environment",
        title="Environment",
        purpose="Envelope kind for GStreamer environment inspection JSON.",
        fields=(),
    ),
    SchemaDocument(
        schema_id="group_validation",
        title="Group Validation",
        purpose="Envelope kind for composite group validation JSON.",
        fields=(),
    ),
    SchemaDocument(
        schema_id="grouping_metadata",
        title="Grouping Metadata",
        purpose="Envelope kind for grouping evidence metadata JSON.",
        fields=(),
    ),
    SchemaDocument(
        schema_id="pipeline_diagnostics",
        title="Pipeline Diagnostics",
        purpose="Envelope kind for pipeline diagnostic JSON.",
        fields=(),
    ),
    SchemaDocument(
        schema_id="system_report",
        title="System Report",
        purpose="Envelope kind for system report JSON.",
        fields=(),
    ),
    SchemaDocument(
        schema_id="video_candidates",
        title="Video Candidates",
        purpose="Envelope kind for video pipeline candidate JSON.",
        fields=(),
    ),
    SchemaDocument(
        schema_id="video_capabilities",
        title="Video Capabilities",
        purpose="Envelope kind for V4L2 capability JSON.",
        fields=(),
    ),
    SchemaDocument(
        schema_id="support_bundle_manifest",
        title="Support Bundle Manifest",
        purpose="Envelope kind for the support bundle manifest JSON written to manifest.json.",
        fields=(
            SchemaField(
                name="bundle_format",
                value_type="string",
                description='Bundle storage format. Currently always "directory".',
            ),
            SchemaField(
                name="created_at",
                value_type="string",
                description="ISO 8601 UTC timestamp of bundle creation.",
            ),
            SchemaField(
                name="files",
                value_type="array",
                description="List of files written into the bundle.",
            ),
            SchemaField(
                name="kind",
                value_type="string",
                description='Always "support_bundle_manifest".',
            ),
            SchemaField(
                name="notes",
                value_type="array",
                description="Informational notes about the bundle.",
            ),
            SchemaField(
                name="schema_version",
                value_type="string",
                description="Manifest schema version.",
            ),
            SchemaField(
                name="tool_version",
                value_type="string",
                description="gst-device-explorer version used to create the bundle.",
            ),
            SchemaField(
                name="warnings",
                value_type="array",
                description="Non-fatal warnings encountered while writing the bundle.",
            ),
        ),
    ),
    SchemaDocument(
        schema_id="suggestion_catalog",
        title="Suggestion Catalog",
        purpose="Envelope kind for the generic suggested command catalog JSON.",
        fields=(
            SchemaField(
                name="suggested_commands",
                value_type="array",
                description="List of generic suggested commands in catalog order.",
            ),
        ),
    ),
    SchemaDocument(
        schema_id="suggested_command",
        title="Suggested Command",
        purpose="Structured advisory command suggestion included in profile, report, and validation JSON payloads.",
        fields=(
            SchemaField(
                name="id",
                value_type="string",
                description="Deterministic slug derived from argv.",
            ),
            SchemaField(
                name="title",
                value_type="string",
                description="Human-readable command title.",
            ),
            SchemaField(
                name="argv",
                value_type="array",
                description="Structured command arguments.",
            ),
            SchemaField(
                name="command",
                value_type="string",
                description="Shell-safe display string rendered from argv.",
            ),
            SchemaField(
                name="purpose",
                value_type="string",
                description="Explanation of why this command is suggested.",
            ),
            SchemaField(
                name="source",
                value_type="string",
                description="Subsystem that generated this suggestion.",
            ),
            SchemaField(
                name="safety",
                value_type="string",
                description="Safety category: inspection, dry_run, bounded_capture, safe_execution, external_check.",
            ),
            SchemaField(
                name="target_kind",
                value_type="string|null",
                description="Optional target device kind.",
            ),
            SchemaField(
                name="target",
                value_type="string|null",
                description="Optional target device or group identifier.",
            ),
            SchemaField(
                name="notes",
                value_type="array",
                description="Optional advisory notes.",
            ),
        ),
    ),
)


def wrap_json(kind: str, data: Any) -> dict[str, Any]:
    """Wrap a command payload in the stable JSON envelope."""

    envelope = JsonEnvelope(
        schema_version=JSON_SCHEMA_VERSION,
        tool_version=__version__,
        kind=kind,
        data=data,
    )
    return {
        "schema_version": envelope.schema_version,
        "tool_version": envelope.tool_version,
        "kind": envelope.kind,
        "data": envelope.data,
    }


def list_schema_documents() -> list[SchemaDocument]:
    """Return schema discovery entries in deterministic order."""

    return list(_SCHEMA_DOCUMENTS)


def get_schema_document(schema_id: str) -> SchemaDocument | None:
    """Return one schema discovery entry by ID."""

    return next(
        (document for document in _SCHEMA_DOCUMENTS if document.schema_id == schema_id),
        None,
    )
