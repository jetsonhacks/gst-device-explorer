"""Explore tab rendering for selected GUI detail items."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from gst_device_explorer.gui.model import DetailPaneModel
from gst_device_explorer.gui.qt_audio_input_explorer import (
    audio_input_explore_lines,
    create_audio_input_explorer_widget,
    has_audio_input_explorer,
)
from gst_device_explorer.gui.qt_audio_output_explorer import (
    audio_output_explore_lines,
    create_audio_output_explorer_widget,
    has_audio_output_explorer,
)
from gst_device_explorer.gui.qt_camera_explorer import (
    camera_explore_lines,
    create_camera_explorer_widget,
    has_camera_explorer,
)
from gst_device_explorer.gui.qt_sections import create_text_label, create_title_label


@dataclass(frozen=True)
class GroupEndpointCard:
    role_label: str
    target: str
    node_kind: str
    node_id: str
    summary: str

    @property
    def action_label(self) -> str:
        return f"Explore {self.role_label if self.role_label != 'Other Endpoint' else 'Endpoint'}"


def explore_accessible_text(detail: DetailPaneModel) -> str:
    """Return the text intended for the default Explore tab."""

    lines = ["Explore"]
    if has_camera_explorer(detail):
        lines.extend(camera_explore_lines(detail))
    elif has_audio_input_explorer(detail):
        lines.extend(audio_input_explore_lines(detail))
    elif has_audio_output_explorer(detail):
        lines.extend(audio_output_explore_lines(detail))
    elif has_group_explorer(detail):
        lines.extend(group_explore_lines(detail))
    else:
        lines.append(detail.title)
        lines.extend(detail.summary)
        lines.extend(explore_placeholder_lines(detail))
    return "\n".join(lines)


def create_explore_widget(
    detail: DetailPaneModel,
    *,
    status_callback: Callable[[str], None] | None = None,
    navigate_callback: Callable[[str], None] | None = None,
    preview_runner: object | None = None,
) -> object:
    from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QWidget

    pane = QWidget()
    layout = QVBoxLayout(pane)
    layout.setContentsMargins(16, 16, 16, 16)
    layout.setSpacing(12)
    pane.setAccessibleName(detail.title)
    pane.setAccessibleDescription(explore_accessible_text(detail))
    if has_camera_explorer(detail):
        layout.addWidget(
            create_camera_explorer_widget(
                detail,
                status_callback=status_callback,
                preview_runner=preview_runner,
            ),
            1,
        )
    elif has_audio_input_explorer(detail):
        layout.addWidget(create_audio_input_explorer_widget(detail, status_callback=status_callback), 1)
    elif has_audio_output_explorer(detail):
        layout.addWidget(create_audio_output_explorer_widget(detail, status_callback=status_callback), 1)
    elif has_group_explorer(detail):
        layout.addWidget(
            create_group_explorer_widget(detail, navigate_callback=navigate_callback),
            1,
        )
    else:
        layout.addWidget(create_title_label(detail.title))
        box = QGroupBox("Explore")
        box_layout = QVBoxLayout(box)
        for line in explore_placeholder_lines(detail):
            box_layout.addWidget(create_text_label(line))
        layout.addWidget(box)
        layout.addStretch(1)
    return pane


def has_group_explorer(detail: DetailPaneModel) -> bool:
    return detail.kind == "group" and bool(group_endpoint_cards(detail))


def group_explore_lines(detail: DetailPaneModel) -> tuple[str, ...]:
    lines = ["Group Explore", detail.title, "Group Summary"]
    lines.extend(_compact_group_summary(detail))
    lines.append("Endpoints")
    for card in group_endpoint_cards(detail):
        lines.extend((card.role_label, card.target, card.summary, card.action_label))
    return tuple(lines)


def create_group_explorer_widget(
    detail: DetailPaneModel,
    *,
    navigate_callback: Callable[[str], None] | None = None,
) -> object:
    from PySide6.QtWidgets import QFrame, QGroupBox, QVBoxLayout, QWidget

    pane = QWidget()
    layout = QVBoxLayout(pane)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(10)

    layout.addWidget(create_title_label(detail.title))

    summary_box = QGroupBox("Group Summary")
    summary_layout = QVBoxLayout(summary_box)
    for line in _compact_group_summary(detail):
        summary_layout.addWidget(create_text_label(line))
    layout.addWidget(summary_box, 0)

    endpoints_box = QGroupBox("Endpoints")
    endpoints_layout = QVBoxLayout(endpoints_box)
    endpoints_layout.setSpacing(8)
    for card in group_endpoint_cards(detail):
        endpoints_layout.addWidget(_endpoint_card_widget(card, navigate_callback=navigate_callback))
    layout.addWidget(endpoints_box, 0)

    note = QFrame()
    note.setFrameShape(QFrame.HLine)
    note.setFrameShadow(QFrame.Plain)
    layout.addWidget(note)
    layout.addWidget(
        create_text_label("Group Explore is a navigation dashboard. Run, preview, and capture remain endpoint-scoped.")
    )
    layout.addStretch(1)
    return pane


def group_endpoint_cards(detail: DetailPaneModel) -> tuple[GroupEndpointCard, ...]:
    endpoints = _section_items(detail, "Endpoints")
    group_prefix = f"{detail.selected_id}:"
    cards = []
    for item in endpoints:
        if ": " not in item:
            continue
        role, target = item.split(": ", 1)
        role_label = _endpoint_role_label(role)
        node_kind = _node_kind_for_role(role)
        cards.append(
            GroupEndpointCard(
                role_label=role_label,
                target=target,
                node_kind=node_kind,
                node_id=f"{group_prefix}{node_kind}:{target}",
                summary=_endpoint_card_summary(role_label, target),
            )
        )
    return tuple(cards)


def _endpoint_card_widget(
    card: GroupEndpointCard,
    *,
    navigate_callback: Callable[[str], None] | None = None,
) -> object:
    from PySide6.QtWidgets import QFrame, QPushButton, QSizePolicy, QVBoxLayout

    frame = QFrame()
    frame.setObjectName("groupEndpointCard")
    frame.setProperty("targetNodeId", card.node_id)
    frame.setFrameShape(QFrame.StyledPanel)
    frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(10, 8, 10, 8)
    layout.setSpacing(4)
    layout.addWidget(create_text_label(card.role_label))
    layout.addWidget(create_text_label(card.target))
    layout.addWidget(create_text_label(card.summary))
    button = QPushButton(card.action_label)
    button.setObjectName("groupEndpointExploreButton")
    button.setProperty("targetNodeId", card.node_id)
    button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    if navigate_callback is not None:
        button.clicked.connect(lambda _checked=False, node_id=card.node_id: navigate_callback(node_id))
    layout.addWidget(button)
    return frame


def _compact_group_summary(detail: DetailPaneModel) -> tuple[str, ...]:
    lines = []
    for line in detail.summary:
        if line.startswith(("Group id:", "Kind:", "Confidence:", "Members:")):
            lines.append(line)
    evidence = _section_items(detail, "Grouping Evidence")
    if evidence:
        lines.append(f"Evidence: {evidence[0]}")
    return tuple(lines)


def _section_items(detail: DetailPaneModel, title: str) -> tuple[str, ...]:
    section = next((section for section in detail.sections if section.title == title), None)
    return () if section is None else section.items


def _endpoint_role_label(role: str) -> str:
    normalized = _normalized_role(role)
    return {
        "camera": "Camera",
        "video": "Camera",
        "video-input": "Camera",
        "audio-input": "Microphone",
        "microphone": "Microphone",
        "audio-output": "Speaker",
        "speaker": "Speaker",
    }.get(normalized, "Other Endpoint")


def _node_kind_for_role(role: str) -> str:
    normalized = _normalized_role(role)
    return {
        "camera": "video",
        "video": "video",
        "video-input": "video",
        "audio-input": "audio_input",
        "microphone": "audio_input",
        "audio-output": "audio_output",
        "speaker": "audio_output",
    }.get(normalized, "section")


def _normalized_role(role: str) -> str:
    return role.lower().replace("_", "-").replace(" ", "-")


def _endpoint_card_summary(role_label: str, target: str) -> str:
    if role_label == "Camera":
        return f"Video input endpoint {target}."
    if role_label == "Microphone":
        return f"Audio input endpoint {target}."
    if role_label == "Speaker":
        return f"Audio output endpoint {target}."
    return f"Endpoint {target}."


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
