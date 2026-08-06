"""Demonstrates wiring okf-tools into a Google ADK agent.

`google-adk` is a dev-only dependency of this repository (used to run
this example) — it is NOT part of the `okf-agent-tools[adk]` extra beyond the
bare `google-adk` package itself, which is all `okf_tools.integrations.adk`
needs for the `FunctionTool` primitive.

Run from the repository root:

    export GOOGLE_API_KEY=...   # or GEMINI_API_KEY; optional, see below
    uv run python examples/adk_agent.py

Without a key set, this prints the wired-up tools and exits without
making any API calls, so the example stays runnable in environments
with no credentials configured.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from okf_tools.catalog import Catalog
from okf_tools.integrations.adk import get_adk_tools

EXAMPLE_BUNDLE = Path(__file__).parent / "data" / "sample_bundle"
APP_NAME = "okf_tools_example"
USER_ID = "demo-user"
PROMPT = (
    "Using the 'demo' bundle, search for concepts about customers and "
    "tell me what you find, including any related concepts."
)


async def _run(agent: object) -> None:
    from google.adk.runners import InMemoryRunner
    from google.genai import types

    runner = InMemoryRunner(agent, app_name=APP_NAME)  # type: ignore[arg-type]
    session = await runner.session_service.create_session(app_name=APP_NAME, user_id=USER_ID)
    message = types.Content(role="user", parts=[types.Part(text=PROMPT)])

    async for event in runner.run_async(
        user_id=USER_ID, session_id=session.id, new_message=message
    ):
        if event.is_final_response() and event.content and event.content.parts:
            print(event.content.parts[0].text)


def main() -> None:
    catalog = Catalog()
    catalog.register("demo", EXAMPLE_BUNDLE)
    catalog.load_all()

    tools = get_adk_tools(catalog)

    if not (os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")):
        print("GOOGLE_API_KEY/GEMINI_API_KEY not set - showing the wired-up tools, no API call.")
        for tool in tools:
            print(f"  - {tool.name}: {(tool.description or '').splitlines()[0]}")
        return

    from google.adk.agents import Agent

    agent = Agent(
        name="okf_tools_demo_agent",
        model="gemini-2.0-flash",
        instruction="You help users explore Open Knowledge Format data catalogs.",
        tools=tools,
    )
    asyncio.run(_run(agent))


if __name__ == "__main__":
    main()
