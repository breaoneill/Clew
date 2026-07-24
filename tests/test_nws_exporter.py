import csv
from datetime import date
from io import StringIO

from clew.exporters.nws import export_nws
from clew.model import SourceProvenance, WorkEvent


def test_nws_export_has_stable_columns_and_csv_escaping() -> None:
    events = (
        WorkEvent(
            date=date(2026, 7, 6),
            subject="Widgets, Inc",
            category="SUP",
            description='Investigated "printer" issue.\nResolved it.',
            provenance=SourceProvenance("markdown", "20260706.md"),
        ),
    )

    rendered = export_nws(events)

    assert list(csv.reader(StringIO(rendered))) == [
        ["Date", "Subject", "Category", "Description"],
        [
            "2026-07-06",
            "Widgets, Inc",
            "SUP",
            'Investigated "printer" issue.\nResolved it.',
        ],
    ]


def test_empty_nws_export_still_has_header() -> None:
    assert export_nws(()) == "Date,Subject,Category,Description\n"
