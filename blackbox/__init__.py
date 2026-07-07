"""blackbox - Black Box flight recorder for Elite Dangerous."""

from pathlib import Path

__version__ = "0.1.0"

_PROJECT_DIR = Path(__file__).resolve().parent.parent


def get_db_path(config: dict | None = None) -> str:
    """Get the default database path from config or return a fallback path."""
    if config and "db_path" in config:
        return config["db_path"]
    return str(_PROJECT_DIR / "blackbox" / "blackbox.db")
