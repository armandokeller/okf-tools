"""Demonstrates wiring okf-tools into a LangChain agent.

`langchain` and `langchain-anthropic` are dev-only dependencies of this
repository (used to run this example) — they are NOT part of the
`okf-agent-tools[langchain]` extra, which only needs `langchain-core` for the
`Tool` primitive `okf_tools.integrations.langchain` wraps.

Run from the repository root:

    export ANTHROPIC_API_KEY=...   # optional; see below
    uv run python examples/langchain_agent.py

Without `ANTHROPIC_API_KEY` set, this prints the wired-up tools and exits
without making any API calls, so the example stays runnable in
environments with no credentials configured.
"""

from __future__ import annotations

import os
from pathlib import Path

from okf_tools.catalog import Catalog
from okf_tools.integrations.langchain import get_langchain_tools

EXAMPLE_BUNDLE = Path(__file__).parent / "data" / "sample_bundle"


def main() -> None:
    catalog = Catalog()
    catalog.register("demo", EXAMPLE_BUNDLE)
    catalog.load_all()

    tools = get_langchain_tools(catalog)

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set - showing the wired-up tools without calling a model.")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description.splitlines()[0]}")
        return

    from langchain.agents import create_agent
    from langchain_anthropic import ChatAnthropic

    model = ChatAnthropic(model="claude-opus-4-8")
    agent = create_agent(model, tools=tools)

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Using the 'demo' bundle, search for concepts about "
                        "customers and tell me what you find, including any "
                        "related concepts."
                    ),
                }
            ]
        }
    )
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
