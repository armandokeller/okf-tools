"""Filtering and search over a bundle's concepts."""

from __future__ import annotations

from datetime import date

from okf_tools.bundle import Bundle
from okf_tools.models import Concept, TrustTier
from okf_tools.parsing import is_stale, trust_tier


def filter_concepts(
    bundle: Bundle,
    *,
    concept_type: str | None = None,
    tags: list[str] | None = None,
    status: str | None = None,
    trust: TrustTier | None = None,
    stale: bool | None = None,
    today: date | None = None,
) -> list[Concept]:
    """Filter a bundle's concepts by any combination of the given criteria (AND semantics).

    `tags` matches a concept if it carries at least one of the given tags.
    """
    results = []
    for concept in bundle.concepts.values():
        if concept_type is not None and concept.type != concept_type:
            continue
        if tags is not None and not (set(tags) & set(concept.tags)):
            continue
        if status is not None and concept.status != status:
            continue
        if trust is not None and trust_tier(concept) != trust:
            continue
        if stale is not None and is_stale(concept, today=today) != stale:
            continue
        results.append(concept)
    return results


def search_concepts(
    bundle: Bundle,
    query: str,
    *,
    concept_type: str | None = None,
    tags: list[str] | None = None,
    status: str | None = None,
    trust: TrustTier | None = None,
    stale: bool | None = None,
    today: date | None = None,
) -> list[Concept]:
    """Case-insensitive substring search over title/description/body, plus optional filters.

    v1 search is keyword/substring only; semantic search is out of scope
    (see the project's backlog).
    """
    needle = query.lower()
    candidates = filter_concepts(
        bundle,
        concept_type=concept_type,
        tags=tags,
        status=status,
        trust=trust,
        stale=stale,
        today=today,
    )
    return [c for c in candidates if _matches(c, needle)]


def _matches(concept: Concept, needle: str) -> bool:
    haystack = " ".join(part for part in (concept.title, concept.description, concept.body) if part)
    return needle in haystack.lower()
