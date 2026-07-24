"""Validate Clew DayNotes without producing an export."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from clew.normalize import normalize_entries
from clew.parsed import ParsedEntry
from clew.parser import (
    ParseError,
    day_note_paths,
    parse_day_note,
    parse_week,
)

CORE_CATEGORIES = frozenset({"DEV", "SUP"})


@dataclass(frozen=True, slots=True)
class ValidationReport:
    """Stable validation result for one file or week directory."""

    path: str
    valid: bool
    daynotes: int
    events: int
    start_date: str | None
    end_date: str | None
    categories: tuple[str, ...]
    errors: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        """Return the stable JSON-compatible representation."""
        return {
            "path": self.path,
            "valid": self.valid,
            "daynotes": self.daynotes,
            "events": self.events,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "categories": list(self.categories),
            "errors": list(self.errors),
        }


def validate_path(path: str | Path) -> ValidationReport:
    """Validate a DayNote file or directory using Clew's existing parsers."""
    source = Path(path)
    errors: list[str] = []
    daynotes = 0
    parsed_entries: tuple[ParsedEntry, ...] = ()

    if not source.exists():
        errors.append(f"path does not exist: {source}")
    elif source.is_dir():
        if source.suffix.lower() == ".md":
            errors.append("a directory whose name ends in .md is not a DayNote")
        else:
            try:
                notes = day_note_paths(source)
                daynotes = len(notes)
                if not notes:
                    errors.append("directory contains no DayNotes")
                else:
                    parsed_entries = parse_week(source)
            except (OSError, UnicodeError, ParseError) as error:
                errors.append(str(error))
    elif source.is_file():
        if source.suffix.lower() != ".md":
            errors.append("invalid file type; expected a Markdown DayNote")
        else:
            daynotes = 1
            try:
                parsed_entries = parse_day_note(source)
            except (OSError, UnicodeError, ParseError) as error:
                errors.append(str(error))
    else:
        errors.append("path is neither a file nor a directory")

    events = normalize_entries(parsed_entries)
    categories = tuple(sorted({event.category for event in events}))
    unsupported = sorted(set(categories) - CORE_CATEGORIES)
    if unsupported:
        errors.append(f"unsupported categories: {', '.join(unsupported)}")

    dates = [event.date for event in events]
    return ValidationReport(
        path=str(source),
        valid=not errors,
        daynotes=daynotes,
        events=len(events),
        start_date=min(dates).isoformat() if dates else None,
        end_date=max(dates).isoformat() if dates else None,
        categories=categories,
        errors=tuple(errors),
    )
