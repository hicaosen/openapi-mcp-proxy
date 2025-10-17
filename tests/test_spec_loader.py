"""测试 OpenAPI 规范加载器。"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from mcp_cnb_knowledge.spec_loader import OpenAPISpecError, OpenAPISpecLoader


SAMPLE_SPEC = """openapi: 3.0.3
info:
  title: Loader Test
  version: 1.0.0
paths: {}
"""


def _write(tmp_path: Path, name: str, content: str) -> Path:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_loader_reads_yaml_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    spec_path = _write(tmp_path, "spec.yaml", SAMPLE_SPEC)
    loader = OpenAPISpecLoader()

    spec = loader.load(str(spec_path))
    assert spec["info"]["title"] == "Loader Test"

    read_calls = 0
    original_read_text = Path.read_text

    def counting_read_text(self: Path, *args, **kwargs):
        nonlocal read_calls
        read_calls += 1
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", counting_read_text)

    spec_second = loader.load(str(spec_path))
    assert spec_second["info"]["title"] == "Loader Test"
    assert read_calls == 0  # 缓存命中，不会再次读取文件


def test_loader_reads_json_file(tmp_path: Path):
    spec_json = '{"openapi": "3.0.3", "info": {"title": "JSON", "version": "1.0"}, "paths": {}}'
    spec_path = _write(tmp_path, "spec.json", spec_json)

    loader = OpenAPISpecLoader()
    spec = loader.load(str(spec_path))

    assert spec["info"]["title"] == "JSON"


def test_loader_missing_file_error(tmp_path: Path):
    loader = OpenAPISpecLoader()

    with pytest.raises(OpenAPISpecError, match="不存在"):
        loader.load(str(tmp_path / "missing.yaml"))


def test_loader_fetches_http_yaml(monkeypatch: pytest.MonkeyPatch):
    loader = OpenAPISpecLoader()

    class DummyClient:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, url: str):
            return httpx.Response(
                200,
                text=SAMPLE_SPEC,
                request=httpx.Request("GET", url),
            )

    monkeypatch.setattr("mcp_cnb_knowledge.spec_loader.httpx.Client", DummyClient)

    spec = loader.load("https://example.com/openapi.yaml")
    assert spec["info"]["title"] == "Loader Test"


def test_loader_http_error(monkeypatch: pytest.MonkeyPatch):
    loader = OpenAPISpecLoader()

    class ErrorClient:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, url: str):
            return httpx.Response(500, text="error", request=httpx.Request("GET", url))

    monkeypatch.setattr("mcp_cnb_knowledge.spec_loader.httpx.Client", ErrorClient)

    with pytest.raises(OpenAPISpecError, match="HTTP 错误"):
        loader.load("https://example.com/openapi.yaml")


def test_loader_http_timeout(monkeypatch: pytest.MonkeyPatch):
    loader = OpenAPISpecLoader()

    class TimeoutClient:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, url: str):
            raise httpx.TimeoutException("timeout")

    monkeypatch.setattr("mcp_cnb_knowledge.spec_loader.httpx.Client", TimeoutClient)

    with pytest.raises(OpenAPISpecError, match="超时"):
        loader.load("https://example.com/openapi.yaml")


def test_loader_invalid_yaml(tmp_path: Path):
    invalid = "openapi: ["  # 非法 YAML
    spec_path = _write(tmp_path, "bad.yaml", invalid)

    loader = OpenAPISpecLoader()

    with pytest.raises(OpenAPISpecError, match="YAML"):
        loader.load(str(spec_path))


def test_loader_invalid_json(tmp_path: Path):
    invalid = "{"  # 非法 JSON
    spec_path = _write(tmp_path, "bad.json", invalid)

    loader = OpenAPISpecLoader()

    with pytest.raises(OpenAPISpecError, match="JSON"):
        loader.load(str(spec_path))


def test_loader_unknown_scheme():
    loader = OpenAPISpecLoader()

    with pytest.raises(OpenAPISpecError, match="不支持"):
        loader.load("ftp://example.com/openapi.yaml")
