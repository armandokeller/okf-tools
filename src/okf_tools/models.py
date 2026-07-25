"""Typed data model for OKF (Open Knowledge Format) v0.2 concepts and reserved files."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

TrustTier = Literal["unverified", "machine-confirmed", "human-reviewed"]
Status = Literal["draft", "stable", "deprecated"]


class Source(BaseModel):
    """A single entry of a concept's ``sources`` frontmatter family (SPEC §5.1)."""

    resource: str
    id: str | None = None
    title: str | None = None
    author: str | None = None
    usage_count: int | None = None
    last_modified: date | None = None


class UsageWindow(BaseModel):
    """The ``{ from, to }`` date range framing every ``sources[].usage_count`` (SPEC §5.1)."""

    model_config = ConfigDict(populate_by_name=True)

    from_: date = Field(alias="from")
    to: date


class Generated(BaseModel):
    """Records how the current content was produced (SPEC §5.2)."""

    by: str
    at: datetime | None = None


class Verified(BaseModel):
    """A single verification event (SPEC §5.2)."""

    by: str
    at: datetime | None = None


class Parameter(BaseModel):
    """A typed, named hole an Attested Computation may be parameterized with (SPEC §10.2)."""

    name: str
    type: str
    required: bool = False


class Executor(BaseModel):
    """How an Attested Computation is run (SPEC §10.2)."""

    resource: str | None = None
    receipt: list[str] = Field(default_factory=list)


class Attester(BaseModel):
    """The deterministic check for an Attested Computation's receipt (SPEC §10.2)."""

    resource: str | None = None


class Concept(BaseModel):
    """A single OKF concept document: frontmatter fields plus its raw markdown body."""

    id: str
    type: str
    title: str | None = None
    description: str | None = None
    resource: str | None = None
    tags: list[str] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)
    usage_window: UsageWindow | None = None
    generated: Generated | None = None
    verified: list[Verified] = Field(default_factory=list)
    status: Status = "stable"
    stale_after: date | None = None

    # Attested Computation fields (SPEC §10.2); populated only when
    # ``type == "Attested Computation"``.
    runtime: str | None = None
    parameters: list[Parameter] = Field(default_factory=list)
    computation: str | None = None
    executor: Executor | None = None
    attester: Attester | None = None

    # Legacy v0.1 field (SPEC §13.1), kept separate from `generated` rather
    # than synthesized into it, since `Generated.by` is required and a
    # legacy `timestamp` never carried an actor.
    timestamp: datetime | None = None

    # Unrecognized frontmatter keys, preserved verbatim (SPEC §4.1: producers
    # MAY include any additional keys; consumers MUST NOT reject them).
    extra: dict[str, Any] = Field(default_factory=dict)

    body: str = ""

    @field_validator("verified", mode="before")
    @classmethod
    def _normalize_verified(cls, value: Any) -> Any:
        """A bare ``{by, at}`` mapping is a one-element list (SPEC §5.2)."""
        if isinstance(value, dict):
            return [value]
        return value


class IndexEntry(BaseModel):
    """A single bullet entry in an `index.md` section (SPEC §8)."""

    title: str
    link: str
    description: str | None = None


class IndexSection(BaseModel):
    """A heading-grouped list of entries in an `index.md` (SPEC §8)."""

    heading: str
    entries: list[IndexEntry] = Field(default_factory=list)


class IndexFile(BaseModel):
    """A parsed `index.md`. Only a bundle-root index may carry `okf_version` (SPEC §8, §12)."""

    path: str
    okf_version: str | None = None
    sections: list[IndexSection] = Field(default_factory=list)


class LogDateGroup(BaseModel):
    """Entries recorded under one `## YYYY-MM-DD` heading in a `log.md` (SPEC §9)."""

    date: date
    entries: list[str] = Field(default_factory=list)


class LogFile(BaseModel):
    """A parsed `log.md`: date-grouped entries, newest first (SPEC §9)."""

    path: str
    groups: list[LogDateGroup] = Field(default_factory=list)


class LoadError(BaseModel):
    """Records a single concept file that failed to parse, without aborting the bundle load."""

    path: str
    error: str
