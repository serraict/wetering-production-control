"""Textual TUI over the PLC monitor: live view of PLC + Leuze nodes,
each pane fed by the same supervised connect loops as the headless
JSONL monitor.

Run:
    uv run python -m production_control.opcua.tui

Quits on `q`. Skips the Leuze pane if VINEAPP_OPCUA_LEUZE_URL is unset.

Independent of `production_control.opcua.monitor`'s stdout JSONL stream
(this slice is TUI-only; file logging is v4).
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import partial
from typing import Any

from asyncua import ua

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, Header, Input, Static

from . import config
from .monitor import _parse_value, run_plc, supervise

logger = logging.getLogger("opcua_tui")


@dataclass
class Row:
    name: str
    value: Any = None
    server_ts: datetime | None = None
    status: str | None = None
    received_at: datetime | None = None


class StateHandler:
    """asyncua subscription handler that mirrors notifications into a shared
    dict instead of writing JSONL. The TUI reads from the dict on a timer.

    Also keeps a reference to the live `asyncua.Client` so the TUI can issue
    ad-hoc writes through the same connection (set/cleared by run_plc /
    run_leuze around the `async with client:` block)."""

    def __init__(self, source: str, state: dict[tuple[str, str], Row]) -> None:
        self._source = source
        self._state = state
        self._names: dict[str, str] = {}
        self.client = None  # set by run_plc/run_leuze; None when disconnected

    def register(self, node, name: str) -> None:
        node_id = node.nodeid.to_string()
        self._names[node_id] = name
        self._state.setdefault((self._source, node_id), Row(name=name))

    def set_client(self, client) -> None:
        self.client = client

    def datachange_notification(self, node, val, data) -> None:
        node_id = node.nodeid.to_string()
        monitored = data.monitored_item.Value
        self._state[(self._source, node_id)] = Row(
            name=self._names.get(node_id, node_id),
            value=val,
            server_ts=monitored.ServerTimestamp,
            status=str(monitored.StatusCode.name) if monitored.StatusCode else None,
            received_at=datetime.now(timezone.utc),
        )

    def status_change_notification(self, status) -> None:  # noqa: D401
        logger.info("status: %s", status)

    def event_notification(self, event) -> None:  # noqa: D401
        pass


def _ago(received: datetime | None, now: datetime) -> str:
    if received is None:
        return "—"
    secs = (now - received).total_seconds()
    if secs < 60:
        return f"{secs:.0f}s ago"
    if secs < 3600:
        return f"{secs / 60:.0f}m ago"
    return f"{secs / 3600:.0f}h ago"


def _value_str(v: Any) -> str:
    if v is None:
        return "—"
    return str(v)


class WriteValueScreen(ModalScreen[str | None]):
    """Modal prompt for writing a new value to a node. Returns the entered
    string on submit, or None on cancel. The caller is responsible for
    coercing the string into the node's VariantType and performing the
    actual write."""

    BINDINGS = [("escape", "cancel", "Cancel")]
    CSS = """
    WriteValueScreen {
        align: center middle;
    }
    #write-dialog {
        background: $surface;
        border: thick $accent;
        padding: 1 2;
        width: 70;
        height: auto;
    }
    #write-dialog .muted {
        color: $text-muted;
    }
    """

    def __init__(self, *, source: str, node_name: str, node_id: str, current: str) -> None:
        super().__init__()
        self._source = source
        self._node_name = node_name
        self._node_id = node_id
        self._current = current

    def compose(self) -> ComposeResult:
        with Vertical(id="write-dialog"):
            yield Static(f"Write to {self._source}: [b]{self._node_name}[/b]")
            yield Static(self._node_id, classes="muted")
            yield Static(f"current: {self._current}", classes="muted")
            yield Input(value=self._current, id="value_input")
            yield Static("Enter = write · Esc = cancel", classes="muted")

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value)

    def action_cancel(self) -> None:
        self.dismiss(None)


class MonitorApp(App):
    """Two-pane live view of the PLC and Leuze subscriptions."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("w", "write_selected", "Write"),
    ]
    CSS = """
    Static.source-header {
        padding: 0 1;
        background: $accent 20%;
        color: $text;
    }
    DataTable {
        height: 1fr;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.state: dict[tuple[str, str], Row] = {}
        self._tasks: list[asyncio.Task] = []
        self._leuze_enabled = bool(os.environ.get("VINEAPP_OPCUA_LEUZE_URL"))
        self._handlers: dict[str, StateHandler] = {}
        # Per-source ordered list of node_ids matching the DataTable's row
        # order. Used to map `cursor_row` -> node_id for the write action.
        self._order: dict[str, list[str]] = {"plc": [], "leuze": []}

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical():
            yield Static("PLC — connecting…", id="plc_header", classes="source-header")
            yield DataTable(id="plc_table", zebra_stripes=True)
            if self._leuze_enabled:
                yield Static("Leuze — connecting…", id="leuze_header", classes="source-header")
                yield DataTable(id="leuze_table", zebra_stripes=True)
        yield Footer()

    async def on_mount(self) -> None:
        table_ids = ["plc_table"] + (["leuze_table"] if self._leuze_enabled else [])
        for tbl_id in table_ids:
            tbl = self.query_one(f"#{tbl_id}", DataTable)
            # Explicit column keys so `_refresh_pane` can `update_cell` by key
            # rather than clearing+re-adding (which would reset the cursor).
            # Value last so long payloads (e.g. Leuze scan URLs) can grow
            # into the remaining width instead of squeezing the other columns.
            tbl.add_column("Node", key="name")
            tbl.add_column("Updated", key="updated")
            tbl.add_column("Value", key="value")
            tbl.cursor_type = "row"

        plc_handler = StateHandler("plc", self.state)
        self._handlers["plc"] = plc_handler
        self._tasks.append(
            asyncio.create_task(supervise("plc", partial(run_plc, plc_handler)), name="plc")
        )

        if self._leuze_enabled:
            from .leuze import run_leuze  # lazy: triggers cert monkey-patch

            leuze_handler = StateHandler("leuze", self.state)
            self._handlers["leuze"] = leuze_handler
            self._tasks.append(
                asyncio.create_task(
                    supervise("leuze", partial(run_leuze, leuze_handler)), name="leuze"
                )
            )

        # Focus the PLC table so 'w' works without an extra Tab press.
        self.query_one("#plc_table", DataTable).focus()
        self.set_interval(0.25, self._refresh)

    async def on_unmount(self) -> None:
        for t in self._tasks:
            t.cancel()
        for t in self._tasks:
            try:
                await t
            except (asyncio.CancelledError, Exception):
                pass

    def _refresh(self) -> None:
        now = datetime.now(timezone.utc)
        self._refresh_pane("plc", "PLC (10.0.0.190)", header_keys=("Mode", "ErrorStatus"), now=now)
        if self._leuze_enabled:
            self._refresh_pane("leuze", "Leuze (10.0.0.191)", header_keys=(), now=now)

    def _refresh_pane(
        self, source: str, label: str, header_keys: tuple[str, ...], now: datetime
    ) -> None:
        # Pull this source's rows out of the shared state as (node_id, Row).
        # Sort by name for first-add ordering; subsequent refreshes only
        # touch existing rows in place, so the visual order matches the
        # alphabetical order from the first batch even if new rows arrive
        # later (they get appended at the bottom — rare in practice).
        items = [(nid, r) for (src, nid), r in self.state.items() if src == source]
        rows = [r for _, r in items]

        header = self.query_one(f"#{source}_header", Static)
        if not rows:
            header.update(f"{label} — connecting…")
        else:
            latest = max((r.received_at for r in rows if r.received_at), default=None)
            parts = [label, f"upd {_ago(latest, now)}"]
            for key in header_keys:
                hit = next((r for r in rows if r.name == key), None)
                if hit is not None:
                    parts.append(f"{key}: {_value_str(hit.value)}")
            header.update("  ·  ".join(parts))

        tbl = self.query_one(f"#{source}_table", DataTable)
        known = self._order[source]
        known_set = set(known)

        # Add rows not yet in the table — sort the new arrivals by name so
        # the initial population is alphabetical.
        new_items = sorted(
            ((nid, r) for nid, r in items if nid not in known_set),
            key=lambda nr: nr[1].name,
        )
        for nid, row in new_items:
            tbl.add_row(
                row.name,
                _ago(row.received_at, now),
                _value_str(row.value),
                key=nid,
            )
            known.append(nid)

        # Update value/updated cells in place. Skip "name" — it doesn't change
        # after registration, and update_cell with the same value is wasteful.
        for nid, row in items:
            try:
                # update_width: without it the column keeps the width of the
                # first-seen value and longer payloads get clipped.
                tbl.update_cell(nid, "value", _value_str(row.value), update_width=True)
                tbl.update_cell(nid, "updated", _ago(row.received_at, now))
            except Exception:  # pragma: no cover — row removed mid-refresh
                pass

    # --- Write action ----------------------------------------------------

    def action_write_selected(self) -> None:
        """Open the write modal for the row under the cursor of the
        currently focused DataTable."""
        focused = self.focused
        if not isinstance(focused, DataTable):
            self.notify("Focus a table (Tab) before pressing w", severity="warning")
            return
        source = "plc" if focused.id == "plc_table" else "leuze"
        row_idx = focused.cursor_row
        order = self._order.get(source, [])
        if row_idx is None or row_idx < 0 or row_idx >= len(order):
            return
        node_id = order[row_idx]
        row = self.state.get((source, node_id))
        if row is None:
            return

        def on_value(value: str | None) -> None:
            if value is None:
                return
            asyncio.create_task(self._perform_write(source, node_id, value))

        self.push_screen(
            WriteValueScreen(
                source=source,
                node_name=row.name,
                node_id=node_id,
                current=_value_str(row.value),
            ),
            on_value,
        )

    async def _perform_write(self, source: str, node_id: str, raw_value: str) -> None:
        """Write `raw_value` to `node_id` through the live client owned by
        the source's subscription loop. Builds the DataValue with no
        timestamps — Omron NX rejects WriteValue otherwise."""
        handler = self._handlers.get(source)
        if handler is None or handler.client is None:
            self.notify(f"{source} not connected; cannot write", severity="error")
            return
        try:
            node = handler.client.get_node(node_id)
            current = await node.read_data_value()
            vtype = current.Value.VariantType
            parsed = _parse_value(raw_value, vtype)
            await node.write_value(ua.DataValue(ua.Variant(parsed, vtype)))
            self.notify(f"wrote {parsed!r} to {node_id} ({vtype.name})")
        except Exception as exc:  # noqa: BLE001 — surface any write failure
            logger.warning("write %s = %r failed: %r", node_id, raw_value, exc)
            self.notify(f"write failed: {exc}", severity="error")


def cli() -> None:
    # Preflight before Textual grabs the alternate screen; otherwise a
    # missing env var fails inside an asyncio task and the message is
    # wiped when the screen is restored. Ask config for the exact list
    # so VINEAPP_OPCUA_SECURITY=none only requires the URLs.
    mode = config.current_mode()
    required = [
        *config.required_env_for(mode, "plc"),
        *config.required_env_for(mode, "leuze"),
    ]
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        print(
            f"opc-monitor: missing required env vars (VINEAPP_OPCUA_SECURITY={mode}):",
            file=sys.stderr,
        )
        for name in missing:
            print(f"  {name}", file=sys.stderr)
        print("See docs/deployment.md for what each var should hold.", file=sys.stderr)
        sys.exit(2)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )
    logging.getLogger("asyncua").setLevel(logging.WARNING)
    MonitorApp().run()


if __name__ == "__main__":
    cli()
