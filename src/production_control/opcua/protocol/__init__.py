"""OS ↔ PC scan-cycle protocol implementation.

See `docs/protocol.md` for the contract, `features/protocol/` for the
executable spec, and `work/notes/os_pc_protocol_implementation.md` for
the implementation slice plan.
"""

from .scan_parser import parse_scan

__all__ = ["parse_scan"]
