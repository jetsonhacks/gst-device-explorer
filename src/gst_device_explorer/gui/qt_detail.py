"""Qt detail pane rendering for GUI models."""

from __future__ import annotations

from gst_device_explorer.gui.model import DetailPaneModel, GuiAction


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


def create_detail_pane_widget() -> object:
    """Create the concrete Qt detail widget.

    PySide6 imports stay inside this factory so non-GUI imports remain light.
    """

    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QFrame,
        QGroupBox,
        QLabel,
        QPushButton,
        QScrollArea,
        QSizePolicy,
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
            title = QLabel(detail.title)
            title.setObjectName("detailTitle")
            title.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self._layout.addWidget(title)

            meta = QLabel(f"{detail.kind}  |  {detail.status}")
            meta.setObjectName("detailMeta")
            meta.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self._layout.addWidget(meta)

            if detail.summary:
                summary_box = QGroupBox("Summary")
                summary_layout = QVBoxLayout(summary_box)
                for line in detail.summary:
                    summary_layout.addWidget(_text_label(line))
                self._layout.addWidget(summary_box)

            for section in detail.sections:
                section_box = QGroupBox(section.title)
                section_layout = QVBoxLayout(section_box)
                for item in section.items:
                    section_layout.addWidget(_text_label(item))
                self._layout.addWidget(section_box)

            actions_box = QGroupBox("Actions")
            actions_layout = QVBoxLayout(actions_box)
            for action in detail.actions:
                button = QPushButton(action.label)
                button.setEnabled(action.enabled)
                button.setToolTip("\n".join(action_display_lines(action)))
                button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                actions_layout.addWidget(button)
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

    def _clear_layout(layout: object) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    return DetailScrollArea()
