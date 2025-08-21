"""OPC/UA configuration management."""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class OPCConfig:
    """OPC/UA configuration settings."""

    # Connection settings
    endpoint: str = "opc.tcp://127.0.0.1:4840"
    connection_timeout: int = 10
    watchdog_interval: int = 30

    # Retry settings
    retry_attempts: int = 3
    retry_delay: float = 1.0
    max_retry_delay: float = 30.0

    # Node configuration
    namespace_uri: str = "http://wetering.potlilium.nl/potting-lines"

    # Security settings (for production)
    use_security: bool = False
    certificate_path: Optional[str] = None
    private_key_path: Optional[str] = None

    # Environment-specific overrides
    environment: str = "development"


class OPCConfigManager:
    """Configuration manager for OPC/UA settings."""

    def __init__(self):
        self._config: Optional[OPCConfig] = None

    def load_config(self, config_file: Optional[Path] = None) -> OPCConfig:
        """Load configuration from file and environment variables."""
        if self._config is not None:
            return self._config

        # Start with defaults
        config_dict = asdict(OPCConfig())

        # Load from config file if provided
        if config_file and config_file.exists():
            try:
                import json

                with open(config_file) as f:
                    file_config = json.load(f)
                config_dict.update(file_config.get("opc", {}))
                logger.info(f"Loaded OPC config from {config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config from {config_file}: {e}")

        # Override with environment variables
        env_overrides = self._load_env_overrides()
        config_dict.update(env_overrides)

        self._config = OPCConfig(**config_dict)
        logger.info(f"OPC configuration loaded for environment: {self._config.environment}")

        return self._config

    def _load_env_overrides(self) -> Dict[str, Any]:
        """Load configuration overrides from environment variables."""
        overrides = {}

        # Map environment variables to config fields
        env_mappings = {
            "OPC_ENDPOINT": "endpoint",
            "OPC_CONNECTION_TIMEOUT": "connection_timeout",
            "OPC_WATCHDOG_INTERVAL": "watchdog_interval",
            "OPC_RETRY_ATTEMPTS": "retry_attempts",
            "OPC_RETRY_DELAY": "retry_delay",
            "OPC_USE_SECURITY": "use_security",
            "OPC_CERTIFICATE_PATH": "certificate_path",
            "OPC_PRIVATE_KEY_PATH": "private_key_path",
            "ENVIRONMENT": "environment",
        }

        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Type conversion
                if config_key in ["connection_timeout", "watchdog_interval", "retry_attempts"]:
                    overrides[config_key] = int(value)
                elif config_key in ["retry_delay", "max_retry_delay"]:
                    overrides[config_key] = float(value)
                elif config_key in ["use_security"]:
                    overrides[config_key] = value.lower() in ("true", "1", "yes")
                else:
                    overrides[config_key] = value

                logger.debug(f"Override from env: {config_key} = {overrides[config_key]}")

        return overrides

    def get_config(self) -> OPCConfig:
        """Get the current configuration."""
        if self._config is None:
            return self.load_config()
        return self._config

    def reload_config(self, config_file: Optional[Path] = None) -> OPCConfig:
        """Reload configuration from file and environment."""
        self._config = None
        return self.load_config(config_file)

    def validate_config(self, config: OPCConfig) -> bool:
        """Validate configuration settings."""
        errors = []

        if not config.endpoint:
            errors.append("OPC endpoint cannot be empty")

        if config.connection_timeout <= 0:
            errors.append("Connection timeout must be positive")

        if config.retry_attempts < 0:
            errors.append("Retry attempts cannot be negative")

        if config.retry_delay <= 0:
            errors.append("Retry delay must be positive")

        if config.use_security:
            if not config.certificate_path or not Path(config.certificate_path).exists():
                errors.append("Certificate file not found when security is enabled")
            if not config.private_key_path or not Path(config.private_key_path).exists():
                errors.append("Private key file not found when security is enabled")

        if errors:
            for error in errors:
                logger.error(f"Configuration error: {error}")
            return False

        logger.info("OPC configuration validation passed")
        return True


# Global configuration manager instance
_config_manager: Optional[OPCConfigManager] = None


def get_config_manager() -> OPCConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = OPCConfigManager()
    return _config_manager


def get_opc_config() -> OPCConfig:
    """Get the current OPC configuration."""
    return get_config_manager().get_config()


def reload_opc_config(config_file: Optional[Path] = None) -> OPCConfig:
    """Reload OPC configuration."""
    return get_config_manager().reload_config(config_file)
