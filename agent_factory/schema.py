"""Blueprint schema: the contract between the meta-agent and the crew builder.

The architect crew emits a `CrewSpec` (validated by pydantic via
`Task(output_pydantic=CrewSpec)`), and `builder.build_crew` turns that spec into
live `crewai` objects. Keeping the schema in one place means a hallucinated
agent reference or a dangling tool name is caught before anything is executed.

Field-level validation is deliberately *forgiving* (names are normalised rather
than rejected) so that a near-miss from the LLM does not blow up output parsing.
The strict cross-reference checks live in `CrewSpec.check_semantics`, which the
architect's guardrail runs so the model gets a readable retry message.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

__all__ = ["AgentSpec", "TaskSpec", "CrewSpec", "SpecError"]

PROCESS = Literal["sequential", "hierarchical"]


class SpecError(ValueError):
    """Raised when a blueprint is structurally valid but semantically broken."""


def slugify(value: str) -> str:
    """Normalise a free-text name into a stable snake_case identifier."""
    slug = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    return slug or "unnamed"


class AgentSpec(BaseModel):
    """One worker agent in a generated crew."""

    name: str = Field(description="snake_case identifier, unique within the crew")
    role: str = Field(description="Short job title, e.g. 'Senior Market Analyst'")
    goal: str = Field(description="What this agent is trying to achieve, one sentence")
    backstory: str = Field(description="Persona and expertise that primes the agent")
    tools: list[str] = Field(
        default_factory=list,
        description="Tool names drawn from the provided catalog. Never invent one.",
    )
    allow_delegation: bool = False
    planning: bool = Field(
        default=False,
        description="Let the agent draft a plan before acting. Improves multi-step "
        "work at the cost of an extra LLM call per task.",
    )
    max_iter: int = Field(default=20, ge=1, le=50)

    @field_validator("name", mode="before")
    @classmethod
    def _normalise_name(cls, v: str) -> str:
        return slugify(str(v))

    @field_validator("tools", mode="before")
    @classmethod
    def _dedupe_tools(cls, v: object) -> list[str]:
        if v in (None, ""):
            return []
        if isinstance(v, str):
            v = [v]
        seen: dict[str, None] = {}
        for name in v:  # type: ignore[union-attr]
            seen.setdefault(str(name).strip(), None)
        return [t for t in seen if t]


class TaskSpec(BaseModel):
    """One unit of work, assigned to exactly one agent."""

    name: str = Field(description="snake_case identifier, unique within the crew")
    description: str = Field(
        description="The instruction given to the agent. May contain {placeholders} "
        "that are filled from the kickoff inputs."
    )
    expected_output: str = Field(
        description="Concrete description of a good result — shape, length, format"
    )
    agent: str = Field(description="`name` of the AgentSpec that owns this task")
    context: list[str] = Field(
        default_factory=list,
        description="Names of earlier tasks whose output feeds this one",
    )
    output_file: str | None = Field(
        default=None, description="Optional relative path to persist the result"
    )
    markdown: bool = False

    @field_validator("name", "agent", mode="before")
    @classmethod
    def _normalise_name(cls, v: str) -> str:
        return slugify(str(v))

    @field_validator("context", mode="before")
    @classmethod
    def _normalise_context(cls, v: object) -> list[str]:
        if v in (None, ""):
            return []
        if isinstance(v, str):
            v = [v]
        return [slugify(str(x)) for x in v]  # type: ignore[union-attr]


class CrewSpec(BaseModel):
    """A complete, executable crew blueprint."""

    name: str = Field(description="snake_case identifier for the crew")
    description: str = Field(description="One paragraph on what this crew does")
    process: PROCESS = "sequential"
    manager_role: str | None = Field(
        default=None,
        description="Hierarchical process only: role for the auto-created manager. "
        "Leave null to let the framework manage with the default manager.",
    )
    agents: list[AgentSpec] = Field(min_length=1)
    tasks: list[TaskSpec] = Field(min_length=1)

    @field_validator("name", mode="before")
    @classmethod
    def _normalise_name(cls, v: str) -> str:
        return slugify(str(v))

    # -- semantic checks -------------------------------------------------

    def check_semantics(self, allowed_tools: set[str] | None = None) -> list[str]:
        """Return a list of human-readable problems. Empty list means valid."""
        problems: list[str] = []

        agent_names = [a.name for a in self.agents]
        task_names = [t.name for t in self.tasks]

        for label, names in (("agent", agent_names), ("task", task_names)):
            dupes = {n for n in names if names.count(n) > 1}
            for d in sorted(dupes):
                problems.append(f"Duplicate {label} name {d!r}; names must be unique.")

        agent_set = set(agent_names)
        for task in self.tasks:
            if task.agent not in agent_set:
                problems.append(
                    f"Task {task.name!r} is assigned to unknown agent {task.agent!r}. "
                    f"Known agents: {sorted(agent_set)}."
                )

        # Context may only reference tasks defined earlier, which keeps the
        # dependency graph acyclic and executable in list order.
        seen: set[str] = set()
        for task in self.tasks:
            for ref in task.context:
                if ref == task.name:
                    problems.append(f"Task {task.name!r} lists itself as context.")
                elif ref not in seen:
                    problems.append(
                        f"Task {task.name!r} depends on {ref!r}, which is not defined "
                        "before it. Reorder the tasks or fix the reference."
                    )
            seen.add(task.name)

        idle = agent_set - {t.agent for t in self.tasks}
        for name in sorted(idle):
            problems.append(f"Agent {name!r} has no task assigned; remove it or use it.")

        if allowed_tools is not None:
            for agent in self.agents:
                for tool in agent.tools:
                    if tool not in allowed_tools:
                        problems.append(
                            f"Agent {agent.name!r} requests unavailable tool {tool!r}. "
                            f"Available tools: {sorted(allowed_tools) or ['(none)']}."
                        )

        if self.process == "hierarchical":
            delegators = [a.name for a in self.agents if a.allow_delegation]
            if delegators:
                problems.append(
                    "In a hierarchical crew the manager handles delegation; set "
                    f"allow_delegation=false on {delegators}."
                )
        elif self.manager_role:
            problems.append("manager_role is only valid when process='hierarchical'.")

        return problems

    def raise_for_problems(self, allowed_tools: set[str] | None = None) -> None:
        problems = self.check_semantics(allowed_tools)
        if problems:
            raise SpecError(
                "Invalid crew blueprint:\n"
                + "\n".join(f"  - {p}" for p in problems)
            )

    # -- helpers ---------------------------------------------------------

    def agent_by_name(self, name: str) -> AgentSpec:
        for agent in self.agents:
            if agent.name == name:
                return agent
        raise SpecError(f"No agent named {name!r} in blueprint {self.name!r}.")

    def placeholders(self) -> set[str]:
        """Every `{placeholder}` the tasks expect at kickoff time."""
        found: set[str] = set()
        for task in self.tasks:
            for text in (task.description, task.expected_output):
                found.update(re.findall(r"\{(\w+)\}", text))
        return found
