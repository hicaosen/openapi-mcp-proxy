"""OpenAPI specification loading with caching and normalization."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict
from urllib.parse import ParseResult, urlparse
from urllib.request import url2pathname

import httpx
import yaml


class OpenAPISpecError(RuntimeError):
    """Raised when an OpenAPI document cannot be retrieved or parsed."""


@dataclass(slots=True)
class _CacheEntry:
    spec: dict
    mtime: float | None = None
    etag: str | None = None
    last_modified: str | None = None


class OpenAPISpecLoader:
    """Load OpenAPI specifications from local paths or remote URLs."""

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout
        self._cache: Dict[str, _CacheEntry] = {}

    def load(self, source: str) -> dict:
        key = self._normalize_key(source)

        parsed = urlparse(source)
        scheme = parsed.scheme.lower()

        if scheme in {"http", "https"}:
            return self._load_http(source, key)

        if scheme == "file":
            path = self._path_from_file_url(parsed)
            return self._load_path(path, key)

        if not scheme:
            path = Path(source)
            return self._load_path(path, key)

        raise OpenAPISpecError(f"Unsupported OpenAPI specification source: {source}")

    # Internal helpers -------------------------------------------------

    def _normalize_key(self, source: str) -> str:
        parsed = urlparse(source)
        scheme = parsed.scheme.lower()
        if scheme in {"http", "https"}:
            return source
        if scheme == "file":
            path = self._path_from_file_url(parsed)
            return path.resolve().as_uri()
        if not scheme:
            return Path(source).resolve().as_uri()
        return source

    def _load_http(self, source: str, key: str) -> dict:
        if key in self._cache:
            return self._cache[key].spec

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(source)
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise OpenAPISpecError(
                f"OpenAPI specification download timeout ({self.timeout}s): {source}"
            ) from exc
        except httpx.HTTPError as exc:
            raise OpenAPISpecError(
                f"Failed to download OpenAPI specification: {source}\nHTTP Error: {exc}"
            ) from exc

        spec = self._parse_spec(response.text, Path(source).suffix.lower())
        self._cache[key] = _CacheEntry(
            spec=spec,
            mtime=None,
            etag=response.headers.get("ETag"),
            last_modified=response.headers.get("Last-Modified"),
        )
        return spec

    def _load_path(self, path: Path, key: str) -> dict:
        try:
            stat = path.stat()
        except FileNotFoundError as exc:
            raise OpenAPISpecError(f"OpenAPI specification file does not exist: {path}") from exc
        except OSError as exc:
            raise OpenAPISpecError(
                f"Cannot access OpenAPI specification file: {path}\n{exc}"
            ) from exc

        mtime = stat.st_mtime
        cached = self._cache.get(key)
        if cached and cached.mtime == mtime:
            return cached.spec

        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise OpenAPISpecError(
                f"Failed to read OpenAPI specification file: {path}\n{exc}"
            ) from exc

        spec = self._parse_spec(content, path.suffix.lower())
        self._cache[key] = _CacheEntry(spec=spec, mtime=mtime)
        return spec

    def _parse_spec(self, content: str, format_hint: str) -> dict:
        if format_hint == ".json":
            return self._parse_json(content)
        if format_hint in {".yaml", ".yml"}:
            return self._parse_yaml(content)

        try:
            return self._parse_yaml(content)
        except OpenAPISpecError:
            return self._parse_json(content)

    def _parse_yaml(self, content: str) -> dict:
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as exc:
            raise OpenAPISpecError("OpenAPI specification is not valid YAML format") from exc
        return self._validate_dict(data, "YAML")

    def _parse_json(self, content: str) -> dict:
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise OpenAPISpecError("OpenAPI specification is not valid JSON format") from exc
        return self._validate_dict(data, "JSON")

    @staticmethod
    def _validate_dict(data: object, source: str) -> dict:
        if not isinstance(data, dict):
            raise OpenAPISpecError(
                f"Parsed OpenAPI specification from {source} must be an object type"
            )
        return data

    @staticmethod
    def _path_from_file_url(parsed: ParseResult) -> Path:
        if parsed.netloc and parsed.netloc not in {"", "localhost"}:
            raise OpenAPISpecError(
                f"File URLs with hostnames are not yet supported: {parsed.geturl()}"
            )

        path = url2pathname(parsed.path)
        if not path:
            raise OpenAPISpecError("file:// URL does not provide path information")
        return Path(path)


__all__ = ["OpenAPISpecError", "OpenAPISpecLoader"]
