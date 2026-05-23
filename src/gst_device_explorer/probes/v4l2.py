"""V4L2 video device discovery probes."""

from __future__ import annotations

from pathlib import Path
import stat

from gst_device_explorer.core import Device


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


def _is_char_device(path: Path) -> bool:
    try:
        return stat.S_ISCHR(path.stat().st_mode)
    except OSError:
        return False
