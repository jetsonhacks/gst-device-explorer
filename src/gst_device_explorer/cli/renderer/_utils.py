"""Shared JSON printing utilities for CLI renderers."""

from __future__ import annotations

import json

from gst_device_explorer.cli.serializers import make_error_envelope
from gst_device_explorer.core.errors import ErrorResponse
from gst_device_explorer.core.schema import wrap_json


def _print_json(kind: str, data) -> None:
    print(json.dumps(wrap_json(kind, data), indent=2, sort_keys=True))


def print_json_error(error: ErrorResponse) -> None:
    print(json.dumps(make_error_envelope(error), indent=2, sort_keys=True))
