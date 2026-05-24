"""Read-only TUI review model and rendering helpers."""

from __future__ import annotations

from dataclasses import dataclass

from gst_device_explorer.core.config import ConfigValidationResult
from gst_device_explorer.core.models import Device, EnvironmentFact, SystemReport
from gst_device_explorer.core.presets import PresetDefinition
from gst_device_explorer.core.schema import SchemaDocument


@dataclass(frozen=True)
class TuiReviewModel:
    """Structured read-only data reviewed by the TUI."""

    report: SystemReport
    presets: tuple[PresetDefinition, ...]
    config: ConfigValidationResult
    schema_documents: tuple[SchemaDocument, ...]


@dataclass(frozen=True)
class TuiSection:
    """One section in the read-only TUI."""

    section_id: str
    title: str
    lines: tuple[str, ...]


@dataclass(frozen=True)
class TuiNavigationState:
    """Small pure navigation state for the TUI."""

    selected_index: int = 0
    active_section_id: str | None = None
    quit_requested: bool = False


SECTION_ORDER = (
    ("environment", "Environment"),
    ("devices", "Devices"),
    ("groups", "Composite Groups"),
    ("presets", "Presets"),
    ("configuration", "Configuration"),
    ("schemas", "Schemas"),
    ("suggested_commands", "Suggested Commands"),
)


def build_tui_review_model(
    report: SystemReport,
    presets: list[PresetDefinition],
    config: ConfigValidationResult,
    schema_documents: list[SchemaDocument],
) -> TuiReviewModel:
    """Build the pure TUI review model from already-gathered data."""

    return TuiReviewModel(
        report=report,
        presets=tuple(presets),
        config=config,
        schema_documents=tuple(schema_documents),
    )


def build_tui_sections(model: TuiReviewModel) -> tuple[TuiSection, ...]:
    """Render all review sections into deterministic line models."""

    builders = {
        "environment": _environment_lines,
        "devices": _device_lines,
        "groups": _group_lines,
        "presets": _preset_lines,
        "configuration": _config_lines,
        "schemas": _schema_lines,
        "suggested_commands": _suggested_command_lines,
    }
    return tuple(
        TuiSection(section_id=section_id, title=title, lines=builders[section_id](model))
        for section_id, title in SECTION_ORDER
    )


def render_overview_lines(
    model: TuiReviewModel,
    state: TuiNavigationState | None = None,
) -> tuple[str, ...]:
    """Render the overview screen as plain lines."""

    state = state or TuiNavigationState()
    sections = build_tui_sections(model)
    lines = [
        "gst-device-explorer TUI",
        "",
        "Overview",
        f"  Environment: {_environment_status(model.report.environment)}",
        f"  Video devices: {len(model.report.devices.video)}",
        f"  Audio inputs: {len(model.report.devices.audio_inputs)}",
        f"  Audio outputs: {len(model.report.devices.audio_outputs)}",
        f"  Composite groups: {len(model.report.groups)}",
        f"  Presets: {len(model.presets)}",
        f"  Schema kinds: {len(model.schema_documents)}",
        f"  Config: {_config_status(model.config)}",
        "",
        "Sections",
    ]
    for index, section in enumerate(sections):
        marker = ">" if index == state.selected_index else " "
        lines.append(f"{marker} {index + 1}. {section.title}")
    lines.extend(
        [
            "",
            "Enter: open   Esc: back   q: quit",
            "Read-only: suggested commands are displayed, not executed.",
        ]
    )
    return tuple(lines)


def render_section_lines(section: TuiSection) -> tuple[str, ...]:
    """Render one section page as plain lines."""

    return (
        section.title,
        "",
        *section.lines,
        "",
        "Esc: back   q: quit",
        "Read-only: suggested commands are displayed, not executed.",
    )


def render_current_screen(
    model: TuiReviewModel,
    state: TuiNavigationState,
) -> tuple[str, ...]:
    """Render the current overview or section screen."""

    if state.active_section_id is None:
        return render_overview_lines(model, state)

    section = get_section(model, state.active_section_id)
    if section is None:
        return render_overview_lines(model, state)
    return render_section_lines(section)


def get_section(model: TuiReviewModel, section_id: str) -> TuiSection | None:
    """Return one rendered TUI section by ID."""

    return next(
        (section for section in build_tui_sections(model) if section.section_id == section_id),
        None,
    )


def handle_tui_key(
    state: TuiNavigationState,
    key: str,
    section_count: int | None = None,
) -> TuiNavigationState:
    """Apply a key press to the pure navigation state."""

    count = section_count or len(SECTION_ORDER)
    if key == "q":
        return TuiNavigationState(
            selected_index=state.selected_index,
            active_section_id=state.active_section_id,
            quit_requested=True,
        )
    if key in {"escape", "backspace"}:
        return TuiNavigationState(selected_index=state.selected_index)
    if state.active_section_id is not None:
        return state
    if key == "up":
        return TuiNavigationState(selected_index=max(0, state.selected_index - 1))
    if key == "down":
        return TuiNavigationState(
            selected_index=min(count - 1, state.selected_index + 1)
        )
    if key == "enter":
        section_id = SECTION_ORDER[state.selected_index][0]
        return TuiNavigationState(
            selected_index=state.selected_index,
            active_section_id=section_id,
        )
    if key.isdigit():
        index = int(key) - 1
        if 0 <= index < count:
            section_id = SECTION_ORDER[index][0]
            return TuiNavigationState(selected_index=index, active_section_id=section_id)
    return state


