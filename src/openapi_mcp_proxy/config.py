"""Public configuration helpers wrapping the core runtime modules."""

from __future__ import annotations

# Re-export frequently used symbols for backwards compatibility.
from .core.config import (
    DEFAULT_SERVER_NAME,
    ENV_PREFIX,
    OPENAPI_SPEC_ENV_VAR,
    AuthConfig,
    ClientConfig,
    ConfigError,
    ConfigSource,
    RuntimeConfig,
    build_arg_parser,
    load_runtime_config,
)


__all__ = [
    "AuthConfig",
    "ClientConfig",
    "ConfigError",
    "ConfigSource",
    "RuntimeConfig",
    "DEFAULT_SERVER_NAME",
    "ENV_PREFIX",
    "OPENAPI_SPEC_ENV_VAR",
    "build_arg_parser",
    "load_runtime_config",
]
