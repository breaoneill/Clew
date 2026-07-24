# Clew

> Leave clues, not paperwork.

Clew is an editor-agnostic work journal built on plain Markdown.

Capture lightweight notes while you work.
Generate timesheets, progress reports and other artefacts afterwards.

## Principles

- Markdown is the source of truth.
- Notes remain useful without Clew.
- Clew never modifies your notes.
- Reports are generated from notes.
- AI is optional.

## Installation

Clew requires Python 3.11 or newer. From a checkout of this repository, create
and activate a virtual environment, then install Clew in editable mode:

```console
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

To install the test dependencies as well:

```console
python -m pip install -e ".[test]"
```

Install the static-analysis tools with:

```console
python -m pip install -e ".[test,quality]"
```

## Day-note format

A day-note filename must be a date in `YYYYMMDD.md` format. Each work entry has
a subject and category header followed by one or more description lines:

```markdown
[Widgets Inc] [SUP]
Investigate SELinux log report error.
```

A file may contain multiple entries. Clew ignores unrelated Markdown outside
recognized entries and reports malformed entry-like content with its source
line number. It never modifies the source note.

The complete v0.1 rules, including multi-paragraph descriptions and code-block
handling, are in [docs/grammar.md](docs/grammar.md).

## Usage

Parse a day-note using the default human-readable output:

```console
clew parse 20260723.md
```

Pass a directory to parse its dated day-notes as one chronological timeline:

```console
clew parse ./notes
```

Emit structured JSON instead:

```console
clew parse 20260723.md --json
```

Validate a day-note or week directory without exporting it:

```console
clew validate 20260723.md
clew validate ./notes --json
```

Validation checks parsing and the core `DEV` and `SUP` categories. Reports are
written to standard output; validation diagnostics are written to standard
error.

Export a day-note or directory as an NWS CSV timesheet:

```console
clew export nws ./notes
clew export nws ./notes --output timesheet.csv
```

The CSV has stable `Date`, `Subject`, `Category`, and `Description` columns.
Without `--output`, it is written to standard output.

Successful commands exit with status 0. File, encoding, filename-date, and
parse failures are written as human-readable errors to standard error and exit
with status 1. Invalid command-line usage exits with status 2. Errors remain
human-readable when `--json` is requested in v0.1.

An empty note or a note containing no entries is successful. Human output says
`No work events found.` and JSON output contains an empty `events` array.

## JSON contract

`--json` emits the versioned `clew.work-events` schema:

```json
{
  "schema": "clew.work-events",
  "version": 1,
  "events": [
    {
      "date": "2026-07-23",
      "subject": "Widgets Inc",
      "category": "SUP",
      "description": "Investigate SELinux log report error.",
      "provenance": {
        "source_type": "markdown",
        "source_id": "20260723.md",
        "location": "20260723.md",
        "span": {
          "start_line": 1,
          "end_line": 2
        }
      }
    }
  ]
}
```

The envelope name and version identify the contract. JSON fields are serialized
explicitly, so changes to internal Python dataclasses do not implicitly change
the public representation. Additive or breaking schema changes require an
intentional contract decision; breaking changes require a new version.

## Development

Run the test suite from the repository root:

```console
python -m pytest
```

Run the complete local quality gate with:

```console
ruff check .
ruff format --check .
mypy
python -m pytest
```
