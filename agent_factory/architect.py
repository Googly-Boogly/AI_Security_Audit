"""The meta-agent: a crew whose product is another crew.

Two agents, two tasks:

1. **Crew Architect** drafts a team — who is needed, what each one does, and in
   what order the work flows.
2. **Blueprint Auditor** hardens that draft into a `CrewSpec`. Its task declares
   `output_pydantic=CrewSpec`, so CrewAI parses and type-validates the result,
   and a guardrail then runs the cross-reference checks. A failed guardrail
   hands the auditor its own errors and it tries again — up to
   `guardrail_max_retries` times — so malformed blueprints self-repair instead
   of reaching the builder.
"""

from __future__ import annotations

from crewai import Agent, Crew, Process, Task
from crewai.llms.base_llm import BaseLLM
from crewai.tasks.task_output import TaskOutput

from agent_factory.config import ARCHITECT_MODEL, build_llm
from agent_factory.registry import ToolRegistry, default_registry
from agent_factory.schema import CrewSpec

__all__ = ["AgentFactory", "design_rules"]


def design_rules(registry: ToolRegistry) -> str:
    """The hard constraints, injected into both tasks so neither drifts."""
    return f"""
AVAILABLE TOOLS — an agent may only use tools from this list, by exact name.
An agent with no suitable tool gets an empty tool list and reasons from context.
{registry.catalog()}

RULES THE BLUEPRINT MUST SATISFY:
1. Every agent has a task. Do not invent staff with nothing to do.
2. Every task names exactly one owning agent, by that agent's `name`.
3. `context` lists tasks that appear EARLIER in the task list. Work flows
   forward; there are no cycles and no forward references.
4. Prefer 2-4 agents. Each one needs a distinct specialism — if two agents
   would share a job description, they should be one agent.
5. `description` is the instruction the agent receives; `expected_output` is a
   concrete description of a good result (its shape, length and format).
6. Use curly-brace placeholders — written like {{placeholder_example}} — in task
   descriptions for values supplied at run time. Keep them few and obviously
   named.
7. For process='sequential' (the default, and correct for most work) the tasks
   run top to bottom. Only choose 'hierarchical' when the work genuinely needs
   a manager to route and re-assign it dynamically; then set
   allow_delegation=false on every worker.
8. The final task must produce the deliverable the user actually asked for.
""".strip()


def _make_guardrail(registry: ToolRegistry):
    """Validate the parsed blueprint, returning actionable feedback on failure."""

    # No return annotation: this module uses `from __future__ import annotations`,
    # so CrewAI's guardrail validator sees the annotation as a string and cannot
    # match it against Tuple[bool, Any]. It returns (bool, str | TaskOutput).
    def guardrail(output: TaskOutput):
        spec = output.pydantic
        if not isinstance(spec, CrewSpec):
            return False, (
                "Output was not parsed into a CrewSpec. Return a single JSON object "
                "matching the schema exactly — no prose, no markdown fences."
            )

        problems = spec.check_semantics(allowed_tools=registry.names)
        if problems:
            return False, (
                "The blueprint has these problems. Fix every one and return the "
                "corrected JSON object:\n"
                + "\n".join(f"- {p}" for p in problems)
            )

        # Returning the original TaskOutput keeps `.pydantic` intact downstream.
        return True, output

    return guardrail


