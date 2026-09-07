# agent_factory

An AI agent that builds other AI agents, on [CrewAI](https://docs.crewai.com).

You describe a goal in plain language. A two-agent **architect crew** designs the
team that can deliver it, validates the design against a schema, and emits a
**blueprint**. The blueprint is then either built into a live crew and run, or
written out as an ordinary CrewAI project you can edit and check into git.

```
brief ──▶ Architect ──▶ Auditor ──▶ CrewSpec ──┬──▶ build_crew()   → runs now
          (designs)     (validates)  (blueprint)└──▶ write_project() → editable project
                            ▲                │
                            └── guardrail ◀──┘  invalid? retry with the errors
```

## Setup

```bash
pip install -r requirements.txt

cp .env.example .env      # then put your key in it
# or, for one shell only:
export ANTHROPIC_API_KEY=sk-ant-...
```

Keys come from <https://console.anthropic.com/settings/keys>. A real environment
variable takes precedence over `.env`.

## Use

```bash
# design a crew, write it to generated/
python main.py "Research a company and write a one-page investment briefing"

# design it and run it straight away
python main.py "Summarise a research paper" --run --input paper_url=https://arxiv.org/abs/...

# re-run a crew designed earlier — no model call to rebuild it
python main.py --from-blueprint generated/company_research/blueprint.json --run --input company=Acme
```

Or from Python:

```python
from agent_factory import AgentFactory, build_crew, write_project

spec = AgentFactory().design("Research a company and write an investment briefing")
write_project(spec)                                   # generated/<crew>/
result = build_crew(spec).kickoff(inputs={"company": "Acme"})
```

## How it holds together

| Module | Role |
|---|---|
| `schema.py` | `CrewSpec` / `AgentSpec` / `TaskSpec` — the contract. Names are normalised; cross-references are checked by `check_semantics`. |
| `architect.py` | The meta-agent: an Architect that designs and an Auditor that emits a validated `CrewSpec`. |
| `registry.py` | The tool whitelist. The architect may only pick from it. |
| `builder.py` | Blueprint → live `Agent` / `Task` / `Crew`. No LLM involved. |
| `codegen.py` | Blueprint → `config/*.yaml` + `crew.py` + `blueprint.json`. |

**Generated output is a normal CrewAI project.** `config/agents.yaml`,
`config/tasks.yaml` and a `@CrewBase` class — the layout CrewAI's own scaffolding
produces. Nothing about it depends on the factory once written.

### Why a generated crew can't be broken

Three gates sit between the model and anything that executes:

1. **`output_pydantic=CrewSpec`** — CrewAI parses the auditor's output into a
   typed model, or fails loudly.
2. **A guardrail** re-runs the cross-reference checks: every task owned by an
   agent that exists, every dependency pointing at an earlier task, every tool
   present in the registry, no idle agents. On failure the auditor gets its own
   error list back and retries (up to 3 times).
3. **`build_crew` re-validates** before instantiating anything, so a
   hand-edited `blueprint.json` is held to the same bar.

A hallucinated tool name is therefore a retry, not a runtime crash.

### Tools

The architect can only wire up tools registered in `registry.py`. Three ship by
default — `read_file`, `write_file`, `list_workspace` — all confined to
`./workspace` (override with `AGENT_FACTORY_WORKSPACE`); paths that escape it are
rejected. If [`crewai-tools`](https://github.com/crewAIInc/crewAI-tools) is
installed, a few of its tools are picked up automatically when their API keys are
present.

Add your own:

```python
from agent_factory import ToolRegistry, AgentFactory, default_registry

registry = default_registry()
registry.register_tool(MyTool())            # reuses the tool's own name/description
spec = AgentFactory(registry=registry).design("...")
```

## Models

Both the architect and the generated crews use `anthropic/claude-opus-5` through
CrewAI's native Anthropic provider, which calls the official `anthropic` SDK.
Override per environment:

```bash
export AGENT_FACTORY_ARCHITECT_MODEL=anthropic/claude-opus-5
export AGENT_FACTORY_WORKER_MODEL=anthropic/claude-sonnet-5   # cheaper workers
```

`thinking` is deliberately left unset: adaptive thinking is on by default for
Opus 5, and CrewAI's `AnthropicThinkingConfig` only models the legacy
`budget_tokens` shape, which Opus 5 rejects. `max_tokens` is pinned to 16000
because CrewAI calls the Messages API without streaming.

## Tests

```bash
pip install pytest && python -m pytest
```

18 tests covering schema normalisation, every class of invalid blueprint, the
guardrail, builder wiring, codegen round-trip, the workspace sandbox, and prompt
interpolation safety. None of them call a model.
