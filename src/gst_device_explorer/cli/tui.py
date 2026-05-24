"""Thin terminal runner for the read-only TUI review mode."""

from __future__ import annotations

import curses

import gst_device_explorer.cli.commands as commands
import gst_device_explorer.core.config as config
import gst_device_explorer.core.presets as presets
import gst_device_explorer.core.schema as schema
from gst_device_explorer.core.tui import (
    TuiNavigationState,
    TuiReviewModel,
    build_tui_review_model,
    handle_tui_key,
    render_current_screen,
    render_overview_lines,
)


def build_review_model() -> TuiReviewModel:
    """Gather existing read-only information for the TUI."""

    return build_tui_review_model(
        report=commands.build_system_report(),
        presets=presets.list_presets(),
        config=config.effective_config(),
        schema_documents=schema.list_schema_documents(),
    )


def render_snapshot(model: TuiReviewModel | None = None) -> str:
    """Render the initial overview without entering interactive mode."""

    model = model or build_review_model()
    return "\n".join(render_overview_lines(model)) + "\n"


def run_tui(model: TuiReviewModel | None = None) -> int:
    """Run the interactive curses TUI."""

    model = model or build_review_model()
    curses.wrapper(lambda stdscr: _run_curses(stdscr, model))
    return 0


def _run_curses(stdscr, model: TuiReviewModel) -> None:
    curses.curs_set(0)
    stdscr.keypad(True)
    state = TuiNavigationState()

    while not state.quit_requested:
        _draw(stdscr, render_current_screen(model, state))
        key = _read_key(stdscr.getch())
        state = handle_tui_key(state, key)


def _draw(stdscr, lines: tuple[str, ...]) -> None:
    stdscr.erase()
    height, width = stdscr.getmaxyx()
    if height < 4 or width < 20:
        message = "Terminal too small. Press q to quit."
        stdscr.addnstr(0, 0, message, max(0, width - 1))
        stdscr.refresh()
        return

    for row, line in enumerate(lines[: max(0, height - 1)]):
        stdscr.addnstr(row, 0, line, max(0, width - 1))
    stdscr.refresh()


def _read_key(code: int) -> str:
    if code in (ord("q"), ord("Q")):
        return "q"
    if code in (curses.KEY_UP, ord("k")):
        return "up"
    if code in (curses.KEY_DOWN, ord("j")):
        return "down"
    if code in (10, 13, curses.KEY_ENTER):
        return "enter"
    if code in (27,):
        return "escape"
    if code in (curses.KEY_BACKSPACE, 8, 127):
        return "backspace"
    if ord("1") <= code <= ord("9"):
        return chr(code)
    return ""
