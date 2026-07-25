from datetime import date
from pathlib import Path

from okf_tools.bundle import Bundle
from okf_tools.queries import filter_concepts, search_concepts

FIXTURES = Path(__file__).parent / "fixtures"


def _ids(concepts: list) -> set[str]:
    return {c.id for c in concepts}


def test_filter_by_type() -> None:
    bundle = Bundle.load(FIXTURES / "sample_bundle")
    result = filter_concepts(bundle, concept_type="BigQuery Table")
    assert _ids(result) == {"tables/orders", "tables/customers"}


def test_filter_by_tags_any_match() -> None:
    bundle = Bundle.load(FIXTURES / "sample_bundle")
    result = filter_concepts(bundle, tags=["sales"])
    assert _ids(result) == {"tables/orders"}


def test_filter_by_trust_tier() -> None:
    bundle = Bundle.load(FIXTURES / "sample_bundle")
    assert _ids(filter_concepts(bundle, trust="human-reviewed")) == {"tables/orders"}
    assert _ids(filter_concepts(bundle, trust="unverified")) == {
        "tables/customers",
        "minimal",
        "computations/revenue",
        "sub/nested",
    }


def test_filter_by_status_default_stable() -> None:
    bundle = Bundle.load(FIXTURES / "sample_bundle")
    result = filter_concepts(bundle, status="stable")
    assert len(result) == len(bundle.concepts)


def test_filter_by_staleness() -> None:
    bundle = Bundle.load(FIXTURES / "sample_bundle")
    result = filter_concepts(bundle, stale=True, today=date(2027, 1, 1))
    assert _ids(result) == {"tables/orders"}

    result = filter_concepts(bundle, stale=True, today=date(2026, 1, 1))
    assert result == []


def test_filter_combines_criteria_with_and_semantics() -> None:
    bundle = Bundle.load(FIXTURES / "sample_bundle")
    result = filter_concepts(bundle, concept_type="BigQuery Table", tags=["sales"])
    assert _ids(result) == {"tables/orders"}


def test_search_matches_title_and_body_case_insensitively() -> None:
    bundle = Bundle.load(FIXTURES / "sample_bundle")
    result = search_concepts(bundle, "CUSTOMER")
    assert _ids(result) == {"tables/orders", "tables/customers"}


def test_search_with_additional_filter() -> None:
    bundle = Bundle.load(FIXTURES / "sample_bundle")
    result = search_concepts(bundle, "customer", tags=["sales"])
    assert _ids(result) == {"tables/orders"}


def test_search_no_match_returns_empty() -> None:
    bundle = Bundle.load(FIXTURES / "sample_bundle")
    assert search_concepts(bundle, "nonexistent_keyword_xyz") == []
