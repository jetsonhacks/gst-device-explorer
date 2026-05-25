"""Qt selected-item detail pane orchestration."""

from __future__ import annotations

from collections.abc import Callable

from gst_device_explorer.gui.model import DetailPaneModel
from gst_device_explorer.gui.qt_device_info import (
    create_device_information_widget,
    device_information_accessible_text,
)
from gst_device_explorer.gui.qt_explore import create_explore_widget, explore_accessible_text
from gst_device_explorer.gui.qt_sections import (
    action_copy_text,
    action_display_lines,
    copy_display_text,
    copyable_texts,
    detail_accessible_text,
    detail_identity_items,
    section_display_title,
    section_kind,
)

DETAIL_TAB_TITLES = ("Explore", "Device Information")


class DetailPaneWidgetMixin:
    """Mixin containing renderer logic shared by the concrete QWidget."""

    def render_detail(self, detail: DetailPaneModel) -> None:
        raise NotImplementedError


def detail_tab_titles(_detail: DetailPaneModel) -> tuple[str, str]:
    """Return the selected-item tab labels."""

    return DETAIL_TAB_TITLES


def create_detail_pane_widget(
    *,
    status_callback: Callable[[str], None] | None = None,
) -> object:
    """Create the concrete Qt detail widget.

    PySide6 imports stay inside this factory so non-GUI imports remain light.
    """

    from PySide6.QtWidgets import QScrollArea, QSizePolicy, QTabWidget

    class DetailTabbedWidget(QTabWidget, DetailPaneWidgetMixin):
        def __init__(self) -> None:
            super().__init__()
            self.setObjectName("detailTabs")
            self._explore = _scroll_area()
            self._information = _scroll_area()
            self.addTab(self._explore, DETAIL_TAB_TITLES[0])
            self.addTab(self._information, DETAIL_TAB_TITLES[1])

        def render_detail(self, detail: DetailPaneModel) -> None:
            self.setAccessibleName(detail.title)
            self.setAccessibleDescription(detail_accessible_text(detail))
            _replace_scroll_widget(
                self._explore,
                create_explore_widget(detail, status_callback=status_callback),
            )
            _replace_scroll_widget(
                self._information,
                create_device_information_widget(detail, status_callback=status_callback),
            )
            self.setCurrentIndex(0)

    def _scroll_area() -> object:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        return scroll

    def _replace_scroll_widget(scroll: object, widget: object) -> None:
        old = scroll.takeWidget()
        if old is not None:
            old.deleteLater()
        scroll.setWidget(widget)

    return DetailTabbedWidget()
