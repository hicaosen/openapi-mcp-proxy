"""测试配置解析工具。"""

from __future__ import annotations

import pytest

from mcp_cnb_knowledge.config import (
    OPENAPI_SPEC_ENV_VAR,
    parse_openapi_source,
)


def test_config_cli_overrides_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv(OPENAPI_SPEC_ENV_VAR, "env.yaml")

    source, remaining = parse_openapi_source([
        "--openapi-spec",
        "cli.yaml",
        "--other",
        "value",
    ])

    assert source == "cli.yaml"
    assert remaining == ["--other", "value"]


def test_config_env_used_when_cli_absent(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv(OPENAPI_SPEC_ENV_VAR, "env.yaml")

    source, remaining = parse_openapi_source([])

    assert source == "env.yaml"
    assert remaining == []


def test_config_missing_source_raises(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv(OPENAPI_SPEC_ENV_VAR, raising=False)

    with pytest.raises(ValueError, match="未提供 OpenAPI 规范来源"):
        parse_openapi_source([])
