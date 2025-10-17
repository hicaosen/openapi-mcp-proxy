# Repository Guidelines

## Project Structure & Module Organization
- `src/openapi_mcp_proxy/` contains the runtime package. The `core/` folder hosts the proxy registry, spec translation, and authentication helpers, while `config.py` merges CLI input, environment variables, and config files into a single `RuntimeConfig`.
- `tests/` mirrors the package layout with `test_*.py` modules; add new suites beside the code they exercise. Keep example OpenAPI fixtures under `tests/fixtures/` if additional schemas are needed.

## Build, Test, and Development Commands
- `poetry install` – create an isolated environment with application and `pytest` dev dependencies.
- `pip install -e .[dev]` – alternative editable install when Poetry is unavailable.
- `poetry run openapi-mcp-proxy --openapi-spec ./petstore.yaml --server-name Demo` – quick sanity check that the CLI assembles a proxy.
- `pytest` or `pytest -k <pattern>` – execute the asynchronous and configuration-driven tests in `tests/`.

## Coding Style & Naming Conventions
- Target Python 3.12+, four-space indentation, and PEP 8 naming (`snake_case` for functions/modules, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants).
- Preserve existing type hints and return annotations; prefer `pathlib.Path` for filesystem references and explicit `RuntimeConfig` usage when passing configuration.
- Document non-obvious behavior with short doctrings or inline comments, but keep logging or `print` usage restricted to user-facing CLI messaging.

## Testing Guidelines
- Write `pytest` tests alongside new features, naming files `test_<unit>.py` and using fixtures for config variants. Mock external HTTP calls with `httpx.MockTransport` or equivalent to avoid live network traffic.
- Ensure new CLI behaviors or configuration branches maintain at least one assertion in the test suite; run `pytest --maxfail=1` locally before raising a PR.

## Commit & Pull Request Guidelines
- Craft commits in the imperative mood (“Add configurable retries”), limited to roughly 50 characters, and group related changes into cohesive commits. Reference issue IDs when relevant.
- Pull requests should summarize the motivation, outline testing performed, and link any OpenAPI fixtures or config files touched. Include reproduction steps or CLI examples when the change affects runtime behavior.

## Configuration & Security Notes
- Store secrets via environment variables using the `MCP_PROXY_` prefix; avoid hard-coding tokens in examples. When sharing sample specs, redact private endpoints and credentials while preserving structure so reviewers can validate the runtime.
