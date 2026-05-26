"""Camera-oriented GUI adapter models."""

from __future__ import annotations

from dataclasses import dataclass

from gst_device_explorer.core.models import CameraControlSet, Capability, Device
from gst_device_explorer.gui.model import DetailSection, GuiAction


@dataclass(frozen=True)
class CameraFrameRateOption:
    """One selectable frame-rate option for a camera resolution."""

    fps: float
    label: str


@dataclass(frozen=True)
class CameraResolutionOption:
    """One selectable resolution for a camera pixel format."""

    width: int
    height: int
    frame_rates: tuple[CameraFrameRateOption, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "frame_rates", tuple(self.frame_rates))

    @property
    def label(self) -> str:
        return f"{self.width}x{self.height}"


@dataclass(frozen=True)
class CameraFormatOption:
    """One selectable pixel format with supported resolutions."""

    pixel_format: str
    description: str | None = None
    media_type: str = "video/x-raw"
    resolutions: tuple[CameraResolutionOption, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "resolutions", tuple(self.resolutions))

    @property
    def label(self) -> str:
        if self.description:
            return f"{self.pixel_format} ({self.description})"
        return self.pixel_format


@dataclass(frozen=True)
class CameraExplorerState:
    """Task-oriented camera explorer state for one selected camera."""

    device_path: str
    display_name: str
    formats: tuple[CameraFormatOption, ...] = ()
    selected_format: str | None = None
    selected_resolution: str | None = None
    selected_frame_rate: str | None = None
    pipeline_text: str | None = None
    unavailable_reason: str | None = None
    control_set: CameraControlSet | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "formats", tuple(self.formats))


def build_camera_explorer_state(
    device: Device,
    *,
    control_set: CameraControlSet | None = None,
) -> CameraExplorerState:
    """Build camera explorer state from normalized device capabilities."""

    device_path = _device_path(device)
    formats = _format_options(device.capabilities)
    selected_format = formats[0].pixel_format if formats else None
    selected_resolution = formats[0].resolutions[0].label if formats and formats[0].resolutions else None
    rates = formats[0].resolutions[0].frame_rates if formats and formats[0].resolutions else ()
    selected_rate = rates[0].label if rates else None
    pipeline = (
        build_camera_pipeline_text(
            device_path=device_path,
            pixel_format=selected_format,
            resolution=selected_resolution,
            frame_rate=selected_rate,
            media_type=formats[0].media_type if formats else None,
        )
        if selected_format and selected_resolution
        else None
    )
    return CameraExplorerState(
        device_path=device_path,
        display_name=device.name or device_path,
        formats=formats,
        selected_format=selected_format,
        selected_resolution=selected_resolution,
        selected_frame_rate=selected_rate,
        pipeline_text=pipeline,
        unavailable_reason=None if pipeline else "No supported camera mode is available.",
        control_set=control_set,
    )


def camera_explorer_sections(state: CameraExplorerState) -> tuple[DetailSection, ...]:
    """Build detail sections consumed by the Qt camera pane."""

    format_items = []
    for fmt in state.formats:
        resolutions = ", ".join(resolution.label for resolution in fmt.resolutions) or "No resolutions"
        format_items.append(f"{fmt.pixel_format}: {resolutions}")

    rate_items = []
    for fmt in state.formats:
        for resolution in fmt.resolutions:
            rates = ", ".join(rate.label for rate in resolution.frame_rates) or "No frame rates"
            rate_items.append(f"{fmt.pixel_format} {resolution.label}: {rates}")

    control_items = []
    if state.control_set is None or not state.control_set.controls:
        control_items.append("No V4L2 controls advertised.")
    else:
        for control in state.control_set.controls:
            parts = [
                f"type={control.control_type}",
                f"value={control.current_value}" if control.current_value is not None else "value=",
            ]
            if control.minimum is not None and control.maximum is not None:
                parts.append(f"range={control.minimum}..{control.maximum}")
            if control.step is not None:
                parts.append(f"step={control.step}")
            if control.default_value is not None:
                parts.append(f"default={control.default_value}")
            if control.flags:
                parts.append("flags=" + ",".join(control.flags))
            if control.choices:
                parts.append(
                    "choices="
                    + "|".join(f"{choice.value}={choice.label}" for choice in control.choices)
                )
            control_items.append(f"{control.name}: " + "; ".join(parts))

    return (
        DetailSection(
            title="Camera Explorer",
            items=(
                f"Device: {state.device_path}",
                f"Selected format: {state.selected_format or 'unavailable'}",
                f"Selected resolution: {state.selected_resolution or 'unavailable'}",
                f"Selected frame rate: {state.selected_frame_rate or 'unavailable'}",
            ),
        ),
        DetailSection(
            title="Camera Modes",
            items=tuple(format_items) or ("No supported camera modes discovered.",),
        ),
        DetailSection(
            title="Frame Rates",
            items=tuple(rate_items) or ("No frame rates discovered for the selected format.",),
        ),
        DetailSection(
            title="Generated Pipeline",
            items=(state.pipeline_text or state.unavailable_reason or "Pipeline unavailable.",),
        ),
        DetailSection(
            title="V4L2 Controls",
            items=tuple(control_items),
        ),
    )


