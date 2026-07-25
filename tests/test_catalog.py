from pathlib import Path

from okf_tools.catalog import Catalog
from okf_tools.queries import filter_concepts, search_concepts

FIXTURES = Path(__file__).parent / "fixtures"


def _make_catalog() -> Catalog:
    catalog = Catalog()
    catalog.register("sample", FIXTURES / "sample_bundle")
    catalog.register("second", FIXTURES / "second_bundle")
    catalog.load_all()
    return catalog


def test_register_and_load_all() -> None:
    catalog = _make_catalog()
    assert set(catalog.names) == {"sample", "second"}
    assert len(catalog.get("sample").concepts) == 5
    assert len(catalog.get("second").concepts) == 1
    assert catalog.get_graph("sample") is not None


def test_query_all_search_federates_across_bundles() -> None:
    catalog = _make_catalog()
    results = catalog.query_all(search_concepts, "widget")
    assert {c.id for c in results["sample"]} == set()
    assert {c.id for c in results["second"]} == {"widgets"}


def test_query_all_filter_tags_by_bundle_name() -> None:
    catalog = _make_catalog()
    results = catalog.query_all(filter_concepts, concept_type="Note")
    assert {c.id for c in results["sample"]} == {"minimal", "sub/nested"}
    assert {c.id for c in results["second"]} == {"widgets"}
