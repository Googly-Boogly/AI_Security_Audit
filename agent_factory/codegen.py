"""Render a `CrewSpec` as a standalone CrewAI project on disk.

The output is a complete, self-contained project in the layout `crewai create
crew` produces — `pyproject.toml`, `src/<name>/crew.py`, `config/*.yaml`, and a
`tools/` package — with no import back into `agent_factory`. Copy the directory
anywhere, `pip install -e .`, and `crewai run` it.

`blueprint.json` is written alongside so the same crew can be rebuilt in memory
by the factory later without another trip to the model.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import yaml

from agent_factory.schema import CrewSpec

__all__ = ["write_project", "BUILTIN_TOOLS"]

# Tools the exported project carries its own copy of. Anything an agent asks for
# that is not in here becomes a clearly-marked stub in tools/custom_tools.py.
BUILTIN_TOOLS: dict[str, str] = {
    "read_file": "ReadFileTool",
    "write_file": "WriteFileTool",
    "list_workspace": "ListWorkspaceTool",
}


def _class_name(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_")) or "GeneratedCrew"


def _q(text: str) -> str:
    """Quote a string for embedding in generated Python source."""
    return repr(text)


# ---------------------------------------------------------------------------
# config/*.yaml
# ---------------------------------------------------------------------------


def _agents_yaml(spec: CrewSpec) -> str:
    payload = {
        a.name: {"role": a.role, "goal": a.goal, "backstory": a.backstory}
        for a in spec.agents
    }
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, width=88)


def _tasks_yaml(spec: CrewSpec) -> str:
    payload: dict[str, dict[str, object]] = {}
    for task in spec.tasks:
        entry: dict[str, object] = {
            "description": task.description,
            "expected_output": task.expected_output,
            "agent": task.agent,
        }
        if task.context:
            entry["context"] = list(task.context)
        if task.output_file:
            entry["output_file"] = task.output_file
        if task.markdown:
            entry["markdown"] = True
        payload[task.name] = entry
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, width=88)


# ---------------------------------------------------------------------------
# src/<name>/crew.py
# ---------------------------------------------------------------------------


def _crew_py(spec: CrewSpec) -> str:
    """Emit the `@CrewBase` module.

    `@CrewBase` resolves each task's `agent:` and `context:` YAML keys against
    the decorated method names, so the method names here must match the YAML
    keys exactly. Config paths resolve relative to this file, not the working
    directory, so the project runs from anywhere.
    """
    cls = _class_name(spec.name)
    lines: list[str] = [
        '"""Crew definition for ' + spec.name + '."""',
        "",
        "from crewai import Agent, Crew, PlanningConfig, Process, Task",
        "from crewai.agents.agent_builder.base_agent import BaseAgent",
        "from crewai.project import CrewBase, agent, crew, task",
        "",
        "from .llm import build_llm",
        "from .tools import build_tools",
        "",
        "",
        "@CrewBase",
        f"class {cls}:",
        f'    """{spec.description.strip()}"""',
        "",
        "    agents: list[BaseAgent]",
        "    tasks: list[Task]",
        "",
        "    def __init__(self, verbose: bool = True) -> None:",
        "        self.verbose = verbose",
        "        self.llm = build_llm()",
        "",
    ]

    for a in spec.agents:
        tools = ", ".join(_q(t) for t in a.tools)
        planning = "PlanningConfig()" if a.planning else "None"
        lines += [
            "    @agent",
            f"    def {a.name}(self) -> Agent:",
            "        return Agent(",
            f'            config=self.agents_config["{a.name}"],',
            f"            tools=build_tools([{tools}]),",
            f"            allow_delegation={a.allow_delegation},",
            f"            planning_config={planning},",
            f"            max_iter={a.max_iter},",
            "            llm=self.llm,",
            "            verbose=self.verbose,",
            "        )",
            "",
        ]

    for t in spec.tasks:
        lines += [
            "    @task",
            f"    def {t.name}(self) -> Task:",
            f'        return Task(config=self.tasks_config["{t.name}"])',
            "",
        ]

    lines += [
        "    @crew",
        "    def crew(self) -> Crew:",
        f'        """Assemble the {spec.name} crew."""',
        "        return Crew(",
        f"            name={_q(spec.name)},",
        "            agents=self.agents,",
        "            tasks=self.tasks,",
    ]
    if spec.process == "hierarchical":
        lines += [
            "            process=Process.hierarchical,",
            "            manager_llm=self.llm,",
        ]
    else:
        lines.append("            process=Process.sequential,")
    lines += [
        "            verbose=self.verbose,",
        "        )",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# src/<name>/llm.py
# ---------------------------------------------------------------------------

_LLM_PY = '''"""Model configuration.

