"""Framework-agnostic public API: the functions meant to become agent tools.

Every function here takes an already-loaded `Catalog` as its first
argument and returns pydantic models, so the exact same signatures and
JSON schemas are reused by the LangChain/PydanticAI/ADK adapters (later
phases). Nothing in this module requires any agent framework to be
installed — see `examples/standalone_usage.py` for plain usage.
"""

from __future__ import annotations

import posixpath
import re

from pydantic import BaseModel

from okf_tools.bundle import Bundle
from okf_tools.catalog import Catalog
from okf_tools.models import Concept, IndexEntry, IndexSection
from okf_tools.queries import search_concepts as _search_bundle


class BundleSummary(BaseModel):
    """A one-line summary of a loaded bundle, for `list_bundles`."""

    name: str
    root: str
    concept_count: int
    okf_version: str | None = None


class SearchHit(BaseModel):
    """One search result, tagged with the bundle it came from."""

    bundle: str
    concept: Concept


class RelatedConcept(BaseModel):
    """A concept reached while expanding context around another concept."""

    concept: Concept
    distance: int


class RelatedConcepts(BaseModel):
    """The result of `get_related`: a concept plus what surrounds it in the graph."""

    concept: Concept
    related: list[RelatedConcept]


class IndexListing(BaseModel):
    """The result of `get_index`: a directory listing within a bundle.

    `synthesized` is `True` when the bundle had no `index.md` at `path`
    and this listing was built on the fly from the concepts directly
    inside that directory (SPEC §8 explicitly allows this).
    """

    bundle: str
    path: str
    okf_version: str | None = None
    sections: list[IndexSection]
    synthesized: bool


def list_bundles(catalog: Catalog) -> list[BundleSummary]:
    """List every bundle currently loaded in `catalog`, with its concept count.

    Use this first to discover what's available before calling any other
    function with a specific `bundle` name.
    """
    return [
        BundleSummary(
            name=name,
            root=bundle.root,
            concept_count=len(bundle.concepts),
            okf_version=bundle.index.okf_version if bundle.index else None,
        )
        for name, bundle in catalog.bundles.items()
    ]


def get_concept(catalog: Catalog, bundle: str, concept_id: str) -> Concept:
    """Fetch a single concept by id (its path within the bundle, without the `.md` suffix).

    Raises `ValueError` with a clear message if `bundle` isn't loaded or
    `concept_id` doesn't exist in it — use `list_bundles` or `get_index`
    to discover valid names first.
    """
    loaded_bundle = _require_bundle(catalog, bundle)
    try:
        return loaded_bundle.concepts[concept_id]
    except KeyError:
        raise ValueError(
            f"no concept {concept_id!r} in bundle {bundle!r} "
            f"({len(loaded_bundle.concepts)} concepts loaded)"
        ) from None


def search_concepts(
    catalog: Catalog,
    query: str,
    *,
    bundle: str | None = None,
    concept_type: str | None = None,
    tags: list[str] | None = None,
) -> list[SearchHit]:
    """Search concepts by keyword, in one bundle or across every loaded bundle.

    Case-insensitive substring match over title, description, and body.
    Pass `bundle` to restrict the search to one bundle; omit it to search
    every bundle currently loaded in `catalog`. Each hit records which
    bundle it came from, since the same concept id can exist in more than
    one bundle.
    """
    bundle_names = [bundle] if bundle is not None else list(catalog.bundles)
    hits: list[SearchHit] = []
    for name in bundle_names:
        loaded_bundle = _require_bundle(catalog, name)
        for concept in _search_bundle(loaded_bundle, query, concept_type=concept_type, tags=tags):
            hits.append(SearchHit(bundle=name, concept=concept))
    return hits


def get_related(catalog: Catalog, bundle: str, concept_id: str, depth: int = 1) -> RelatedConcepts:
    """Get a concept plus its surrounding context: concepts within `depth` hops.

    "Related" means either direction: concepts `concept_id` links to, and
    concepts that link to `concept_id` (its "cited by" backlinks). Use
    `depth > 1` to pull in a wider neighborhood when one hop of context
    isn't enough.
    """
    loaded_bundle = _require_bundle(catalog, bundle)
    concept = get_concept(catalog, bundle, concept_id)
    graph = catalog.get_graph(bundle)
    distances = graph.bfs(concept_id, max_depth=depth)
    related = [
        RelatedConcept(concept=loaded_bundle.concepts[other_id], distance=distance)
        for other_id, distance in distances.items()
        if other_id != concept_id
    ]
    related.sort(key=lambda r: (r.distance, r.concept.id))
    return RelatedConcepts(concept=concept, related=related)


def get_index(catalog: Catalog, bundle: str, path: str = "/") -> IndexListing:
    """Get the directory listing at `path` within a bundle (`"/"` for the bundle root).

    Returns the bundle's own `index.md` for that directory when one
    exists; otherwise synthesizes a listing from the concepts directly
    inside that directory (never nested subdirectories), per SPEC §8.
    Use this to browse a bundle level by level instead of loading every
    concept at once.
    """
    loaded_bundle = _require_bundle(catalog, bundle)
    normalized = _normalize_path(path)
    index_file = loaded_bundle.indexes.get(normalized)
    if index_file is not None:
        return IndexListing(
            bundle=bundle,
            path=normalized,
            okf_version=index_file.okf_version,
            sections=index_file.sections,
            synthesized=False,
        )
    return IndexListing(
        bundle=bundle,
        path=normalized,
        okf_version=None,
        sections=[_synthesize_section(loaded_bundle, normalized)],
        synthesized=True,
    )


def get_section(concept: Concept, heading: str) -> str | None:
    """Extract a top-level (`# Heading`) body section by name, e.g. `"Schema"`.

    Matches case-insensitively. Returns `None` when the concept's body
    has no such heading — these headings are a convention (SPEC §4.2),
    not a requirement, so callers must handle the missing case.
    """
    pattern = re.compile(rf"^#\s+{re.escape(heading)}\s*$", re.MULTILINE | re.IGNORECASE)
    match = pattern.search(concept.body)
    if match is None:
        return None
    rest = concept.body[match.end() :]
    next_heading = re.search(r"^#\s+\S", rest, re.MULTILINE)
    end = match.end() + next_heading.start() if next_heading else len(concept.body)
    return concept.body[match.end() : end].strip()


def _require_bundle(catalog: Catalog, name: str) -> Bundle:
    try:
        return catalog.bundles[name]
    except KeyError:
        raise ValueError(
            f"no bundle named {name!r} loaded in this catalog (loaded: {sorted(catalog.bundles)})"
        ) from None


def _normalize_path(path: str) -> str:
    return path.strip("/")


def _synthesize_section(bundle: Bundle, normalized_path: str) -> IndexSection:
    entries = [
        IndexEntry(
            title=concept.title or concept_id.rsplit("/", 1)[-1],
            link=f"/{concept_id}.md",
            description=concept.description,
        )
        for concept_id, concept in sorted(bundle.concepts.items())
        if posixpath.dirname(concept_id) == normalized_path
    ]
    return IndexSection(heading="Concepts", entries=entries)
