from pathlib import Path

import pytest

from okf_tools.catalog import Catalog
from okf_tools.integrations.adk import get_adk_tools

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
    return {t.name: t for t in get_adk_tools(catalog)}


def test_get_adk_tools_returns_six_tools_with_snake_case_names(tools: dict[str, object]) -> None:
    assert set(tools) == {
        "list_bundles",
        "get_concept",
        "search_concepts",
        "get_related",
        "get_index",
        "get_section",
    }


def test_get_concept_tool_has_description_from_docstring(tools: dict[str, object]) -> None:
    assert "Fetch a single OKF concept" in tools["get_concept"].description  # type: ignore[attr-defined]


def test_list_bundles_tool_invocation_returns_plain_dict(tools: dict[str, object]) -> None:
    result = tools["list_bundles"].func()  # type: ignore[attr-defined]
    assert isinstance(result, dict)
    names = {b["name"] for b in result["bundles"]}
    assert names == {"sample", "second"}


def test_get_concept_tool_invocation(tools: dict[str, object]) -> None:
    result = tools["get_concept"].func(  # type: ignore[attr-defined]
        bundle="sample", concept_id="tables/orders"
    )
    assert isinstance(result, dict)
    assert result["title"] == "Customer Orders"


def test_get_concept_tool_invocation_unknown_raises(tools: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="no concept"):
        tools["get_concept"].func(  # type: ignore[attr-defined]
            bundle="sample", concept_id="does/not/exist"
        )


def test_search_concepts_tool_invocation_federated(tools: dict[str, object]) -> None:
    result = tools["search_concepts"].func(query="widget")  # type: ignore[attr-defined]
    hits = result["hits"]
    assert [(h["bundle"], h["concept"]["id"]) for h in hits] == [("second", "widgets")]


def test_get_related_tool_invocation(tools: dict[str, object]) -> None:
    result = tools["get_related"].func(  # type: ignore[attr-defined]
        bundle="sample", concept_id="tables/customers", depth=1
    )
    assert [r["concept"]["id"] for r in result["related"]] == ["tables/orders"]


def test_get_index_tool_invocation(tools: dict[str, object]) -> None:
    result = tools["get_index"].func(bundle="sample")  # type: ignore[attr-defined]
    assert [s["heading"] for s in result["sections"]] == ["Tables", "Computations"]


def test_get_section_tool_invocation(tools: dict[str, object]) -> None:
    result = tools["get_section"].func(  # type: ignore[attr-defined]
        bundle="sample", concept_id="tables/orders", heading="Schema"
    )
    assert "order_id" in result["section"]


def test_get_section_tool_invocation_missing_heading_returns_none(tools: dict[str, object]) -> None:
    result = tools["get_section"].func(  # type: ignore[attr-defined]
        bundle="sample", concept_id="tables/orders", heading="Nope"
    )
    assert result["section"] is None
