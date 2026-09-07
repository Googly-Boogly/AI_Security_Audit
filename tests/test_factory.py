"""Everything that can be checked without spending a token on a live model.

Run with:  pip install pytest && python -m pytest
"""

from __future__ import annotations

import pytest
from crewai.tasks.task_output import TaskOutput
from crewai.tools import BaseTool

from agent_factory import CrewSpec, SpecError, build_crew, default_registry, write_project
from agent_factory.architect import AgentFactory, _make_guardrail
from agent_factory.registry import ToolRegistry


@pytest.fixture
def registry() -> ToolRegistry:
    return default_registry(include_crewai_tools=False)


@pytest.fixture
def spec() -> CrewSpec:
    return CrewSpec(
        name="Company Research",
        description="Research a company and produce an investment briefing.",
        agents=[
            dict(name="Researcher", role="Market Researcher", goal="Find facts",
                 backstory="Ex-analyst.", tools=["read_file", "write_file"]),
            dict(name="writer", role="Briefing Writer", goal="Write it up",
                 backstory="Editor.", tools=[]),
        ],
        tasks=[
            dict(name="gather", description="Research {company}.",
                 expected_output="Bullet list of facts.", agent="Researcher"),
            dict(name="write_up", description="Write the briefing on {company}.",
                 expected_output="One page of markdown.", agent="writer",
                 context=["gather"], markdown=True),
        ],
    )


# -- schema ---------------------------------------------------------------

def test_names_are_normalised(spec: CrewSpec) -> None:
    assert spec.name == "company_research"
    assert [a.name for a in spec.agents] == ["researcher", "writer"]
    assert spec.tasks[0].agent == "researcher"


def test_placeholders_are_discovered(spec: CrewSpec) -> None:
    assert spec.placeholders() == {"company"}


def test_valid_spec_has_no_problems(spec: CrewSpec, registry: ToolRegistry) -> None:
    assert spec.check_semantics(registry.names) == []


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        (lambda s: setattr(s.tasks[0], "agent", "nobody"), "unknown agent"),
        (lambda s: setattr(s.tasks[0], "context", ["write_up"]), "not defined before"),
        (lambda s: setattr(s.agents[0], "tools", ["nope"]), "unavailable tool"),
        (lambda s: setattr(s.tasks[0], "context", ["gather"]), "lists itself"),
        (lambda s: setattr(s.tasks[1], "agent", "researcher"), "no task assigned"),
    ],
)
def test_broken_specs_are_rejected(spec, registry, mutate, expected) -> None:
    mutate(spec)
    problems = spec.check_semantics(registry.names)
    assert any(expected in p for p in problems), problems


def test_hierarchical_workers_may_not_delegate(spec, registry) -> None:
    spec.process = "hierarchical"
    spec.agents[0].allow_delegation = True
    assert any("allow_delegation=false" in p for p in spec.check_semantics(registry.names))


# -- builder --------------------------------------------------------------

def test_build_crew_wires_agents_tasks_and_context(spec, registry) -> None:
    crew = build_crew(spec, registry=registry, verbose=False)
    assert [a.role for a in crew.agents] == ["Market Researcher", "Briefing Writer"]
    assert [t.name for t in crew.tasks] == ["gather", "write_up"]
    assert [t.name for t in crew.tasks[1].context] == ["gather"]
    assert [t.name for t in crew.agents[0].tools] == ["read_file", "write_file"]


def test_planning_maps_to_planning_config(spec, registry) -> None:
    spec.agents[0].planning = True
    crew = build_crew(spec, registry=registry, verbose=False)
    assert crew.agents[0].planning_config is not None
    assert crew.agents[1].planning_config is None


def test_build_crew_refuses_a_broken_spec(spec, registry) -> None:
    spec.tasks[0].agent = "ghost"
    with pytest.raises(SpecError):
        build_crew(spec, registry=registry)


# -- codegen --------------------------------------------------------------