def camera_copy_actions(state: CameraExplorerState) -> tuple[GuiAction, ...]:
    """Build copy-only GUI actions for camera explorer text."""

    actions = [
        GuiAction(
            id=f"copy-camera-device:{state.device_path}",
            label="Copy Device",
            kind="copy_command",
            enabled=True,
            safety="inspection",
            target_kind="video",
            target=state.device_path,
        )
    ]
    if state.pipeline_text:
        actions.append(
            GuiAction(
                id=f"copy-camera-pipeline:{state.device_path}",
                label="Copy Pipeline",
                kind="copy_pipeline",
                enabled=True,
                safety="inspection",
                target_kind="video",
                target=state.pipeline_text,
            )
        )
    return tuple(actions)


def build_camera_pipeline_text(
    *,
    device_path: str,
    pixel_format: str | None,
    resolution: str | None,
    frame_rate: str | None,
    media_type: str | None = None,
) -> str | None:
    """Build display-only GStreamer pipeline text for a camera mode."""

    if not pixel_format or not resolution:
        return None
    width, height = resolution.split("x", 1)
    caps_media_type = media_type or ("image/jpeg" if pixel_format == "MJPG" else "video/x-raw")
    caps_parts = [caps_media_type, f"width={width}", f"height={height}"]
    if caps_media_type == "video/x-raw":
        gst_format = "YUY2" if pixel_format == "YUYV" else pixel_format
        caps_parts.append(f"format={gst_format}")
    if frame_rate:
        caps_parts.append(f"framerate={_fps_fraction(frame_rate)}")
    decode = " ! jpegparse ! jpegdec" if caps_media_type == "image/jpeg" else ""
    return f"gst-launch-1.0 v4l2src device={device_path} ! " + ",".join(caps_parts) + (
        f"{decode} ! videoconvert ! autovideosink sync=false"
    )


def _format_options(capabilities: list[Capability]) -> tuple[CameraFormatOption, ...]:
    grouped: dict[str, dict[str, object]] = {}
    for capability in capabilities:
        values = capability.values
        media_type_value = values.get("media_type")
        if media_type_value is not None and media_type_value != "video":
            continue
        pixel_format = str(values.get("pixel_format") or values.get("raw_pixel_format") or "")
        if not pixel_format:
            continue
        width = values.get("width")
        height = values.get("height")
        if not isinstance(width, int) or not isinstance(height, int):
            continue
        fps_values = values.get("fps", [])
        if isinstance(fps_values, (int, float)):
            fps_values = [float(fps_values)]
        elif not isinstance(fps_values, list):
            fps_values = []
        entry = grouped.setdefault(
            pixel_format,
            {
                "description": values.get("description"),
                "media_type": "image/jpeg" if pixel_format == "MJPG" else "video/x-raw",
                "resolutions": {},
            },
        )
        resolutions = entry["resolutions"]
        if not isinstance(resolutions, dict):
            continue
        rates = tuple(
            CameraFrameRateOption(fps=float(rate), label=_format_fps(float(rate)))
            for rate in fps_values
        )
        resolutions[(width, height)] = CameraResolutionOption(width=width, height=height, frame_rates=rates)

    result = []
    for pixel_format in sorted(grouped):
        entry = grouped[pixel_format]
        resolutions = entry["resolutions"]
        if not isinstance(resolutions, dict):
            resolutions = {}
        result.append(
            CameraFormatOption(
                pixel_format=pixel_format,
                description=str(entry["description"]) if entry.get("description") else None,
                media_type=str(entry["media_type"]),
                resolutions=tuple(resolutions[key] for key in sorted(resolutions)),
            )
        )
    return tuple(result)


def _find_format(state: CameraExplorerState) -> CameraFormatOption | None:
    for fmt in state.formats:
        if fmt.pixel_format == state.selected_format:
            return fmt
    return state.formats[0] if state.formats else None


def _device_path(device: Device) -> str:
    value = device.metadata.get("path")
    if isinstance(value, str) and value:
        return value
    return device.id


def _format_fps(value: float) -> str:
    if value.is_integer():
        return f"{int(value)} fps"
    return f"{value:g} fps"


def _fps_fraction(label: str) -> str:
    value = label.removesuffix(" fps").strip()
    try:
        fps = float(value)
    except ValueError:
        return value
    if fps.is_integer():
        return f"{int(fps)}/1"
    return f"{round(fps * 1000)}/1000"
