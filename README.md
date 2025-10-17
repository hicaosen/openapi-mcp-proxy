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
        "mcp-cnb-knowledge",
        "--openapi-spec",
        "https://example.com/openapi.yaml"
      ],
      "env": {
        "CNB_ACCESS_TOKEN": "your_token_here"
      }
    }
  }
}
```

## 配置

### 获取 CNB 访问令牌

1. 访问 https://cnb.cool/-/user/tokens
2. 创建新的访问令牌，至少需要 `repo-code:r` 权限
3. 复制生成的令牌

### 指定 OpenAPI 规范

运行服务器时必须指定 OpenAPI 规范的来源（支持本地路径、`file://`、`http(s)://`）：

- **命令行参数**：启动时传入 `--openapi-spec <路径或URL>`。
- **环境变量**：设置 `MCP_OPENAPI_SPEC=<路径或URL>`，当命令行未提供时生效。

示例：

```bash
poetry run mcp-cnb-knowledge --openapi-spec ./openapi.yaml
# 或
export MCP_OPENAPI_SPEC="https://api.example.com/openapi.json"
poetry run mcp-cnb-knowledge
```

## API 工具

### queryKnowledgeBase

在指定仓库的知识库中搜索相关文档片段。

**参数：**

- `slug` (string, 必需): 仓库路径，格式为 `owner/repo`
- `query` (string, 必需): 搜索关键词或问题
- `top_k` (integer, 可选): 最大返回结果数，默认 5，范围 1-20

**返回示例：**

```json
[
  {
    "score": 0.95,
    "chunk": "文档内容片段...",
    "metadata": {
      "hash": "abc123",
      "name": "README.md",
      "path": "docs/README.md"
    }
  }
]
```

## 开发

### 项目结构

```
mcp-cnb-knowledge/
├── src/
│   └── mcp_cnb_knowledge/
│       ├── __init__.py
│       ├── config.py           # CLI 与环境变量解析
│       ├── server.py           # 主服务器实现
│       ├── spec_loader.py      # OpenAPI 规范加载与缓存
│       └── openapi.yaml        # 示例 OpenAPI 规范（仅供本地调试）
├── tests/
│   ├── __init__.py
│   └── test_server.py
├── examples/
│   └── query_example.py        # 使用示例
├── pyproject.toml              # 项目配置
├── .env.example                # 环境变量示例
└── README.md
```

## 技术栈

- [FastMCP](https://github.com/jlowin/fastmcp) - MCP 服务器框架
- [httpx](https://www.python-httpx.org/) - 异步 HTTP 客户端与规范下载
- [PyYAML](https://pyyaml.org/) - YAML 解析器

## 常见问题

### 1. 认证失败（401 错误）

检查你的 `CNB_ACCESS_TOKEN` 是否正确配置且具有 `repo-code:r` 权限。

### 2. 仓库不存在或知识库未构建（404 错误）

确认：
- 仓库路径格式正确（`owner/repo`）
- 仓库已启用知识库功能
- 你有权限访问该仓库


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
