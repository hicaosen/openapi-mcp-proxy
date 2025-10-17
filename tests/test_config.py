"""Tests for the unified runtime configuration loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from openapi_mcp_proxy.core.config import (
    ENV_PREFIX,
    OPENAPI_SPEC_ENV_VAR,
    AuthConfig,
    ConfigError,
    load_runtime_config,
)


def test_cli_overrides_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv(f"{ENV_PREFIX}SPEC", "env.yaml")

    runtime, remaining = load_runtime_config([
        "--openapi-spec",
        "cli.yaml",
        "--timeout",
        "5",
    ])

    assert runtime.openapi_source == "cli.yaml"
    assert runtime.client.timeout == 5
    assert remaining == []


def test_env_fallback(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv(f"{ENV_PREFIX}SPEC", raising=False)
    monkeypatch.setenv(OPENAPI_SPEC_ENV_VAR, "env.yaml")

    runtime, remaining = load_runtime_config([])

    assert runtime.openapi_source == "env.yaml"
    assert remaining == []


def test_config_file_and_auth(tmp_path: Path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
openapi_spec: file.yaml
server_name: File Server
headers:
  - X-Debug=true
auth_type: bearer
auth_token: secret-token
""",
        encoding="utf-8",
    )

    runtime, remaining = load_runtime_config([
        "--config",
        str(config_file),
        "--base-url",
        "https://example.com",
    ])

    assert runtime.openapi_source == "file.yaml"
    assert runtime.server_name == "File Server"
    assert runtime.base_url == "https://example.com"
    assert runtime.headers["X-Debug"] == "true"
    assert runtime.auth.scheme == "bearer"
    assert runtime.auth.token == "secret-token"
    assert isinstance(runtime.auth, AuthConfig)
    assert remaining == []


def test_missing_source_raises(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv(f"{ENV_PREFIX}SPEC", raising=False)
    monkeypatch.delenv(OPENAPI_SPEC_ENV_VAR, raising=False)

    with pytest.raises(ConfigError, match="No OpenAPI specification source provided"):
        load_runtime_config([])
