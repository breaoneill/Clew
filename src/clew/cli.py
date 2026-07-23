"""Command-line interface for Clew."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
from typing import Sequence

from clew.model import WorkEvent
from clew.parser import ParseError, parse_day_note


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
        help="write events as JSON",
    )
    return parser


def _event_as_dict(event: WorkEvent) -> dict[str, object]:
    data = asdict(event)
    data["date"] = event.date.isoformat()
    return data


def _human_output(events: tuple[WorkEvent, ...]) -> str:
    rendered: list[str] = []
    for event in events:
        rendered.append(
            "\n".join(
                [
                    f"{event.date.isoformat()} | {event.subject} | {event.category}",
                    event.description,
                    f"Source: {event.source_filename}:{event.source_line_number}",
                ]
            )
        )
    return "\n\n".join(rendered)


def main(argv: Sequence[str] | None = None) -> None:
    """Run the Clew command-line interface."""
    argument_parser = _build_argument_parser()
    arguments = argument_parser.parse_args(argv)

    try:
        events = parse_day_note(arguments.path)
    except (OSError, UnicodeError, ParseError) as error:
        argument_parser.error(str(error))

    if arguments.as_json:
        print(json.dumps([_event_as_dict(event) for event in events], indent=2))
    else:
        output = _human_output(events)
        if output:
            print(output)