def test_generated_project_has_the_standard_layout(spec, tmp_path) -> None:
    root = write_project(spec, tmp_path)
    written = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    pkg = f"src/{spec.name}"
    assert {
        "pyproject.toml",
        "README.md",
        ".env.example",
        "blueprint.json",
        f"{pkg}/crew.py",
        f"{pkg}/llm.py",
        f"{pkg}/main.py",
        f"{pkg}/config/agents.yaml",
        f"{pkg}/config/tasks.yaml",
        f"{pkg}/tools/__init__.py",
        f"{pkg}/tools/workspace_tools.py",
    } <= written


def test_generated_project_round_trips(spec, tmp_path) -> None:
    root = write_project(spec, tmp_path)
    assert CrewSpec.model_validate_json((root / "blueprint.json").read_text()) == spec


def test_generated_project_does_not_import_the_factory(spec, tmp_path) -> None:
    """The export must stand alone; importing agent_factory would break that."""
    root = write_project(spec, tmp_path)
    for path in (root / "src").rglob("*.py"):
        assert "agent_factory" not in path.read_text(), path


def test_generated_project_compiles(spec, tmp_path) -> None:
    import py_compile

    root = write_project(spec, tmp_path)
    for path in (root / "src").rglob("*.py"):
        py_compile.compile(str(path), doraise=True)


def test_unexportable_tools_become_explicit_stubs(spec, tmp_path) -> None:
    """A runtime-registered tool has no source to copy, so it must be stubbed."""
    spec.agents[0].tools = ["read_file", "bespoke_scraper"]
    root = write_project(spec, tmp_path)
    custom = (root / "src" / spec.name / "tools" / "custom_tools.py").read_text()
    assert "BespokeScraperTool" in custom
    assert "NotImplementedError" in custom
    assert "BespokeScraperTool" in (root / "src" / spec.name / "tools" / "__init__.py").read_text()


# -- guardrail ------------------------------------------------------------

def _output(pydantic) -> TaskOutput:
    return TaskOutput(description="d", raw="{}", agent="a", pydantic=pydantic)


def test_guardrail_rejects_unparsed_output(registry) -> None:
    ok, message = _make_guardrail(registry)(_output(None))
    assert not ok and "CrewSpec" in message


def test_guardrail_reports_every_problem(registry) -> None:
    bad = CrewSpec(
        name="x", description="d",
        agents=[dict(name="a1", role="R", goal="G", backstory="B", tools=["nope"])],
        tasks=[dict(name="t1", description="do", expected_output="e", agent="ghost")],
    )
    ok, message = _make_guardrail(registry)(_output(bad))
    assert not ok
    assert "unknown agent" in message and "unavailable tool" in message


def test_guardrail_passes_valid_output_through_untouched(registry) -> None:
    good = CrewSpec(
        name="x", description="d",
        agents=[dict(name="a1", role="R", goal="G", backstory="B", tools=["read_file"])],
        tasks=[dict(name="t1", description="do", expected_output="e", agent="a1")],
    )
    out = _output(good)
    ok, result = _make_guardrail(registry)(out)
    assert ok and result is out and isinstance(result.pydantic, CrewSpec)


# -- prompt safety --------------------------------------------------------

def test_tool_descriptions_cannot_break_kickoff_interpolation() -> None:
    """A tool whose description contains braces must not crash the architect."""

    class Nasty(BaseTool):
        name: str = "nasty"
        description: str = "Reads {path} and writes {content} to {dest}."

        def _run(self, **kwargs: object) -> str:
            return ""

    registry = ToolRegistry()
    registry.register_tool(Nasty())
    crew = AgentFactory(registry=registry, verbose=False).crew()

    inputs = {"brief": "anything", "placeholder_example": "{company_name}"}
    for task in crew.tasks:
        task.interpolate_inputs_and_add_conversation_history(dict(inputs))

    rendered = crew.tasks[0].description + crew.tasks[1].description
    assert "<path>" in rendered and "{path}" not in rendered
    assert "{company_name}" in rendered


# -- workspace sandbox ----------------------------------------------------

def test_file_tools_cannot_escape_the_workspace(registry) -> None:
    read_file = registry.build(["read_file"])[0]
    with pytest.raises(ValueError, match="escapes the workspace"):
        read_file.run(path="../../../etc/passwd")
