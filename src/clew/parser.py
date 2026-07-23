"""Parse Clew entries from Markdown day-notes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
import re

from clew.model import WorkEvent

_DAY_NOTE_NAME = re.compile(r"^(?P<date>\d{8})\.md$")
_ENTRY_HEADER = re.compile(
    r"^\[(?P<subject>[^\[\]]+)\]\s+\[(?P<category>[^\[\]]+)\]\s*$"
)
_FIRST_FIELD = re.compile(r"^\[[^\]]+\]\s+")


@dataclass(frozen=True, slots=True)
class ParseDiagnostic:
    """A source-located problem found while parsing."""

    filename: str
    line_number: int | None
    message: str

    def __str__(self) -> str:
        location = self.filename
        if self.line_number is not None:
            location += f":{self.line_number}"
        return f"{location}: {self.message}"


class ParseError(ValueError):
    """One or more problems prevented a day-note from being parsed."""

    def __init__(self, diagnostics: list[ParseDiagnostic]) -> None:
        self.diagnostics = tuple(diagnostics)
        super().__init__("\n".join(str(item) for item in self.diagnostics))


def _date_from_filename(path: Path) -> date:
    match = _DAY_NOTE_NAME.fullmatch(path.name)
    if match is None:
        raise ParseError(
            [
                ParseDiagnostic(
                    path.name,
                    None,
                    "expected a day-note filename in YYYYMMDD.md format",
                )
            ]
        )

    try:
        return datetime.strptime(match.group("date"), "%Y%m%d").date()
    except ValueError as error:
        raise ParseError(
            [ParseDiagnostic(path.name, None, "filename contains an invalid date")]
        ) from error


def _looks_like_entry_header(line: str) -> bool:
    """Recognize entry-like lines without treating Markdown links as entries."""
    stripped = line.strip()
    return bool(_FIRST_FIELD.match(stripped)) and not re.match(
        r"^\[[^\]]+\]\([^)]+\)", stripped
    )


def parse_day_note(path: str | Path) -> tuple[WorkEvent, ...]:
    """Parse all recognized entries in one Markdown day-note.

    Unrelated Markdown is ignored. If any entry-like content is malformed, all
    diagnostics are reported together and no partial result is returned.
    """
    source = Path(path)
    event_date = _date_from_filename(source)
    lines = source.read_text(encoding="utf-8").splitlines()
    events: list[WorkEvent] = []
    diagnostics: list[ParseDiagnostic] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        header = _ENTRY_HEADER.fullmatch(line.strip())

        if header is None:
            if _looks_like_entry_header(line):
                diagnostics.append(
                    ParseDiagnostic(
                        source.name,
                        index + 1,
                        "malformed entry header; expected [Subject] [Category]",
                    )
                )
            index += 1
            continue

        header_line = index + 1
        subject = header.group("subject").strip()
        category = header.group("category").strip()
        index += 1
        description_lines: list[str] = []

        while index < len(lines):
            candidate = lines[index]
            if not candidate.strip():
                break
            if _ENTRY_HEADER.fullmatch(candidate.strip()) or _looks_like_entry_header(
                candidate
            ):
                break
            description_lines.append(candidate.strip())
            index += 1

        if not description_lines:
            diagnostics.append(
                ParseDiagnostic(
                    source.name,
                    header_line,
                    "entry requires at least one description line",
                )
            )
        else:
            events.append(
                WorkEvent(
                    date=event_date,
                    subject=subject,
                    category=category,
                    description="\n".join(description_lines),
                    source_filename=source.name,
                    source_line_number=header_line,
                )
            )

    if diagnostics:
        raise ParseError(diagnostics)

    return tuple(events)
