from datetime import date

import pytest
from pydantic import ValidationError

from okf_tools.models import Source
from okf_tools.parsing import (
    MalformedConceptError,
    extract_legacy_citations,
    is_stale,
    parse_concept,
    parse_index_file,
    parse_log_file,
    split_frontmatter,
    trust_tier,
)


def test_split_frontmatter_returns_none_when_absent() -> None:
    frontmatter, body = split_frontmatter("just a plain markdown file\n")
    assert frontmatter is None
    assert body == "just a plain markdown file\n"


def test_split_frontmatter_parses_block_and_body() -> None:
    text = "---\ntype: Note\ntitle: Hi\n---\nbody text\n"
    frontmatter, body = split_frontmatter(text)
    assert frontmatter == {"type": "Note", "title": "Hi"}
    assert body == "body text\n"


def test_parse_concept_minimal() -> None:
    concept = parse_concept("minimal", "---\ntype: Note\n---\n\nhello\n")
    assert concept.id == "minimal"
    assert concept.type == "Note"
    assert concept.title is None
    assert concept.status == "stable"
    assert concept.tags == []
    assert concept.sources == []
    assert concept.verified == []


def test_parse_concept_missing_frontmatter_raises() -> None:
    with pytest.raises(MalformedConceptError):
        parse_concept("no_frontmatter", "just text, no frontmatter at all\n")


def test_parse_concept_missing_type_raises() -> None:
    with pytest.raises(MalformedConceptError):
        parse_concept("missing_type", "---\ntitle: No type\n---\nbody\n")


def test_parse_concept_bad_yaml_raises_malformed() -> None:
    with pytest.raises(MalformedConceptError):
        parse_concept("bad_yaml", "---\ntype: [unterminated\n---\nbody\n")


def test_parse_concept_full_v02_families() -> None:
    text = """---
type: BigQuery Table
title: Orders
description: One row per order.
resource: https://example.com/orders
tags: [sales, orders]
generated: { by: agent/v1, at: 2026-01-10T12:00:00Z }
verified: { by: human:tester, at: 2026-01-11T09:00:00Z }
status: stable
stale_after: 2026-12-31
sources:
  - id: handbook
    resource: https://example.com/handbook
    author: human:tester
    usage_count: 10
    last_modified: 2026-01-01
usage_window: { from: 2026-01-01, to: 2026-01-31 }
---

body
"""
    concept = parse_concept("orders", text)
    assert concept.title == "Orders"
    assert concept.tags == ["sales", "orders"]
    assert concept.generated is not None
    assert concept.generated.by == "agent/v1"
    assert len(concept.verified) == 1
    assert concept.verified[0].by == "human:tester"
    assert concept.stale_after == date(2026, 12, 31)
    assert len(concept.sources) == 1
    assert concept.sources[0].resource == "https://example.com/handbook"
    assert concept.usage_window is not None
    assert concept.usage_window.from_ == date(2026, 1, 1)


def test_parse_concept_verified_bare_mapping_becomes_list() -> None:
    text = "---\ntype: Note\nverified: { by: human:x, at: 2026-01-01T00:00:00Z }\n---\nbody\n"
    concept = parse_concept("x", text)
    assert isinstance(concept.verified, list)
    assert len(concept.verified) == 1
    assert concept.verified[0].by == "human:x"


def test_parse_concept_attested_computation_fields() -> None:
    text = """---
type: Attested Computation
runtime: bigquery
parameters:
  - { name: year, type: integer, required: true }
executor:
  resource: references/skills/run-on-bq.md
  receipt: [job_id, executed_sql]
attester:
  resource: references/attesters/revenue.py
---

# Computation

    SELECT 1
"""
    concept = parse_concept("computations/revenue", text)
    assert concept.runtime == "bigquery"
    assert concept.parameters[0].name == "year"
    assert concept.parameters[0].required is True
    assert concept.executor is not None
    assert concept.executor.receipt == ["job_id", "executed_sql"]
    assert concept.attester is not None
    assert concept.attester.resource == "references/attesters/revenue.py"


def test_parse_concept_legacy_timestamp_and_citations_fallback() -> None:
    text = """---
type: Metric
timestamp: '2026-01-01T00:00:00+00:00'
---

# Citations
- https://example.com/a
- https://example.com/b
"""
    concept = parse_concept("legacy", text)
    assert concept.generated is None
    assert concept.timestamp is not None
    assert concept.timestamp.year == 2026
    assert [s.resource for s in concept.sources] == [
        "https://example.com/a",
        "https://example.com/b",
    ]


