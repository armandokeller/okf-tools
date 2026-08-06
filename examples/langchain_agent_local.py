"""Demonstrates okf-tools' LangChain tools against a local, OpenAI-compatible
model server (LM Studio, Ollama, vLLM, etc.) instead of a hosted provider.

Configure via environment variables (defaults match LM Studio's defaults):

    OKF_LOCAL_MODEL_BASE_URL   default: http://127.0.0.1:1234/v1
    OKF_LOCAL_MODEL_NAME       default: google/gemma-4-e4b
    OKF_LOCAL_MODEL_API_KEY    default: "not-needed" (most local servers ignore it)

`langchain-openai` is a dev-only dependency of this repository (used to
run this example) — it is NOT part of the `okf-agent-tools[langchain]` extra,
since the choice of a local vs. hosted OpenAI-compatible client is an
application decision, not something the library should assume.

Run:

    uv run python examples/langchain_agent_local.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from okf_tools.catalog import Catalog
from okf_tools.integrations.langchain import get_langchain_tools

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

    tools = get_langchain_tools(catalog)

    model = ChatOpenAI(base_url=BASE_URL, api_key=API_KEY, model=MODEL_NAME)
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
