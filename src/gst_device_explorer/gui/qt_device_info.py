"""Device Information tab rendering for selected GUI detail items."""

from __future__ import annotations

from collections.abc import Callable

from gst_device_explorer.gui.model import DetailPaneModel
from gst_device_explorer.gui.qt_camera_explorer import is_camera_explore_section
from gst_device_explorer.gui.qt_sections import (
    action_copy_text,
    action_display_lines,
    copyable_texts,
    create_copy_button,
    create_copyable_row,
    create_section_table,
    create_text_label,
    create_title_label,
    detail_identity_items,
    section_display_title,
    section_kind,
)


def device_information_accessible_text(detail: DetailPaneModel) -> str:
    """Return the text intended for the Device Information tab."""

    lines = ["Device Information", detail.title]
    lines.append("Identity")
    lines.extend(f"{label}: {value}" for label, value in detail_identity_items(detail))
    if detail.summary:
        lines.append("Summary")
        lines.extend(detail.summary)
    for section in detail.sections:
        if is_camera_explore_section(detail, section):
            continue
        lines.append(section_display_title(section))
        lines.extend(section.items)
    if copyable_texts(detail):
        lines.append("Copy")
    if detail.actions:
        lines.append("Safe Actions")
        for action in detail.actions:
            lines.append(action.label)
            lines.extend(action_display_lines(action))
    return "\n".join(lines)


def create_device_information_widget(
    detail: DetailPaneModel,
    *,
    status_callback: Callable[[str], None] | None = None,
) -> object:
    from PySide6.QtWidgets import QFrame, QFormLayout, QGroupBox, QHBoxLayout, QPushButton, QSizePolicy
    from PySide6.QtWidgets import QVBoxLayout, QWidget

    pane = QWidget()
    layout = QVBoxLayout(pane)
    layout.setContentsMargins(16, 16, 16, 16)
    layout.setSpacing(12)
    pane.setAccessibleName(f"{detail.title} Device Information")
    pane.setAccessibleDescription(device_information_accessible_text(detail))
    layout.addWidget(create_title_label(detail.title))

    identity_box = QGroupBox("Identity")
    identity_layout = QFormLayout(identity_box)
    for label, value in detail_identity_items(detail):
        identity_layout.addRow(label, create_copyable_row(value, status_callback=status_callback))
    layout.addWidget(identity_box)

    if detail.summary:
        summary_box = QGroupBox("Summary")
        summary_layout = QVBoxLayout(summary_box)
        for line in detail.summary:
            summary_layout.addWidget(create_text_label(line))
        layout.addWidget(summary_box)

    for section in detail.sections:
        if is_camera_explore_section(detail, section):
            continue
        section_box = QGroupBox(section_display_title(section))
        section_layout = QVBoxLayout(section_box)
        if section_kind(section) in {"candidate", "capability", "identity", "group"}:
            section_layout.addWidget(create_section_table(section))
        else:
            for item in section.items:
                section_layout.addWidget(create_text_label(item))
        layout.addWidget(section_box)

    copyable = copyable_texts(detail)
    if copyable:
        copy_box = QGroupBox("Copy")
        copy_layout = QVBoxLayout(copy_box)
        for label, text in copyable:
            copy_layout.addWidget(create_copy_button(label, text, status_callback=status_callback))
        layout.addWidget(copy_box)

    actions_box = QGroupBox("Safe Actions")
    actions_layout = QVBoxLayout(actions_box)
    for action in detail.actions:
        row = QHBoxLayout()
        button = QPushButton(action.label)
        button.setEnabled(False)
        button.setToolTip("Display-only action metadata. This button does not execute commands.")
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        row.addWidget(button)
        copy_text = action_copy_text(action)
        if copy_text is not None:
            row.addWidget(create_copy_button("Copy", copy_text, status_callback=status_callback))
        row.addStretch(1)
        actions_layout.addLayout(row)
        for line in action_display_lines(action):
            actions_layout.addWidget(create_text_label(line))
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        actions_layout.addWidget(divider)
    layout.addWidget(actions_box)
    layout.addStretch(1)
    return pane
