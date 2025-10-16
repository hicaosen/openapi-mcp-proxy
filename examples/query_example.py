"""
CNB知识库查询示例

演示如何在Python代码中直接使用MCP服务器进行知识库查询。
注意：这个示例展示了底层API调用，实际使用时推荐通过Claude Desktop等MCP客户端。
"""

import os
import asyncio
import httpx


async def query_knowledge_base(
    slug: str,
    query: str,
    top_k: int = 5,
    token: str = None
) -> dict:
    """
    查询CNB知识库

    Args:
        slug: 仓库路径，格式为 owner/repo
        query: 搜索关键词或问题
        top_k: 最大返回结果数，默认5
        token: CNB访问令牌，如果不提供则从环境变量读取

    Returns:
        查询结果字典
    """
    if token is None:
        token = os.getenv("CNB_ACCESS_TOKEN")
        if not token:
            raise ValueError(
                "需要提供CNB访问令牌或设置 CNB_ACCESS_TOKEN 环境变量\n"
                "获取令牌: https://cnb.cool/-/user/tokens"
            )

    url = f"https://api.cnb.cool/{slug}/-/knowledge/base/query"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "query": query,
        "top_k": top_k,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()


async def main():
    """主函数：演示知识库查询"""
    # 配置查询参数
    REPO_SLUG = "hicaosen/mcp-cnb-knowledge"  # 替换为你的仓库路径
    QUERY = "FastMCP OpenAPI集成"              # 替换为你的查询内容

    print(f"🔍 正在查询仓库 {REPO_SLUG} 的知识库...")
    print(f"📝 查询内容: {QUERY}\n")

    try:
        # 执行查询
        results = await query_knowledge_base(
            slug=REPO_SLUG,
            query=QUERY,
            top_k=5
        )

        # 显示结果
        if "results" in results and results["results"]:
            print(f"✅ 找到 {len(results['results'])} 个相关文档片段:\n")

            for i, result in enumerate(results["results"], 1):
                score = result.get("score", 0)
                chunk = result.get("chunk", "")
                metadata = result.get("metadata", {})

                print(f"--- 结果 #{i} (相关度: {score:.2f}) ---")
                print(f"📄 文件: {metadata.get('path', 'N/A')}")
                print(f"📍 位置: {metadata.get('position', 'N/A')}")
                print(f"📖 内容预览:\n{chunk[:200]}...\n")
        else:
            print("⚠️ 未找到相关内容")

    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP错误: {e.response.status_code}")
        if e.response.status_code == 401:
            print("   认证失败，请检查你的访问令牌")
        elif e.response.status_code == 404:
            print("   仓库不存在或知识库未构建")
        print(f"   详情: {e.response.text}")
    except Exception as e:
        print(f"❌ 错误: {e}")


if __name__ == "__main__":
    # 使用说明
    print("=" * 60)
    print("CNB 知识库查询示例")
    print("=" * 60)
    print("\n⚙️  配置说明:")
    print("1. 设置环境变量: export CNB_ACCESS_TOKEN='your_token_here'")
    print("2. 修改 REPO_SLUG 为你的仓库路径")
    print("3. 修改 QUERY 为你要搜索的内容\n")
    print("=" * 60)
    print()

    # 检查环境变量
    if not os.getenv("CNB_ACCESS_TOKEN"):
        print("⚠️  警告: CNB_ACCESS_TOKEN 环境变量未设置")
        print("   某些示例可能无法运行\n")

    # 运行示例
    asyncio.run(main())
