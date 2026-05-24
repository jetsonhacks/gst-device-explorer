"""Qt detail pane rendering for GUI models."""

from __future__ import annotations

from collections.abc import Callable

from gst_device_explorer.gui.model import DetailPaneModel, DetailSection, GuiAction

COPYABLE_ACTION_KINDS = frozenset(
    {
        "copy_command",
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


class DetailPaneWidgetMixin:
    """Mixin containing renderer logic shared by the concrete QWidget."""

    def render_detail(self, detail: DetailPaneModel) -> None:
        raise NotImplementedError


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
    target = _target_from_summary(detail)
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
        maybe = _copyable_line_value(line)
        if maybe is not None:
            values.append((f"Copy {_copy_label(line)}", maybe))
    for action in detail.actions:
        command = action_copy_text(action)
        if command is not None:
            values.append((f"Copy {action.label}", command))
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


def create_detail_pane_widget(
    *,
    status_callback: Callable[[str], None] | None = None,
) -> object:
    """Create the concrete Qt detail widget.

    PySide6 imports stay inside this factory so non-GUI imports remain light.
    """

    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QAbstractItemView,
        QFrame,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QScrollArea,
        QSizePolicy,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )

    class DetailPaneWidget(QWidget, DetailPaneWidgetMixin):
        def __init__(self) -> None:
            super().__init__()
            self._layout = QVBoxLayout(self)
            self._layout.setContentsMargins(16, 16, 16, 16)
            self._layout.setSpacing(12)

        def render_detail(self, detail: DetailPaneModel) -> None:
            _clear_layout(self._layout)
            self.setAccessibleName(detail.title)
            self.setAccessibleDescription(detail_accessible_text(detail))
            title = QLabel(detail.title)
            title.setObjectName("detailTitle")
            title.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self._layout.addWidget(title)

            identity_box = QGroupBox("Identity")
            identity_layout = QFormLayout(identity_box)
            for label, value in detail_identity_items(detail):
                identity_layout.addRow(label, _copyable_row(value))
            self._layout.addWidget(identity_box)

            if detail.summary:
                summary_box = QGroupBox("Summary")
                summary_layout = QVBoxLayout(summary_box)
                for line in detail.summary:
                    summary_layout.addWidget(_text_label(line))
                self._layout.addWidget(summary_box)

            for section in detail.sections:
                section_box = QGroupBox(section_display_title(section))
                section_layout = QVBoxLayout(section_box)
                if section_kind(section) in {"candidate", "capability", "identity", "group"}:
                    section_layout.addWidget(_table_for_section(section))
                else:
                    for item in section.items:
                        section_layout.addWidget(_text_label(item))
                self._layout.addWidget(section_box)

            copyable = copyable_texts(detail)
            if copyable:
                copy_box = QGroupBox("Copy")
                copy_layout = QVBoxLayout(copy_box)
                for label, text in copyable:
                    copy_layout.addWidget(_copy_button(label, text))
                self._layout.addWidget(copy_box)

            actions_box = QGroupBox("Safe Actions")
            actions_layout = QVBoxLayout(actions_box)
            for action in detail.actions:
                row = QHBoxLayout()
                button = QPushButton(action.label)
                button.setEnabled(False)
                button.setToolTip(
                    "Display-only action metadata. This button does not execute commands."
                )
                button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                row.addWidget(button)
                copy_text = action_copy_text(action)
                if copy_text is not None:
                    row.addWidget(_copy_button("Copy", copy_text))
                row.addStretch(1)
                actions_layout.addLayout(row)
                for line in action_display_lines(action):
                    actions_layout.addWidget(_text_label(line))
                divider = QFrame()
                divider.setFrameShape(QFrame.HLine)
                divider.setFrameShadow(QFrame.Sunken)
                actions_layout.addWidget(divider)
            self._layout.addWidget(actions_box)
            self._layout.addStretch(1)

    class DetailScrollArea(QScrollArea):
        def __init__(self) -> None:
            super().__init__()
            self.setWidgetResizable(True)
            self._pane = DetailPaneWidget()
            self.setWidget(self._pane)

        def render_detail(self, detail: DetailPaneModel) -> None:
            self._pane.render_detail(detail)

    def _text_label(text: str) -> object:
        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        return label

    def _copyable_row(text: str) -> object:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(_text_label(text))
        layout.addWidget(_copy_button("Copy", text))
        layout.addStretch(1)
        return row

    def _copy_button(label: str, text: str) -> object:
        button = QPushButton(label)
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        button.clicked.connect(lambda _checked=False, value=text: _copy_to_clipboard(value))
        return button

    def _copy_to_clipboard(text: str) -> None:
        from PySide6.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        copy_display_text(
            text,
            set_clipboard_text=clipboard.setText,
            status_callback=status_callback,
        )

    def _table_for_section(section: DetailSection) -> object:
        rows = [_split_display_row(item) for item in section.items] or [("", "")]
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

    def _clear_layout(layout: object) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    return DetailScrollArea()


def _target_from_summary(detail: DetailPaneModel) -> str | None:
    for line in detail.summary:
        maybe = _copyable_line_value(line)
        if maybe is not None:
            return maybe
    return None


def _copyable_line_value(line: str) -> str | None:
    for prefix in COPYABLE_LINE_PREFIXES:
        if line.startswith(prefix):
            return line.removeprefix(prefix).strip()
    return None


def _copy_label(line: str) -> str:
    return line.split(":", 1)[0].strip().lower()


def _split_display_row(item: str) -> tuple[str, str]:
    for separator in (": ", " - "):
        if separator in item:
            left, right = item.split(separator, 1)
            return left, right
    return item, ""