def _environment_lines(model: TuiReviewModel) -> tuple[str, ...]:
    facts = model.report.environment
    lines = [f"GStreamer: {_environment_status(facts)}"]
    for fact in facts:
        if fact.name == "gstreamer_tool_available":
            tool = fact.metadata.get("tool", fact.source or "tool")
            lines.append(f"{tool}: {_availability(fact.value)}")
    if len(lines) == 1:
        lines.append("No environment facts found.")
    lines.extend(
        [
            "",
            "Suggested commands:",
            "  gst-device-explorer env",
            "  gst-device-explorer env --json",
        ]
    )
    return tuple(lines)


def _device_lines(model: TuiReviewModel) -> tuple[str, ...]:
    lines = ["Video"]
    lines.extend(_device_summary_lines(model.report.devices.video))
    lines.append("")
    lines.append("Audio Inputs")
    lines.extend(_device_summary_lines(model.report.devices.audio_inputs))
    lines.append("")
    lines.append("Audio Outputs")
    lines.extend(_device_summary_lines(model.report.devices.audio_outputs))
    lines.extend(
        [
            "",
            "Suggested commands:",
            "  gst-device-explorer devices",
            "  gst-device-explorer audio-inputs",
            "  gst-device-explorer audio-outputs",
        ]
    )
    return tuple(lines)


def _group_lines(model: TuiReviewModel) -> tuple[str, ...]:
    if not model.report.groups:
        lines = ["No composite groups discovered."]
    else:
        lines = []
        for group in model.report.groups:
            lines.append(f"{group.id}: {group.name}")
            lines.append(f"  members: {len(group.members)}")
            lines.append(f"  evidence: {len(group.evidence)}")
    lines.extend(
        [
            "",
            "Suggested commands:",
            "  gst-device-explorer groups",
            "  gst-device-explorer groups --metadata",
        ]
    )
    return tuple(lines)


def _preset_lines(model: TuiReviewModel) -> tuple[str, ...]:
    lines = [
        f"{preset.preset_id} ({preset.target_kind}): {preset.description}"
        for preset in model.presets
    ]
    if not lines:
        lines = ["No presets found."]
    lines.extend(
        [
            "",
            "Suggested commands:",
            "  gst-device-explorer preset list",
            "  gst-device-explorer preset show camera-preview",
        ]
    )
    return tuple(lines)


def _config_lines(model: TuiReviewModel) -> tuple[str, ...]:
    result = model.config
    source = result.path if result.path is not None else "defaults"
    lines = [
        f"Status: {'valid' if result.valid else 'invalid'}",
        f"Source: {source}",
        f"Applied to behavior: {'yes' if result.applied else 'no'}",
    ]
    if result.errors:
        lines.append("Errors:")
        lines.extend(f"  {issue.path}: {issue.message}" for issue in result.errors)
    if result.warnings:
        lines.append("Warnings:")
        lines.extend(f"  {issue.path}: {issue.message}" for issue in result.warnings)
    lines.extend(
        [
            "",
            "Suggested commands:",
            "  gst-device-explorer config show",
            "  gst-device-explorer config validate",
        ]
    )
    return tuple(lines)


def _schema_lines(model: TuiReviewModel) -> tuple[str, ...]:
    lines = [document.schema_id for document in model.schema_documents]
    if not lines:
        lines = ["No schema documents found."]
    lines.extend(
        [
            "",
            "Suggested commands:",
            "  gst-device-explorer schema list",
            "  gst-device-explorer schema show json-envelope",
        ]
    )
    return tuple(lines)


def _suggested_command_lines(model: TuiReviewModel) -> tuple[str, ...]:
    report_commands = [cmd.command for cmd in model.report.suggested_next_commands]
    commands = _dedupe(
        [
            "gst-device-explorer report",
            "gst-device-explorer report --json",
            *report_commands,
            "gst-device-explorer preset list",
            "gst-device-explorer config show",
            "gst-device-explorer schema list",
        ]
    )
    return tuple(commands) if commands else ("No suggested commands.",)


def _device_summary_lines(devices: list[Device]) -> list[str]:
    if not devices:
        return ["  none"]
    return [f"  {device.id}  {device.name}" for device in devices]


def _environment_status(facts: list[EnvironmentFact]) -> str:
    tool_facts = [
        fact for fact in facts
        if fact.name == "gstreamer_tool_available"
    ]
    if not tool_facts:
        return "unknown"
    if all(bool(fact.value) for fact in tool_facts):
        return "available"
    if any(bool(fact.value) for fact in tool_facts):
        return "partial"
    return "unavailable"


def _config_status(result: ConfigValidationResult) -> str:
    if not result.valid:
        return "invalid"
    if result.path is None:
        return "defaults"
    return "loaded"


def _availability(value) -> str:
    return "available" if bool(value) else "missing"


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result
