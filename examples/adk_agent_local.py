"""Demonstrates okf-tools' ADK tools against a local, OpenAI-compatible
model server (LM Studio, Ollama, vLLM, etc.) instead of a hosted provider.

This needs the `extensions` extra of `google-adk` (which pulls in
LiteLLM, used here to reach a non-Gemini/OpenAI-compatible endpoint).
It is deliberately NOT a committed dev dependency of this repo:
`google-adk[extensions]` pulls in a large dependency tree that conflicts
with this project's `langchain>=1.0` dev dependency via incompatible
`langgraph` version ranges (confirmed by a real `uv sync` failure, not
assumed). Run this example in its own ephemeral environment instead:

    uv run --with "google-adk[extensions]" python examples/adk_agent_local.py

Configure via environment variables (defaults match LM Studio's defaults):

    OKF_LOCAL_MODEL_BASE_URL   default: http://127.0.0.1:1234/v1
    OKF_LOCAL_MODEL_NAME       default: google/gemma-4-e4b
    OKF_LOCAL_MODEL_API_KEY    default: "not-needed" (most local servers ignore it)

Known issue: as of google-adk 2.5.0 / litellm 1.93.0, sending ANY tool
declaration through this path can trip up LM Studio's OpenAI-compatible
endpoint — reproduced with a single trivial tool against two different
local models (one raised `litellm.BadRequestError: Invalid 'content'`,
the other returned a non-answer). This reproduces with a minimal tool
unrelated to okf-tools' own schemas, so it looks like an ADK+LiteLLM
request-shape incompatibility with LM Studio's server, not a bug in
`okf_tools.integrations.adk`. A plain (tool-less) call through the same
stack works fine. See `docs/planning/07-adk-integration.md` for details;
if your local server handles ADK's tool-calling requests better, this
script should still work unmodified.
"""

from __future__ import annotations

import asyncio
import os
import sys
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

BASE_URL = os.environ.get("OKF_LOCAL_MODEL_BASE_URL", "http://127.0.0.1:1234/v1")
MODEL_NAME = os.environ.get("OKF_LOCAL_MODEL_NAME", "google/gemma-4-e4b")
API_KEY = os.environ.get("OKF_LOCAL_MODEL_API_KEY", "not-needed")


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
    # Local models sometimes emit emoji; make sure the terminal can print them
    # regardless of the platform's default stdout encoding (notably Windows).
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    catalog = Catalog()
    catalog.register("demo", EXAMPLE_BUNDLE)
    catalog.load_all()

    tools = get_adk_tools(catalog)

    from google.adk.agents import Agent
    from google.adk.models.lite_llm import LiteLlm

    model = LiteLlm(model=f"openai/{MODEL_NAME}", api_base=BASE_URL, api_key=API_KEY)
    agent = Agent(
        name="okf_tools_demo_agent",
        model=model,
        instruction="You help users explore Open Knowledge Format data catalogs.",
        tools=tools,
    )
    asyncio.run(_run(agent))


if __name__ == "__main__":
    main()
