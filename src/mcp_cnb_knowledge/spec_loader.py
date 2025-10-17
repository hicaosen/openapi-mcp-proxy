"""OpenAPI 规范加载工具。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse, ParseResult
from urllib.request import url2pathname

import httpx
import yaml


class OpenAPISpecError(Exception):
    """包装 OpenAPI 加载相关的异常。"""


@dataclass(frozen=True)
class _CacheEntry:
    mtime: Optional[float]
    spec: dict


class OpenAPISpecLoader:
    """根据给定来源加载并缓存 OpenAPI 规范。"""

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout
        self._cache: Dict[str, _CacheEntry] = {}

    def load(self, source: str) -> dict:
        """加载 OpenAPI 规范。

        Args:
            source: 规范来源，支持本地路径、file:// URL、HTTP(S) URL。

        Returns:
            dict: 解析后的 OpenAPI 规范。

        Raises:
            OpenAPISpecError: 解析或加载失败时抛出。
        """

        parsed = urlparse(source)
        scheme = parsed.scheme.lower()

        if scheme in ("http", "https"):
            return self._load_http(source, parsed)
        if scheme == "file":
            path = self._path_from_file_url(parsed)
            return self._load_path(path, source)
        if not scheme:
            return self._load_path(Path(source), str(Path(source).resolve()))

        raise OpenAPISpecError(f"不支持的 OpenAPI 规范来源: {source}")

    def _load_http(self, source: str, parsed: ParseResult) -> dict:
        cached = self._cache.get(source)
        if cached:
            return cached.spec

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(source)
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise OpenAPISpecError(
                f"下载 OpenAPI 规范超时（{self.timeout}s）: {source}"
            ) from exc
        except httpx.HTTPError as exc:
            raise OpenAPISpecError(
                f"下载 OpenAPI 规范失败: {source}\n"
                f"HTTP 错误: {exc}"
            ) from exc

        content = response.text
        format_hint = Path(parsed.path or "").suffix.lower()
        spec = self._parse_spec(content, format_hint)
        self._cache[source] = _CacheEntry(mtime=None, spec=spec)
        return spec

    def _load_path(self, path: Path, cache_key: str) -> dict:
        try:
            stat_result = path.stat()
        except FileNotFoundError as exc:
            raise OpenAPISpecError(f"OpenAPI 规范文件不存在: {path}") from exc
        except OSError as exc:
            raise OpenAPISpecError(
                f"无法访问 OpenAPI 规范文件: {path}\n{exc}"
            ) from exc

        mtime = stat_result.st_mtime
        cached = self._cache.get(cache_key)
        if cached and cached.mtime == mtime:
            return cached.spec

        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise OpenAPISpecError(
                f"读取 OpenAPI 规范文件失败: {path}\n{exc}"
            ) from exc

        format_hint = path.suffix.lower()
        spec = self._parse_spec(content, format_hint)
        resolved_key = cache_key or str(path.resolve())
        self._cache[resolved_key] = _CacheEntry(mtime=mtime, spec=spec)
        return spec

    def _parse_spec(self, content: str, format_hint: str) -> dict:
        if format_hint == ".json":
            return self._parse_as_json(content)

        if format_hint in {".yaml", ".yml"}:
            return self._parse_as_yaml(content)

        # 未提供明确扩展名时，先尝试 YAML，再回退到 JSON
        try:
            return self._parse_as_yaml(content)
        except OpenAPISpecError:
            return self._parse_as_json(content)

    def _parse_as_yaml(self, content: str) -> dict:
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as exc:
            raise OpenAPISpecError("OpenAPI 规范不是有效的 YAML 格式") from exc
        return self._validate_dict(data, "YAML")

    def _parse_as_json(self, content: str) -> dict:
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise OpenAPISpecError("OpenAPI 规范不是有效的 JSON 格式") from exc
        return self._validate_dict(data, "JSON")

    @staticmethod
    def _validate_dict(data: object, source_label: str) -> dict:
        if not isinstance(data, dict):
            raise OpenAPISpecError(
                f"解析 {source_label} 后的 OpenAPI 规范必须是对象类型"
            )
        return data

    @staticmethod
    def _path_from_file_url(parsed: ParseResult) -> Path:
        if parsed.netloc and parsed.netloc not in {"", "localhost"}:
            raise OpenAPISpecError(
                f"暂不支持带主机名的 file URL: {parsed.geturl()}"
            )

        path_str = url2pathname(parsed.path)
        if not path_str:
            raise OpenAPISpecError("file:// URL 未提供路径信息")
        return Path(path_str)


__all__ = ["OpenAPISpecError", "OpenAPISpecLoader"]

