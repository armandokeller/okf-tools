"""Demonstrates okf-tools' PydanticAI tools against a local, OpenAI-compatible
model server (LM Studio, Ollama, vLLM, etc.) instead of a hosted provider.

Configure via environment variables (defaults match LM Studio's defaults):

    OKF_LOCAL_MODEL_BASE_URL   default: http://127.0.0.1:1234/v1
    OKF_LOCAL_MODEL_NAME       default: google/gemma-4-e4b
    OKF_LOCAL_MODEL_API_KEY    default: "not-needed" (most local servers ignore it)

`pydantic-ai-slim[openai]` is a dev-only dependency of this repository
(used to run this example) — it is NOT part of the
`okf-tools[pydantic-ai]` extra, since the choice of a local vs. hosted
OpenAI-compatible client is an application decision, not something the
library should assume.

Run:

    uv run python examples/pydantic_ai_agent_local.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from okf_tools.catalog import Catalog
from okf_tools.integrations.pydantic_ai import get_pydantic_ai_tools

EXAMPLE_BUNDLE = Path(__file__).parent / "data" / "sample_bundle"

BASE_URL = os.environ.get("OKF_LOCAL_MODEL_BASE_URL", "http://127.0.0.1:1234/v1")
MODEL_NAME = os.environ.get("OKF_LOCAL_MODEL_NAME", "google/gemma-4-e4b")
API_KEY = os.environ.get("OKF_LOCAL_MODEL_API_KEY", "not-needed")


def main() -> None:
    # Local models sometimes emit emoji; make sure the terminal can print them
    # regardless of the platform's default stdout encoding (notably Windows).
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    catalog = Catalog()
    catalog.register("demo", EXAMPLE_BUNDLE)
    catalog.load_all()

    tools = get_pydantic_ai_tools(catalog)

    model = OpenAIChatModel(MODEL_NAME, provider=OpenAIProvider(base_url=BASE_URL, api_key=API_KEY))
    agent = Agent(model, tools=tools)

    result = agent.run_sync(
        "Using the 'demo' bundle, search for concepts about customers and "
        "tell me what you find, including any related concepts."
    )
    print(result.output)


if __name__ == "__main__":
    main()
