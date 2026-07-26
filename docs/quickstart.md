# Quickstart

## Standalone

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

A fully runnable version of this, with a small bundled sample dataset, is
at [`examples/standalone_usage.py`](https://github.com/armandokeller/okf-tools/blob/main/examples/standalone_usage.py)
in the repository.

See the [Public API reference](api/public-api.md) for every function
shown above.

## Agent frameworks

Every adapter wraps the same functions shown above — `list_bundles`,
`get_concept`, `search_concepts`, `get_related`, `get_index`, and
`get_section` — as tools bound to an already-loaded `Catalog`.

### LangChain

```python
from okf_tools.integrations.langchain import get_langchain_tools

tools = get_langchain_tools(catalog)
# tools is a list[BaseTool] — pass it to create_agent(), an AgentExecutor, etc.
```

Full example: [`examples/langchain_agent.py`](https://github.com/armandokeller/okf-tools/blob/main/examples/langchain_agent.py)
(hosted model) and [`examples/langchain_agent_local.py`](https://github.com/armandokeller/okf-tools/blob/main/examples/langchain_agent_local.py)
(any local OpenAI-compatible server — LM Studio, Ollama, vLLM, ...).

### PydanticAI

```python
from pydantic_ai import Agent
from okf_tools.integrations.pydantic_ai import get_pydantic_ai_tools

tools = get_pydantic_ai_tools(catalog)
agent = Agent("anthropic:claude-opus-4-8", tools=tools)
```

Full example: [`examples/pydantic_ai_agent.py`](https://github.com/armandokeller/okf-tools/blob/main/examples/pydantic_ai_agent.py)
and [`examples/pydantic_ai_agent_local.py`](https://github.com/armandokeller/okf-tools/blob/main/examples/pydantic_ai_agent_local.py).

### Google ADK

```python
from google.adk.agents import Agent
from okf_tools.integrations.adk import get_adk_tools

tools = get_adk_tools(catalog)
agent = Agent(name="catalog_agent", model="gemini-2.0-flash", tools=tools)
```

Full example: [`examples/adk_agent.py`](https://github.com/armandokeller/okf-tools/blob/main/examples/adk_agent.py)
and [`examples/adk_agent_local.py`](https://github.com/armandokeller/okf-tools/blob/main/examples/adk_agent_local.py).
