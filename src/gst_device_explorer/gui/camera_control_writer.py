"""Structured camera-control write requests for the Qt layer."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import gst_device_explorer.probes.v4l2 as v4l2_probe


@dataclass(frozen=True)
class CameraControlWriteRequest:
    """One structured camera-control write for the selected endpoint."""

    endpoint: str
    control_name: str
    value: str
    control_id: str | None = None
    control_type: str | None = None

    def __post_init__(self) -> None:
        if not self.endpoint:
            raise ValueError("camera-control writes require an endpoint")
        if not self.control_name:
            raise ValueError("camera-control writes require a discovered control name")


@dataclass(frozen=True)
class CameraControlWriteResult:
    """Result of one camera-control write attempt."""

    success: bool
    message: str = ""


class CameraControlWriter:
    """Small GUI-facing adapter for scoped V4L2 control writes."""

    def __init__(
        self,
        *,
        write_control: Callable[[str, str, str], CameraControlWriteResult | bool] | None = None,
    ) -> None:
        self._write_control = write_control

    def write(self, request: CameraControlWriteRequest) -> CameraControlWriteResult:
        if self._write_control is not None:
            result = self._write_control(request.endpoint, request.control_name, request.value)
            if isinstance(result, CameraControlWriteResult):
                return result
            return CameraControlWriteResult(bool(result))

        result = v4l2_probe.write_v4l2_control(
            request.endpoint,
            request.control_name,
            request.value,
        )
        if result is None:
            return CameraControlWriteResult(False, "Camera control write failed.")
        if result.returncode == 0:
            return CameraControlWriteResult(True)
        message = (result.stderr or result.stdout or "Camera control write failed.").strip()
        return CameraControlWriteResult(False, message)
