"""Convert source-adapter output into Clew's canonical event model."""

from __future__ import annotations

from collections.abc import Iterable

from clew.model import WorkEvent
from clew.parsed import ParsedEntry


def normalize_entry(entry: ParsedEntry) -> WorkEvent:
    """Normalize one parsed entry without adding source-specific policy."""
    return WorkEvent(
        date=entry.date,
        subject=entry.subject,
        category=entry.category,
        description=entry.description,
        provenance=entry.provenance,
    )


def normalize_entries(entries: Iterable[ParsedEntry]) -> tuple[WorkEvent, ...]:
    """Normalize parsed entries while preserving their source order."""
    return tuple(normalize_entry(entry) for entry in entries)
