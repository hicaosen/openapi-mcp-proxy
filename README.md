# OpenAPI → MCP Proxy

This project turns any OpenAPI specification into a fully fledged MCP server. It
builds on [FastMCP](https://github.com/jlowin/fastmcp) while providing
configuration primitives, authentication helpers, and runtime factories that are
decoupled from any specific upstream platform.

## Features

- **Modular core**: clearly separated modules for configuration, spec loading,
  authentication, HTTP client creation, and server orchestration.
- **Configurable runtime**: merge command-line flags, environment variables, and
  optional config files into a single `RuntimeConfig` object.
- **Extensible authentication**: built-in support for bearer tokens, API keys,
  custom headers, and basic auth, with room for future plugins.
- **Extensible defaults**: bring your own base URLs, headers, and auth schemes
  without touching the core runtime.
- **Async HTTP client**: `httpx.AsyncClient` factory with configurable
  timeouts, retries, and default headers derived from the OpenAPI spec.

## Quick start

1. Provide an OpenAPI schema (local file or URL).
2. Install dependencies (`pip install .` or `poetry install`).
3. Launch the proxy:

   ```bash
   openapi-mcp-proxy --openapi-spec ./petstore.yaml --server-name "Petstore"
   ```

   The command reads configuration from CLI flags, environment variables, and
   optional config files. Remaining arguments are preserved and can be consumed
   by MCP clients if needed.

You can also embed the server inside a Python project:

```python
from openapi_mcp_proxy import RuntimeConfig, create_proxy

config = RuntimeConfig(openapi_source="./petstore.yaml")
proxy = create_proxy(config)
proxy.run()
```

### Claude Desktop 示例配置

在 `claude_desktop_config.json` 中注册 MCP 服务器：

```json
{
  "mcpServers": {
    "openapi-mcp-proxy": {
      "command": "uvx",
      "args": [
        "--prerelease=allow",
        "--from",
        "git+https://cnb.cool/hicaosen/openapi-mcp-proxy",
        "openapi-mcp-proxy",
        "--openapi-spec",
        "https://example.com/openapi.yaml",
        "--server-name",
        "My OpenAPI Proxy",
        "--base-url",
        "https://api.example.com"
      ],
      "env": {
        "MCP_PROXY_TIMEOUT": "30",
        "MCP_PROXY_VERIFY_SSL": "true"
      }
    }
  }
}
```

如需认证，可再补充诸如 `MCP_PROXY_AUTH_TYPE`、`MCP_PROXY_AUTH_TOKEN` 等环境变量。

## Runtime configuration

### CLI options

| Flag | Description |
| ---- | ----------- |
| `--openapi-spec` | Path or URL to the OpenAPI document (required unless supplied via env/config). |
| `--config` | Path to a YAML/JSON config file used as a base. |
| `--server-name` | Name for the MCP server (defaults to `OpenAPI MCP Proxy`). |
| `--base-url` | Override the base URL derived from the spec `servers` array. |
| `--timeout` | HTTP timeout in seconds (default `30`). |
| `--verify-ssl`/`--no-verify-ssl` | Toggle TLS certificate verification. |
| `--retries` | Number of automatic retries for the HTTP client. |
| `--proxy` | Proxy configuration passed to `httpx` (URL or JSON mapping). |
| `--header` | Extra default header (`KEY=VALUE`). Repeat for multiple entries. |
| `--auth-type` | Authentication scheme: `none`, `bearer`, `basic`, `header`, `api-key`. |
| `--auth-token` | Token for bearer auth. |
| `--auth-username` / `--auth-password` | Credentials for basic auth. |
| `--auth-header` | Custom auth header (`KEY=VALUE`). Repeatable. |
| `--auth-key-name` / `--auth-key-value` | API key name and secret. |
| `--auth-key-location` | Where to inject the API key (`header`, `query`, `cookie`). |

### Environment variables

All environment variables share the `MCP_PROXY_` prefix. The most important
ones are:

- `MCP_PROXY_SPEC` (alias: `MCP_OPENAPI_SPEC`): OpenAPI location.
- `MCP_PROXY_SERVER_NAME`: override server name.
- `MCP_PROXY_BASE_URL`: override base URL.
- `MCP_PROXY_TIMEOUT`, `MCP_PROXY_RETRIES`, `MCP_PROXY_VERIFY_SSL`.
- `MCP_PROXY_HEADERS`: comma-separated list of `KEY=VALUE` pairs.
- `MCP_PROXY_AUTH_TYPE`, `MCP_PROXY_AUTH_TOKEN`, `MCP_PROXY_AUTH_USERNAME`,
  `MCP_PROXY_AUTH_PASSWORD`, `MCP_PROXY_AUTH_HEADERS`, `MCP_PROXY_AUTH_KEY_NAME`,
  `MCP_PROXY_AUTH_KEY_VALUE`, `MCP_PROXY_AUTH_KEY_LOCATION`.

Environment values are merged with any config file provided and finally with CLI
flags (which take precedence).

### Config file example

```yaml
openapi_spec: ./petstore.yaml
server_name: Petstore Proxy
base_url: https://petstore.swagger.io/v2
timeout: 45
headers:
  - X-Debug=true
auth_type: api-key
auth_key_name: X-API-Key
auth_key_value: ${PETSTORE_API_KEY}
```

Pass the file with `--config config.yaml`. Environment variables and CLI flags
still override individual fields.

## Authentication strategies

Authentication is described by `AuthConfig`. The HTTP client factory converts it
into headers, cookies, query parameters, or `httpx` auth handlers.

- **Bearer**: `Authorization: Bearer <token>`.
- **Basic**: `httpx.BasicAuth(username, password)`.
- **Header**: arbitrary header pairs via `--auth-header` / `MCP_PROXY_AUTH_HEADERS`.
- **API Key**: inject into headers, query string, or cookies.
- **None**: no additional credentials.

Additional headers defined in the auth configuration are merged with global
headers so you can mix concerns when needed.

## Development

- The project targets Python 3.12+.
- Install dependencies via `poetry install` or `pip install -e .[dev]`.
- Run tests with `pytest`.
- Source code lives under `src/openapi_mcp_proxy/` and is organised into
  `core/` plus package-level convenience APIs.

Contributions are welcome—feel free to open issues or pull requests with ideas
for additional authentication schemes or client-side plugins.
