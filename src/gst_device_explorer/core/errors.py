"""Structured JSON error response model.

Error responses are advisory metadata. Recovery commands are never executed automatically.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from gst_device_explorer.core.suggestions import SuggestedCommand


@dataclass(frozen=True)
class ErrorResponse:
    """Structured error payload for selected known JSON error paths."""

    code: str
    message: str
    details: Mapping[str, object] = field(default_factory=dict)
    suggested_commands: tuple[SuggestedCommand, ...] = ()
