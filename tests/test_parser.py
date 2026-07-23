from datetime import date
from pathlib import Path

import pytest

from clew.model import WorkEvent
from clew.parser import ParseError, parse_day_note

FIXTURES = Path(__file__).parent / "fixtures"


def test_parses_multiple_entries_and_ignores_unrelated_markdown() -> None:
    events = parse_day_note(FIXTURES / "20260723.md")

    assert events == (
        WorkEvent(
            date=date(2026, 7, 23),
            subject="Widgets Inc",
            category="SUP",
            description="Investigate SELinux log report error.",
            source_filename="20260723.md",
            source_line_number=5,
        ),
        WorkEvent(
            date=date(2026, 7, 23),
            subject="NWB",
            category="DEV",
            description=(
                "Cloud server imaging.\nRecord the resulting image identifier."
            ),
            source_filename="20260723.md",
            source_line_number=10,
        ),
    )


def test_reports_all_malformed_entries_with_source_locations() -> None:
    with pytest.raises(ParseError) as raised:
        parse_day_note(FIXTURES / "20260724.md")

    assert [str(item) for item in raised.value.diagnostics] == [
        "20260724.md:1: malformed entry header; expected [Subject] [Category]",
        "20260724.md:4: entry requires at least one description line",
    ]


@pytest.mark.parametrize("filename", ["notes.md", "20260230.md"])
def test_rejects_filename_without_a_valid_date(
    tmp_path: Path, filename: str
) -> None:
    note = tmp_path / filename
    note.write_text("[Subject] [CAT]\nDescription.\n", encoding="utf-8")

    with pytest.raises(ParseError):
        parse_day_note(note)


def test_work_event_is_immutable() -> None:
    event = parse_day_note(FIXTURES / "20260723.md")[0]

    with pytest.raises((AttributeError, TypeError)):
        event.subject = "Changed"  # type: ignore[misc]
