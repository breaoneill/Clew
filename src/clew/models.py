from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class WorkEvent:
    source_file: str
    subject: str
    category: str
    body: str
    event_date: date | None = None
