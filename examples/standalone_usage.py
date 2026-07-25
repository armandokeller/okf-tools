"""Demonstrates using okf-tools as plain Python functions, no agent framework required.

Run from the repository root:

    uv run python examples/standalone_usage.py
"""

from pathlib import Path

from okf_tools.api import (
    get_concept,
    get_index,
    get_related,
    get_section,
    list_bundles,
    search_concepts,
)
from okf_tools.catalog import Catalog

EXAMPLE_BUNDLE = Path(__file__).parent / "data" / "sample_bundle"


def main() -> None:
    catalog = Catalog()
    catalog.register("demo", EXAMPLE_BUNDLE)
    catalog.load_all()

    print("Bundles:")
    for summary in list_bundles(catalog):
        print(f"  {summary.name}: {summary.concept_count} concepts (root={summary.root})")

    print("\nSearching for 'customer':")
    for hit in search_concepts(catalog, "customer"):
        print(f"  [{hit.bundle}] {hit.concept.id} -- {hit.concept.title}")

    print("\nFetching tables/orders directly:")
    orders = get_concept(catalog, "demo", "tables/orders")
    print(f"  title={orders.title!r} tags={orders.tags}")

    print("\nSchema section of tables/orders:")
    print(get_section(orders, "Schema"))

    print("\nConcepts related to tables/customers (depth=1):")
    related = get_related(catalog, "demo", "tables/customers", depth=1)
    for r in related.related:
        print(f"  {r.concept.id} (distance={r.distance})")

    print("\nRoot index listing:")
    index = get_index(catalog, "demo")
    for section in index.sections:
        print(f"  # {section.heading}")
        for entry in section.entries:
            print(f"    - {entry.title} -> {entry.link}")


if __name__ == "__main__":
    main()
