"""Parse Clew DayNotes into structured work events."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from clew.models import WorkEvent


HEADER_RE = re.compile(
    r"^\[(?P<subject>[^\]]+)\]\s+\[(?P<category>[^\]]+)\]\s*$"
)


def date_from_filename(path: Path):
    """Extract the event date from a YYYYMMDD.md filename."""

    try:
        return datetime.strptime(path.stem, "%Y%m%d").date()
    except ValueError as exc:
        raise ValueError(
            f"{path.name}: filename must use YYYYMMDD.md"
        ) from exc


def parse_daynote(path: Path) -> list[WorkEvent]:
    """Parse one DayNote into an ordered list of WorkEvent objects."""

    event_date = date_from_filename(path)
    lines = path.read_text(encoding="utf-8").splitlines()

    events: list[WorkEvent] = []

    subject: str | None = None
    category: str | None = None
    body_lines: list[str] = []
    header_line = 0

    def finish_event() -> None:
        nonlocal subject, category, body_lines, header_line

        if subject is None or category is None:
            return

        body = "\n".join(body_lines).strip()

        if not body:
            raise ValueError(
                f"{path.name}:{header_line}: event has no body"
            )

        events.append(
            WorkEvent(
                event_date=event_date,
                source_file=path,
                line_number=header_line,
                subject=subject,
                category=category,
                body=body,
            )
        )

        subject = None
        category = None
        body_lines = []
        header_line = 0

    for line_number, line in enumerate(lines, start=1):
        match = HEADER_RE.match(line)

        if match:
            finish_event()

            subject = match.group("subject").strip()
            category = match.group("category").strip()
            header_line = line_number
            continue

        if subject is not None:
            body_lines.append(line)
        elif line.strip():
            raise ValueError(
                f"{path.name}:{line_number}: text before first event"
            )

    finish_event()

    return events
