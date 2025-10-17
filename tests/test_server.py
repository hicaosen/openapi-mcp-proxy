"""测试 MCP 服务器模块。"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from mcp_cnb_knowledge.server import (
    create_mcp_server,
    get_cnb_token,
    load_openapi_spec,
)
from mcp_cnb_knowledge.spec_loader import OpenAPISpecError


SAMPLE_SPEC = """openapi: 3.0.3
info:
  title: Test API
  version: 1.0.0
paths:
  /ping:
    get:
      operationId: ping
      responses:
        '200':
          description: ok
"""


def _write_spec(tmp_path: Path, name: str = "spec.yaml") -> Path:
    spec_path = tmp_path / name
    spec_path.write_text(SAMPLE_SPEC, encoding="utf-8")
    return spec_path


def test_load_openapi_spec_from_file(tmp_path: Path):
    spec_path = _write_spec(tmp_path)

    spec = load_openapi_spec(str(spec_path))

    assert spec["openapi"] == "3.0.3"
    assert spec["info"]["title"] == "Test API"
    assert "/ping" in spec["paths"]


def test_get_cnb_token_missing(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("CNB_ACCESS_TOKEN", raising=False)

    with pytest.raises(ValueError, match="CNB_ACCESS_TOKEN环境变量未设置"):
        get_cnb_token()


def test_get_cnb_token_exists(monkeypatch: pytest.MonkeyPatch):
    test_token = "test_token_12345"
    monkeypatch.setenv("CNB_ACCESS_TOKEN", test_token)

    token = get_cnb_token()
    assert token == test_token


def test_create_mcp_server_requires_source(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("MCP_OPENAPI_SPEC", raising=False)

    with pytest.raises(OpenAPISpecError, match="未提供 OpenAPI 规范来源"):
        create_mcp_server()


def test_create_mcp_server_with_source(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    spec_path = _write_spec(tmp_path)
    monkeypatch.setenv("CNB_ACCESS_TOKEN", "fake-token")

    created = {}

    class DummyMCP:
        def __init__(self, *, openapi_spec, client, name):
            self.openapi_spec = openapi_spec
            self.client = client
            self.name = name

        def run(self):
            pass

    def fake_from_openapi(*, openapi_spec, client, name):
        created["spec"] = openapi_spec
        created["client"] = client
        created["name"] = name
        return DummyMCP(openapi_spec=openapi_spec, client=client, name=name)

    class DummyAsyncClient:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    monkeypatch.setattr(
        "mcp_cnb_knowledge.server.FastMCP.from_openapi",
        staticmethod(fake_from_openapi),
    )
    monkeypatch.setattr("mcp_cnb_knowledge.server.httpx.AsyncClient", DummyAsyncClient)

    mcp = create_mcp_server(openapi_source=str(spec_path))

    assert isinstance(mcp, DummyMCP)
    assert created["spec"]["info"]["title"] == "Test API"
    assert created["name"] == "CNB Knowledge Base"
    assert created["client"].kwargs["base_url"] == "https://api.cnb.cool"
