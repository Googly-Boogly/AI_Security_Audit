"""Turn a validated `CrewSpec` into live CrewAI objects.

This is the half of the system that does not involve an LLM: given a blueprint,
it deterministically instantiates `Agent`, `Task` and `Crew`. Keeping it pure
means a blueprint can be reviewed, edited by hand, checked into git, and rebuilt
identically later.
"""

from __future__ import annotations

from crewai import Agent, Crew, PlanningConfig, Process, Task
from crewai.llms.base_llm import BaseLLM

from agent_factory.config import WORKER_MODEL, build_llm
from agent_factory.registry import ToolRegistry, default_registry
from agent_factory.schema import CrewSpec

__all__ = ["build_agents", "build_tasks", "build_crew"]


def build_agents(
    spec: CrewSpec,
    *,
    registry: ToolRegistry,
    llm: BaseLLM,
    verbose: bool = False,
) -> dict[str, Agent]:
    """Instantiate one `Agent` per `AgentSpec`, keyed by blueprint name."""
    return {
        agent_spec.name: Agent(
            role=agent_spec.role,
            goal=agent_spec.goal,
            backstory=agent_spec.backstory,
            tools=registry.build(agent_spec.tools),
            allow_delegation=agent_spec.allow_delegation,
            planning_config=PlanningConfig() if agent_spec.planning else None,
            max_iter=agent_spec.max_iter,
            llm=llm,
            verbose=verbose,
        )
        for agent_spec in spec.agents
    }


def build_tasks(spec: CrewSpec, agents: dict[str, Agent]) -> list[Task]:
    """Instantiate tasks in blueprint order, wiring `context` to earlier tasks.

    `check_semantics` has already guaranteed that every context reference points
    backwards, so the tasks a given task depends on always exist by the time we
    reach it.
    """
    built: dict[str, Task] = {}
    for task_spec in spec.tasks:
        built[task_spec.name] = Task(
            name=task_spec.name,
            description=task_spec.description,
            expected_output=task_spec.expected_output,
            agent=agents[task_spec.agent],
            context=[built[ref] for ref in task_spec.context],
            output_file=task_spec.output_file,
            markdown=task_spec.markdown,
        )
    return list(built.values())


def build_crew(
    spec: CrewSpec,
    *,
    registry: ToolRegistry | None = None,
    llm: BaseLLM | None = None,
    verbose: bool = False,
) -> Crew:
    """Validate a blueprint and assemble the runnable crew it describes."""
    registry = registry if registry is not None else default_registry()
    spec.raise_for_problems(allowed_tools=registry.names)

    llm = llm if llm is not None else build_llm(WORKER_MODEL)
    agents = build_agents(spec, registry=registry, llm=llm, verbose=verbose)
    tasks = build_tasks(spec, agents)

    kwargs: dict[str, object] = {
        "name": spec.name,
        "agents": list(agents.values()),
        "tasks": tasks,
        "verbose": verbose,
    }

    if spec.process == "hierarchical":
        kwargs["process"] = Process.hierarchical
        # A hierarchical crew needs a manager. Unless the blueprint names a
        # specific manager role, let CrewAI create the default one.
        if spec.manager_role:
            kwargs["manager_agent"] = Agent(
                role=spec.manager_role,
                goal=f"Coordinate the crew to deliver: {spec.description}",
                backstory=(
                    "An experienced delivery lead who breaks work down, assigns it "
                    "to the right specialist, and holds the final quality bar."
                ),
                allow_delegation=True,
                llm=llm,
                verbose=verbose,
            )
        else:
            kwargs["manager_llm"] = llm
    else:
        kwargs["process"] = Process.sequential

    return Crew(**kwargs)
