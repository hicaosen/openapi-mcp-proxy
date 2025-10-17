"""Compatibility shim for the new core spec loader."""

from .core.spec import OpenAPISpecError, OpenAPISpecLoader

__all__ = ["OpenAPISpecError", "OpenAPISpecLoader"]
