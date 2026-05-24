"""Built-in preset catalog and command suggestion builders."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PresetArgument:
    """A named argument accepted by one preset."""

    name: str
    description: str
    required: bool = False


@dataclass(frozen=True)
class PresetCommandSuggestion:
    """A structured command suggestion for an existing CLI workflow."""

    argv: tuple[str, ...]
    dry_run: bool
    description: str


@dataclass(frozen=True)
class PresetDefinition:
    """A built-in named workflow over existing safe commands."""

    preset_id: str
    title: str
    description: str
    target_kind: str
    safety_notes: tuple[str, ...]
    arguments: tuple[PresetArgument, ...] = ()
    related_command: str | None = None


@dataclass(frozen=True)
class PresetCommandRequest:
    """A request to build command suggestions for one preset target."""

    preset_id: str
    target_kind: str
    target: str
    duration: str | None = None
    output: str | None = None


@dataclass(frozen=True)
class PresetCommandSuggestions:
    """Command suggestions generated for a preset target."""

    preset_id: str
    target_kind: str
    target: str
    suggestions: tuple[PresetCommandSuggestion, ...] = field(default_factory=tuple)


class PresetError(ValueError):
    """Base class for preset command suggestion errors."""


class UnknownPresetError(PresetError):
    """Raised when a preset ID is not in the built-in catalog."""


class PresetTargetKindError(PresetError):
    """Raised when a preset is used with the wrong target kind."""


class PresetMissingArgumentError(PresetError):
    """Raised when required preset command arguments are missing."""


_PRESETS: tuple[PresetDefinition, ...] = (
    PresetDefinition(
        preset_id="camera-preview",
        title="Camera Preview",
        description="Preview a video endpoint using the existing safe video run flow.",
        target_kind="video",
        safety_notes=(
            "Uses generated candidates only.",
            "Suggests dry-run first.",
            "Delegates execution to `gst-device-explorer run video`.",
        ),
        related_command="run video",
    ),
    PresetDefinition(
        preset_id="video-diagnostics",
        title="Video Diagnostics",
        description="Explain video candidate availability for a video endpoint.",
        target_kind="video",
        safety_notes=(
            "Inspects generated candidate diagnostics only.",
            "Does not execute GStreamer.",
            "Delegates diagnostics to `gst-device-explorer pipeline video --diagnostics`.",
        ),
        related_command="pipeline video --diagnostics",
    ),
    PresetDefinition(
        preset_id="audio-input-test",
        title="Audio Input Test",
        description="Test an ALSA audio input endpoint using the existing safe run flow.",
        target_kind="audio-input",
        safety_notes=(
            "Uses generated candidates only.",
            "Suggests dry-run first.",
            "Delegates execution to `gst-device-explorer run audio-input`.",
        ),
        related_command="run audio-input",
    ),
    PresetDefinition(
        preset_id="audio-output-test",
        title="Audio Output Test",
        description="Test an ALSA audio output endpoint using the existing safe run flow.",
        target_kind="audio-output",
        safety_notes=(
            "Uses generated candidates only.",
            "Suggests dry-run first.",
            "Delegates execution to `gst-device-explorer run audio-output`.",
        ),
        related_command="run audio-output",
    ),
    PresetDefinition(
        preset_id="short-video-capture",
        title="Short Video Capture",
        description="Suggest a bounded video capture command using the existing capture flow.",
        target_kind="video",
        safety_notes=(
            "Uses generated capture candidates only.",
            "Requires explicit duration and output path.",
            "Suggests dry-run first.",
        ),
        arguments=(
            PresetArgument("duration", "Positive capture duration in seconds.", True),
            PresetArgument("output", "Explicit output path for the captured file.", True),
        ),
        related_command="capture video",
    ),
    PresetDefinition(
        preset_id="short-audio-capture",
        title="Short Audio Capture",
        description="Suggest a bounded audio input capture command using the existing capture flow.",
        target_kind="audio-input",
        safety_notes=(
            "Uses generated capture candidates only.",
            "Requires explicit duration and output path.",
            "Suggests dry-run first.",
        ),
        arguments=(
            PresetArgument("duration", "Positive capture duration in seconds.", True),
            PresetArgument("output", "Explicit output path for the captured file.", True),
        ),
        related_command="capture audio-input",
    ),
    PresetDefinition(
        preset_id="composite-device-validation",
        title="Composite Device Validation",
        description="Validate a discovered composite device group.",
        target_kind="group",
        safety_notes=(
            "Summarizes existing endpoint profiles.",
            "Does not execute group commands.",
            "Delegates validation to `gst-device-explorer validate group`.",
        ),
        related_command="validate group",
    ),
)


def list_presets() -> list[PresetDefinition]:
    """Return the built-in presets in deterministic catalog order."""

    return list(_PRESETS)


def get_preset(preset_id: str) -> PresetDefinition | None:
    """Return one built-in preset by ID."""

    return next(
        (preset for preset in _PRESETS if preset.preset_id == preset_id),
        None,
    )


def build_preset_command_suggestions(
    request: PresetCommandRequest,
) -> PresetCommandSuggestions:
    """Build structured command suggestions for a preset target."""

    preset = get_preset(request.preset_id)
    if preset is None:
        raise UnknownPresetError(f"Preset not found: {request.preset_id}")

    if request.target_kind != preset.target_kind:
        raise PresetTargetKindError(
            f"Preset `{preset.preset_id}` requires target kind `{preset.target_kind}`. "
            f"Received: {request.target_kind}"
        )

    _validate_required_arguments(preset, request)

    return PresetCommandSuggestions(
        preset_id=preset.preset_id,
        target_kind=request.target_kind,
        target=request.target,
        suggestions=tuple(_suggestions_for_request(request)),
    )


def _validate_required_arguments(
    preset: PresetDefinition,
    request: PresetCommandRequest,
) -> None:
    missing = [
        argument.name
        for argument in preset.arguments
        if argument.required and getattr(request, argument.name) is None
    ]
    if missing:
        rendered = " and ".join(f"--{name}" for name in missing)
        raise PresetMissingArgumentError(
            f"Preset `{preset.preset_id}` requires {rendered}."
        )


def _suggestions_for_request(
    request: PresetCommandRequest,
) -> list[PresetCommandSuggestion]:
    if request.preset_id == "camera-preview":
        return [
            PresetCommandSuggestion(
                argv=(
                    "gst-device-explorer",
                    "run",
                    "video",
                    request.target,
                    "--dry-run",
                ),
                dry_run=True,
                description="Inspect the generated video preview command before execution.",
            )
        ]

    if request.preset_id == "video-diagnostics":
        return [
            PresetCommandSuggestion(
                argv=(
                    "gst-device-explorer",
                    "pipeline",
                    "video",
                    request.target,
                    "--diagnostics",
                ),
                dry_run=False,
                description="Explain video candidate availability without execution.",
            )
        ]

    if request.preset_id == "audio-input-test":
        return [
            PresetCommandSuggestion(
                argv=(
                    "gst-device-explorer",
                    "run",
                    "audio-input",
                    request.target,
                    "--dry-run",
                ),
                dry_run=True,
                description="Inspect the generated audio input test command before execution.",
            )
        ]

    if request.preset_id == "audio-output-test":
        return [
            PresetCommandSuggestion(
                argv=(
                    "gst-device-explorer",
                    "run",
                    "audio-output",
                    request.target,
                    "--dry-run",
                ),
                dry_run=True,
                description="Inspect the generated audio output test command before execution.",
            )
        ]

    if request.preset_id == "short-video-capture":
        return [
            PresetCommandSuggestion(
                argv=(
                    "gst-device-explorer",
                    "capture",
                    "video",
                    request.target,
                    "--duration",
                    str(request.duration),
                    "--output",
                    str(request.output),
                    "--dry-run",
                ),
                dry_run=True,
                description="Inspect the bounded video capture command before execution.",
            )
        ]

    if request.preset_id == "short-audio-capture":
        return [
            PresetCommandSuggestion(
                argv=(
                    "gst-device-explorer",
                    "capture",
                    "audio-input",
                    request.target,
                    "--duration",
                    str(request.duration),
                    "--output",
                    str(request.output),
                    "--dry-run",
                ),
                dry_run=True,
                description="Inspect the bounded audio input capture command before execution.",
            )
        ]

    if request.preset_id == "composite-device-validation":
        return [
            PresetCommandSuggestion(
                argv=("gst-device-explorer", "validate", "group", request.target),
                dry_run=False,
                description="Validate the composite group without execution.",
            )
        ]

    raise UnknownPresetError(f"Preset not found: {request.preset_id}")
