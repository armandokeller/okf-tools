from pathlib import Path

from okf_tools.bundle import Bundle

FIXTURES = Path(__file__).parent / "fixtures"


def test_load_sample_bundle_concepts() -> None:
    bundle = Bundle.load(FIXTURES / "sample_bundle")

    assert set(bundle.concepts) == {
        "minimal",
        "tables/orders",
        "tables/customers",
        "computations/revenue",
        "sub/nested",
    }
    assert bundle.load_errors == []


def test_load_sample_bundle_reserved_files_excluded_from_concepts() -> None:
    bundle = Bundle.load(FIXTURES / "sample_bundle")

    assert "index" not in bundle.concepts
    assert "log" not in bundle.concepts
    assert "sub/index" not in bundle.concepts
    assert "sub/log" not in bundle.concepts


def test_load_sample_bundle_root_index_and_log() -> None:
    bundle = Bundle.load(FIXTURES / "sample_bundle")

    assert bundle.index is not None
    assert bundle.index.okf_version == "0.2"
    assert [s.heading for s in bundle.index.sections] == ["Tables", "Computations"]

    assert bundle.log is not None
    assert len(bundle.log.groups) == 2


def test_load_sample_bundle_nested_index_and_log() -> None:
    bundle = Bundle.load(FIXTURES / "sample_bundle")

    assert "sub" in bundle.indexes
    assert bundle.indexes["sub"].sections[0].entries[0].title == "Nested note"

    assert "sub" in bundle.logs
    assert bundle.logs["sub"].groups[0].entries == ["**Creation**: Added nested note."]


def test_load_sample_bundle_attested_computation() -> None:
    bundle = Bundle.load(FIXTURES / "sample_bundle")

    revenue = bundle.concepts["computations/revenue"]
    assert revenue.type == "Attested Computation"
    assert revenue.runtime == "bigquery"
    assert revenue.parameters[0].name == "start_date"


def test_load_sample_bundle_tolerates_unresolved_link() -> None:
    bundle = Bundle.load(FIXTURES / "sample_bundle")

    orders = bundle.concepts["tables/orders"]
    assert "/tables/missing.md" in orders.body


def test_load_legacy_bundle_fallbacks() -> None:
    bundle = Bundle.load(FIXTURES / "legacy_bundle")

    income = bundle.concepts["income"]
    assert income.generated is None
    assert income.timestamp is not None
    assert [s.resource for s in income.sources] == [
        "https://example.com/finance/handbook",
        "https://example.com/finance/policy",
    ]


def test_load_broken_bundle_collects_load_errors_without_raising() -> None:
    bundle = Bundle.load(FIXTURES / "broken_bundle")

    assert set(bundle.concepts) == {"good"}
    error_paths = {e.path for e in bundle.load_errors}
    assert error_paths == {"bad_yaml.md", "missing_type.md"}
