"""Internal, source-adapter output types."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from clew.model import SourceProvenance


@dataclass(frozen=True, slots=True)
class ParsedEntry:
    """A syntactically valid entry awaiting semantic normalization."""

    date: date
    subject: str
    category: str
    description: str
    provenance: SourceProvenance
