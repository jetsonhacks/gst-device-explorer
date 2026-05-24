"""Minimal PySide6 main window for the GUI shell."""

from __future__ import annotations

from collections.abc import Mapping

from gst_device_explorer.gui.model import DetailPaneModel, MediaExplorerSnapshot


def create_main_window(
    snapshot: MediaExplorerSnapshot,
    detail_panes: Mapping[str, DetailPaneModel] | None = None,
) -> object:
    """Create the main Qt window for a GUI snapshot."""

    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QMainWindow, QSplitter, QTreeWidget

    from gst_device_explorer.gui.builders import build_unknown_detail_pane
    from gst_device_explorer.gui.qt_detail import create_detail_pane_widget
    from gst_device_explorer.gui.qt_sidebar import populate_sidebar

    class MediaExplorerMainWindow(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle("gst-device-explorer")
            self.resize(980, 680)
            self._detail_panes = dict(detail_panes or {})

            splitter = QSplitter(Qt.Horizontal)
            self._tree = QTreeWidget()
            self._tree.setObjectName("sidebarTree")
            self._tree.setMinimumWidth(280)
            self._tree.setMaximumWidth(420)
            self._detail = create_detail_pane_widget()
            splitter.addWidget(self._tree)
            splitter.addWidget(self._detail)
            splitter.setStretchFactor(0, 0)
            splitter.setStretchFactor(1, 1)
            self.setCentralWidget(splitter)

            populate_sidebar(self._tree, snapshot.sidebar_roots)
            self._tree.itemSelectionChanged.connect(self._selection_changed)
            self._select_initial(snapshot)

        def _selection_changed(self) -> None:
            items = self._tree.selectedItems()
            if not items:
                self._detail.render_detail(snapshot.detail_pane)
                return
            node_id = items[0].data(0, Qt.UserRole)
            detail = self._detail_panes.get(str(node_id), build_unknown_detail_pane(str(node_id)))
            self._detail.render_detail(detail)

        def _select_initial(self, initial_snapshot: MediaExplorerSnapshot) -> None:
            selected = initial_snapshot.selected_node_id
            if selected is not None:
                item = _find_item_by_node_id(self._tree, selected, Qt.UserRole)
                if item is not None:
                    self._tree.setCurrentItem(item)
                    return
            self._detail.render_detail(initial_snapshot.detail_pane)

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
