"""Qt sidebar rendering helpers."""

from __future__ import annotations

from gst_device_explorer.gui.model import SidebarNode


def populate_sidebar(tree: object, roots: tuple[SidebarNode, ...]) -> None:
    """Populate a QTreeWidget with sidebar nodes.

    The tree object is intentionally typed loosely so this module can still be
    imported by documentation tools without requiring PySide6 type imports.
    """

    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QTreeWidgetItem

    tree.clear()
    tree.setHeaderLabels(["Devices / Groups"])
    for node in roots:
        tree.addTopLevelItem(_tree_item(node, QTreeWidgetItem, Qt.UserRole))
    tree.expandAll()


def _tree_item(node: SidebarNode, item_type: type, user_role: object) -> object:
    item = item_type([_label_for_node(node)])
    item.setData(0, user_role, node.id)
    item.setToolTip(0, _tooltip_for_node(node))
    for child in node.children:
        item.addChild(_tree_item(child, item_type, user_role))
    return item


def _label_for_node(node: SidebarNode) -> str:
    prefix = {
        "root": "",
        "section": "",
        "group": "",
        "video": "",
        "audio_input": "",
        "audio_output": "",
    }.get(node.kind, "")
    return f"{prefix}{node.label}"


def _tooltip_for_node(node: SidebarNode) -> str:
    parts = [f"id: {node.id}", f"kind: {node.kind}", f"status: {node.status}"]
    if node.summary:
        parts.append(node.summary)
    return "\n".join(parts)
