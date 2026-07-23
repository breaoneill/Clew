"""Command-line interface for Clew."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

from clew.model import SourceProvenance, WorkEvent
from clew.normalize import normalize_entries
from clew.parser import ParseError, parse_day_note

JSON_SCHEMA = "clew.work-events"
JSON_VERSION = 1


def _build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="clew",
        description="Turn lightweight Markdown notes into structured work events.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    parse_command = commands.add_parser("parse", help="parse one Markdown day-note")
    parse_command.add_argument("path", type=Path, metavar="PATH")
    parse_command.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="write events using the versioned JSON contract",
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


def main(argv: Sequence[str] | None = None) -> int:
    """Run Clew, returning 0 on success and 1 on input or parsing failure."""
    argument_parser = _build_argument_parser()
    arguments = argument_parser.parse_args(argv)

    try:
        parsed_entries = parse_day_note(arguments.path)
        events = normalize_entries(parsed_entries)
    except (OSError, UnicodeError, ParseError) as error:
        print(f"clew: error: {error}", file=sys.stderr)
        return 1

    print(_json_output(events) if arguments.as_json else _human_output(events))
    return 0
