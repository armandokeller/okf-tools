from pathlib import Path

import pytest

from okf_tools.api import (
    get_concept,
    get_index,
    get_related,
    get_section,
    list_bundles,
    search_concepts,
)
from okf_tools.catalog import Catalog

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def catalog() -> Catalog:
    cat = Catalog()
    cat.register("sample", FIXTURES / "sample_bundle")
    cat.register("second", FIXTURES / "second_bundle")
    cat.load_all()
    return cat


def test_list_bundles(catalog: Catalog) -> None:
    summaries = {s.name: s for s in list_bundles(catalog)}
    assert summaries["sample"].concept_count == 5
    assert summaries["sample"].okf_version == "0.2"
    assert summaries["second"].concept_count == 1
    assert summaries["second"].okf_version is None


def test_get_concept(catalog: Catalog) -> None:
    concept = get_concept(catalog, "sample", "tables/orders")
    assert concept.title == "Customer Orders"


def test_get_concept_unknown_bundle_raises(catalog: Catalog) -> None:
    with pytest.raises(ValueError, match="no bundle named 'nope'"):
        get_concept(catalog, "nope", "tables/orders")


def test_get_concept_unknown_id_raises(catalog: Catalog) -> None:
    with pytest.raises(ValueError, match="no concept 'does/not/exist'"):
        get_concept(catalog, "sample", "does/not/exist")


def test_search_concepts_restricted_to_one_bundle(catalog: Catalog) -> None:
    hits = search_concepts(catalog, "customer", bundle="sample")
    assert {h.concept.id for h in hits} == {"tables/orders", "tables/customers"}
    assert all(h.bundle == "sample" for h in hits)


def test_search_concepts_across_all_bundles(catalog: Catalog) -> None:
    hits = search_concepts(catalog, "widget")
    assert [(h.bundle, h.concept.id) for h in hits] == [("second", "widgets")]


def test_search_concepts_with_type_and_tags_filters(catalog: Catalog) -> None:
    hits = search_concepts(catalog, "order", bundle="sample", concept_type="BigQuery Table")
    assert {h.concept.id for h in hits} == {"tables/orders"}


def test_get_related_includes_outgoing_and_backlinks(catalog: Catalog) -> None:
    result = get_related(catalog, "sample", "tables/customers", depth=1)
    assert result.concept.id == "tables/customers"
    assert [r.concept.id for r in result.related] == ["tables/orders"]
    assert result.related[0].distance == 1


def test_get_related_depth_zero_returns_no_related(catalog: Catalog) -> None:
    result = get_related(catalog, "sample", "tables/orders", depth=0)
    assert result.related == []


def test_get_index_returns_existing_index_md(catalog: Catalog) -> None:
    listing = get_index(catalog, "sample", "/")
    assert listing.synthesized is False
    assert listing.okf_version == "0.2"
    assert [s.heading for s in listing.sections] == ["Tables", "Computations"]


def test_get_index_synthesizes_when_missing(catalog: Catalog) -> None:
    listing = get_index(catalog, "sample", "tables")
    assert listing.synthesized is True
    assert listing.okf_version is None
    entries = listing.sections[0].entries
    assert {e.link for e in entries} == {"/tables/orders.md", "/tables/customers.md"}


def test_get_section_found_case_insensitively(catalog: Catalog) -> None:
    concept = get_concept(catalog, "sample", "tables/orders")
    section = get_section(concept, "schema")
    assert section is not None
    assert "order_id" in section


def test_get_section_not_found_returns_none(catalog: Catalog) -> None:
    concept = get_concept(catalog, "sample", "tables/orders")
    assert get_section(concept, "Nonexistent Heading") is None


def test_get_section_stops_at_next_heading(catalog: Catalog) -> None:
    concept = get_concept(catalog, "sample", "tables/orders")
    section = get_section(concept, "Schema")
    assert section is not None
    assert "Notes" not in section
    assert "missing.md" not in section
