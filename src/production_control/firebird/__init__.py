"""Firebird database connection and operations."""

from .connection import get_firebird_config, execute_firebird_command

__all__ = ["get_firebird_config", "execute_firebird_command"]
