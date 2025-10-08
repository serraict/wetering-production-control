"""Firebird database connection utilities."""

import os
import subprocess
from typing import Dict


def get_firebird_config() -> Dict[str, str]:
    """Get Firebird connection configuration from environment.

    Returns:
        Dict with connection parameters for Firebird database.
    """
    return {
        "host": os.getenv("FIREBIRD_HOST", "localhost"),
        "port": os.getenv("FIREBIRD_PORT", "3050"),
        "database": os.getenv("FIREBIRD_DATABASE", "/firebird/data/production.fdb"),
        "user": os.getenv("FIREBIRD_USER", "SYSDBA"),
        "password": os.getenv("FIREBIRD_PASSWORD", "masterkey"),
    }


def execute_firebird_command(sql: str) -> Dict[str, any]:
    """Execute a SQL command on Firebird database via docker exec.

    Args:
        sql: SQL command to execute

    Returns:
        Dict with 'success' boolean and 'message' or 'error' string

    Note:
        This uses docker compose exec to run isql commands since we don't have
        the Firebird client library installed locally.
    """
    config = get_firebird_config()

    try:
        # Build the SQL with COMMIT on the same line to avoid isql parser issues
        full_sql = f"{sql}; COMMIT;"

        # Execute SQL via docker compose exec
        result = subprocess.run(
            [
                "docker",
                "compose",
                "exec",
                "-T",
                "firebird",
                "/opt/firebird/bin/isql",
                "-user",
                config["user"],
                "-password",
                config["password"],
                f"{config['host']}:{config['database']}",
            ],
            input=full_sql,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            return {"success": True, "message": "Command executed successfully"}
        else:
            return {"success": False, "error": result.stderr or "Unknown error"}

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}
