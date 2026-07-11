from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class WorkEvent:
    """A single event extracted from a DayNote."""

    event_date: date
    source_file: Path
    line_number: int
    subject: str
    category: str
    body: str


@dataclass(frozen=True)
class WeekNotes:
    """A chronological collection of WorkEvents."""

    start_date: date
    end_date: date
    events: list[WorkEvent]
