"""Registry for loading and querying across multiple named OKF bundles at once."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

from okf_tools.bundle import Bundle
from okf_tools.graph import Graph

T = TypeVar("T")


class Catalog:
    """Registers bundles by name, loads them, and federates queries across them."""

    def __init__(self) -> None:
        self._paths: dict[str, Path] = {}
        self.bundles: dict[str, Bundle] = {}
        self.graphs: dict[str, Graph] = {}

    def register(self, name: str, path: str | Path) -> None:
        """Register a bundle by name without loading it yet."""
        self._paths[name] = Path(path)

    def load_all(self) -> None:
        """Load (or reload) every registered bundle and build its `Graph`."""
        for name, path in self._paths.items():
            bundle = Bundle.load(path)
            self.bundles[name] = bundle
            self.graphs[name] = Graph.build(bundle)

    def get(self, name: str) -> Bundle:
        """The loaded `Bundle` registered under `name`."""
        return self.bundles[name]

    def get_graph(self, name: str) -> Graph:
        """The `Graph` built for the bundle registered under `name`."""
        return self.graphs[name]

    @property
    def names(self) -> list[str]:
        """Names of every registered bundle, loaded or not."""
        return list(self._paths)

    def query_all(
        self, fn: Callable[..., list[T]], *args: Any, **kwargs: Any
    ) -> dict[str, list[T]]:
        """Run `fn(bundle, *args, **kwargs)` against every loaded bundle.

        Returns a mapping of bundle name to that bundle's results, so a
        caller can tell which catalog a hit came from.
        """
        return {name: fn(bundle, *args, **kwargs) for name, bundle in self.bundles.items()}
