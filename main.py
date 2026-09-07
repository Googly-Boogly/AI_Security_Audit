"""CLI for the agent factory.

    # design a crew and write it out as an editable CrewAI project
    python main.py "Research a company and write a one-page investment briefing"

    # design it, then run it immediately with inputs
    python main.py "Summarise a research paper" --run --input paper_url=https://...

    # rebuild and run a crew that was generated earlier
    python main.py --from-blueprint generated/company_research/blueprint.json --run
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from agent_factory import AgentFactory, CrewSpec, build_crew, default_registry, write_project
from agent_factory.config import require_api_key

# Read ANTHROPIC_API_KEY from a .env file next to this script, if there is one.
# A real environment variable always wins over the file.
load_dotenv(Path(__file__).parent / ".env", override=False)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="agent-factory",
        description="Design, persist and run CrewAI crews from a plain-language brief.",
    )
    parser.add_argument(
        "brief",
        nargs="?",
        help="What the generated crew should accomplish.",
    )
    parser.add_argument(
        "--from-blueprint",
        type=Path,
        metavar="PATH",
        help="Skip the architect and load a previously generated blueprint.json.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("generated"),
        help="Directory to write the generated project into (default: generated/).",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Design the crew but do not write it to disk.",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Execute the generated crew after building it.",
    )
    parser.add_argument(
        "--input",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Input for the generated crew's placeholders. Repeatable.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress CrewAI's step-by-step execution log.",
    )
    return parser.parse_args(argv)


def parse_inputs(pairs: list[str]) -> dict[str, str]:
    inputs: dict[str, str] = {}
    for pair in pairs:
        key, sep, value = pair.partition("=")
        if not sep:
            raise SystemExit(f"--input expects KEY=VALUE, got {pair!r}")
        inputs[key.strip()] = value
    return inputs


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.brief and not args.from_blueprint:
        raise SystemExit("Provide a brief, or --from-blueprint to reuse an existing one.")

    try:
        require_api_key()
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from None

    registry = default_registry()
    verbose = not args.quiet

    if args.from_blueprint:
        try:
            spec = CrewSpec.model_validate_json(args.from_blueprint.read_text("utf-8"))
            spec.raise_for_problems(allowed_tools=registry.names)
        except (OSError, ValueError) as exc:
            raise SystemExit(
                f"Could not load blueprint {args.from_blueprint}: {exc}"
            ) from None
        print(f"Loaded blueprint {spec.name!r} from {args.from_blueprint}")
    else:
        factory = AgentFactory(registry=registry, verbose=verbose)
        spec = factory.design(args.brief)
        print(f"\nDesigned crew {spec.name!r}: {spec.description}")

    print(f"  agents: {', '.join(a.name for a in spec.agents)}")
    print(f"  tasks:  {' -> '.join(t.name for t in spec.tasks)}")

    if not args.no_write:
        root = write_project(spec, args.out)
        print(f"  written to {root}/  (crew.py, config/, blueprint.json)")

    if not args.run:
        placeholders = spec.placeholders()
        hint = " ".join(f"--input {p}=..." for p in sorted(placeholders))
        print(f"\nTo run it: python main.py --from-blueprint {args.out / spec.name}/blueprint.json --run {hint}".rstrip())
        return 0

    inputs = parse_inputs(args.input)
    missing = spec.placeholders() - inputs.keys()
    if missing:
        raise SystemExit(
            f"The crew needs values for: {', '.join(sorted(missing))}. "
            "Supply them with --input KEY=VALUE."
        )

    print(f"\nRunning {spec.name!r}...\n")
    result = build_crew(spec, registry=registry, verbose=verbose).kickoff(inputs=inputs)
    print("\n" + "=" * 72 + f"\nResult of {spec.name!r}\n" + "=" * 72)
    print(result.raw)
    return 0


if __name__ == "__main__":
    sys.exit(main())
