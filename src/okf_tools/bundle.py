"""Loading a whole OKF bundle from a local directory tree."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

from okf_tools.models import Concept, IndexFile, LoadError, LogFile
from okf_tools.parsing import MalformedConceptError, parse_concept, parse_index_file, parse_log_file


class Bundle(BaseModel):
    """A loaded OKF bundle: its concepts, index/log files, and any load errors.

    `indexes`/`logs` are keyed by the directory's path relative to the
    bundle root (`""` for the root itself), since `index.md`/`log.md` may
    appear at any level (SPEC §8, §9), not just the root.
    """

    root: str
    concepts: dict[str, Concept] = Field(default_factory=dict)
    indexes: dict[str, IndexFile] = Field(default_factory=dict)
    logs: dict[str, LogFile] = Field(default_factory=dict)
    load_errors: list[LoadError] = Field(default_factory=list)

    @property
    def index(self) -> IndexFile | None:
        """The bundle-root `index.md`, if present."""
        return self.indexes.get("")

    @property
    def log(self) -> LogFile | None:
        """The bundle-root `log.md`, if present."""
        return self.logs.get("")

    @classmethod
    def load(cls, root: str | Path) -> Bundle:
        """Walk `root` and parse every markdown file into a `Bundle`.

        A single malformed concept file never aborts the load: it is
        recorded in `load_errors` and skipped, per SPEC §11's permissive
        conformance philosophy.
        """
        root_path = Path(root)
        concepts: dict[str, Concept] = {}
        indexes: dict[str, IndexFile] = {}
        logs: dict[str, LogFile] = {}
        load_errors: list[LoadError] = []

        for file_path in sorted(root_path.rglob("*.md")):
            rel_path = file_path.relative_to(root_path)
            dir_rel = (
                ""
                if file_path.parent == root_path
                else file_path.parent.relative_to(root_path).as_posix()
            )
            text = file_path.read_text(encoding="utf-8")

            if file_path.name == "index.md":
                indexes[dir_rel] = parse_index_file(dir_rel, text)
                continue
            if file_path.name == "log.md":
                logs[dir_rel] = parse_log_file(dir_rel, text)
                continue

            concept_id = rel_path.with_suffix("").as_posix()
            try:
                concepts[concept_id] = parse_concept(concept_id, text)
            except (MalformedConceptError, ValidationError) as exc:
                load_errors.append(LoadError(path=rel_path.as_posix(), error=str(exc)))

        return cls(
            root=str(root_path),
            concepts=concepts,
            indexes=indexes,
            logs=logs,
            load_errors=load_errors,
        )
