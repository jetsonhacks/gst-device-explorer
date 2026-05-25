"""Explore tab rendering for selected GUI detail items."""

from __future__ import annotations

from collections.abc import Callable

from gst_device_explorer.gui.model import DetailPaneModel
from gst_device_explorer.gui.qt_camera_explorer import (
    camera_explore_lines,
    create_camera_explorer_widget,
    has_camera_explorer,
)
from gst_device_explorer.gui.qt_sections import create_text_label, create_title_label


def explore_accessible_text(detail: DetailPaneModel) -> str:
    """Return the text intended for the default Explore tab."""

    lines = ["Explore"]
    if has_camera_explorer(detail):
        lines.extend(camera_explore_lines(detail))
    else:
        lines.append(detail.title)
        lines.extend(detail.summary)
        lines.extend(explore_placeholder_lines(detail))
    return "\n".join(lines)


def create_explore_widget(
    detail: DetailPaneModel,
    *,
    status_callback: Callable[[str], None] | None = None,
) -> object:
    from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QWidget

    pane = QWidget()
    layout = QVBoxLayout(pane)
    layout.setContentsMargins(16, 16, 16, 16)
    layout.setSpacing(12)
    pane.setAccessibleName(detail.title)
    pane.setAccessibleDescription(explore_accessible_text(detail))
    if has_camera_explorer(detail):
        layout.addWidget(create_camera_explorer_widget(detail, status_callback=status_callback), 1)
    else:
        layout.addWidget(create_title_label(detail.title))
        box = QGroupBox("Explore")
        box_layout = QVBoxLayout(box)
        for line in explore_placeholder_lines(detail):
            box_layout.addWidget(create_text_label(line))
        layout.addWidget(box)
        layout.addStretch(1)
    return pane


def explore_placeholder_lines(detail: DetailPaneModel) -> tuple[str, ...]:
    if detail.kind == "group":
        return (
            "Group exploration dashboard is deferred.",
            "Select an endpoint in the sidebar to explore it directly.",
        )
    if detail.kind == "audio_input":
        return (
            "Audio input exploration controls are deferred.",
            "Open Device Information for discovered capabilities and generated candidates.",
        )
    if detail.kind == "audio_output":
        return (
            "Audio output exploration controls are deferred.",
            "Open Device Information for discovered capabilities and generated candidates.",
        )
    if detail.kind in {"empty", "error", "unknown"}:
        return detail.summary
    return (
        "Exploration controls are not available for this selection yet.",
        "Open Device Information for discovered details.",
    )
