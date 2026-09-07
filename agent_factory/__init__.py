"""agent_factory — an AI agent that designs and builds other AI agents.

    from agent_factory import AgentFactory, build_crew, write_project

    spec = AgentFactory().design("Research a company and write a briefing")
    write_project(spec)                       # persist as an editable project
    build_crew(spec).kickoff(inputs={...})    # or run it right now
"""

from agent_factory.architect import AgentFactory
from agent_factory.builder import build_crew
from agent_factory.codegen import write_project
from agent_factory.registry import ToolRegistry, default_registry
from agent_factory.schema import AgentSpec, CrewSpec, SpecError, TaskSpec

__all__ = [
    "AgentFactory",
    "AgentSpec",
    "CrewSpec",
    "SpecError",
    "TaskSpec",
    "ToolRegistry",
    "build_crew",
    "default_registry",
    "write_project",
]
