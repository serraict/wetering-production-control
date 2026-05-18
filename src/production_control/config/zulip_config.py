"""Zulip configuration management."""

import logging
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class ZulipConfig:
    """Zulip integration settings."""

    site: str = ""
    bot_email: str = ""
    bot_api_key: str = ""
    stream: str = "teelt"
    request_timeout: int = 5
    message_history_limit: int = 50


class ZulipConfigManager:
    """Load and cache the Zulip configuration."""

    def __init__(self) -> None:
        self._config: Optional[ZulipConfig] = None

    def load_config(self, config_file: Optional[Path] = None) -> ZulipConfig:
        if self._config is not None:
            return self._config

        config_dict = asdict(ZulipConfig())

        if config_file and config_file.exists():
            try:
                import json

                with open(config_file) as f:
                    file_config = json.load(f)
                config_dict.update(file_config.get("zulip", {}))
                logger.info(f"Loaded Zulip config from {config_file}")
            except Exception as e:
                logger.warning(f"Failed to load Zulip config from {config_file}: {e}")

        config_dict.update(self._load_env_overrides())

        self._config = ZulipConfig(**config_dict)
        return self._config

    def _load_env_overrides(self) -> Dict[str, Any]:
        env_mappings = {
            "ZULIP_SITE": "site",
            "ZULIP_BOT_EMAIL": "bot_email",
            "ZULIP_BOT_API_KEY": "bot_api_key",
            "ZULIP_STREAM": "stream",
            "ZULIP_TIMEOUT": "request_timeout",
            "ZULIP_HISTORY_LIMIT": "message_history_limit",
        }

        overrides: Dict[str, Any] = {}
        for env_var, key in env_mappings.items():
            value = os.getenv(env_var)
            if value is None:
                continue
            if key in {"request_timeout", "message_history_limit"}:
                overrides[key] = int(value)
            else:
                overrides[key] = value
        return overrides

    def get_config(self) -> ZulipConfig:
        if self._config is None:
            return self.load_config()
        return self._config

    def reload_config(self, config_file: Optional[Path] = None) -> ZulipConfig:
        self._config = None
        return self.load_config(config_file)

    def is_configured(self, config: Optional[ZulipConfig] = None) -> bool:
        """Whether the bot has enough config to actually talk to Zulip."""
        cfg = config or self.get_config()
        return bool(cfg.site and cfg.bot_email and cfg.bot_api_key)


_config_manager: Optional[ZulipConfigManager] = None


def get_config_manager() -> ZulipConfigManager:
    global _config_manager
    if _config_manager is None:
        _config_manager = ZulipConfigManager()
    return _config_manager


def get_zulip_config() -> ZulipConfig:
    return get_config_manager().get_config()
