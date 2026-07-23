# Markdown day-note grammar

This document defines the Clew v0.1 Markdown grammar. These rules are
deliberately narrow so that a note is interpreted consistently and remains
useful in any Markdown editor.

## File name and encoding

A day-note must:

- be a regular file;
- be UTF-8 text;
- have a filename consisting of a valid calendar date in `YYYYMMDD.md` form.

For example, `20260723.md` represents 23 July 2026. Names such as `notes.md`,
`2026-07-23.md`, and `20260230.md` are invalid.

A UTF-8 byte-order mark (BOM) at the start of a file is accepted and removed
before parsing. A BOM elsewhere has no special meaning.

The filename supplies the date for every entry in the file.

## Entry header

An entry begins with a header on a line by itself:

```text
[Subject] [Category]
```

The header must:

- begin in column one, with no leading spaces or tabs;
- contain exactly two bracketed fields;
- have one or more spaces or tabs between the fields;
- contain no text after the category, apart from spaces or tabs.

Spaces and tabs immediately inside either pair of brackets are allowed and are
removed. Whitespace within a subject is retained. Both fields must contain at
least one non-whitespace character.

These are valid:

```text
[Widgets Inc] [SUP]
[ Widgets Inc ]   [ SUP ]
[Widgets Inc]	[SUP]
```

These are malformed:

```text
[] [SUP]
[Widgets Inc] []
[Widgets Inc] SUP]
[Widgets Inc] [SUP
[Widgets Inc] [SUP] trailing text
```

Field values cannot contain `[` or `]` in v0.1.

`[label][reference]` has no separating whitespace and is therefore a Markdown
reference link, not a Clew header. It is ignored outside an entry and retained
inside a description.

## Description and entry boundaries

The description starts on the line after a valid header.

An entry ends immediately before:

- the next valid entry header;
- the next malformed entry-like header; or
- the end of the file.

A description must contain at least one non-blank line. Blank lines immediately
after its header and immediately before its end are discarded.

All other description lines are preserved verbatim and joined with `\n`.
Internal blank lines are preserved, so descriptions may contain multiple
paragraphs.

Consecutive headers do not need a blank separator:

```text
[First] [DEV]
First description.
[Second] [SUP]
Second description.
```

A header followed directly by another header has no description and is
malformed.

## Markdown within descriptions

Once an entry has begun, all Markdown other than a column-one entry-like header
belongs to its description. This includes:

- headings;
- lists;
- inline and reference links;
- quoted text;
- fenced code blocks;
- indented code blocks.

Blank lines do not end an entry. This makes multi-paragraph Markdown
descriptions possible.

Because there is no explicit closing marker, Markdown after the first entry is
part of that entry until another entry-like header or the end of the file.

## Fenced and indented code

Lines inside CommonMark-style fenced code blocks are never interpreted as
entry headers. Clew recognizes fences made from at least three backticks or
tildes, indented by no more than three spaces. A closing fence must use the
same character and at least the opening fence's length.

Lines indented by four or more spaces, or by a tab, are also never interpreted
as entry headers.

Code outside an entry is ignored. Code inside an entry is retained as
description content.

Headers with one to three leading spaces are not Clew headers and are ignored
outside an entry or retained inside an entry. Clew never silently removes
indentation from description lines.

## Unrelated Markdown

Markdown before the first valid entry is ignored. An empty file and a file
containing no recognized entries both parse successfully and produce zero work
events.

The human-readable CLI makes this explicit by printing:

```text
No work events found.
```

Headings, lists, block quotes, ordinary prose, inline links, reference links,
and link definitions do not begin entries.

A column-one line beginning with `[` is considered entry-like unless it is a
valid inline link, reference link, or link definition. Entry-like lines that
do not satisfy the header grammar are errors. This rule makes likely entry
mistakes visible instead of silently dropping work.

## Malformed input

Clew reports every malformed entry-like header it can identify, including its
one-based source line number. Empty subjects and categories receive specific
diagnostics.

If a header has no non-blank description, Clew reports the header line.

If any parse diagnostic is produced, parsing fails as a whole. Clew does not
return a partial set of events and never modifies the source file.
