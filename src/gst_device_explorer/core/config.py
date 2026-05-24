"""Bounded configuration models and validation helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping
import os


@dataclass(frozen=True)
class VideoPreferences:
    """Video-related preferences for future behavior."""

    preferred_sink: str | None = None
    prefer_jetson_acceleration: bool = True
    max_preview_width: int | None = None
    max_preview_height: int | None = None


@dataclass(frozen=True)
class AudioPreferences:
    """Audio-related preferences for future behavior."""

    output_test_frequency: int = 440
    prefer_silent_input_tests: bool = True


@dataclass(frozen=True)
class ReportPreferences:
    """Report-related preferences for future behavior."""

    include_metadata: bool = True
    include_diagnostics: bool = True


@dataclass(frozen=True)
class ExplorerConfig:
    """Effective bounded configuration for gst-device-explorer."""

    video: VideoPreferences = field(default_factory=VideoPreferences)
    audio: AudioPreferences = field(default_factory=AudioPreferences)
    report: ReportPreferences = field(default_factory=ReportPreferences)


@dataclass(frozen=True)
class ConfigIssue:
    """One configuration validation issue."""

    path: str
    message: str


@dataclass(frozen=True)
class ConfigValidationResult:
    """Result of loading and validating configuration."""

    path: str | None
    valid: bool
    config: ExplorerConfig | None
    errors: tuple[ConfigIssue, ...] = ()
    warnings: tuple[ConfigIssue, ...] = ()
    applied: bool = False
    discovered: bool = False


_KNOWN_SECTIONS = {
    "video": {
        "preferred_sink",
        "prefer_jetson_acceleration",
        "max_preview_width",
        "max_preview_height",
    },
    "audio": {
        "output_test_frequency",
        "prefer_silent_input_tests",
    },
    "report": {
        "include_metadata",
        "include_diagnostics",
    },
}


def default_config() -> ExplorerConfig:
    """Return the deterministic default configuration."""

    return ExplorerConfig()


def config_search_paths() -> tuple[Path, ...]:
    """Return the configuration search paths in lookup order."""

    config_home = os.environ.get("XDG_CONFIG_HOME")
    if config_home:
        user_config = Path(config_home) / "gst-device-explorer" / "config.toml"
    else:
        user_config = Path.home() / ".config" / "gst-device-explorer" / "config.toml"

    return (
        user_config,
        Path.cwd() / "gst-device-explorer.toml",
    )


def load_config_file(path: Path) -> ConfigValidationResult:
    """Load and validate one TOML configuration file."""

    if not path.exists():
        return ConfigValidationResult(
            path=str(path),
            valid=False,
            config=None,
            errors=(ConfigIssue(str(path), "configuration file not found"),),
        )

    try:
        import tomllib
    except ModuleNotFoundError:
        return ConfigValidationResult(
            path=str(path),
            valid=False,
            config=None,
            errors=(
                ConfigIssue(
                    str(path),
                    "TOML parsing requires Python 3.11 or newer",
                ),
            ),
        )

    try:
        with path.open("rb") as handle:
            mapping = tomllib.load(handle)
    except tomllib.TOMLDecodeError as error:
        return ConfigValidationResult(
            path=str(path),
            valid=False,
            config=None,
            errors=(ConfigIssue(str(path), f"invalid TOML: {error}"),),
        )
    except OSError as error:
        return ConfigValidationResult(
            path=str(path),
            valid=False,
            config=None,
            errors=(ConfigIssue(str(path), str(error)),),
        )

    return validate_config_mapping(mapping, path=str(path))


def validate_config_mapping(
    mapping: Mapping[str, Any],
    path: str | None = None,
) -> ConfigValidationResult:
    """Validate a parsed configuration mapping and merge it over defaults."""

    errors: list[ConfigIssue] = []
    warnings: list[ConfigIssue] = []
    source = path or None

    if not isinstance(mapping, Mapping):
        return ConfigValidationResult(
            path=source,
            valid=False,
            config=None,
            errors=(ConfigIssue("root", "expected TOML table"),),
        )

    config = default_config()
    video = config.video
    audio = config.audio
    report = config.report

    for section in sorted(mapping):
        section_value = mapping[section]
        if section not in _KNOWN_SECTIONS:
            warnings.append(ConfigIssue(section, "unknown section"))
            continue
        if not isinstance(section_value, Mapping):
            errors.append(ConfigIssue(section, "expected table"))
            continue

        for key in sorted(section_value):
            value = section_value[key]
            dotted_path = f"{section}.{key}"
            if key not in _KNOWN_SECTIONS[section]:
                warnings.append(ConfigIssue(dotted_path, "unknown key"))
                continue

            if section == "video":
                video = _validate_video_value(video, key, value, dotted_path, errors)
            elif section == "audio":
                audio = _validate_audio_value(audio, key, value, dotted_path, errors)
            elif section == "report":
                report = _validate_report_value(report, key, value, dotted_path, errors)

    merged = ExplorerConfig(video=video, audio=audio, report=report)
    return ConfigValidationResult(
        path=source,
        valid=not errors,
        config=merged if not errors else None,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def effective_config(path: Path | None = None) -> ConfigValidationResult:
    """Return the explicit or discovered effective configuration."""

    if path is not None:
        return load_config_file(path)

    for candidate in config_search_paths():
        if candidate.exists():
            result = load_config_file(candidate)
            return ConfigValidationResult(
                path=result.path,
                valid=result.valid,
                config=result.config,
                errors=result.errors,
                warnings=result.warnings,
                applied=False,
                discovered=True,
            )

    return ConfigValidationResult(
        path=None,
        valid=True,
        config=default_config(),
        applied=False,
        discovered=False,
    )


def _validate_video_value(
    video: VideoPreferences,
    key: str,
    value: Any,
    path: str,
    errors: list[ConfigIssue],
) -> VideoPreferences:
    if key == "preferred_sink":
        if not isinstance(value, str):
            errors.append(ConfigIssue(path, "expected string"))
            return video
        return VideoPreferences(
            preferred_sink=value,
            prefer_jetson_acceleration=video.prefer_jetson_acceleration,
            max_preview_width=video.max_preview_width,
            max_preview_height=video.max_preview_height,
        )

    if key == "prefer_jetson_acceleration":
        if not isinstance(value, bool):
            errors.append(ConfigIssue(path, "expected boolean"))
            return video
        return VideoPreferences(
            preferred_sink=video.preferred_sink,
            prefer_jetson_acceleration=value,
            max_preview_width=video.max_preview_width,
            max_preview_height=video.max_preview_height,
        )

    if key == "max_preview_width":
        width = _positive_int(value, path, errors)
        return video if width is None else VideoPreferences(
            preferred_sink=video.preferred_sink,
            prefer_jetson_acceleration=video.prefer_jetson_acceleration,
            max_preview_width=width,
            max_preview_height=video.max_preview_height,
        )

    if key == "max_preview_height":
        height = _positive_int(value, path, errors)
        return video if height is None else VideoPreferences(
            preferred_sink=video.preferred_sink,
            prefer_jetson_acceleration=video.prefer_jetson_acceleration,
            max_preview_width=video.max_preview_width,
            max_preview_height=height,
        )

    return video


def _validate_audio_value(
    audio: AudioPreferences,
    key: str,
    value: Any,
    path: str,
    errors: list[ConfigIssue],
) -> AudioPreferences:
    if key == "output_test_frequency":
        frequency = _positive_int(value, path, errors)
        return audio if frequency is None else AudioPreferences(
            output_test_frequency=frequency,
            prefer_silent_input_tests=audio.prefer_silent_input_tests,
        )

    if key == "prefer_silent_input_tests":
        if not isinstance(value, bool):
            errors.append(ConfigIssue(path, "expected boolean"))
            return audio
        return AudioPreferences(
            output_test_frequency=audio.output_test_frequency,
            prefer_silent_input_tests=value,
        )

    return audio


def _validate_report_value(
    report: ReportPreferences,
    key: str,
    value: Any,
    path: str,
    errors: list[ConfigIssue],
) -> ReportPreferences:
    if not isinstance(value, bool):
        errors.append(ConfigIssue(path, "expected boolean"))
        return report

    if key == "include_metadata":
        return ReportPreferences(
            include_metadata=value,
            include_diagnostics=report.include_diagnostics,
        )
    if key == "include_diagnostics":
        return ReportPreferences(
            include_metadata=report.include_metadata,
            include_diagnostics=value,
        )
    return report


def _positive_int(
    value: Any,
    path: str,
    errors: list[ConfigIssue],
) -> int | None:
    if not isinstance(value, int) or isinstance(value, bool):
        errors.append(ConfigIssue(path, "expected positive integer"))
        return None
    if value <= 0:
        errors.append(ConfigIssue(path, "expected positive integer"))
        return None
    return value
