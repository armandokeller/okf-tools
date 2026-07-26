# okf-tools

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

See [Quickstart](quickstart.md) to get started, or the
[API Reference](api/public-api.md) for the full function-by-function
documentation.
