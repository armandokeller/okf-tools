"""Parsing of OKF frontmatter/body, reserved files, and trust/lifecycle helpers."""

from __future__ import annotations

import re
from datetime import date
from typing import Any

import yaml

from okf_tools.models import (
    Concept,
    Generated,
    IndexEntry,
    IndexFile,
    IndexSection,
    LogDateGroup,
    LogFile,
    Source,
    TrustTier,
    UsageWindow,
)

RESERVED_FILENAMES = {"index.md", "log.md"}

_FRONTMATTER_RE = re.compile(
    r"\A---\r?\n(?P<frontmatter>.*?)\r?\n---\r?\n?(?P<body>.*)\Z", re.DOTALL
)
_CITATIONS_RE = re.compile(r"^#\s*Citations\s*$", re.MULTILINE)
_CITATION_ENTRY_RE = re.compile(r"^[*-]\s*(.+?)\s*$", re.MULTILINE)
_SECTION_HEADING_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_INDEX_ENTRY_RE = re.compile(
    r"^[*-]\s*\[(?P<title>[^\]]+)\]\((?P<link>[^)]+)\)(?:\s*-\s*(?P<description>.*))?$",
    re.MULTILINE,
)
_LOG_DATE_HEADING_RE = re.compile(r"^##\s+(?P<date>\d{4}-\d{2}-\d{2})\s*$", re.MULTILINE)
_LOG_ENTRY_RE = re.compile(r"^[*-]\s*(.+?)\s*$", re.MULTILINE)


class MalformedConceptError(Exception):
    """Raised when a concept file's frontmatter cannot be parsed or lacks `type`."""


def split_frontmatter(text: str) -> tuple[dict[str, Any] | None, str]:
    """Split a markdown file into its YAML frontmatter (if any) and body.

    Returns ``(None, text)`` when the file has no frontmatter block at all.
    Raises `yaml.YAMLError` when a frontmatter block is present but not
    valid YAML, or if it does not parse to a mapping.
    """
    match = _FRONTMATTER_RE.match(text)
    if match is None:
        return None, text
    raw_frontmatter = match.group("frontmatter")
    body = match.group("body")
    loaded = yaml.safe_load(raw_frontmatter)
    if loaded is None:
        return {}, body
    if not isinstance(loaded, dict):
        kind = type(loaded).__name__
        raise yaml.YAMLError(f"frontmatter did not parse to a mapping (got {kind})")
    return loaded, body


def extract_legacy_citations(body: str) -> list[Source]:
    """Parse a legacy v0.1 `# Citations` URL list into synthetic `Source` entries (SPEC §13.1)."""
    heading_match = _CITATIONS_RE.search(body)
    if heading_match is None:
        return []
    section = body[heading_match.end() :]
    next_heading = re.search(r"^#\s", section, re.MULTILINE)
    if next_heading is not None:
        section = section[: next_heading.start()]
    sources: list[Source] = []
    for line in section.splitlines():
        line = line.strip()
        entry_match = _CITATION_ENTRY_RE.match(line)
        if entry_match:
            sources.append(Source(resource=entry_match.group(1)))
    return sources


def parse_concept(concept_id: str, text: str) -> Concept:
    """Parse a single concept file's raw text into a `Concept`.

    Raises `MalformedConceptError` when the frontmatter is missing, invalid
    YAML, not a mapping, or lacks a non-empty `type` (SPEC §11) — callers
    (`Bundle.load`) are expected to catch this per file, not let it abort
    the whole bundle load.
    """
    try:
        frontmatter, body = split_frontmatter(text)
    except yaml.YAMLError as exc:
        raise MalformedConceptError(f"invalid YAML frontmatter: {exc}") from exc

    if frontmatter is None:
        raise MalformedConceptError("missing frontmatter block")

    data = dict(frontmatter)
    type_ = data.pop("type", None)
    if not type_ or not isinstance(type_, str):
        raise MalformedConceptError("missing or empty required `type` field")

    sources_raw = data.pop("sources", None) or []
    sources = [Source(**s) for s in sources_raw]
    if not sources:
        sources = extract_legacy_citations(body)

    usage_window_raw = data.pop("usage_window", None)
    usage_window = UsageWindow(**usage_window_raw) if usage_window_raw else None

    generated_raw = data.pop("generated", None)
    generated = Generated(**generated_raw) if generated_raw else None

    verified_raw = data.pop("verified", None) or []

    executor_raw = data.pop("executor", None)
    attester_raw = data.pop("attester", None)
    parameters_raw = data.pop("parameters", None) or []

    known_kwargs: dict[str, Any] = {
        "title": data.pop("title", None),
        "description": data.pop("description", None),
        "resource": data.pop("resource", None),
        "tags": data.pop("tags", None) or [],
        "sources": sources,
        "usage_window": usage_window,
        "generated": generated,
        "verified": verified_raw,
        "status": data.pop("status", "stable"),
        "stale_after": data.pop("stale_after", None),
        "runtime": data.pop("runtime", None),
        "parameters": parameters_raw,
        "computation": data.pop("computation", None),
        "executor": executor_raw,
        "attester": attester_raw,
        "timestamp": data.pop("timestamp", None),
    }

    return Concept(id=concept_id, type=type_, extra=data, body=body, **known_kwargs)


def trust_tier(concept: Concept) -> TrustTier:
    """Derive a concept's trust tier from `verified`, lowest to highest (SPEC §5.3)."""
    if not concept.verified:
        return "unverified"
    if any(v.by.startswith("human:") for v in concept.verified):
        return "human-reviewed"
    return "machine-confirmed"


def is_stale(concept: Concept, today: date | None = None) -> bool:
    """A concept is stale once `today >= stale_after` (SPEC §5.5)."""
    if concept.stale_after is None:
        return False
    reference = today if today is not None else date.today()
    return reference >= concept.stale_after


def parse_index_file(path: str, text: str) -> IndexFile:
    """Parse an `index.md`: optional root `okf_version` frontmatter, then sections (SPEC §8)."""
    frontmatter, body = split_frontmatter(text)
    okf_version = None
    if frontmatter:
        version = frontmatter.get("okf_version")
        okf_version = str(version) if version is not None else None

    headings = list(_SECTION_HEADING_RE.finditer(body))
    sections: list[IndexSection] = []
    for i, heading_match in enumerate(headings):
        heading = heading_match.group(1)
        start = heading_match.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(body)
        section_body = body[start:end]
        entries = [
            IndexEntry(
                title=m.group("title"),
                link=m.group("link"),
                description=m.group("description") or None,
            )
            for m in _INDEX_ENTRY_RE.finditer(section_body)
        ]
        sections.append(IndexSection(heading=heading, entries=entries))

    return IndexFile(path=path, okf_version=okf_version, sections=sections)


def parse_log_file(path: str, text: str) -> LogFile:
    """Parse a `log.md`: date-grouped entries under `## YYYY-MM-DD` headings (SPEC §9)."""
    headings = list(_LOG_DATE_HEADING_RE.finditer(text))
    groups: list[LogDateGroup] = []
    for i, heading_match in enumerate(headings):
        group_date = date.fromisoformat(heading_match.group("date"))
        start = heading_match.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        group_body = text[start:end]
        entries = [m.group(1) for m in _LOG_ENTRY_RE.finditer(group_body)]
        groups.append(LogDateGroup(date=group_date, entries=entries))
    return LogFile(path=path, groups=groups)
