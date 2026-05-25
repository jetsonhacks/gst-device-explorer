"""V4L2 video device discovery probes."""

from __future__ import annotations

from pathlib import Path
import re
import shutil
import stat
import subprocess

from gst_device_explorer.core.models import (
    CameraControl,
    CameraControlChoice,
    CameraControlSet,
    Capability,
    Device,
)


V4L2_CTL = "v4l2-ctl"


def discover_v4l2_video_devices(device_dir: str | Path = "/dev") -> list[Device]:
    """Discover likely V4L2 video input device nodes."""

    root = Path(device_dir)
    if not root.exists() or not root.is_dir():
        return []

    devices: list[Device] = []
    for path in sorted(root.glob("video*")):
        if not path.name.startswith("video"):
            continue

        devices.append(
            Device(
                id=str(path),
                kind="video_input",
                name=path.name,
                metadata={
                    "backend": "v4l2",
                    "path": str(path),
                    "node_name": path.name,
                    "exists": path.exists(),
                    "is_char_device": _is_char_device(path),
                },
            )
        )

    return devices


def discover_v4l2_capabilities(device_path: str | Path) -> list[Capability]:
    """Discover video capabilities for one V4L2 device."""

    if shutil.which(V4L2_CTL) is None:
        return []

    path = Path(device_path)
    result = _run_v4l2_ctl(
        [V4L2_CTL, "--device", str(path), "--list-formats-ext"]
    )
    if result is None or result.returncode != 0:
        return []

    return _parse_v4l2_formats(result.stdout, device_path=str(path))


def discover_v4l2_controls(device_path: str | Path) -> CameraControlSet:
    """Discover advertised V4L2 controls for one video device.

    This is read-only. It calls `v4l2-ctl --list-ctrls-menus` and never writes
    controls or invokes `--set-ctrl`.
    """

    path = Path(device_path)
    if shutil.which(V4L2_CTL) is None:
        return CameraControlSet(device_path=str(path), source=V4L2_CTL)

    result = _run_v4l2_ctl(
        [V4L2_CTL, "--device", str(path), "--list-ctrls-menus"]
    )
    if result is None or result.returncode != 0:
        return CameraControlSet(device_path=str(path), source=V4L2_CTL)

    return _parse_v4l2_controls(result.stdout, device_path=str(path))


def _is_char_device(path: Path) -> bool:
    try:
        return stat.S_ISCHR(path.stat().st_mode)
    except OSError:
        return False


def _run_v4l2_ctl(command: list[str]) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.SubprocessError, OSError):
        return None


def _parse_v4l2_formats(output: str, device_path: str) -> list[Capability]:
    capabilities: list[Capability] = []
    current_format: dict[str, str] | None = None
    current_size: dict[str, int | list[float]] | None = None

    for line in output.splitlines():
        format_match = re.search(r"\[\d+\]:\s+'([^']+)'\s+\((.*)\)", line)
        if format_match is not None:
            _append_video_capability(
                capabilities=capabilities,
                device_path=device_path,
                current_format=current_format,
                current_size=current_size,
            )
            current_format = {
                "pixel_format": format_match.group(1),
                "description": format_match.group(2),
            }
            current_size = None
            continue

        size_match = re.search(r"Size:\s+Discrete\s+(\d+)x(\d+)", line)
        if size_match is not None:
            _append_video_capability(
                capabilities=capabilities,
                device_path=device_path,
                current_format=current_format,
                current_size=current_size,
            )
            current_size = {
                "width": int(size_match.group(1)),
                "height": int(size_match.group(2)),
                "fps": [],
            }
            continue

        fps_match = re.search(r"\((\d+(?:\.\d+)?)\s+fps\)", line)
        if fps_match is not None and current_size is not None:
            fps_values = current_size["fps"]
            if isinstance(fps_values, list):
                fps_values.append(float(fps_match.group(1)))

    _append_video_capability(
        capabilities=capabilities,
        device_path=device_path,
        current_format=current_format,
        current_size=current_size,
    )
    return capabilities


