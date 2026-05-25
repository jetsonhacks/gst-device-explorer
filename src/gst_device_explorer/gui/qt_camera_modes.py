"""Camera mode parsing and pipeline helpers for the Qt camera explorer."""

from __future__ import annotations

from gst_device_explorer.gui.model import DetailPaneModel, DetailSection
from gst_device_explorer.gui.qt_sections import target_from_summary


def camera_section(detail: DetailPaneModel, title: str) -> DetailSection | None:
    return next((section for section in detail.sections if section.title == title), None)


def camera_mode_tree(detail: DetailPaneModel) -> dict[str, dict[str, tuple[str, ...]]]:
    """Return selectable camera modes grouped by format and resolution."""

    raw = _raw_camera_mode_tree(detail)
    if raw:
        return raw

    modes = camera_section(detail, "Camera Modes")
    rates = camera_section(detail, "Frame Rates")
    result: dict[str, dict[str, tuple[str, ...]]] = {}
    if modes is None:
        return result

    rate_by_resolution: dict[str, tuple[str, ...]] = {}
    if rates is not None:
        for item in rates.items:
            if ":" not in item:
                continue
            key, values = item.split(":", 1)
            rate_by_resolution[key.strip()] = tuple(
                value.strip() for value in values.split(",") if value.strip()
            )

    for item in modes.items:
        if ":" not in item:
            continue
        pixel_format, values = item.split(":", 1)
        resolutions = tuple(value.strip() for value in values.split(",") if value.strip())
        if not resolutions:
            continue
        fmt = pixel_format.strip()
        result[fmt] = {
            resolution: rate_by_resolution.get(
                f"{fmt} {resolution}",
                rate_by_resolution.get(resolution, ()),
            )
            for resolution in resolutions
        }
    return result


def format_labels(detail: DetailPaneModel) -> dict[str, str]:
    labels: dict[str, str] = {}
    raw = camera_section(detail, "Raw Camera Capabilities")
    if raw is not None:
        for item in raw.items:
            values = _raw_capability_values(item)
            pixel_format = values.get("pixel_format")
            if not pixel_format:
                continue
            description = values.get("description")
            if description:
                labels[pixel_format] = f"{pixel_format} ({description})"
            else:
                labels.setdefault(pixel_format, pixel_format)
        if labels:
            return labels

    capabilities = camera_section(detail, "Capabilities")
    if capabilities is None:
        return labels
    for item in capabilities.items:
        values = _capability_values(item)
        pixel_format = values.get("pixel_format") or values.get("raw_pixel_format")
        if not pixel_format:
            continue
        description = values.get("description")
        if description:
            labels[pixel_format] = f"{pixel_format} ({description})"
        else:
            labels.setdefault(pixel_format, pixel_format)
    return labels


def initial_selected_mode(detail: DetailPaneModel) -> tuple[str, str, str] | None:
    mode_tree = camera_mode_tree(detail)
    for pixel_format, resolutions in mode_tree.items():
        for resolution, rates in resolutions.items():
            return pixel_format, resolution, rates[0] if rates else "Unavailable"
    return None


def selected_mode_text(pixel_format: str, resolution: str, frame_rate: str) -> str:
    if frame_rate and frame_rate != "Unavailable":
        return f"{pixel_format}, {resolution}, {frame_rate}"
    return f"{pixel_format}, {resolution}"


def camera_pipeline_for_selection(
    detail: DetailPaneModel,
    pixel_format: str,
    resolution: str,
    frame_rate: str,
) -> str | None:
    device_path = target_from_summary(detail)
    if (
        device_path is None
        or not pixel_format
        or pixel_format == "Unavailable"
        or not resolution
        or resolution == "Unavailable"
        or "x" not in resolution
    ):
        return None
    width, height = resolution.split("x", 1)
    caps_type = "image/jpeg" if pixel_format == "MJPG" else "video/x-raw"
    caps_parts = [caps_type, f"width={width}", f"height={height}"]
    if caps_type == "video/x-raw":
        caps_parts.append(f"format={pixel_format}")
    if frame_rate and frame_rate != "Unavailable":
        caps_parts.append(f"framerate={_fps_fraction(frame_rate)}")
    return f"gst-launch-1.0 v4l2src device={device_path} ! {','.join(caps_parts)} ! autovideosink"


def _capability_values(item: str) -> dict[str, str]:
    if ": " not in item:
        return {}
    _name, raw_values = item.split(": ", 1)
    result: dict[str, str] = {}
    known_keys = (
        "device_path",
        "fps",
        "height",
        "media_type",
        "pixel_format",
        "raw_pixel_format",
        "width",
    )
    for key in known_keys:
        marker = f", {key}="
        if marker in raw_values:
            prefix, suffix = raw_values.split(marker, 1)
            if prefix.startswith("description="):
                result["description"] = prefix.removeprefix("description=")
            raw_values = f"{key}={suffix}"
            break
    for part in raw_values.split(", "):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        result[key] = value
    return result


def _raw_camera_mode_tree(detail: DetailPaneModel) -> dict[str, dict[str, tuple[str, ...]]]:
    raw = camera_section(detail, "Raw Camera Capabilities")
    result: dict[str, dict[str, tuple[str, ...]]] = {}
    if raw is None:
        return result
    for item in raw.items:
        values = _raw_capability_values(item)
        pixel_format = values.get("pixel_format")
        width = values.get("width")
        height = values.get("height")
        if not pixel_format or not width or not height:
            continue
        resolution = f"{width}x{height}"
        fps_values = tuple(
            _format_fps_label(value)
            for value in values.get("fps", "").split("|")
            if value
        )
        resolutions = result.setdefault(pixel_format, {})
        resolutions[resolution] = fps_values
    return result


def _raw_capability_values(item: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for part in item.split("; "):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        result[key] = value
    return result


def _format_fps_label(value: str) -> str:
    try:
        fps = float(value)
    except ValueError:
        return f"{value} fps"
    if fps.is_integer():
        return f"{int(fps)} fps"
    return f"{fps:g} fps"


def _fps_fraction(label: str) -> str:
    value = label.removesuffix(" fps").strip()
    try:
        fps = float(value)
    except ValueError:
        return value
    if fps.is_integer():
        return f"{int(fps)}/1"
    return f"{round(fps * 1000)}/1000"
