"""Lightweight directed graph over the markdown links between a bundle's concepts."""

from __future__ import annotations

import posixpath
import re
from collections import deque

from okf_tools.bundle import Bundle

_LINK_RE = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)]+)\)")


def extract_links(concept_id: str, body: str) -> tuple[set[str], set[str]]:
    """Extract markdown links from a concept body (SPEC §6.1).

    Returns `(internal_candidate_ids, external_urls)`. An internal
    candidate is only a *shape* match (bundle-relative or relative path
    ending in `.md`, resolved against `concept_id`'s directory) — whether
    it actually names an existing concept is for the caller to decide,
    since this function has no knowledge of the bundle's concepts.
    Directory links (ending in `/`) and non-`.md` targets are ignored:
    they cannot resolve to a concept.
    """
    internal: set[str] = set()
    external: set[str] = set()
    for _text, raw_target in _LINK_RE.findall(body):
        target = raw_target.split(maxsplit=1)[0] if raw_target.split() else raw_target
        target = target.split("#", 1)[0].strip()
        if not target:
            continue
        if target.startswith(("http://", "https://")):
            external.add(target)
            continue
        if target.endswith("/") or not target.endswith(".md"):
            continue
        internal.add(_resolve_relative(concept_id, target))
    return internal, external


def _resolve_relative(concept_id: str, target: str) -> str:
    """Resolve a link target to a candidate concept id (SPEC §6.1, §6.2)."""
    if target.startswith("/"):
        joined = target[1:]
    else:
        source_dir = posixpath.dirname(concept_id)
        joined = posixpath.join(source_dir, target) if source_dir else target
    joined = posixpath.normpath(joined)
    if joined.endswith(".md"):
        joined = joined[: -len(".md")]
    return joined


class Graph:
    """A directed graph of concept-to-concept links within a single bundle.

    Broken links are tolerated per SPEC §6.1: a link whose target does not
    exist in the bundle is recorded in `unresolved` rather than raising or
    being silently dropped.
    """

    def __init__(
        self,
        edges: dict[str, set[str]],
        unresolved: dict[str, set[str]],
        external: dict[str, set[str]],
    ) -> None:
        self._edges = edges
        self._reverse = _reverse_of(edges)
        self.unresolved = unresolved
        self.external = external

    @classmethod
    def build(cls, bundle: Bundle) -> Graph:
        """Build a `Graph` by extracting and resolving links from every concept in `bundle`."""
        edges: dict[str, set[str]] = {}
        unresolved: dict[str, set[str]] = {}
        external: dict[str, set[str]] = {}
        for concept_id, concept in bundle.concepts.items():
            internal_candidates, external_targets = extract_links(concept_id, concept.body)
            resolved = {t for t in internal_candidates if t in bundle.concepts}
            broken = internal_candidates - resolved
            if resolved:
                edges[concept_id] = resolved
            if broken:
                unresolved[concept_id] = broken
            if external_targets:
                external[concept_id] = external_targets
        return cls(edges, unresolved, external)

    def neighbors(self, concept_id: str) -> set[str]:
        """Concepts `concept_id` links to."""
        return set(self._edges.get(concept_id, set()))

    def backlinks(self, concept_id: str) -> set[str]:
        """Concepts that link to `concept_id` ("cited by", SPEC's viewer feature)."""
        return set(self._reverse.get(concept_id, set()))

    def bfs(self, start: str, max_depth: int = 1) -> dict[str, int]:
        """Breadth-first expansion from `start`, following edges in both directions.

        Returns a mapping of reached concept id to hop distance from
        `start` (0 for `start` itself). Undirected on purpose: this serves
        the "give me this concept plus N hops of surrounding context"
        pattern, where an agent cares about relatedness, not link
        direction.
        """
        distances: dict[str, int] = {start: 0}
        queue: deque[str] = deque([start])
        while queue:
            current = queue.popleft()
            current_depth = distances[current]
            if current_depth >= max_depth:
                continue
            for neighbor in self.neighbors(current) | self.backlinks(current):
                if neighbor not in distances:
                    distances[neighbor] = current_depth + 1
                    queue.append(neighbor)
        return distances


def _reverse_of(edges: dict[str, set[str]]) -> dict[str, set[str]]:
    reverse: dict[str, set[str]] = {}
    for source, targets in edges.items():
        for target in targets:
            reverse.setdefault(target, set()).add(source)
    return reverse