def _parse_v4l2_controls(output: str, device_path: str) -> CameraControlSet:
    controls: list[CameraControl] = []
    current: dict[str, object] | None = None

    for raw_line in output.splitlines():
        if not raw_line.strip():
            continue
        stripped = raw_line.strip()
        if stripped.endswith("Controls") or stripped.endswith("Controls:"):
            continue

        menu_match = re.match(r"^\s*(\d+)\s*:\s*(.+)$", raw_line)
        if menu_match is not None and current is not None:
            choices = current.setdefault("choices", [])
            if isinstance(choices, list):
                choices.append(
                    CameraControlChoice(
                        value=menu_match.group(1),
                        label=menu_match.group(2).strip(),
                    )
                )
            continue

        control = _finish_control(current, device_path)
        if control is not None:
            controls.append(control)
        current = _parse_control_line(stripped)

    control = _finish_control(current, device_path)
    if control is not None:
        controls.append(control)

    return CameraControlSet(
        device_path=device_path,
        controls=tuple(controls),
        source=V4L2_CTL,
    )


def _parse_control_line(line: str) -> dict[str, object] | None:
    match = re.match(
        r"^(?P<name>\S+)\s+"
        r"(?P<id>0x[0-9a-fA-F]+)\s+"
        r"\((?P<type>[^)]+)\)\s*:\s*"
        r"(?P<body>.*)$",
        line,
    )
    if match is None:
        return None

    body = match.group("body")
    values = dict(re.findall(r"([A-Za-z0-9_-]+)=([^\s,]+)", body))
    flags = _parse_control_flags(body, values)
    return {
        "name": match.group("name"),
        "control_id": match.group("id"),
        "control_type": match.group("type"),
        "values": values,
        "flags": flags,
        "choices": [],
    }


def _finish_control(
    parsed: dict[str, object] | None,
    device_path: str,
) -> CameraControl | None:
    if parsed is None:
        return None
    values = parsed.get("values", {})
    if not isinstance(values, dict):
        values = {}
    choices = parsed.get("choices", [])
    if not isinstance(choices, list):
        choices = []
    flags = parsed.get("flags", [])
    if not isinstance(flags, list):
        flags = []
    name = str(parsed["name"])
    return CameraControl(
        name=name,
        label=name.replace("_", " ").replace("-", " ").title(),
        control_type=str(parsed["control_type"]),
        device_path=device_path,
        control_id=str(parsed["control_id"]),
        current_value=_string_or_none(values.get("value")),
        default_value=_string_or_none(values.get("default")),
        minimum=_string_or_none(values.get("min")),
        maximum=_string_or_none(values.get("max")),
        step=_string_or_none(values.get("step")),
        choices=tuple(choices),
        flags=tuple(flags),
    )


def _parse_control_flags(body: str, values: dict[str, str]) -> list[str]:
    result: list[str] = []
    flag_value = values.get("flags")
    if flag_value:
        result.extend(part.strip() for part in flag_value.split(",") if part.strip())

    segments = [segment.strip() for segment in body.split(",")]
    for segment in segments[1:]:
        if segment and "=" not in segment:
            result.append(segment)
    return sorted(set(result))


def _string_or_none(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _append_video_capability(
    capabilities: list[Capability],
    device_path: str,
    current_format: dict[str, str] | None,
    current_size: dict[str, int | list[float]] | None,
) -> None:
    if current_format is None or current_size is None:
        return

    fps_values = current_size.get("fps", [])
    fps = fps_values if isinstance(fps_values, list) else []
    width = current_size["width"]
    height = current_size["height"]
    pixel_format = current_format["pixel_format"]
    description = current_format["description"]

    capabilities.append(
        Capability(
            name="video_format",
            values={
                "media_type": "video",
                "pixel_format": pixel_format,
                "raw_pixel_format": pixel_format,
                "description": description,
                "width": width,
                "height": height,
                "size": {"width": width, "height": height},
                "fps": fps,
                "device_path": device_path,
            },
            source=V4L2_CTL,
        )
    )
