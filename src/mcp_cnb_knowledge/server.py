"""CNB Knowledge Base MCP Server.

基于 FastMCP 实现的 CNB 知识库查询服务器，支持通过 RAG 技术检索仓库文档内容。
"""

from __future__ import annotations

import os
import sys
from typing import Optional

import httpx
from fastmcp import FastMCP

from .config import OPENAPI_SPEC_ENV_VAR, parse_openapi_source
from .spec_loader import OpenAPISpecError, OpenAPISpecLoader


_spec_loader = OpenAPISpecLoader()
_OPENAPI_SOURCE: Optional[str] = None


def load_openapi_spec(source: str) -> dict:
    """根据来源加载 OpenAPI 规范。"""

    return _spec_loader.load(source)


def get_cnb_token() -> str:
    """从环境变量获取CNB访问令牌"""
    token = os.getenv("CNB_ACCESS_TOKEN")
    if not token:
        raise ValueError(
            "CNB_ACCESS_TOKEN环境变量未设置\n"
            "请设置环境变量: export CNB_ACCESS_TOKEN='your_token_here'\n"
            "或在Claude Desktop配置中添加该环境变量\n"
            "获取token: https://cnb.cool/-/user/tokens (需要 repo-code:r 权限)"
        )
    return token


def create_mcp_server(openapi_source: str | None = None) -> FastMCP:
    """创建并配置MCP服务器"""
    # 确定 OpenAPI 规范来源
    source = openapi_source or os.getenv(OPENAPI_SPEC_ENV_VAR)
    if not source:
        raise OpenAPISpecError(
            "未提供 OpenAPI 规范来源，请通过 --openapi-spec 参数或设置 "
            f"{OPENAPI_SPEC_ENV_VAR} 环境变量。"
        )

    # 加载 OpenAPI 规范
    openapi_spec = load_openapi_spec(source)

    # 获取CNB访问令牌
    token = get_cnb_token()

    # 创建带认证的HTTP客户端
    api_client = httpx.AsyncClient(
        base_url="https://api.cnb.cool",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        timeout=30.0,
    )

    # 从OpenAPI规范创建MCP服务器
    return FastMCP.from_openapi(
        openapi_spec=openapi_spec,
        client=api_client,
        name="CNB Knowledge Base",
    )


# 延迟创建MCP服务器实例（只在需要时创建）
_mcp_instance: Optional[FastMCP] = None


def get_mcp_instance(openapi_source: str | None = None) -> FastMCP:
    """获取或创建MCP服务器实例（单例模式）"""
    global _mcp_instance, _OPENAPI_SOURCE

    if openapi_source is not None:
        if _OPENAPI_SOURCE is None:
            _OPENAPI_SOURCE = openapi_source
        elif openapi_source != _OPENAPI_SOURCE:
            raise RuntimeError(
                "MCP服务器实例已创建，且 OpenAPI 规范来源不同。如需切换，"
                "请重启进程。"
            )

    create_source = _OPENAPI_SOURCE if _OPENAPI_SOURCE is not None else openapi_source
    if create_source is None:
        create_source = os.getenv(OPENAPI_SPEC_ENV_VAR)

    if _mcp_instance is None:
        _mcp_instance = create_mcp_server(openapi_source=create_source)
        if _OPENAPI_SOURCE is None:
            _OPENAPI_SOURCE = create_source
    return _mcp_instance


# 为了兼容 project.scripts 入口点，提供一个便捷函数
def run(argv: list[str] | None = None):
    """运行MCP服务器的入口函数"""
    if argv is None:
        argv = sys.argv[1:]

    try:
        source, remaining = parse_openapi_source(argv, os.environ)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc

    # 将未消费的参数写回 sys.argv，避免影响后续逻辑
    sys.argv = [sys.argv[0], *remaining]

    try:
        mcp = get_mcp_instance(openapi_source=source)
    except OpenAPISpecError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc

    mcp.run()


if __name__ == "__main__":
    # 直接运行时使用
    run()
