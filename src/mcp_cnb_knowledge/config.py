"""配置解析工具。

负责解析命令行参数与环境变量，确定 OpenAPI 规范的来源。
"""

from __future__ import annotations

import argparse
import os
from typing import Mapping, Sequence


OPENAPI_SPEC_ENV_VAR = "MCP_OPENAPI_SPEC"


def build_arg_parser() -> argparse.ArgumentParser:
    """创建命令行解析器，仅处理 OpenAPI 相关参数。"""

    parser = argparse.ArgumentParser(
        description=(
            "CNB Knowledge Base MCP Server — 指定 OpenAPI 规范来源"
        )
    )
    parser.add_argument(
        "--openapi-spec",
        dest="openapi_spec",
        metavar="URI_OR_PATH",
        help=(
            "OpenAPI 规范的路径或 URL，支持本地文件路径、file://、http(s)://"
        ),
    )
    return parser


def parse_openapi_source(
    argv: Sequence[str] | None,
    env: Mapping[str, str] | None = None,
) -> tuple[str, Sequence[str]]:
    """解析命令行和环境变量，返回 OpenAPI 规范来源及剩余参数。

    Args:
        argv: 需要解析的命令行参数（不含程序名），传入 None 时默认解析
              当前进程的命令行参数。
        env: 环境变量字典，默认使用 ``os.environ``。

    Returns:
        Tuple[str, Sequence[str]]: 解析出的规范来源，以及未被解析器消费
        的剩余参数（用于向后传递给其他组件）。

    Raises:
        ValueError: 当命令行与环境变量都未提供规范来源时抛出。
    """

    parser = build_arg_parser()
    args, remaining = parser.parse_known_args(argv)

    if args.openapi_spec:
        return args.openapi_spec, remaining

    env = os.environ if env is None else env
    env_value = env.get(OPENAPI_SPEC_ENV_VAR)
    if env_value:
        return env_value, remaining

    raise ValueError(
        "未提供 OpenAPI 规范来源，请通过 --openapi-spec 参数或设置"
        f" {OPENAPI_SPEC_ENV_VAR} 环境变量。"
    )


__all__ = [
    "OPENAPI_SPEC_ENV_VAR",
    "build_arg_parser",
    "parse_openapi_source",
]
