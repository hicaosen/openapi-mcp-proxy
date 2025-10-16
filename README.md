# CNB Knowledge Base MCP Server

基于 FastMCP 实现的 CNB 知识库查询服务器，支持通过 RAG（检索增强生成）技术检索 CNB 仓库文档内容。

## 特性

- 🚀 基于 [FastMCP](https://github.com/jlowin/fastmcp) 框架快速构建
- 🔍 支持通过 RAG 技术智能检索仓库文档
- 🔌 兼容所有 MCP 客户端（Claude Desktop、Cline 等）
- 📚 自动从 OpenAPI 规范生成工具定义
- ⚡ 异步 HTTP 客户端，性能优异

## 前置要求

- Python 3.12 或更高版本
- CNB 访问令牌（需要 `repo-code:r` 权限）

## 安装

### 方法 1：通过 uvx 直接运行（推荐）

无需安装，MCP 客户端会自动处理：

```json
{
  "mcpServers": {
    "cnb-knowledge": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "--prerelease=allow",
        "--from",
        "git+https://cnb.cool/hicaosen/mcp-cnb-knowledge",
        "mcp-cnb-knowledge"
      ],
      "env": {
        "CNB_ACCESS_TOKEN": "your_token_here"
      }
    }
  }
}
```

### 方法 2：本地开发安装

```bash
# 克隆仓库
git clone https://cnb.cool/hicaosen/mcp-cnb-knowledge
cd mcp-cnb-knowledge

# 安装依赖
pip install -e .

# 或使用 poetry
poetry install
```

## 配置

### 获取 CNB 访问令牌

1. 访问 https://cnb.cool/-/user/tokens
2. 创建新的访问令牌，至少需要 `repo-code:r` 权限
3. 复制生成的令牌

### 环境变量配置

创建 `.env` 文件（可参考 `.env.example`）：

```bash
# CNB访问令牌（必需）
CNB_ACCESS_TOKEN=your_token_here
```

**安全提示：** 不要将包含真实令牌的 `.env` 或配置文件提交到版本控制系统。

### MCP 客户端配置

#### Claude Desktop

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`（macOS）或 `%APPDATA%\Claude\claude_desktop_config.json`（Windows）：

```json
{
  "mcpServers": {
    "cnb-knowledge": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "--prerelease=allow",
        "--from",
        "git+https://cnb.cool/hicaosen/mcp-cnb-knowledge",
        "mcp-cnb-knowledge"
      ],
      "env": {
        "CNB_ACCESS_TOKEN": "your_token_here"
      }
    }
  }
}
```

#### Cline（VSCode）

在 Cline 的 MCP 设置中添加相同的配置。

## 使用

配置完成后，在支持的 MCP 客户端中即可使用知识库查询功能。

### 通过 Claude Desktop

启动 Claude Desktop 后，你可以这样提问：

```
请查询 hicaosen/mcp-cnb-knowledge 仓库中关于 FastMCP 集成的文档
```

Claude 会自动调用 `queryKnowledgeBase` 工具并返回相关文档片段。

### Python API 示例

虽然推荐通过 MCP 客户端使用，但也可以直接在 Python 代码中调用：

```python
import asyncio
from mcp_cnb_knowledge.server import get_mcp_instance

async def main():
    mcp = get_mcp_instance()
    # 你的查询逻辑

asyncio.run(main())
```

更完整的示例请参考 [`examples/query_example.py`](examples/query_example.py)。

## API 工具

### queryKnowledgeBase

在指定仓库的知识库中搜索相关文档片段。

**参数：**

- `slug` (string, 必需): 仓库路径，格式为 `owner/repo`
- `query` (string, 必需): 搜索关键词或问题
- `top_k` (integer, 可选): 最大返回结果数，默认 5，范围 1-20

**返回示例：**

```json
{
  "results": [
    {
      "score": 0.95,
      "chunk": "文档内容片段...",
      "metadata": {
        "hash": "abc123",
        "name": "README.md",
        "path": "docs/README.md",
        "position": 0
      }
    }
  ]
}
```

## 开发

### 项目结构

```
mcp-cnb-knowledge/
├── src/
│   └── mcp_cnb_knowledge/
│       ├── __init__.py
│       ├── server.py           # 主服务器实现
│       └── openapi.yaml        # OpenAPI 规范
├── tests/
│   ├── __init__.py
│   └── test_server.py
├── examples/
│   └── query_example.py        # 使用示例
├── pyproject.toml              # 项目配置
├── .env.example                # 环境变量示例
└── README.md
```

### 运行测试

```bash
pytest
```

### 本地运行

```bash
# 方法 1：使用 Python 模块
python -m mcp_cnb_knowledge.server

# 方法 2：使用命令行入口
mcp-cnb-knowledge

# 方法 3：使用 poetry
poetry run mcp-cnb-knowledge
```

## 技术栈

- [FastMCP](https://github.com/jlowin/fastmcp) - MCP 服务器框架
- [httpx](https://www.python-httpx.org/) - 异步 HTTP 客户端
- [PyYAML](https://pyyaml.org/) - YAML 解析器

## 常见问题

### 1. 认证失败（401 错误）

检查你的 `CNB_ACCESS_TOKEN` 是否正确配置且具有 `repo-code:r` 权限。

### 2. 仓库不存在或知识库未构建（404 错误）

确认：
- 仓库路径格式正确（`owner/repo`）
- 仓库已启用知识库功能
- 你有权限访问该仓库

### 3. 导入错误

确保已正确安装依赖：

```bash
pip install -e .
# 或
poetry install
```

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

本项目采用 MIT 许可证。

## 作者

- **hicaosen** - [cscg52@qq.com](mailto:cscg52@qq.com)

## 相关链接

- [CNB 平台](https://cnb.cool)
- [FastMCP 文档](https://github.com/jlowin/fastmcp)
- [MCP 协议规范](https://modelcontextprotocol.io)
