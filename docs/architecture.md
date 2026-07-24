# Clew Architecture

## Overview

Above all, Clew is a framework, not a workflow.

Clew provides a stable, local-first representation of work events captured in
Markdown. It does not dictate how organisations record, process or report work.

```text
Markdown DayNotes
        │
        ▼
      Parser
        │
        ▼
   Work Journal Model
        │
   ┌────┼────────┬─────────┐
   ▼    ▼        ▼         ▼
Validation  Timesheet  Progress  Plugins
```

The parser and data model form Clew's core. Everything else builds on these
components.

---

# Design Principles

## Markdown is the source of truth

Users own their notes.

Clew reads Markdown. It does not own storage, synchronisation or editing.

Any editor capable of producing plain Markdown can be used.

Examples include:

- Obsidian
- Vim
- VS Code
- Typora
- Emacs

Clew deliberately avoids locking users into a particular application.

---

## Parse once

Information should only be interpreted once.

The parser converts Markdown into immutable structured objects.

Everything else operates on those objects.

```
Markdown
    │
    ▼
Parser
    │
    ▼
WeekNotes
```

No plugin reparses Markdown.

---

## Validation is separate from parsing

Parsing answers:

> What does this document contain?

Validation answers:

> Is this document acceptable?

This separation allows future plugins to impose additional rules without
changing the parser.

---

## Models describe data

The core data model is intentionally simple.

```
WorkEvent
WeekNotes
```

Models are immutable.

Models contain data.

Models contain no business logic.

---

## Plugins describe behaviour

Plugins consume `WeekNotes`.

Plugins never modify them.

Examples include:

- NWS Timesheets
- Weekly summaries
- Wellbeing reports
- CSV exports
- PDF exports
- Future integrations

The core never contains organisation-specific behaviour.

---

# Boundary

Clew describes work events.

Clew does not decide what an organisation does with those events.

Plugins consume Clew's structured output and generate reports, updates,
exports or integrations.

---

# External Systems

Clew may reference external systems such as:

- Zammad
- GitHub
- Teams
- Email
- Issue trackers

Clew does not mirror those systems.

Only stable identifiers and concise summaries are recorded.

Verbose conversations remain in their source system.

---

# Reliability

Clew is designed to preserve information.

Core principles include:

- No event is silently discarded.
- Every exported record must be traceable back to its source Markdown.
- Validation errors are explicit.
- Parser behaviour is deterministic.
- Canonical example datasets are retained as regression tests.

---

# Interfaces

The Clew core is independent of its user interface.

Multiple clients may exist.

```
                Clew Core
                    │
      ┌─────────────┼─────────────┐
      ▼             ▼             ▼
     CLI       Local Web UI     Future API
```

Each interface uses the same parser, validator and plugin system.

No interface contains business logic.

---

# Philosophy

Humans capture.

Clew accounts.

Plugins present.
