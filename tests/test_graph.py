from pathlib import Path

from okf_tools.bundle import Bundle
from okf_tools.graph import Graph, extract_links

FIXTURES = Path(__file__).parent / "fixtures"


def test_extract_links_resolves_absolute_and_ignores_external_and_directory() -> None:
    body = (
        "See [customers](/tables/customers.md) and "
        "[docs](https://example.com/docs) and "
        "[a dir](/tables/) and "
        "[an image target](/tables/logo.png)."
    )
    internal, external = extract_links("tables/orders", body)
    assert internal == {"tables/customers"}
    assert external == {"https://example.com/docs"}


def test_extract_links_resolves_relative_paths() -> None:
    internal, _ = extract_links("sub/nested", "See [sibling](../tables/orders.md).")
    assert internal == {"tables/orders"}

    internal, _ = extract_links("tables/orders", "See [sibling](./customers.md).")
    assert internal == {"tables/customers"}


def test_extract_links_ignores_footnote_definitions() -> None:
    body = "A claim.[^src]\n\n[^src]: Some source, not a link.\n"
    internal, external = extract_links("x", body)
    assert internal == set()
    assert external == set()


def test_graph_build_from_sample_bundle() -> None:
    bundle = Bundle.load(FIXTURES / "sample_bundle")
    graph = Graph.build(bundle)

    assert graph.neighbors("tables/orders") == {"tables/customers"}
    assert graph.neighbors("tables/customers") == set()
    assert graph.unresolved["tables/orders"] == {"tables/missing"}


def test_graph_backlinks() -> None:
    bundle = Bundle.load(FIXTURES / "sample_bundle")
    graph = Graph.build(bundle)

    assert graph.backlinks("tables/customers") == {"tables/orders"}
    assert graph.backlinks("tables/orders") == set()


def test_graph_bfs_is_undirected_and_depth_limited() -> None:
    bundle = Bundle.load(FIXTURES / "sample_bundle")
    graph = Graph.build(bundle)

    assert graph.bfs("tables/customers", max_depth=1) == {
        "tables/customers": 0,
        "tables/orders": 1,
    }
    assert graph.bfs("tables/customers", max_depth=0) == {"tables/customers": 0}


def test_graph_bfs_unknown_start_returns_only_itself() -> None:
    bundle = Bundle.load(FIXTURES / "sample_bundle")
    graph = Graph.build(bundle)

    assert graph.bfs("does/not/exist", max_depth=2) == {"does/not/exist": 0}
