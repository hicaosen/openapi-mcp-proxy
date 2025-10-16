"""测试MCP服务器基本功能"""

import os
import pytest
from mcp_cnb_knowledge.server import (
    load_openapi_spec,
    get_cnb_token,
    create_mcp_server,
)


def test_load_openapi_spec():
    """测试加载OpenAPI规范"""
    spec = load_openapi_spec()

    assert spec is not None
    assert spec['openapi'] == '3.0.3'
    assert spec['info']['title'] == 'CNB Knowledge Base API'
    assert '/{slug}/-/knowledge/base/query' in spec['paths']


def test_get_cnb_token_missing():
    """测试环境变量缺失时的错误处理"""
    # 保存原有环境变量
    original_token = os.environ.get('CNB_ACCESS_TOKEN')

    # 临时删除环境变量
    if 'CNB_ACCESS_TOKEN' in os.environ:
        del os.environ['CNB_ACCESS_TOKEN']

    try:
        with pytest.raises(ValueError, match="CNB_ACCESS_TOKEN环境变量未设置"):
            get_cnb_token()
    finally:
        # 恢复环境变量
        if original_token:
            os.environ['CNB_ACCESS_TOKEN'] = original_token


def test_get_cnb_token_exists():
    """测试环境变量存在时的正常情况"""
    # 设置测试token
    test_token = "test_token_12345"
    os.environ['CNB_ACCESS_TOKEN'] = test_token

    try:
        token = get_cnb_token()
        assert token == test_token
    finally:
        # 清理
        del os.environ['CNB_ACCESS_TOKEN']


@pytest.mark.skipif(
    not os.environ.get('CNB_ACCESS_TOKEN'),
    reason="需要设置 CNB_ACCESS_TOKEN 环境变量"
)
def test_create_mcp_server():
    """测试创建MCP服务器（需要真实token）"""
    mcp = create_mcp_server()

    assert mcp is not None
    assert mcp.name == "CNB Knowledge Base"


if __name__ == "__main__":
    # 运行基本测试
    print("运行测试...")
    test_load_openapi_spec()
    print("✓ OpenAPI规范加载测试通过")

    test_get_cnb_token_missing()
    print("✓ Token缺失错误处理测试通过")

    test_get_cnb_token_exists()
    print("✓ Token存在测试通过")

    if os.environ.get('CNB_ACCESS_TOKEN'):
        test_create_mcp_server()
        print("✓ MCP服务器创建测试通过")
    else:
        print("⚠ 跳过MCP服务器创建测试（未设置 CNB_ACCESS_TOKEN）")

    print("\n所有测试通过！")
