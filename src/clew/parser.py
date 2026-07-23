"""Parse Clew entries from Markdown day-notes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
import re

from clew.model import SourceProvenance, SourceSpan
from clew.parsed import ParsedEntry

_DAY_NOTE_NAME = re.compile(r"^(?P<date>\d{8})\.md$")
_ENTRY_HEADER = re.compile(
    r"^\[(?P<subject>[^\[\]]*)\][ \t]+\[(?P<category>[^\[\]]*)\][ \t]*$"
)
_FENCE_OPEN = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,}).*$")
_INLINE_LINK = re.compile(r"^\[[^\]\n]+\]\([^)]+\)(?:[ \t]+.*)?$")
_REFERENCE_LINK = re.compile(r"^\[[^\]\n]+\]\[[^\]\n]*\](?:[ \t]+.*)?$")
_REFERENCE_DEFINITION = re.compile(r"^\[[^\]\n]+\]:[ \t]*\S.*$")


@dataclass(frozen=True, slots=True)
class ParseDiagnostic:
    """A source-located problem found while parsing."""

    source_id: str
    line_number: int | None
    message: str

    def __str__(self) -> str:
        location = self.source_id
        if self.line_number is not None:
            location += f":{self.line_number}"
        return f"{location}: {self.message}"


class ParseError(ValueError):
    """One or more problems prevented a day-note from being parsed."""

    def __init__(self, diagnostics: list[ParseDiagnostic]) -> None:
        self.diagnostics = tuple(diagnostics)
        super().__init__("\n".join(str(item) for item in self.diagnostics))


@dataclass(slots=True)
class _PendingEntry:
    date: date
    subject: str
    category: str
    header_line: int
    description_lines: list[tuple[int, str]]


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


def _fenced_code_lines(lines: list[str]) -> set[int]:
    """Return zero-based indexes belonging to fenced code blocks."""
    code_lines: set[int] = set()
    fence_character: str | None = None
    fence_length = 0

    for index, line in enumerate(lines):
        if fence_character is None:
            opening = _FENCE_OPEN.match(line)
            if opening is None:
                continue
            fence = opening.group("fence")
            fence_character = fence[0]
            fence_length = len(fence)
            code_lines.add(index)
            continue

        code_lines.add(index)
        closing = re.match(
            rf"^ {{0,3}}{re.escape(fence_character)}{{{fence_length},}}[ \t]*$",
            line,
        )
        if closing is not None:
            fence_character = None
            fence_length = 0

    return code_lines


def _is_indented_code(line: str) -> bool:
    return line.startswith("    ") or line.startswith("\t")


def _is_markdown_link(line: str) -> bool:
    return any(
        pattern.fullmatch(line)
        for pattern in (_INLINE_LINK, _REFERENCE_LINK, _REFERENCE_DEFINITION)
    )


def _is_entry_like(line: str) -> bool:
    """Return whether a column-zero line claims Clew entry syntax."""
    return line.startswith("[") and not _is_markdown_link(line)


def _trim_description(
    lines: list[tuple[int, str]],
) -> list[tuple[int, str]]:
    start = 0
    end = len(lines)
    while start < end and not lines[start][1].strip():
        start += 1
    while end > start and not lines[end - 1][1].strip():
        end -= 1
    return lines[start:end]


def _finish_entry(
    pending: _PendingEntry,
    source: Path,
    entries: list[ParsedEntry],
    diagnostics: list[ParseDiagnostic],
) -> None:
    description_lines = _trim_description(pending.description_lines)
    if not description_lines:
        diagnostics.append(
            ParseDiagnostic(
                source.name,
                pending.header_line,
                "entry requires at least one non-blank description line",
            )
        )
        return

    entries.append(
        ParsedEntry(
            date=pending.date,
            subject=pending.subject,
            category=pending.category,
            description="\n".join(line for _, line in description_lines),
            provenance=SourceProvenance(
                source_type="markdown",
                source_id=source.name,
                location=str(source),
                span=SourceSpan(
                    start_line=pending.header_line,
                    end_line=description_lines[-1][0],
                ),
            ),
        )
    )


def parse_day_note(path: str | Path) -> tuple[ParsedEntry, ...]:
    """Parse all recognized entries in one UTF-8 Markdown day-note.

    Unrelated Markdown outside entries is ignored. Any malformed entry-like
    header makes the complete parse fail with aggregated diagnostics.
    """
    source = Path(path)
    event_date = _date_from_filename(source)
    text = source.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    fenced_lines = _fenced_code_lines(lines)
    entries: list[ParsedEntry] = []
    diagnostics: list[ParseDiagnostic] = []
    pending: _PendingEntry | None = None

    for index, line in enumerate(lines):
        line_number = index + 1
        is_code = index in fenced_lines or _is_indented_code(line)
        header = None if is_code or line[:1].isspace() else _ENTRY_HEADER.fullmatch(line)
        entry_like = not is_code and not line[:1].isspace() and _is_entry_like(line)

        if header is not None or entry_like:
            if pending is not None:
                _finish_entry(pending, source, entries, diagnostics)
                pending = None

            if header is None:
                diagnostics.append(
                    ParseDiagnostic(
                        source.name,
                        line_number,
                        "malformed entry header; expected [Subject] [Category]",
                    )
                )
                continue

            subject = header.group("subject").strip()
            category = header.group("category").strip()
            empty_fields = [
                name
                for name, value in (("subject", subject), ("category", category))
                if not value
            ]
            if empty_fields:
                diagnostics.append(
                    ParseDiagnostic(
                        source.name,
                        line_number,
                        f"entry {', '.join(empty_fields)} must not be empty",
                    )
                )
                continue

            pending = _PendingEntry(
                date=event_date,
                subject=subject,
                category=category,
                header_line=line_number,
                description_lines=[],
            )
            continue

        if pending is not None:
            pending.description_lines.append((line_number, line))

    if pending is not None:
        _finish_entry(pending, source, entries, diagnostics)

    if diagnostics:
        raise ParseError(diagnostics)

    return tuple(entries)
