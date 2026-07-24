"""Command-line interface for Clew."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from clew.exporters.nws import export_nws
from clew.model import SourceProvenance, WorkEvent
from clew.normalize import normalize_entries
from clew.parser import ParseError, parse_day_note, parse_week
from clew.validation import ValidationReport, validate_path

JSON_SCHEMA = "clew.work-events"
JSON_VERSION = 1


def _build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="clew",
        description="Turn lightweight Markdown notes into structured work events.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    parse_command = commands.add_parser(
        "parse", help="parse a Markdown day-note or directory of day-notes"
    )
    parse_command.add_argument("path", type=Path, metavar="PATH")
    parse_command.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="write events using the versioned JSON contract",
    )

    validate_command = commands.add_parser(
        "validate", help="validate a DayNote or directory of DayNotes"
    )
    validate_command.add_argument("path", type=Path, metavar="PATH")
    validate_command.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="write a stable JSON validation report",
    )

    export_command = commands.add_parser(
        "export", help="export work events to an external format"
    )
    export_formats = export_command.add_subparsers(dest="export_format", required=True)
    nws_command = export_formats.add_parser("nws", help="export an NWS CSV timesheet")
    nws_command.add_argument("path", type=Path, metavar="PATH")
    nws_command.add_argument(
        "-o",
        "--output",
        type=Path,
        metavar="PATH",
        help="write the CSV to PATH instead of standard output",
    )
    return parser


def _provenance_as_json(provenance: SourceProvenance) -> dict[str, object]:
    span = provenance.span
    return {
        "source_type": provenance.source_type,
        "source_id": provenance.source_id,
        "location": provenance.location,
        "span": (
            None
            if span is None
            else {
                "start_line": span.start_line,
                "end_line": span.end_line,
            }
        ),
    }


def _event_as_json(event: WorkEvent) -> dict[str, object]:
    """Serialize exactly the public JSON v1 event fields."""
    return {
        "date": event.date.isoformat(),
        "subject": event.subject,
        "category": event.category,
        "description": event.description,
        "provenance": _provenance_as_json(event.provenance),
    }


def _json_output(events: tuple[WorkEvent, ...]) -> str:
    document = {
        "schema": JSON_SCHEMA,
        "version": JSON_VERSION,
        "events": [_event_as_json(event) for event in events],
    }
    return json.dumps(document, indent=2, ensure_ascii=False)


def _human_output(events: tuple[WorkEvent, ...]) -> str:
    if not events:
        return "No work events found."

    rendered: list[str] = []
    for event in events:
        span = event.provenance.span
        source = event.provenance.source_id
        if span is not None:
            source += f":{span.start_line}-{span.end_line}"
        rendered.append(
            "\n".join(
                [
                    f"{event.date.isoformat()} | {event.subject} | {event.category}",
                    event.description,
                    f"Source: {source}",
                ]
            )
        )
    return "\n\n".join(rendered)


def _events_from_path(path: Path) -> tuple[WorkEvent, ...]:
    is_week_directory = path.is_dir() and path.suffix.lower() != ".md"
    parsed_entries = parse_week(path) if is_week_directory else parse_day_note(path)
    return normalize_entries(parsed_entries)


def _validation_human_output(report: ValidationReport) -> str:
    date_range = (
        f"{report.start_date} to {report.end_date}"
        if report.start_date is not None
        else "none"
    )
    categories = ", ".join(report.categories) or "none"
    return "\n".join(
        (
            f"Validating: {report.path}",
            f"DayNotes: {report.daynotes}",
            f"Events: {report.events}",
            f"Date range: {date_range}",
            f"Categories: {categories}",
            f"Status: {'valid' if report.valid else 'invalid'}",
        )
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run Clew, returning 0 on success and 1 on input or parsing failure."""
    argument_parser = _build_argument_parser()
    arguments = argument_parser.parse_args(argv)

    if arguments.command == "validate":
        report = validate_path(arguments.path)
        if report.errors:
            for error in report.errors:
                print(f"clew: validation error: {error}", file=sys.stderr)
        print(
            json.dumps(report.as_dict(), indent=2, ensure_ascii=False)
            if arguments.as_json
            else _validation_human_output(report)
        )
        return 0 if report.valid else 1

    try:
        events = _events_from_path(arguments.path)

        if arguments.command == "export":
            rendered = export_nws(events)
            if arguments.output is not None:
                arguments.output.write_text(rendered, encoding="utf-8", newline="")
            else:
                sys.stdout.write(rendered)
            return 0
    except (OSError, UnicodeError, ParseError) as error:
        print(f"clew: error: {error}", file=sys.stderr)
        return 1

    print(_json_output(events) if arguments.as_json else _human_output(events))
    return 0
