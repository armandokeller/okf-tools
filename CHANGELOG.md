# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Core OKF v0.2 parser (`okf_tools.models`, `okf_tools.parsing`,
  `okf_tools.bundle`): concept, `index.md`, and `log.md` parsing,
  provenance/trust/lifecycle frontmatter families, Attested Computation
  fields, tolerant of legacy v0.1 fields (`timestamp`, `# Citations`)
  and malformed files (a bad concept is recorded in
  `Bundle.load_errors`, never raised).
- Lightweight directed link graph (`okf_tools.graph`) with
  neighbors/backlinks/BFS traversal, tolerant of broken links.
- Filtering and keyword search over a bundle's concepts
  (`okf_tools.queries`).
- Multi-bundle `Catalog` registry (`okf_tools.catalog`) for loading and
  federating queries across several named bundles at once.
- Framework-agnostic public API (`okf_tools.api`): `list_bundles`,
  `get_concept`, `search_concepts`, `get_related`, `get_index`,
  `get_section` — pydantic in/out, usable standalone with no agent
  framework installed.
- LangChain adapter (`okf_tools.integrations.langchain`,
  `okf-tools[langchain]` extra).
- PydanticAI adapter (`okf_tools.integrations.pydantic_ai`,
  `okf-tools[pydantic-ai]` extra).
- Google ADK adapter (`okf_tools.integrations.adk`, `okf-tools[adk]`
  extra).
- Example scripts for standalone usage and each framework, including
  local-model variants for any OpenAI-compatible server (LM Studio,
  Ollama, vLLM, ...).
