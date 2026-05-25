"""Shared Qt detail-pane formatting and section helpers."""

from __future__ import annotations

from collections.abc import Callable

from gst_device_explorer.gui.model import DetailPaneModel, DetailSection, GuiAction

COPYABLE_ACTION_KINDS = frozenset(
    {
        "copy_command",
        "copy_pipeline",
        "dry_run",
        "show_diagnostics",
        "validate_group",
        "export_report",
        "refresh",
    }
)

COPYABLE_LINE_PREFIXES = (
    "Endpoint:",
    "Group id:",
    "command:",
    "target:",
)


def action_display_lines(action: GuiAction) -> tuple[str, ...]:
    """Return stable action metadata lines for rendering and tests."""

    lines = [
        f"kind: {action.kind}",
        f"safety: {action.safety}",
        f"enabled: {action.enabled}",
    ]
    if action.target_kind and action.target:
        lines.append(f"target: {action.target_kind} {action.target}")
    if action.suggested_command is not None:
        lines.append(f"command: {action.suggested_command.command}")
    if action.disabled_reason:
        lines.append(f"disabled: {action.disabled_reason}")
    return tuple(lines)


def detail_identity_items(detail: DetailPaneModel) -> tuple[tuple[str, str], ...]:
    """Return stable identity rows for the detail header."""

    rows = [
        ("Selection", detail.selected_id),
        ("Kind", detail.kind),
        ("Status", detail.status),
    ]
    target = target_from_summary(detail)
    if target is not None:
        rows.append(("Target", target))
    return tuple(rows)


def section_display_title(section: DetailSection) -> str:
    """Normalize section titles into friendlier GUI headings."""

    title = section.title.strip()
    mapping = {
        "Metadata": "Identity and Metadata",
        "Capabilities": "Capabilities",
        "Candidate Summary": "Candidate Pipelines",
        "Recommendation": "Recommended Candidate",
        "Missing Elements": "Missing Elements",
        "Grouping Evidence": "Grouping Evidence",
        "Endpoints": "Constituent Endpoints",
        "Validation": "Endpoint Status",
        "Safe Actions": "Notes and Limitations",
        "Suggested Next Step": "Suggested Next Step",
        "Details": "Diagnostic Details",
        "Refresh": "Refresh",
        "Discovery": "Discovery",
        "Selection": "Selection",
        "V4L2 Controls": "Dynamic V4L2 Controls (Read-Only)",
    }
    return mapping.get(title, title)


def section_kind(section: DetailSection) -> str:
    """Classify a section for renderer decisions and tests."""

    title = section.title.lower()
    if "candidate" in title or "recommendation" in title:
        return "candidate"
    if "capabilit" in title:
        return "capability"
    if "missing" in title or "diagnostic" in title or "detail" in title:
        return "diagnostic"
    if "endpoint" in title or "evidence" in title or "validation" in title:
        return "group"
    if "metadata" in title or "summary" in title or "identity" in title:
        return "identity"
    return "notes"


def copyable_texts(detail: DetailPaneModel) -> tuple[tuple[str, str], ...]:
    """Return display-only strings that are safe to copy."""

    values: list[tuple[str, str]] = []
    for label, value in detail_identity_items(detail):
        if label in {"Selection", "Target"} and value:
            values.append((f"Copy {label}", value))
    for line in detail.summary:
        maybe = copyable_line_value(line)
        if maybe is not None:
            values.append((f"Copy {_copy_label(line)}", maybe))
    for action in detail.actions:
        command = action_copy_text(action)
        if command is not None:
            label = action.label if action.label.startswith("Copy ") else f"Copy {action.label}"
            values.append((label, command))
    return tuple(dict(values).items())


def action_copy_text(action: GuiAction) -> str | None:
    """Return the safe copy text for an action, if one exists."""

    if action.suggested_command is not None:
        return action.suggested_command.command
    if action.kind in COPYABLE_ACTION_KINDS and action.target:
        return action.target
    return None


def copy_display_text(
    text: str,
    *,
    set_clipboard_text: Callable[[str], None],
    status_callback: Callable[[str], None] | None = None,
) -> None:
    """Copy display text through an injected clipboard setter."""

    set_clipboard_text(text)
    if status_callback is not None:
        status_callback("Copied to clipboard.")


def detail_accessible_text(detail: DetailPaneModel) -> str:
    """Return a compact text representation for headless tests."""

    lines = [detail.title]
    lines.extend(f"{label}: {value}" for label, value in detail_identity_items(detail))
    lines.extend(detail.summary)
    for section in detail.sections:
        lines.append(section_display_title(section))
        lines.extend(section.items)
    for action in detail.actions:
        lines.append(action.label)
        lines.extend(action_display_lines(action))
    return "\n".join(lines)


def target_from_summary(detail: DetailPaneModel) -> str | None:
    for line in detail.summary:
        maybe = copyable_line_value(line)
        if maybe is not None:
            return maybe
    return None


def copyable_line_value(line: str) -> str | None:
    for prefix in COPYABLE_LINE_PREFIXES:
        if line.startswith(prefix):
            return line.removeprefix(prefix).strip()
    return None


def split_display_row(item: str) -> tuple[str, str]:
    for separator in (": ", " - "):
        if separator in item:
            left, right = item.split(separator, 1)
            return left, right
    return item, ""


def create_text_label(text: str) -> object:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QLabel

    label = QLabel(text)
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.TextSelectableByMouse)
    return label


def create_title_label(text: str) -> object:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QLabel

    title = QLabel(text)
    title.setObjectName("detailTitle")
    title.setTextInteractionFlags(Qt.TextSelectableByMouse)
    return title


def create_copy_button(
    label: str,
    text: str,
    *,
    status_callback: Callable[[str], None] | None = None,
) -> object:
    from PySide6.QtWidgets import QPushButton, QSizePolicy

    button = QPushButton(label)
    button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    button.clicked.connect(
        lambda _checked=False, value=text: copy_to_clipboard(
            value,
            status_callback=status_callback,
        )
    )
    return button


def create_copyable_row(
    text: str,
    *,
    status_callback: Callable[[str], None] | None = None,
) -> object:
    from PySide6.QtWidgets import QHBoxLayout, QWidget

    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(create_text_label(text))
    layout.addWidget(create_copy_button("Copy", text, status_callback=status_callback))
    layout.addStretch(1)
    return row


def create_section_table(section: DetailSection) -> object:
    from PySide6.QtWidgets import QAbstractItemView, QTableWidget, QTableWidgetItem

    rows = [split_display_row(item) for item in section.items] or [("", "")]
    table = QTableWidget(len(rows), 2)
    table.setHorizontalHeaderLabels(["Item", "Value"])
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setAlternatingRowColors(True)
    table.setMinimumHeight(min(220, 48 + 28 * max(1, len(rows))))
    for row_index, (key, value) in enumerate(rows):
        table.setItem(row_index, 0, QTableWidgetItem(key))
        table.setItem(row_index, 1, QTableWidgetItem(value))
    table.resizeColumnsToContents()
    table.horizontalHeader().setStretchLastSection(True)
    return table


def copy_to_clipboard(
    text: str,
    *,
    status_callback: Callable[[str], None] | None = None,
) -> None:
    from PySide6.QtWidgets import QApplication

    clipboard = QApplication.clipboard()
    copy_display_text(
        text,
        set_clipboard_text=clipboard.setText,
        status_callback=status_callback,
    )


def _copy_label(line: str) -> str:
    return line.split(":", 1)[0].strip().lower()
