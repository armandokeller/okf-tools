"""Google ADK adapter: exposes `okf_tools.api` functions as ADK function tools.

Requires the `adk` extra (`pip install okf-agent-tools[adk]`); this
module is not imported anywhere in the base package, so installing
okf-agent-tools without the extra never pulls in `google.adk`.

ADK's own convention is for a function tool to return a plain dict (a
non-dict return is auto-wrapped as `{"result": ...}`, which would bury
an unserializable pydantic object inside it) — unlike the LangChain and
PydanticAI adapters, which return `okf_tools.api`'s pydantic models
directly. Each tool here therefore serializes its result with
`model_dump(mode="json")` before returning.
"""

from __future__ import annotations

from typing import Any

from google.adk.tools.function_tool import FunctionTool

from okf_tools.api import get_concept as _get_concept
from okf_tools.api import get_index as _get_index
from okf_tools.api import get_related as _get_related
from okf_tools.api import get_section as _get_section
from okf_tools.api import list_bundles as _list_bundles
from okf_tools.api import search_concepts as _search_concepts
from okf_tools.catalog import Catalog


def get_adk_tools(catalog: Catalog) -> list[FunctionTool]:
    """Build ADK function tools bound to an already-loaded `Catalog`.

    Pass the result straight to `Agent(..., tools=get_adk_tools(catalog))`.

    Each tool wraps one `okf_tools.api` function with `catalog` already
    bound, exposing only the remaining, agent-fillable arguments, and
    returns a plain JSON-serializable dict per ADK's own tool convention.
    """

    def list_bundles() -> dict[str, Any]:
        """List every OKF bundle loaded in this catalog, with its concept count.

        Call this first to discover which bundle names are available
        before calling any other tool that takes a `bundle` argument.

        Returns:
            A dict with a `bundles` key: a list of bundle summaries.
        """
        return {"bundles": [b.model_dump(mode="json") for b in _list_bundles(catalog)]}

    def get_concept(bundle: str, concept_id: str) -> dict[str, Any]:
        """Fetch a single OKF concept by id (its path within the bundle, no `.md` suffix).

        Args:
            bundle: Name of the loaded bundle to look in.
            concept_id: The concept's id (its path within the bundle, without `.md`).

        Returns:
            The concept as a dict.
        """
        return _get_concept(catalog, bundle, concept_id).model_dump(mode="json")

    def search_concepts(
        query: str,
        bundle: str | None = None,
        concept_type: str | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Search OKF concepts by keyword, in one bundle or across every loaded bundle.

        Case-insensitive substring match over title, description, and body.

        Args:
            query: The keyword or phrase to search for.
            bundle: Restrict the search to this bundle name; omit to search every
                bundle currently loaded in the catalog.
            concept_type: Only match concepts of this `type` (e.g. `"BigQuery Table"`).
            tags: Only match concepts carrying at least one of these tags.

        Returns:
            A dict with a `hits` key: a list of `{bundle, concept}` matches.
        """
        hits = _search_concepts(catalog, query, bundle=bundle, concept_type=concept_type, tags=tags)
        return {"hits": [h.model_dump(mode="json") for h in hits]}

    def get_related(bundle: str, concept_id: str, depth: int = 1) -> dict[str, Any]:
        """Get an OKF concept plus concepts within `depth` hops of it, in either link direction.

        Args:
            bundle: Name of the loaded bundle to look in.
            concept_id: The concept's id (its path within the bundle, without `.md`).
            depth: How many hops of context to expand around the concept.

        Returns:
            A dict with the concept and its related concepts (each with a hop distance).
        """
        return _get_related(catalog, bundle, concept_id, depth=depth).model_dump(mode="json")

    def get_index(bundle: str, path: str = "/") -> dict[str, Any]:
        """Browse an OKF bundle's directory listing at `path` (`"/"` for the bundle root).

        Args:
            bundle: Name of the loaded bundle to browse.
            path: Directory path within the bundle to list.

        Returns:
            The directory listing as a dict.
        """
        return _get_index(catalog, bundle, path=path).model_dump(mode="json")

    def get_section(bundle: str, concept_id: str, heading: str) -> dict[str, Any]:
        """Extract a named top-level section (e.g. `"Schema"`) from a concept's body.

        Args:
            bundle: Name of the loaded bundle to look in.
            concept_id: The concept's id (its path within the bundle, without `.md`).
            heading: The section heading to extract, e.g. `"Schema"`.

        Returns:
            A dict with a `section` key: the extracted text, or `null` if the
            concept has no such heading.
        """
        concept = _get_concept(catalog, bundle, concept_id)
        return {"section": _get_section(concept, heading)}

    return [
        FunctionTool(list_bundles),
        FunctionTool(get_concept),
        FunctionTool(search_concepts),
        FunctionTool(get_related),
        FunctionTool(get_index),
        FunctionTool(get_section),
    ]
