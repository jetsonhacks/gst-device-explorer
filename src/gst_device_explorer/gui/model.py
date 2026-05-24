"""Toolkit-neutral GUI application models.

These dataclasses describe what a future GUI can render. They are metadata
only: no model here probes hardware, launches pipelines, captures media, or
imports a GUI toolkit.
"""

from __future__ import annotations

from dataclasses import dataclass

from gst_device_explorer.core.suggestions import SuggestedCommand


@dataclass(frozen=True)
class SidebarNode:
    """One node in the GUI sidebar tree."""

    id: str
    label: str
    kind: str
    status: str
    children: tuple["SidebarNode", ...] = ()
    target_kind: str | None = None
    target: str | None = None
    summary: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "children", tuple(self.children))


@dataclass(frozen=True)
class DetailSection:
    """A simple titled section in the selected item detail pane."""

    title: str
    items: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "items", tuple(self.items))


@dataclass(frozen=True)
class GuiAction:
    """Advisory metadata for a GUI button or menu item."""

    id: str
    label: str
    kind: str
    enabled: bool
    safety: str
    target_kind: str | None = None
    target: str | None = None
    suggested_command: SuggestedCommand | None = None
    disabled_reason: str | None = None


@dataclass(frozen=True)
class GuiActionResult:
    """Display model for a completed GUI action result.

    Milestone 19 does not execute actions; this exists so future GUI tests can
    render result states without coupling to a toolkit.
    """

    action_id: str
    status: str
    title: str
    messages: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "messages", tuple(self.messages))


@dataclass(frozen=True)
class DetailPaneModel:
    """The main detail pane for the selected sidebar node."""

    selected_id: str
    title: str
    kind: str
    status: str
    summary: tuple[str, ...] = ()
    sections: tuple[DetailSection, ...] = ()
    actions: tuple[GuiAction, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "summary", tuple(self.summary))
        object.__setattr__(self, "sections", tuple(self.sections))
        object.__setattr__(self, "actions", tuple(self.actions))


@dataclass(frozen=True)
class MediaExplorerSnapshot:
    """A complete GUI-facing snapshot of the current media explorer state."""

    sidebar_roots: tuple[SidebarNode, ...]
    detail_pane: DetailPaneModel
    selected_node_id: str | None = None
    status: str = "ok"
    summary: tuple[str, ...] = ()
    generated_at: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "sidebar_roots", tuple(self.sidebar_roots))
        object.__setattr__(self, "summary", tuple(self.summary))
