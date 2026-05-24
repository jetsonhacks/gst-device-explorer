"""Support bundle models and output path validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SupportBundleFile:
    """Describes one file written into a support bundle."""

    path: str
    kind: str
    description: str
    required: bool


@dataclass(frozen=True)
class SupportBundleManifest:
    """Manifest describing a support bundle export."""

    schema_version: str
    tool_version: str
    kind: str
    created_at: str
    bundle_format: str
    files: tuple[SupportBundleFile, ...]
    warnings: tuple[str, ...]
    notes: tuple[str, ...]


def validate_bundle_output_path(path: Path) -> None:
    """Validate the output path for a support bundle.

    Raises:
        FileExistsError: if the path already exists.
        ValueError: if the parent directory is missing or is not a directory.
    """
    if path.exists():
        raise FileExistsError(f"Output path already exists: {path}")
    parent = path.parent
    if not parent.exists():
        raise ValueError(f"Parent directory does not exist: {parent}")
    if not parent.is_dir():
        raise ValueError(f"Parent path is not a directory: {parent}")