Uses CrewAI's native Anthropic provider, which calls the official `anthropic`
SDK. `thinking` is deliberately left unset: adaptive thinking is on by default
for Claude Opus 5, and CrewAI's thinking config only models the legacy
`budget_tokens` shape, which Opus 5 rejects. `max_tokens` is pinned because
CrewAI calls the Messages API without streaming.
"""

from __future__ import annotations

import os

from crewai import LLM

MODEL = os.environ.get("CREW_MODEL", "anthropic/claude-opus-5")


def build_llm(max_tokens: int = 16000) -> LLM:
    """Build the LLM every agent in this crew shares."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add "
            "your key, or export it in your shell."
        )
    return LLM(model=MODEL, max_tokens=max_tokens)
'''


# ---------------------------------------------------------------------------
# src/<name>/tools/
# ---------------------------------------------------------------------------

_WORKSPACE_TOOLS_PY = '''"""Workspace-scoped file tools. No third-party dependencies.

Every path is resolved inside a single workspace root; anything that escapes it
is rejected. Point the workspace somewhere else with the CREW_WORKSPACE
environment variable.
"""

from __future__ import annotations

import os
from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

WORKSPACE = Path(os.environ.get("CREW_WORKSPACE", "workspace")).resolve()


def _resolve_inside_workspace(relative_path: str) -> Path:
    """Resolve a path, refusing anything that escapes the workspace root."""
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    target = (WORKSPACE / relative_path).resolve()
    if target != WORKSPACE and WORKSPACE not in target.parents:
        raise ValueError(f"Path {relative_path!r} escapes the workspace at {WORKSPACE}.")
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
        "List every file currently in the shared workspace. Input: path "
        "(relative, use '.' for the root)."
    )
    args_schema: type[BaseModel] = _PathInput

    def _run(self, path: str = ".") -> str:
        target = _resolve_inside_workspace(path)
        if not target.is_dir():
            return f"No directory at {path!r}."
        entries = sorted(
            str(p.relative_to(WORKSPACE)) for p in target.rglob("*") if p.is_file()
        )
        return "\\n".join(entries) if entries else "(workspace is empty)"
