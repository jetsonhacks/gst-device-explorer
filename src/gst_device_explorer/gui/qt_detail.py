"""Qt selected-item detail pane orchestration."""

from __future__ import annotations

from collections.abc import Callable

from gst_device_explorer.core.models import CameraControlSet
from gst_device_explorer.gui.model import DetailPaneModel
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

DETAIL_TAB_TITLES = ("Explore",)


class DetailPaneWidgetMixin:
    """Mixin containing renderer logic shared by the concrete QWidget."""

    def render_detail(self, detail: DetailPaneModel, *, preview_runner: object | None = None) -> None:
        raise NotImplementedError


def detail_tab_titles(_detail: DetailPaneModel) -> tuple[str, str]:
    """Return the selected-item tab labels."""

    return DETAIL_TAB_TITLES


def create_detail_pane_widget(
    *,
    status_callback: Callable[[str], None] | None = None,
    navigate_callback: Callable[[str], None] | None = None,
    preview_runner: object | None = None,
    camera_control_writer: object | None = None,
    camera_control_refresher: Callable[[str], CameraControlSet | None] | None = None,
    current_endpoint_getter: Callable[[], str | None] | None = None,
) -> object:
    """Create the concrete Qt detail widget.

    PySide6 imports stay inside this factory so non-GUI imports remain light.
    """

    from PySide6.QtCore import QEvent
    from PySide6.QtWidgets import QScrollArea, QSizePolicy, QTabWidget

    class _NoAutoScrollArea(QScrollArea):
        def focusNextPrevChild(self, next_: bool) -> bool:
            from PySide6.QtWidgets import QWidget
            return QWidget.focusNextPrevChild(self, next_)

    class DetailTabbedWidget(QTabWidget, DetailPaneWidgetMixin):
        def __init__(self) -> None:
            super().__init__()
            self.setObjectName("detailTabs")
            self._explore = _scroll_area()
            self._fallback_runner = preview_runner
            self.addTab(self._explore, DETAIL_TAB_TITLES[0])

        def render_detail(self, detail: DetailPaneModel, *, preview_runner: object | None = None) -> None:
            _runner = preview_runner if preview_runner is not None else self._fallback_runner
            self.setAccessibleName(detail.title)
            self.setAccessibleDescription(detail_accessible_text(detail))
            _replace_scroll_widget(
                self._explore,
                create_explore_widget(
                    detail,
                    status_callback=status_callback,
                    navigate_callback=navigate_callback,
                    preview_runner=_runner,
                    camera_control_writer=camera_control_writer,
                    camera_control_refresher=camera_control_refresher,
                    current_endpoint_getter=current_endpoint_getter,
                ),
            )
            self.setCurrentIndex(0)

    def _scroll_area() -> object:
        scroll = _NoAutoScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        return scroll

    def _replace_scroll_widget(scroll: object, widget: object) -> None:
        old = scroll.takeWidget()
        if old is not None:
            old.deleteLater()
        scroll.setWidget(widget)

    return DetailTabbedWidget()
