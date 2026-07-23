from dataclasses import FrozenInstanceError
from datetime import date
from pathlib import Path

import pytest

from clew.model import SourceProvenance, SourceSpan, WorkEvent
from clew.normalize import normalize_entries
from clew.parsed import ParsedEntry
from clew.parser import ParseError, parse_day_note

FIXTURES = Path(__file__).parent / "fixtures"


def test_parses_multiple_entries_with_accurate_spans() -> None:
    entries = parse_day_note(FIXTURES / "20260723.md")

    assert entries == (
        ParsedEntry(
            date=date(2026, 7, 23),
            subject="Widgets Inc",
            category="SUP",
            description="Investigate SELinux log report error.",
            provenance=SourceProvenance(
                source_type="markdown",
                source_id="20260723.md",
                location=str(FIXTURES / "20260723.md"),
                span=SourceSpan(start_line=5, end_line=6),
            ),
        ),
        ParsedEntry(
            date=date(2026, 7, 23),
            subject="NWB",
            category="DEV",
            description=(
                "Cloud server imaging.\nRecord the resulting image identifier."
            ),
            provenance=SourceProvenance(
                source_type="markdown",
                source_id="20260723.md",
                location=str(FIXTURES / "20260723.md"),
                span=SourceSpan(start_line=8, end_line=10),
            ),
        ),
    )


def test_supports_consecutive_entries() -> None:
    entries = parse_day_note(FIXTURES / "20260725.md")

    assert [entry.subject for entry in entries] == ["First", "Second"]
    assert [entry.provenance.span for entry in entries] == [
        SourceSpan(1, 2),
        SourceSpan(3, 4),
    ]


def test_preserves_multi_paragraph_markdown_and_unicode() -> None:
    entry = parse_day_note(FIXTURES / "20260726.md")[0]

    assert entry.description == (
        "First paragraph.\n"
        "\n"
        "## A heading\n"
        "\n"
        "- A list item\n"
        "- Another item with [an inline link](https://example.com)\n"
        "\n"
        "> Quoted text\n"
        "\n"
        "[reference]: https://example.com/reference\n"
        "See [reference][] and café notes."
    )
    assert entry.provenance.span == SourceSpan(1, 13)


def test_ignores_headers_in_fenced_and_indented_code() -> None:
    entries = parse_day_note(FIXTURES / "20260727.md")

    assert [entry.subject for entry in entries] == ["Real event", "Second real event"]
    assert "[Still not an event] [SUP]" in entries[0].description
    assert "    [Indented description content] [DEV]" in entries[0].description
    assert entries[0].provenance.span == SourceSpan(11, 19)
    assert entries[1].provenance.span == SourceSpan(21, 22)


def test_zero_recognized_entries_is_successful() -> None:
    assert parse_day_note(FIXTURES / "20260728.md") == ()


def test_empty_file_is_successful(tmp_path: Path) -> None:
    note = tmp_path / "20260729.md"
    note.write_text("", encoding="utf-8")

    assert parse_day_note(note) == ()


def test_reports_empty_fields_and_malformed_headers_consistently() -> None:
    with pytest.raises(ParseError) as raised:
        parse_day_note(FIXTURES / "20260724.md")

    assert [diagnostic.line_number for diagnostic in raised.value.diagnostics] == [
        3,
        6,
        9,
        12,
        15,
        18,
        24,
    ]
    messages = [diagnostic.message for diagnostic in raised.value.diagnostics]
    assert messages[:2] == [
        "entry subject must not be empty",
        "entry category must not be empty",
    ]
    assert messages[2:] == [
        "malformed entry header; expected [Subject] [Category]"
    ] * 5


def test_missing_description_is_reported_for_consecutive_headers(
    tmp_path: Path,
) -> None:
    note = tmp_path / "20260730.md"
    note.write_text("[Empty] [DEV]\n[Complete] [SUP]\nDone.\n", encoding="utf-8")

    with pytest.raises(ParseError, match="at least one non-blank description"):
        parse_day_note(note)


def test_whitespace_rules(tmp_path: Path) -> None:
    note = tmp_path / "20260731.md"
    note.write_text(
        "[ Widgets Inc ]\t [ SUP ]  \nDescription.\n"
        "   [Not a header] [DEV]\n",
        encoding="utf-8",
    )

    entry = parse_day_note(note)[0]
    assert entry.subject == "Widgets Inc"
    assert entry.category == "SUP"
    assert entry.description.endswith("   [Not a header] [DEV]")


@pytest.mark.parametrize("filename", ["notes.md", "20260230.md"])
def test_rejects_filename_without_a_valid_date(
    tmp_path: Path, filename: str
) -> None:
    note = tmp_path / filename
    note.write_text("[Subject] [CAT]\nDescription.\n", encoding="utf-8")

    with pytest.raises(ParseError):
        parse_day_note(note)


def test_handles_crlf_bom_and_missing_final_newline(tmp_path: Path) -> None:
    note = tmp_path / "20260801.md"
    note.write_bytes(
        b"\xef\xbb\xbf[Subject] [DEV]\r\nFirst line.\r\nSecond line."
    )

    entry = parse_day_note(note)[0]
    assert entry.description == "First line.\nSecond line."
    assert entry.provenance.span == SourceSpan(1, 3)


def test_invalid_utf8_is_rejected(tmp_path: Path) -> None:
    note = tmp_path / "20260802.md"
    note.write_bytes(b"[Subject] [DEV]\nInvalid: \xff\n")

    with pytest.raises(UnicodeDecodeError):
        parse_day_note(note)


def test_parsed_and_normalized_models_are_immutable() -> None:
    parsed = parse_day_note(FIXTURES / "20260723.md")[0]
    event = normalize_entries([parsed])[0]

    assert event == WorkEvent(
        date=parsed.date,
        subject=parsed.subject,
        category=parsed.category,
        description=parsed.description,
        provenance=parsed.provenance,
    )
    with pytest.raises(FrozenInstanceError):
        parsed.subject = "Changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        event.subject = "Changed"  # type: ignore[misc]
