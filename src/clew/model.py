"""Core work-journal model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class WorkEvent:
    """A single immutable record of work."""

    date: date
    subject: str
    category: str
    description: str
    source_filename: str
    source_line_number: int
