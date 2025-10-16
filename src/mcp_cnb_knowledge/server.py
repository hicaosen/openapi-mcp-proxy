"""CNB Knowledge Base MCP Server

基于FastMCP实现的CNB知识库查询服务器，支持通过RAG技术检索仓库文档内容。
"""

import os
from pathlib import Path
import httpx
import yaml
from fastmcp import FastMCP


def load_openapi_spec() -> dict:
    """加载OpenAPI规范文件"""
    # 获取项目根目录的openapi.yaml路径
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent
    openapi_path = project_root / "openapi.yaml"

    if not openapi_path.exists():
        raise FileNotFoundError(
            f"OpenAPI规范文件未找到: {openapi_path}\n"
            "请确保在项目根目录下有 openapi.yaml 文件"
        )

    with open(openapi_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


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


def create_mcp_server() -> FastMCP:
    """创建并配置MCP服务器"""
    # 加载OpenAPI规范
    openapi_spec = load_openapi_spec()

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
    mcp = FastMCP.from_openapi(
        openapi_spec=openapi_spec,
        client=api_client,
        name="CNB Knowledge Base",
    )

    return mcp


# 延迟创建MCP服务器实例（只在需要时创建）
_mcp_instance = None


def get_mcp_instance() -> FastMCP:
    """获取或创建MCP服务器实例（单例模式）"""
    global _mcp_instance
    if _mcp_instance is None:
        _mcp_instance = create_mcp_server()
    return _mcp_instance


# 为了兼容 project.scripts 入口点，提供一个便捷函数
def run():
    """运行MCP服务器的入口函数"""
    mcp = get_mcp_instance()
    mcp.run()


if __name__ == "__main__":
    # 直接运行时使用
    run()
