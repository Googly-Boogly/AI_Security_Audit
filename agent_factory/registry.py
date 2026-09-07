"""Whitelist of tools a generated crew is allowed to use.

The meta-agent picks tools by name from this catalog. Anything it invents is
rejected by the blueprint guardrail, so a generated crew can never be wired to a
tool that does not exist — or to one you did not sanction.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

__all__ = ["ToolRegistry", "default_registry"]

ToolFactory = Callable[[], BaseTool]


def _neutralise_braces(text: str) -> str:
    """Make text safe to embed in a CrewAI task description."""
    return text.replace("{", "<").replace("}", ">")


class ToolRegistry:
    """Name -> factory map, plus a prompt-ready catalog of what is available."""

    def __init__(self) -> None:
        self._factories: dict[str, ToolFactory] = {}
        self._descriptions: dict[str, str] = {}

    def register(
        self, name: str, factory: ToolFactory, description: str
    ) -> "ToolRegistry":
        """Register a tool by name. `factory` is called once per built agent."""
        if name in self._factories:
            raise ValueError(f"Tool {name!r} is already registered.")
        self._factories[name] = factory
        self._descriptions[name] = description.strip()
        return self

    def register_tool(self, tool: BaseTool) -> "ToolRegistry":
        """Register an already-instantiated tool, reusing its own metadata."""
        return self.register(tool.name, lambda: tool, tool.description)

    @property
    def names(self) -> set[str]:
        return set(self._factories)

    def build(self, names: list[str]) -> list[BaseTool]:
        missing = [n for n in names if n not in self._factories]
        if missing:
            raise KeyError(
                f"Unknown tool(s) {missing}. Registered: {sorted(self._factories)}"
            )
        return [self._factories[n]() for n in names]

    def catalog(self) -> str:
        """Rendered for the architect's prompt.

        Braces are rewritten to angle brackets on the way out. The catalog is
        embedded in a task description, and CrewAI interpolates those at kickoff
        — a tool whose description mentions `{path}` would otherwise raise a
        missing-variable error before the crew ever starts.
        """
        if not self._factories:
            return "(no tools available — design agents that reason without tools)"
        return "\n".join(
            f"- {name}: {_neutralise_braces(self._descriptions[name])}"
            for name in sorted(self._factories)
        )


# --------------------------------------------------------------------------
# Built-in tools: workspace-scoped file access, no third-party dependencies.
# --------------------------------------------------------------------------

WORKSPACE = Path(os.environ.get("AGENT_FACTORY_WORKSPACE", "workspace")).resolve()


def _resolve_inside_workspace(relative_path: str) -> Path:
    """Resolve a path, refusing anything that escapes the workspace root."""
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    target = (WORKSPACE / relative_path).resolve()
    if target != WORKSPACE and WORKSPACE not in target.parents:
        raise ValueError(
            f"Path {relative_path!r} escapes the workspace at {WORKSPACE}."
        )
    return target


class _PathInput(BaseModel):
    path: str = Field(description="Path relative to the workspace root")


class _WriteInput(BaseModel):
    path: str = Field(description="Path relative to the workspace root")
    content: str = Field(description="Full text content to write")


class ReadFileTool(BaseTool):
    name: str = "read_file"
    description: str = (
        "Read a UTF-8 text file from the shared workspace. Input: path (relative)."
    )
    args_schema: type[BaseModel] = _PathInput

    def _run(self, path: str) -> str:
        target = _resolve_inside_workspace(path)
        if not target.is_file():
            return f"No file at {path!r}."
        return target.read_text(encoding="utf-8")


class WriteFileTool(BaseTool):
    name: str = "write_file"
    description: str = (
        "Write UTF-8 text to a file in the shared workspace, creating parent "
        "directories and overwriting any existing file. Input: path, content."
    )
    args_schema: type[BaseModel] = _WriteInput

    def _run(self, path: str, content: str) -> str:
        target = _resolve_inside_workspace(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Wrote {len(content)} characters to {path}."


class ListWorkspaceTool(BaseTool):
    name: str = "list_workspace"
    description: str = (
        "List every file currently in the shared workspace. Input: path (relative, "
        "use '.' for the root)."
    )
    args_schema: type[BaseModel] = _PathInput

    def _run(self, path: str = ".") -> str:
        target = _resolve_inside_workspace(path)
        if not target.is_dir():
            return f"No directory at {path!r}."
        entries = sorted(
            str(p.relative_to(WORKSPACE)) for p in target.rglob("*") if p.is_file()
        )
        return "\n".join(entries) if entries else "(workspace is empty)"


def default_registry(include_crewai_tools: bool = True) -> ToolRegistry:
    """The registry used by the CLI: local file tools, plus `crewai_tools` if present."""
    registry = ToolRegistry()
    registry.register_tool(ReadFileTool())
    registry.register_tool(WriteFileTool())
    registry.register_tool(ListWorkspaceTool())

    if include_crewai_tools:
        _register_optional_crewai_tools(registry)
    return registry


# `crewai_tools` is an optional extra (`pip install crewai-tools`). Each tool is
# probed individually because most need an API key present to instantiate.
_OPTIONAL_TOOLS: tuple[tuple[str, str], ...] = (
    ("SerperDevTool", "SERPER_API_KEY"),
    ("ScrapeWebsiteTool", ""),
    ("WebsiteSearchTool", ""),
    ("FileReadTool", ""),
    ("CodeInterpreterTool", ""),
)


def _register_optional_crewai_tools(registry: ToolRegistry) -> None:
    try:
        import crewai_tools  # type: ignore[import-not-found]
    except ImportError:
        return

    for class_name, required_env in _OPTIONAL_TOOLS:
        if required_env and not os.environ.get(required_env):
            continue
        tool_cls: Any = getattr(crewai_tools, class_name, None)
        if tool_cls is None:
            continue
        try:
            instance = tool_cls()
        except Exception:  # noqa: BLE001 - a tool that cannot init is simply skipped
            continue
        if instance.name not in registry.names:
            registry.register_tool(instance)
