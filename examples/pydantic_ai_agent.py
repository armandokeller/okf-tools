"""Demonstrates wiring okf-tools into a PydanticAI agent.

`pydantic-ai-slim[openai]` is a dev-only dependency of this repository
(used to run this example) — it is NOT part of the
`okf-tools[pydantic-ai]` extra, which only needs bare `pydantic-ai-slim`
for the `Tool` primitive `okf_tools.integrations.pydantic_ai` wraps.
Bring whichever provider extra (`openai`, `anthropic`, `google`, ...)
matches the model you want to run against.

Run from the repository root:

    export ANTHROPIC_API_KEY=...   # optional; see below
    uv run python examples/pydantic_ai_agent.py

Without `ANTHROPIC_API_KEY` set, this prints the wired-up tools and
exits without making any API calls, so the example stays runnable in
environments with no credentials configured.
"""

from __future__ import annotations

import os
from pathlib import Path

from okf_tools.catalog import Catalog
from okf_tools.integrations.pydantic_ai import get_pydantic_ai_tools

EXAMPLE_BUNDLE = Path(__file__).parent / "data" / "sample_bundle"


def main() -> None:
    catalog = Catalog()
    catalog.register("demo", EXAMPLE_BUNDLE)
    catalog.load_all()

    tools = get_pydantic_ai_tools(catalog)

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set - showing the wired-up tools without calling a model.")
        for tool in tools:
            print(f"  - {tool.name}: {(tool.description or '').splitlines()[0]}")
        return

    from pydantic_ai import Agent

    agent = Agent("anthropic:claude-opus-4-8", tools=tools)

    result = agent.run_sync(
        "Using the 'demo' bundle, search for concepts about customers and "
        "tell me what you find, including any related concepts."
    )
    print(result.output)


if __name__ == "__main__":
    main()
