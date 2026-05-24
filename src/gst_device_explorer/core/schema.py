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
        purpose="Stable wrapper for selected machine-readable JSON outputs.",
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
