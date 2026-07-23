"""Source-neutral work-journal model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class SourceSpan:
    """An inclusive range within a source, when that source has line numbers."""

    start_line: int
    end_line: int


@dataclass(frozen=True, slots=True)
class SourceProvenance:
    """Where a work event came from."""

    source_type: str
    source_id: str
    location: str | None = None
    span: SourceSpan | None = None


@dataclass(frozen=True, slots=True)
class WorkEvent:
    """A single immutable record of work."""

    date: date
    subject: str
    category: str
    description: str
    provenance: SourceProvenance
