import json
from pathlib import Path

import pytest

from clew.cli import main

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_has_exact_human_readable_output(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["parse", str(FIXTURES / "20260725.md")])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == (
        "2026-07-25 | First | DEV\n"
        "First description.\n"
        "Source: 20260725.md:1-2\n"
        "\n"
        "2026-07-25 | Second | SUP\n"
        "Second description.\n"
        "Source: 20260725.md:3-4\n"
    )
    assert captured.err == ""


def test_parse_emits_versioned_json_envelope(
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = FIXTURES / "20260723.md"
    exit_code = main(["parse", str(path), "--json"])

    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert exit_code == 0
    assert result == {
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
                    "location": str(path),
                    "span": {"start_line": 5, "end_line": 6},
                },
            },
            {
                "date": "2026-07-23",
                "subject": "NWB",
                "category": "DEV",
                "description": (
                    "Cloud server imaging.\nRecord the resulting image identifier."
                ),
                "provenance": {
                    "source_type": "markdown",
                    "source_id": "20260723.md",
                    "location": str(path),
                    "span": {"start_line": 8, "end_line": 10},
                },
            },
        ],
    }
    assert captured.err == ""


def test_zero_entries_has_explicit_output(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["parse", str(FIXTURES / "20260728.md")])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "No work events found.\n"
    assert captured.err == ""


@pytest.mark.parametrize(
    "path_factory",
    [
        lambda root: root / "missing" / "20260803.md",
        lambda root: root / "20260803.md",
    ],
)
def test_file_failures_exit_one(
    tmp_path: Path,
    path_factory: object,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = path_factory(tmp_path)  # type: ignore[operator]
    if path == tmp_path / "20260803.md":
        path.mkdir()

    exit_code = main(["parse", str(path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err.startswith("clew: error:")


def test_encoding_date_and_parse_failures_exit_one(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    invalid_encoding = tmp_path / "20260804.md"
    invalid_encoding.write_bytes(b"\xff")
    invalid_date = tmp_path / "notes.md"
    invalid_date.write_text("", encoding="utf-8")

    assert main(["parse", str(invalid_encoding), "--json"]) == 1
    assert main(["parse", str(invalid_date)]) == 1
    assert main(["parse", str(FIXTURES / "20260724.md")]) == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.count("clew: error:") == 3


def test_invalid_cli_usage_exits_two() -> None:
    with pytest.raises(SystemExit) as raised:
        main(["parse"])

    assert raised.value.code == 2


def test_parse_directory_uses_week_parser(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "20260803.md").write_text("[First] [DEV]\nMonday.\n", encoding="utf-8")
    (tmp_path / "20260804.md").write_text(
        "[Second] [SUP]\nTuesday.\n", encoding="utf-8"
    )

    assert main(["parse", str(tmp_path), "--json"]) == 0

    result = json.loads(capsys.readouterr().out)
    assert [event["date"] for event in result["events"]] == [
        "2026-08-03",
        "2026-08-04",
    ]


def test_nws_export_writes_csv_to_stdout(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    note = tmp_path / "20260803.md"
    note.write_text("[Widgets] [DEV]\nBuilt exporter.\n", encoding="utf-8")

    assert main(["export", "nws", str(note)]) == 0
    captured = capsys.readouterr()
    assert captured.out == (
        "Date,Subject,Category,Description\n2026-08-03,Widgets,DEV,Built exporter.\n"
    )
    assert captured.err == ""


def test_nws_export_can_write_a_file(tmp_path: Path) -> None:
    note = tmp_path / "20260803.md"
    note.write_text("[Widgets] [DEV]\nBuilt exporter.\n", encoding="utf-8")
    destination = tmp_path / "timesheet.csv"

    assert main(["export", "nws", str(note), "--output", str(destination)]) == 0

    assert destination.read_text(encoding="utf-8") == (
        "Date,Subject,Category,Description\n2026-08-03,Widgets,DEV,Built exporter.\n"
    )