'''


def _custom_tools_py(stubs: list[str]) -> str:
    """Emit placeholders for tools the factory could not export.

    A tool registered in the factory at runtime has no source the exporter can
    copy, so it becomes an explicit stub. The project still imports and
    assembles; calling the tool fails loudly with instructions rather than
    silently returning nothing.
    """
    lines = [
        '"""Tools this crew expects that the exporter could not carry over.',
        "",
        "TODO: implement each `_run` below. These were registered with the",
        "agent factory at runtime, so there was no source module to copy.",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "from crewai.tools import BaseTool",
        "",
    ]
    for name in stubs:
        cls = "".join(p.capitalize() for p in name.split("_")) + "Tool"
        lines += [
            "",
            f"class {cls}(BaseTool):",
            f"    name: str = {_q(name)}",
            f"    description: str = {_q(f'TODO: describe {name}.')}",
            "",
            "    def _run(self, *args: object, **kwargs: object) -> str:",
            f"        raise NotImplementedError(",
            f"            {_q(f'{name} was not exported with this project. Implement it in tools/custom_tools.py.')}",
            "        )",
        ]
    return "\n".join(lines) + "\n"


def _tools_init_py(used: list[str], stubs: list[str]) -> str:
    builtin_used = [n for n in used if n in BUILTIN_TOOLS]
    lines = [
        '"""Tool registry for this crew."""',
        "",
        "from __future__ import annotations",
        "",
        "from crewai.tools import BaseTool",
        "",
    ]
    if builtin_used:
        imports = ", ".join(BUILTIN_TOOLS[n] for n in builtin_used)
        lines.append(f"from .workspace_tools import {imports}")
    if stubs:
        stub_classes = ", ".join(
            "".join(p.capitalize() for p in n.split("_")) + "Tool" for n in stubs
        )
        lines.append(f"from .custom_tools import {stub_classes}")
    lines += ["", "", "TOOLS: dict[str, BaseTool] = {"]
    for name in used:
        cls = (
            BUILTIN_TOOLS[name]
            if name in BUILTIN_TOOLS
            else "".join(p.capitalize() for p in name.split("_")) + "Tool"
        )
        lines.append(f"    {_q(name)}: {cls}(),")
    lines += [
        "}",
        "",
        "",
        "def build_tools(names: list[str]) -> list[BaseTool]:",
        '    """Look up tools by name, failing loudly on an unknown one."""',
        "    missing = [n for n in names if n not in TOOLS]",
        "    if missing:",
        "        raise KeyError(f\"Unknown tool(s) {missing}. Available: {sorted(TOOLS)}\")",
        "    return [TOOLS[n] for n in names]",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# src/<name>/main.py
# ---------------------------------------------------------------------------


def _main_py(spec: CrewSpec) -> str:
    cls = _class_name(spec.name)
    placeholders = sorted(spec.placeholders())
    default_lines = [
        f'    {_q(p)}: "TODO: supply a value",' for p in placeholders
    ] or ["    # this crew takes no inputs"]
    return "\n".join(
        [
            "#!/usr/bin/env python",
            f'"""Entry points for {spec.name}.',
            "",
            "    crewai run                      # or: run_crew",
            f"    python -m {spec.name}.main key=value",
            '"""',
            "",
            "from __future__ import annotations",
            "",
            "import sys",
            "",
            "from dotenv import load_dotenv",
            "",
            f"from {spec.name}.crew import {cls}",
            "",
            "load_dotenv()",
            "",
            "DEFAULT_INPUTS: dict[str, str] = {",
            *default_lines,
            "}",
            "",
            "",
            "def _inputs_from_argv(argv: list[str]) -> dict[str, str]:",
            '    """Override defaults with KEY=VALUE arguments."""',
            "    inputs = dict(DEFAULT_INPUTS)",
            "    for arg in argv:",
            '        key, sep, value = arg.partition("=")',
            "        if sep:",
            "            inputs[key.strip()] = value",
            "    return inputs",
            "",
            "",
            "def run() -> None:",
            '    """Run the crew."""',
            "    inputs = _inputs_from_argv(sys.argv[1:])",
            f"    result = {cls}().crew().kickoff(inputs=inputs)",
            "    print(result.raw)",
            "",
            "",
            "def train() -> None:",
            '    """Train the crew: train <n_iterations> <filename>."""',
            f"    {cls}().crew().train(",
            "        n_iterations=int(sys.argv[1]),",
            "        filename=sys.argv[2],",
            "        inputs=_inputs_from_argv(sys.argv[3:]),",
            "    )",
            "",
            "",
            "def replay() -> None:",
            '    """Replay from a task id: replay <task_id>."""',
            f"    {cls}().crew().replay(task_id=sys.argv[1])",
            "",
            "",
            "def test() -> None:",
            '    """Test the crew: test <n_iterations> <eval_llm>."""',
            f"    {cls}().crew().test(",
            "        n_iterations=int(sys.argv[1]),",
            "        eval_llm=sys.argv[2],",
            "        inputs=_inputs_from_argv(sys.argv[3:]),",
            "    )",
            "",
            "",
            'if __name__ == "__main__":',
            "    run()",
            "",
        ]
    )


# ---------------------------------------------------------------------------
# project files
# ---------------------------------------------------------------------------


def _pyproject_toml(spec: CrewSpec) -> str:
    summary = " ".join(spec.description.split())[:180].replace('"', "'")
    return f'''[project]
name = "{spec.name}"
version = "0.1.0"
description = "{summary}"
requires-python = ">=3.10,<3.14"
dependencies = [
    "crewai[anthropic]>=1.15.20",
    "python-dotenv>=1.0.0",
]

[project.scripts]
{spec.name} = "{spec.name}.main:run"
run_crew = "{spec.name}.main:run"
train = "{spec.name}.main:train"
replay = "{spec.name}.main:replay"
test = "{spec.name}.main:test"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/{spec.name}"]

