"""Tests for authentication strategy helpers."""

from __future__ import annotations

import httpx
import pytest

from openapi_mcp_proxy.core.auth import create_auth_strategy
from openapi_mcp_proxy.core.config import AuthConfig


def test_bearer_strategy_headers():
    strategy = create_auth_strategy(AuthConfig(scheme="bearer", token="abc"))
    assert strategy.headers()["Authorization"] == "Bearer abc"
    assert strategy.auth() is None


def test_basic_strategy_returns_auth():
    strategy = create_auth_strategy(
        AuthConfig(scheme="basic", username="user", password="pass")
    )
    auth = strategy.auth()
    assert isinstance(auth, httpx.BasicAuth)


def test_api_key_locations():
    header_strategy = create_auth_strategy(
        AuthConfig(scheme="api-key", api_key_value="hv", api_key_name="X-Key")
    )
    assert header_strategy.headers()["X-Key"] == "hv"

    query_strategy = create_auth_strategy(
        AuthConfig(
            scheme="api-key",
            api_key_value="qv",
            api_key_name="key",
            api_key_location="query",
        )
    )
    assert query_strategy.query_params()["key"] == "qv"

    cookie_strategy = create_auth_strategy(
        AuthConfig(
            scheme="api-key",
            api_key_value="cv",
            api_key_name="cookie",
            api_key_location="cookie",
        )
    )
    assert cookie_strategy.cookies()["cookie"] == "cv"


def test_unknown_scheme_raises():
    with pytest.raises(ValueError):
        create_auth_strategy(AuthConfig(scheme="unknown"))