def test_parse_concept_explicit_sources_take_precedence_over_citations() -> None:
    text = """---
type: Metric
sources:
  - resource: https://example.com/real-source
---

# Citations
- https://example.com/should-be-ignored
"""
    concept = parse_concept("x", text)
    assert [s.resource for s in concept.sources] == ["https://example.com/real-source"]


def test_parse_concept_preserves_unknown_extra_keys() -> None:
    text = "---\ntype: Note\ncustom_field: 42\n---\nbody\n"
    concept = parse_concept("x", text)
    assert concept.extra == {"custom_field": 42}


def test_parse_concept_unresolved_link_in_body_does_not_raise() -> None:
    text = "---\ntype: Note\n---\nSee [missing](/tables/missing.md).\n"
    concept = parse_concept("x", text)
    assert "/tables/missing.md" in concept.body


def test_extract_legacy_citations_no_heading_returns_empty() -> None:
    assert extract_legacy_citations("no citations heading here") == []


def test_trust_tier_unverified() -> None:
    concept = parse_concept("x", "---\ntype: Note\n---\nbody\n")
    assert trust_tier(concept) == "unverified"


def test_trust_tier_machine_confirmed() -> None:
    text = (
        "---\ntype: Note\nverified: { by: process:nightly, at: 2026-01-01T00:00:00Z }\n---\nbody\n"
    )
    concept = parse_concept("x", text)
    assert trust_tier(concept) == "machine-confirmed"


def test_trust_tier_human_reviewed() -> None:
    text = (
        "---\ntype: Note\n"
        "verified:\n"
        "  - { by: process:nightly, at: 2026-01-01T00:00:00Z }\n"
        "  - { by: human:ahormati, at: 2026-01-02T00:00:00Z }\n"
        "---\nbody\n"
    )
    concept = parse_concept("x", text)
    assert trust_tier(concept) == "human-reviewed"


def test_is_stale() -> None:
    text = "---\ntype: Note\nstale_after: 2026-06-01\n---\nbody\n"
    concept = parse_concept("x", text)
    assert is_stale(concept, today=date(2026, 5, 1)) is False
    assert is_stale(concept, today=date(2026, 6, 1)) is True
    assert is_stale(concept, today=date(2026, 7, 1)) is True


def test_is_stale_absent_stale_after_is_never_stale() -> None:
    concept = parse_concept("x", "---\ntype: Note\n---\nbody\n")
    assert is_stale(concept, today=date(2099, 1, 1)) is False


def test_source_requires_resource() -> None:
    with pytest.raises(ValidationError):
        Source()  # type: ignore[call-arg]


def test_parse_index_file_root_with_okf_version() -> None:
    text = """---
okf_version: "0.2"
---

# Tables

* [Orders](/tables/orders.md) - Order rows.
* [Customers](/tables/customers.md) - Customer rows.

# Computations

* [Revenue](/computations/revenue.md) - Revenue figure.
"""
    index = parse_index_file("", text)
    assert index.okf_version == "0.2"
    assert [s.heading for s in index.sections] == ["Tables", "Computations"]
    assert index.sections[0].entries[0].title == "Orders"
    assert index.sections[0].entries[0].link == "/tables/orders.md"
    assert index.sections[0].entries[0].description == "Order rows."


def test_parse_index_file_without_frontmatter() -> None:
    text = "# Notes\n\n* [A note](note.md) - A note.\n"
    index = parse_index_file("sub", text)
    assert index.okf_version is None
    assert index.path == "sub"
    assert index.sections[0].entries[0].link == "note.md"


def test_parse_log_file_groups_entries_by_date() -> None:
    text = """# Directory Update Log

## 2026-05-22
* **Update**: Added a table reference.
* **Creation**: Established structure.

## 2026-05-15
* **Initialization**: Created foundational directory structure.
"""
    log = parse_log_file("", text)
    assert [g.date.isoformat() for g in log.groups] == ["2026-05-22", "2026-05-15"]
    assert log.groups[0].entries == [
        "**Update**: Added a table reference.",
        "**Creation**: Established structure.",
    ]
    assert log.groups[1].entries == [
        "**Initialization**: Created foundational directory structure."
    ]
