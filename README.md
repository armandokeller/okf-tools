# okf-tools

[![CI](https://github.com/armandokeller/okf-tools/actions/workflows/ci.yml/badge.svg)](https://github.com/armandokeller/okf-tools/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/okf-tools.svg)](https://pypi.org/project/okf-tools/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Tools to query and consume [Open Knowledge Format (OKF)](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf)
data catalogs — usable as plain standalone Python functions, or wired into
AI agent frameworks (LangChain, PydanticAI, Google ADK).

## What is OKF?

OKF represents a data catalog ("bundle") as a directory tree of markdown
files with YAML frontmatter: each file (a "concept") describes a table,
metric, playbook, or any other unit of knowledge, and concepts link to
each other via ordinary markdown links — the bundle is graph-shaped, not
just a tree. See the [OKF v0.2 spec](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
for the full format.

`okf-tools` parses bundles (tolerating malformed or partial data — a
philosophy the format itself encourages), builds a lightweight graph of
the links between concepts, and exposes a small set of query functions:
list bundles, fetch a concept, search by keyword, expand a concept's
neighborhood, browse a directory listing, and pull a named section out of
a concept's body. The same functions work standalone or as tools handed
to an agent.

## Install

Not yet released to PyPI. In the meantime, install directly from GitHub:

```bash
pip install git+https://github.com/armandokeller/okf-tools
```

Once released, the base package will have no agent-framework
dependencies — add only the framework(s) you use:

```bash
pip install okf-tools                 # standalone use only
pip install okf-tools[langchain]      # + LangChain tools
pip install okf-tools[pydantic-ai]    # + PydanticAI tools
pip install okf-tools[adk]            # + Google ADK tools
```

## Quickstart: standalone

```python
from okf_tools.catalog import Catalog
from okf_tools.api import list_bundles, search_concepts, get_related, get_section

catalog = Catalog()
catalog.register("my_bundle", "/path/to/an/okf/bundle")
catalog.load_all()

for summary in list_bundles(catalog):
    print(summary.name, summary.concept_count, "concepts")

for hit in search_concepts(catalog, "revenue"):
    print(hit.bundle, hit.concept.id, hit.concept.title)

related = get_related(catalog, "my_bundle", "tables/orders", depth=1)
for r in related.related:
    print(r.concept.id, "at distance", r.distance)

print(get_section(related.concept, "Schema"))
```

A fully runnable version of this, with a small bundled sample dataset,
is at [`examples/standalone_usage.py`](examples/standalone_usage.py).

## Quickstart: agent frameworks

Every adapter wraps the same functions shown above — `list_bundles`,
`get_concept`, `search_concepts`, `get_related`, `get_index`, and
`get_section` — as tools bound to an already-loaded `Catalog`.

### LangChain

```python
from okf_tools.integrations.langchain import get_langchain_tools

tools = get_langchain_tools(catalog)
# tools is a list[BaseTool] — pass it to create_agent(), an AgentExecutor, etc.
```

Full example: [`examples/langchain_agent.py`](examples/langchain_agent.py)
(hosted model) and [`examples/langchain_agent_local.py`](examples/langchain_agent_local.py)
(any local OpenAI-compatible server — LM Studio, Ollama, vLLM, ...).

### PydanticAI

```python
from pydantic_ai import Agent
from okf_tools.integrations.pydantic_ai import get_pydantic_ai_tools

tools = get_pydantic_ai_tools(catalog)
agent = Agent("anthropic:claude-opus-4-8", tools=tools)
```

Full example: [`examples/pydantic_ai_agent.py`](examples/pydantic_ai_agent.py)
and [`examples/pydantic_ai_agent_local.py`](examples/pydantic_ai_agent_local.py).

### Google ADK

```python
from google.adk.agents import Agent
from okf_tools.integrations.adk import get_adk_tools

tools = get_adk_tools(catalog)
agent = Agent(name="catalog_agent", model="gemini-2.0-flash", tools=tools)
```

Full example: [`examples/adk_agent.py`](examples/adk_agent.py) and
[`examples/adk_agent_local.py`](examples/adk_agent_local.py).

## Development

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync                    # install package + dev dependencies
uv run pytest              # run the test suite
uv run ruff check .        # lint
uv run ruff format --check .  # formatting
uv run mypy src            # type check
```

Each framework adapter's dev-only local-model example
(`examples/*_agent_local.py`) needs that framework's own model-provider
package (already in the dev dependency group, except Google ADK's
`extensions` extra — see that example's docstring for why it runs in an
ephemeral environment instead).

## License

[MIT](LICENSE)
