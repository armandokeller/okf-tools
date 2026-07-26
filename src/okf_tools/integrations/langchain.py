"""LangChain adapter: exposes `okf_tools.api` functions as LangChain tools.

Requires the `langchain` extra (`pip install okf-tools[langchain]`); this
module is not imported anywhere in the base package, so installing
okf-tools without the extra never pulls in `langchain-core`.
"""

from __future__ import annotations

from langchain_core.tools import BaseTool, tool

from okf_tools.api import BundleSummary, IndexListing, RelatedConcepts, SearchHit
from okf_tools.api import get_concept as _get_concept
from okf_tools.api import get_index as _get_index
from okf_tools.api import get_related as _get_related
from okf_tools.api import get_section as _get_section
from okf_tools.api import list_bundles as _list_bundles
from okf_tools.api import search_concepts as _search_concepts
from okf_tools.catalog import Catalog
from okf_tools.models import Concept


def get_langchain_tools(catalog: Catalog) -> list[BaseTool]:
    """Build LangChain tools bound to an already-loaded `Catalog`.

    Pass the result straight to an agent constructor that accepts a list
    of tools, e.g.:

        tools = get_langchain_tools(catalog)
        agent = create_agent(model, tools=tools)

    Each tool wraps one `okf_tools.api` function with `catalog` already
    bound, exposing only the remaining, agent-fillable arguments.
    """

    @tool
    def list_bundles() -> list[BundleSummary]:
        """List every OKF bundle loaded in this catalog, with its concept count.

        Call this first to discover which bundle names are available
        before calling any other tool that takes a `bundle` argument.
        """
        return _list_bundles(catalog)

    @tool
    def get_concept(bundle: str, concept_id: str) -> Concept:
        """Fetch a single OKF concept by id (its path within the bundle, no `.md` suffix)."""
        return _get_concept(catalog, bundle, concept_id)

    @tool
    def search_concepts(
        query: str,
        bundle: str | None = None,
        concept_type: str | None = None,
        tags: list[str] | None = None,
    ) -> list[SearchHit]:
        """Search OKF concepts by keyword, in one bundle or across every loaded bundle.

        Case-insensitive substring match over title, description, and
        body. Omit `bundle` to search every bundle in the catalog at once.
        """
        return _search_concepts(catalog, query, bundle=bundle, concept_type=concept_type, tags=tags)

    @tool
    def get_related(bundle: str, concept_id: str, depth: int = 1) -> RelatedConcepts:
        """Get an OKF concept plus concepts within `depth` hops of it, in either link direction."""
        return _get_related(catalog, bundle, concept_id, depth=depth)

    @tool
    def get_index(bundle: str, path: str = "/") -> IndexListing:
        """Browse an OKF bundle's directory listing at `path` (`"/"` for the bundle root)."""
        return _get_index(catalog, bundle, path=path)

    @tool
    def get_section(bundle: str, concept_id: str, heading: str) -> str | None:
        """Extract a named top-level section (e.g. `"Schema"`) from a concept's body.

        Returns `None` if the concept has no such heading.
        """
        concept = _get_concept(catalog, bundle, concept_id)
        return _get_section(concept, heading)

    return [
        list_bundles,
        get_concept,
        search_concepts,
        get_related,
        get_index,
        get_section,
    ]
