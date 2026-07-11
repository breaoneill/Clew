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
