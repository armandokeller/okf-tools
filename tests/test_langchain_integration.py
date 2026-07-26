from pathlib import Path

import pytest

from okf_tools.catalog import Catalog
from okf_tools.integrations.langchain import get_langchain_tools

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def catalog() -> Catalog:
    cat = Catalog()
    cat.register("sample", FIXTURES / "sample_bundle")
    cat.register("second", FIXTURES / "second_bundle")
    cat.load_all()
    return cat


@pytest.fixture
def tools(catalog: Catalog) -> dict[str, object]:
    return {t.name: t for t in get_langchain_tools(catalog)}


def test_get_langchain_tools_returns_six_tools_with_snake_case_names(
    tools: dict[str, object],
) -> None:
    assert set(tools) == {
        "list_bundles",
        "get_concept",
        "search_concepts",
        "get_related",
        "get_index",
        "get_section",
    }


def test_get_concept_tool_schema_has_expected_args(tools: dict[str, object]) -> None:
    schema = tools["get_concept"].args  # type: ignore[attr-defined]
    assert set(schema) == {"bundle", "concept_id"}


def test_list_bundles_tool_invocation(tools: dict[str, object]) -> None:
    result = tools["list_bundles"].invoke({})  # type: ignore[attr-defined]
    names = {summary.name for summary in result}
    assert names == {"sample", "second"}


def test_get_concept_tool_invocation(tools: dict[str, object]) -> None:
    result = tools["get_concept"].invoke(  # type: ignore[attr-defined]
        {"bundle": "sample", "concept_id": "tables/orders"}
    )
    assert result.title == "Customer Orders"


def test_get_concept_tool_invocation_unknown_raises(tools: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="no concept"):
        tools["get_concept"].invoke(  # type: ignore[attr-defined]
            {"bundle": "sample", "concept_id": "does/not/exist"}
        )


def test_search_concepts_tool_invocation_federated(tools: dict[str, object]) -> None:
    result = tools["search_concepts"].invoke({"query": "widget"})  # type: ignore[attr-defined]
    assert [(hit.bundle, hit.concept.id) for hit in result] == [("second", "widgets")]


def test_get_related_tool_invocation(tools: dict[str, object]) -> None:
    result = tools["get_related"].invoke(  # type: ignore[attr-defined]
        {"bundle": "sample", "concept_id": "tables/customers", "depth": 1}
    )
    assert [r.concept.id for r in result.related] == ["tables/orders"]


def test_get_index_tool_invocation(tools: dict[str, object]) -> None:
    result = tools["get_index"].invoke({"bundle": "sample"})  # type: ignore[attr-defined]
    assert [s.heading for s in result.sections] == ["Tables", "Computations"]


def test_get_section_tool_invocation(tools: dict[str, object]) -> None:
    result = tools["get_section"].invoke(  # type: ignore[attr-defined]
        {"bundle": "sample", "concept_id": "tables/orders", "heading": "Schema"}
    )
    assert "order_id" in result


def test_get_section_tool_invocation_missing_heading_returns_none(tools: dict[str, object]) -> None:
    result = tools["get_section"].invoke(  # type: ignore[attr-defined]
        {"bundle": "sample", "concept_id": "tables/orders", "heading": "Nope"}
    )
    assert result is None
