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

## Usage

Parse a day-note using the default human-readable output:

```console
clew parse 20260723.md
```

Emit structured JSON instead:

```console
clew parse 20260723.md --json
```

## Development

Run the test suite from the repository root:

```console
python -m pytest
```
