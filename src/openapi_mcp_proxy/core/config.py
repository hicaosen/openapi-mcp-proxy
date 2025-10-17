"""Runtime configuration assembly for the OpenAPI → MCP proxy."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, MutableMapping, Sequence, Tuple

import yaml


DEFAULT_SERVER_NAME = "OpenAPI MCP Proxy"
OPENAPI_SPEC_ENV_VAR = "MCP_OPENAPI_SPEC"
ENV_PREFIX = "MCP_PROXY_"


class ConfigError(ValueError):
    """Raised when configuration sources cannot be resolved."""


@dataclass(slots=True)
class AuthConfig:
    """Unified description of the desired authentication strategy."""

    scheme: str = "none"
    token: str | None = None
    username: str | None = None
    password: str | None = None
    header_name: str | None = None
    header_value: str | None = None
    api_key_name: str | None = None
    api_key_value: str | None = None
    api_key_location: str = "header"
    extra_headers: dict[str, str] = field(default_factory=dict)

    @classmethod
    def none(cls) -> "AuthConfig":
        return cls()


@dataclass(slots=True)
class ClientConfig:
    """HTTP client runtime parameters."""

    timeout: float = 30.0
    verify_ssl: bool | str = True
    retries: int = 0
    proxies: str | Mapping[str, str] | None = None


@dataclass(slots=True)
class RuntimeConfig:
    """Fully hydrated runtime configuration."""

    openapi_source: str
    server_name: str = DEFAULT_SERVER_NAME
    base_url: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    auth: AuthConfig = field(default_factory=AuthConfig.none)
    client: ClientConfig = field(default_factory=ClientConfig)
    raw_sources: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ConfigSource:
    """Represents configuration fragments from different origins."""

    config_file: Mapping[str, Any] | None = None
    environment: Mapping[str, Any] | None = None
    cli: Mapping[str, Any] | None = None


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="OpenAPI specification → MCP proxy runtime configuration"
    )
    parser.add_argument("--openapi-spec", dest="openapi_spec", help="Specification source URI or path.")
    parser.add_argument("--config", dest="config_file", help="Path to a configuration file (YAML or JSON).")
    parser.add_argument("--server-name", dest="server_name", help="Display name for the MCP server.")
    parser.add_argument("--base-url", dest="base_url", help="Explicit base URL for outbound requests.")
    parser.add_argument("--timeout", dest="timeout", type=float, help="HTTP timeout in seconds (default 30).")
    parser.add_argument(
        "--verify-ssl",
        dest="verify_ssl",
        action="store_true",
        help="Enable TLS certificate verification (default).",
    )
    parser.add_argument(
        "--no-verify-ssl",
        dest="verify_ssl",
        action="store_false",
        help="Disable TLS certificate verification.",
    )
    parser.add_argument("--retries", dest="retries", type=int, help="Number of automatic retries when calling the upstream OpenAPI service.")
    parser.add_argument("--proxy", dest="proxies", help="HTTP proxy configuration passed to httpx (URL or JSON mapping).")
    parser.add_argument("--header", dest="headers", action="append", default=[], help="Additional default header in KEY=VALUE form. Can be passed multiple times.")

    # Authentication options
    parser.add_argument("--auth-type", dest="auth_type", help="Authentication scheme: none, bearer, basic, header, api-key.")
    parser.add_argument("--auth-token", dest="auth_token", help="Token for bearer authentication.")
    parser.add_argument("--auth-username", dest="auth_username", help="Username for basic authentication.")
    parser.add_argument("--auth-password", dest="auth_password", help="Password for basic authentication.")
    parser.add_argument("--auth-header", dest="auth_headers", action="append", default=[], help="Custom authentication header in KEY=VALUE form.")
    parser.add_argument("--auth-key-name", dest="auth_key_name", help="Identifier for API key authentication.")
    parser.add_argument("--auth-key-value", dest="auth_key_value", help="Secret value for API key authentication.")
    parser.add_argument(
        "--auth-key-location",
        dest="auth_key_location",
        choices=("header", "query", "cookie"),
        help="Location for injecting the API key (default header).",
    )

    return parser


def load_runtime_config(
    argv: Sequence[str] | None = None,
    env: Mapping[str, str] | None = None,
) -> Tuple[RuntimeConfig, Sequence[str]]:
    env = os.environ if env is None else env
    parser = build_arg_parser()
    args, remaining = parser.parse_known_args(argv)

    config_data: dict[str, Any] = {}
    config_path = args.config_file or env.get(f"{ENV_PREFIX}CONFIG")
    if config_path:
        config_data = _load_config_file(config_path)

    env_data = _extract_env_config(env)
    cli_data = _extract_cli_config(args)

    merged: dict[str, Any] = {}
    if config_data:
        merged.update(config_data)
    merged.update(env_data)
    merged.update(cli_data)

    openapi_source = _resolve_openapi_source(merged, env)
    server_name = merged.get("server_name", DEFAULT_SERVER_NAME)
    base_url = merged.get("base_url")
    headers = _merge_headers(config_data, env_data, cli_data)

    auth = _build_auth_config(merged)
    client_cfg = _build_client_config(merged)

    runtime = RuntimeConfig(
        openapi_source=openapi_source,
        server_name=server_name,
        base_url=base_url,
        headers=headers,
        auth=auth,
        client=client_cfg,
        raw_sources={
            "file": config_data,
            "env": env_data,
            "cli": cli_data,
        },
    )

    return runtime, remaining


def _load_config_file(path: str) -> dict[str, Any]:
    location = Path(path)
    if not location.exists():
        raise ConfigError(f"Specified configuration file does not exist: {path}")

    content = location.read_text(encoding="utf-8")
    suffix = location.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        data = yaml.safe_load(content)
    elif suffix == ".json":
        data = json.loads(content)
    else:
        # Try YAML first, then JSON
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError:
            data = json.loads(content)

    if not isinstance(data, MutableMapping):
        raise ConfigError("Configuration file content must be an object/dictionary structure")

    return dict(data)


def _extract_env_config(env: Mapping[str, str]) -> dict[str, Any]:
    data: dict[str, Any] = {}
    spec_env = env.get(f"{ENV_PREFIX}SPEC") or env.get(OPENAPI_SPEC_ENV_VAR)
    if spec_env:
        data["openapi_spec"] = spec_env

    if server_name := env.get(f"{ENV_PREFIX}SERVER_NAME"):
        data["server_name"] = server_name
    if base_url := env.get(f"{ENV_PREFIX}BASE_URL"):
        data["base_url"] = base_url
    if timeout := env.get(f"{ENV_PREFIX}TIMEOUT"):
        data["timeout"] = float(timeout)
    if retries := env.get(f"{ENV_PREFIX}RETRIES"):
        data["retries"] = int(retries)
    if verify := env.get(f"{ENV_PREFIX}VERIFY_SSL"):
        data["verify_ssl"] = _parse_bool(verify)
    if proxies := env.get(f"{ENV_PREFIX}PROXIES"):
        data["proxies"] = _parse_proxy_value(proxies)
    if headers := env.get(f"{ENV_PREFIX}HEADERS"):
        data.setdefault("headers", []).extend(_split_key_value_list(headers))

    if auth_type := env.get(f"{ENV_PREFIX}AUTH_TYPE"):
        data["auth_type"] = auth_type
    if auth_token := env.get(f"{ENV_PREFIX}AUTH_TOKEN"):
        data["auth_token"] = auth_token
    if auth_user := env.get(f"{ENV_PREFIX}AUTH_USERNAME"):
        data["auth_username"] = auth_user
    if auth_pass := env.get(f"{ENV_PREFIX}AUTH_PASSWORD"):
        data["auth_password"] = auth_pass
    if auth_headers := env.get(f"{ENV_PREFIX}AUTH_HEADERS"):
        data.setdefault("auth_headers", []).extend(_split_key_value_list(auth_headers))
    if key_name := env.get(f"{ENV_PREFIX}AUTH_KEY_NAME"):
        data["auth_key_name"] = key_name
    if key_value := env.get(f"{ENV_PREFIX}AUTH_KEY_VALUE"):
        data["auth_key_value"] = key_value
    if key_location := env.get(f"{ENV_PREFIX}AUTH_KEY_LOCATION"):
        data["auth_key_location"] = key_location

    return data


def _extract_cli_config(args: argparse.Namespace) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for attr in (
        "openapi_spec",
        "server_name",
        "base_url",
        "timeout",
        "verify_ssl",
        "retries",
        "proxies",
        "auth_type",
        "auth_token",
        "auth_username",
        "auth_password",
        "auth_key_name",
        "auth_key_value",
        "auth_key_location",
    ):
        value = getattr(args, attr)
        if value is not None:
            data[attr] = value

    if args.headers:
        data["headers"] = list(args.headers)
    if args.auth_headers:
        data.setdefault("auth_headers", []).extend(args.auth_headers)

    return data


def _resolve_openapi_source(merged: Mapping[str, Any], env: Mapping[str, str]) -> str:
    if openapi := merged.get("openapi_spec"):
        return str(openapi)

    if env_alias := env.get(OPENAPI_SPEC_ENV_VAR):
        return env_alias

    raise ConfigError(
        "No OpenAPI specification source provided. Please specify via --openapi-spec parameter, "
        f"{ENV_PREFIX}SPEC/{OPENAPI_SPEC_ENV_VAR} environment variable, or configuration file."
    )


def _merge_headers(*sources: Mapping[str, Any]) -> dict[str, str]:
    merged: dict[str, str] = {}
    for source in sources:
        headers = source.get("headers")
        if not headers:
            continue
        for raw in headers:
            key, value = _parse_key_value(raw)
            merged[key] = value

    return merged


def _build_auth_config(data: Mapping[str, Any]) -> AuthConfig:
    scheme = str(data.get("auth_type", "none")).lower()
    config = AuthConfig(scheme=scheme)

    if scheme == "bearer":
        token = data.get("auth_token")
        if not token:
            raise ConfigError("Bearer authentication requires auth_token")
        config.token = str(token)
    elif scheme == "basic":
        username = data.get("auth_username")
        password = data.get("auth_password")
        if username is None or password is None:
            raise ConfigError("Basic authentication requires username and password")
        config.username = str(username)
        config.password = str(password)
    elif scheme == "header":
        headers = data.get("auth_headers")
        if not headers:
            raise ConfigError("Header authentication requires at least one --auth-header")
        for raw in headers:
            key, value = _parse_key_value(raw)
            if config.header_name is None:
                config.header_name = key
                config.header_value = value
            else:
                config.extra_headers[key] = value
    elif scheme == "api-key":
        key_value = data.get("auth_key_value")
        if key_value is None:
            raise ConfigError("API Key authentication requires auth_key_value")
        config.api_key_value = str(key_value)
        config.api_key_name = str(data.get("auth_key_name") or "X-API-Key")
        location = str(data.get("auth_key_location") or "header")
        if location not in {"header", "query", "cookie"}:
            raise ConfigError("API Key location must be one of header/query/cookie")
        config.api_key_location = location
    else:
        # For none and any unknown scheme we keep defaults.
        config.scheme = "none" if scheme in {"", "none"} else scheme

    # Additional explicit auth headers (for any scheme)
    for raw in data.get("auth_headers", []) or []:
        key, value = _parse_key_value(raw)
        config.extra_headers.setdefault(key, value)

    return config


def _build_client_config(data: Mapping[str, Any]) -> ClientConfig:
    client = ClientConfig()
    if "timeout" in data and data["timeout"] is not None:
        client.timeout = float(data["timeout"])
    if "verify_ssl" in data and data["verify_ssl"] is not None:
        client.verify_ssl = data["verify_ssl"]
    if "retries" in data and data["retries"] is not None:
        client.retries = int(data["retries"])
    if "proxies" in data and data["proxies"] is not None:
        client.proxies = data["proxies"]
    return client


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ConfigError(f"Cannot parse boolean value: {value}")


def _parse_proxy_value(value: str) -> str | Mapping[str, str]:
    value = value.strip()
    if value.startswith("{"):
        loaded = json.loads(value)
        if not isinstance(loaded, MutableMapping):
            raise ConfigError("PROXIES configuration must be a mapping object")
        return dict(loaded)
    return value


def _split_key_value_list(raw: str) -> list[str]:
    parts = []
    for item in raw.split(","):
        item = item.strip()
        if item:
            parts.append(item)
    return parts


def _parse_key_value(raw: str) -> tuple[str, str]:
    if "=" in raw:
        key, value = raw.split("=", 1)
    elif ":" in raw:
        key, value = raw.split(":", 1)
    else:
        raise ConfigError("Header must be in KEY=VALUE or KEY:VALUE format")
    return key.strip(), value.strip()


__all__ = [
    "AuthConfig",
    "ClientConfig",
    "ConfigError",
    "ConfigSource",
    "RuntimeConfig",
    "build_arg_parser",
    "load_runtime_config",
    "DEFAULT_SERVER_NAME",
    "OPENAPI_SPEC_ENV_VAR",
    "ENV_PREFIX",
]