[tool.crewai]
type = "crew"
'''


def _readme_md(spec: CrewSpec) -> str:
    placeholders = sorted(spec.placeholders())
    example = " ".join(f"{p}='...'" for p in placeholders)
    agent_rows = "\n".join(
        f"| `{a.name}` | {a.role} | {', '.join(a.tools) or '—'} |" for a in spec.agents
    )
    task_rows = "\n".join(
        f"| `{t.name}` | `{t.agent}` | {', '.join(f'`{c}`' for c in t.context) or '—'} |"
        for t in spec.tasks
    )
    inputs_section = (
        "\n".join(f"- `{p}`" for p in placeholders)
        if placeholders
        else "This crew takes no inputs."
    )
    return f"""# {spec.name}

{textwrap.fill(spec.description.strip(), width=88)}

Generated by [agent_factory]. This is a standalone CrewAI project — it does not
import the factory. Edit anything here freely.

## Run it

```bash
cp .env.example .env      # then add your ANTHROPIC_API_KEY
pip install -e .
run_crew {example}
```

Without installing anything:

```bash
PYTHONPATH=src python -m {spec.name}.main {example}
```

`crewai run` also works, but it shells out to [uv](https://docs.astral.sh/uv/),
so install that first if you prefer it.

## Inputs

{inputs_section}

Defaults live in `src/{spec.name}/main.py`; override any of them with
`key=value` arguments.

## Agents

| Name | Role | Tools |
|---|---|---|
{agent_rows}

## Tasks

| Name | Agent | Depends on |
|---|---|---|
{task_rows}

Process: **{spec.process}**.

## Layout

```
pyproject.toml
blueprint.json            rebuild this crew with the factory, no model call
src/{spec.name}/
  crew.py                 the @CrewBase class
  llm.py                  model configuration
  main.py                 entry points
  config/agents.yaml      role / goal / backstory
  config/tasks.yaml       description / expected_output / agent / context
  tools/                  this crew's tools
```
"""


_ENV_EXAMPLE = """# Copy to .env and fill in your key.
# Get one at https://console.anthropic.com/settings/keys
ANTHROPIC_API_KEY=sk-ant-...

# Optional
# CREW_MODEL=anthropic/claude-opus-5
# CREW_WORKSPACE=workspace
"""

_GITIGNORE = """.env
__pycache__/
*.py[cod]
.venv/
workspace/
*.egg-info/
dist/
build/
"""


def write_project(spec: CrewSpec, out_dir: Path | str = "generated") -> Path:
    """Write a standalone CrewAI project to `<out_dir>/<crew name>/`.

    Returns the project root. Re-running overwrites the generated files in
    place, so edits to `crew.py` or the YAML are lost on regeneration — copy the
    project elsewhere before customising it heavily.
    """
    root = Path(out_dir) / spec.name
    pkg = root / "src" / spec.name
    (pkg / "config").mkdir(parents=True, exist_ok=True)
    (pkg / "tools").mkdir(parents=True, exist_ok=True)

    used: list[str] = []
    for agent_spec in spec.agents:
        for tool in agent_spec.tools:
            if tool not in used:
                used.append(tool)
    stubs = [n for n in used if n not in BUILTIN_TOOLS]

    # project root
    (root / "pyproject.toml").write_text(_pyproject_toml(spec), encoding="utf-8")
    (root / "README.md").write_text(_readme_md(spec), encoding="utf-8")
    (root / ".env.example").write_text(_ENV_EXAMPLE, encoding="utf-8")
    (root / ".gitignore").write_text(_GITIGNORE, encoding="utf-8")
    (root / "blueprint.json").write_text(
        spec.model_dump_json(indent=2), encoding="utf-8"
    )

    # package
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "crew.py").write_text(_crew_py(spec), encoding="utf-8")
    (pkg / "llm.py").write_text(_LLM_PY, encoding="utf-8")
    (pkg / "main.py").write_text(_main_py(spec), encoding="utf-8")
    (pkg / "config" / "agents.yaml").write_text(_agents_yaml(spec), encoding="utf-8")
    (pkg / "config" / "tasks.yaml").write_text(_tasks_yaml(spec), encoding="utf-8")

    # tools
    (pkg / "tools" / "workspace_tools.py").write_text(
        _WORKSPACE_TOOLS_PY, encoding="utf-8"
    )
    (pkg / "tools" / "__init__.py").write_text(
        _tools_init_py(used, stubs), encoding="utf-8"
    )
    if stubs:
        (pkg / "tools" / "custom_tools.py").write_text(
            _custom_tools_py(stubs), encoding="utf-8"
        )

    return root