class AgentFactory:
    """Generates validated crew blueprints from a plain-language brief."""

    def __init__(
        self,
        *,
        registry: ToolRegistry | None = None,
        llm: BaseLLM | None = None,
        verbose: bool = True,
    ) -> None:
        self.registry = registry if registry is not None else default_registry()
        self.llm = llm if llm is not None else build_llm(ARCHITECT_MODEL)
        self.verbose = verbose

    # -- the two agents --------------------------------------------------

    def _architect_agent(self) -> Agent:
        return Agent(
            role="Multi-Agent Systems Architect",
            goal=(
                "Given a goal in plain language, design the smallest team of AI "
                "agents that can reliably deliver it, and the order they work in."
            ),
            backstory=(
                "You have shipped dozens of production agent crews. You have learned "
                "that most failures come from too many agents with vague, overlapping "
                "roles, and from tasks whose 'expected output' is not specific enough "
                "to check. You design lean teams where every role is sharply drawn "
                "and every handoff is explicit."
            ),
            llm=self.llm,
            verbose=self.verbose,
            allow_delegation=False,
        )

    def _auditor_agent(self) -> Agent:
        return Agent(
            role="Blueprint Auditor",
            goal=(
                "Convert a crew design into a strictly valid blueprint, correcting "
                "any rule violation you find along the way."
            ),
            backstory=(
                "You are the last check before a design becomes running code. You are "
                "pedantic about references resolving, tools existing, and dependency "
                "order being correct, because you are the one who gets paged when a "
                "generated crew fails at kickoff."
            ),
            llm=self.llm,
            verbose=self.verbose,
            allow_delegation=False,
        )

    # -- the two tasks ---------------------------------------------------

    def _design_task(self, agent: Agent) -> Task:
        return Task(
            name="design_crew",
            description=(
                "Design a crew of AI agents that accomplishes this goal:\n\n"
                "<goal>\n{brief}\n</goal>\n\n"
                "Think about what expertise the goal actually demands, then define "
                "the minimum team that covers it. For each agent give a role, a "
                "goal, a backstory, and which tools it needs. For each task give the "
                "instruction, a precise description of a good result, the owning "
                "agent, and which earlier tasks it builds on.\n\n"
                + design_rules(self.registry)
            ),
            expected_output=(
                "A written design: the crew's name and purpose, each agent with role "
                "/ goal / backstory / tools, and each task in execution order with "
                "its owner, its instruction, its expected output, and its "
                "dependencies."
            ),
            agent=agent,
        )

    def _audit_task(self, agent: Agent, context: list[Task]) -> Task:
        return Task(
            name="audit_blueprint",
            description=(
                "Convert the crew design above into a single JSON blueprint object.\n"
                "Check it against every rule and silently fix any violation — do not "
                "report problems, correct them.\n\n"
                "Names (`name` fields for the crew, agents and tasks) must be "
                "snake_case identifiers. `agent` and `context` fields refer to those "
                "names, never to roles or descriptions.\n\n"
                + design_rules(self.registry)
            ),
            expected_output=(
                "A single JSON object matching the CrewSpec schema. No prose and no "
                "markdown fences."
            ),
            agent=agent,
            context=context,
            output_pydantic=CrewSpec,
            guardrail=_make_guardrail(self.registry),
            guardrail_max_retries=3,
        )

    # -- public API ------------------------------------------------------

    def crew(self) -> Crew:
        """The architect crew itself — exposed so you can inspect or reuse it."""
        architect = self._architect_agent()
        auditor = self._auditor_agent()
        design = self._design_task(architect)
        audit = self._audit_task(auditor, context=[design])
        return Crew(
            name="agent_factory",
            agents=[architect, auditor],
            tasks=[design, audit],
            process=Process.sequential,
            verbose=self.verbose,
        )

    def design(self, brief: str) -> CrewSpec:
        """Run the meta-agent and return a validated blueprint."""
        result = self.crew().kickoff(
            # `placeholder_example` is not part of the brief: it renders the
            # literal braces of rule 6 without CrewAI trying to interpolate
            # them as a variable of its own.
            inputs={"brief": brief, "placeholder_example": "{company_name}"}
        )
        spec = result.pydantic
        if not isinstance(spec, CrewSpec):
            raise RuntimeError(
                "The architect crew did not return a parseable CrewSpec.\n"
                f"Raw output:\n{result.raw}"
            )
        # Belt and braces: the guardrail already checked this, but `build_crew`
        # trusts the spec completely, so verify once more at the boundary.
        spec.raise_for_problems(allowed_tools=self.registry.names)
        return spec
