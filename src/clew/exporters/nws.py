"""Export work events as an NWS-compatible CSV timesheet."""

from __future__ import annotations

import csv
from collections.abc import Iterable
from io import StringIO

from clew.model import WorkEvent


def export_nws(events: Iterable[WorkEvent]) -> str:
    """Render one CSV row per event in deterministic source order."""
    output = StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(("Date", "Subject", "Category", "Description"))

    for event in events:
        writer.writerow(
            (
                event.date.isoformat(),
                event.subject,
                event.category,
                event.description,
            )
        )

    return output.getvalue()
