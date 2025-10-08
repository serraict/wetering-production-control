"""Firebird database connection utilities."""

import os
from typing import Dict, Optional

import fdb


def get_firebird_config() -> Dict[str, str]:
    """Get Firebird connection configuration from environment.

    Returns:
        Dict with connection parameters for Firebird database.
    """
    return {
        "host": os.getenv("FIREBIRD_HOST", "localhost"),
        "port": int(os.getenv("FIREBIRD_PORT", "3050")),
        "database": os.getenv("FIREBIRD_DATABASE", "/firebird/data/production.fdb"),
        "user": os.getenv("FIREBIRD_USER", "SYSDBA"),
        "password": os.getenv("FIREBIRD_PASSWORD", "masterkey"),
    }


def get_connection():
    """Get a Firebird database connection.

    Returns:
        fdb.Connection: Active database connection

    Raises:
        fdb.DatabaseError: If connection fails
    """
    config = get_firebird_config()

    return fdb.connect(
        host=config["host"],
        port=config["port"],
        database=config["database"],
        user=config["user"],
        password=config["password"],
    )


def execute_firebird_command(sql: str, params: Optional[tuple] = None) -> Dict[str, any]:
    """Execute a SQL command on Firebird database.

    Args:
        sql: SQL command to execute (use ? for parameters)
        params: Optional tuple of parameters for the SQL query

    Returns:
        Dict with 'success' boolean and 'message' or 'error' string

    Example:
        execute_firebird_command(
            "UPDATE TEELTPL SET AFW_AFLEV = ? WHERE TEELTNR = ?",
            (10, '24096')
        )
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)

        conn.commit()
        cursor.close()
        conn.close()

        return {"success": True, "message": "Command executed successfully"}

    except fdb.DatabaseError as e:
        return {"success": False, "error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}
