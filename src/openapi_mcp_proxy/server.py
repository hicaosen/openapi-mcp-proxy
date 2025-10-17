"""Entry points for the generic OpenAPI → MCP proxy server."""

from __future__ import annotations

import sys
from typing import Optional, Sequence, Tuple

from .config import ConfigError, RuntimeConfig, load_runtime_config
from .core.server import ProxyRegistry, create_proxy as _create_proxy
from .core.spec import OpenAPISpecError, OpenAPISpecLoader

create_proxy = _create_proxy

__all__ = [
    "load_runtime_config",
    "create_proxy",
    "get_proxy_instance",
    "run",
]


_registry: ProxyRegistry | None = None


def configure_runtime(
    argv: Sequence[str] | None = None,
) -> Tuple[RuntimeConfig, Sequence[str]]:
    """Parse CLI/environment information into a runtime configuration."""

    return load_runtime_config(argv)


def get_proxy_instance(config: RuntimeConfig | None = None):  # pragma: no cover - thin wrapper
    global _registry
    if _registry is None:
        if config is None:
            raise RuntimeError("未初始化代理实例，请先提供 RuntimeConfig。")
        _registry = ProxyRegistry(config=config)
    else:
        if config is not None and config.openapi_source != _registry.config.openapi_source:
            raise RuntimeError(
                "MCP 代理已经基于不同的 OpenAPI 规范创建。如需切换，请重启进程。"
            )
    return _registry.get()


def run(argv: Sequence[str] | None = None) -> None:
    """CLI entry that builds the proxy and starts the MCP server."""

    argv = list(argv) if argv is not None else sys.argv[1:]

    try:
        config, remaining = load_runtime_config(argv)
    except ConfigError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc

    # Preserve remaining arguments for potential downstream consumers
    sys.argv = [sys.argv[0], *remaining]

    global _registry
    try:
        _registry = ProxyRegistry(config=config, loader=OpenAPISpecLoader())
        proxy = _registry.get()
    except (ConfigError, OpenAPISpecError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc

    proxy.run()


if __name__ == "__main__":  # pragma: no cover
    run()
