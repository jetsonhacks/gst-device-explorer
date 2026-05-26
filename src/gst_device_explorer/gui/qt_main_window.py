"""Minimal PySide6 main window for the GUI shell."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Callable

from gst_device_explorer.gui.model import DetailPaneModel, MediaExplorerSnapshot


def create_main_window(
    snapshot: MediaExplorerSnapshot,
    detail_panes: Mapping[str, DetailPaneModel] | None = None,
    refresh_builder: Callable[..., object] | None = None,
    preview_runner: object | None = None,
) -> object:
    """Create the main Qt window for a GUI snapshot."""

    from PySide6.QtCore import Qt
    from PySide6.QtGui import QAction
    from PySide6.QtWidgets import QApplication, QMainWindow, QSplitter, QToolBar, QTreeWidget

    from gst_device_explorer.gui.builders import build_unknown_detail_pane
    from gst_device_explorer.gui.live import build_loading_detail_pane
    from gst_device_explorer.gui.preview_runner import PreviewRunner
    from gst_device_explorer.gui.qt_detail import create_detail_pane_widget
    from gst_device_explorer.gui.qt_sidebar import populate_sidebar

    class MediaExplorerMainWindow(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle("gst-device-explorer")
            self.resize(980, 680)
            self._snapshot = snapshot
            self._detail_panes = dict(detail_panes or {})
            self._refresh_builder = refresh_builder
            self._preview_runners: dict[str, PreviewRunner] = {}
            if preview_runner is not None:
                self._preview_runners["__injected__"] = preview_runner

            splitter = QSplitter(Qt.Horizontal)
            self._tree = QTreeWidget()
            self._tree.setObjectName("sidebarTree")
            self._tree.setMinimumWidth(280)
            self._tree.setMaximumWidth(420)
            self._detail = create_detail_pane_widget(
                status_callback=lambda message: self.statusBar().showMessage(message, 2500),
                navigate_callback=lambda node_id: self.select_node(node_id),
            )
            splitter.addWidget(self._tree)
            splitter.addWidget(self._detail)
            splitter.setStretchFactor(0, 0)
            splitter.setStretchFactor(1, 1)
            self.setCentralWidget(splitter)

            toolbar = QToolBar("Main")
            toolbar.setObjectName("mainToolbar")
            self.addToolBar(toolbar)
            self._refresh_action = QAction("Refresh", self)
            self._refresh_action.setObjectName("refreshAction")
            self._refresh_action.setToolTip("Refresh discovered media devices")
            self._refresh_action.triggered.connect(lambda: self.refresh_snapshot())
            toolbar.addAction(self._refresh_action)

            populate_sidebar(self._tree, self._snapshot.sidebar_roots)
            self._tree.itemSelectionChanged.connect(self._selection_changed)
            self._select_initial(self._snapshot)

        def _runner_for(self, detail: DetailPaneModel) -> PreviewRunner:
            key = detail.selected_id or ""
            if key not in self._preview_runners:
                self._preview_runners[key] = PreviewRunner()
            return self._preview_runners[key]

        def _selection_changed(self) -> None:
            items = self._tree.selectedItems()
            if not items:
                self._detail.render_detail(self._snapshot.detail_pane)
                return
            node_id = items[0].data(0, Qt.UserRole)
            detail = self._detail_panes.get(str(node_id), build_unknown_detail_pane(str(node_id)))
            self._detail.render_detail(detail, preview_runner=self._runner_for(detail))

        def _select_initial(self, initial_snapshot: MediaExplorerSnapshot) -> None:
            selected = initial_snapshot.selected_node_id
            if selected is not None:
                item = _find_item_by_node_id(self._tree, selected, Qt.UserRole)
                if item is not None:
                    self._tree.setCurrentItem(item)
                    return
            self._detail.render_detail(initial_snapshot.detail_pane)

        def select_node(self, node_id: str) -> None:
            item = _find_item_by_node_id(self._tree, node_id, Qt.UserRole)
            if item is None:
                return
            self._tree.setCurrentItem(item)

        def refresh_snapshot(self) -> None:
            if self._refresh_builder is None:
                return
            for runner in self._preview_runners.values():
                runner.cleanup()
            self._preview_runners.clear()
            previous_selection = self._current_node_id()
            self._detail.render_detail(build_loading_detail_pane())
            QApplication.processEvents()
            bundle = self._refresh_builder(previous_selected_id=previous_selection)
            self._snapshot = bundle.snapshot
            self._detail_panes = dict(bundle.detail_panes)
            self._tree.blockSignals(True)
            populate_sidebar(self._tree, self._snapshot.sidebar_roots)
            self._tree.blockSignals(False)
            self._select_initial(self._snapshot)

        def _current_node_id(self) -> str | None:
            items = self._tree.selectedItems()
            if not items:
                return self._snapshot.selected_node_id
            return str(items[0].data(0, Qt.UserRole))

        def closeEvent(self, event: object) -> None:
            for runner in self._preview_runners.values():
                runner.cleanup()
            super().closeEvent(event)

    return MediaExplorerMainWindow()


def _find_item_by_node_id(tree: object, node_id: str, user_role: object) -> object | None:
    for index in range(tree.topLevelItemCount()):
        found = _find_child_by_node_id(tree.topLevelItem(index), node_id, user_role)
        if found is not None:
            return found
    return None


def _find_child_by_node_id(item: object, node_id: str, user_role: object) -> object | None:
    if item.data(0, user_role) == node_id:
        return item
    for index in range(item.childCount()):
        found = _find_child_by_node_id(item.child(index), node_id, user_role)
        if found is not None:
            return found
    return None
