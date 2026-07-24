import json
from pathlib import Path

import pytest

from clew.cli import main

FIXTURES = Path(__file__).parent / "fixtures"


def test_validate_single_daynote(
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = FIXTURES / "20260723.md"

    assert main(["validate", str(path)]) == 0

    captured = capsys.readouterr()
    assert captured.out == (
        f"Validating: {path}\n"
        "DayNotes: 1\n"
        "Events: 2\n"
        "Date range: 2026-07-23 to 2026-07-23\n"
        "Categories: DEV, SUP\n"
        "Status: valid\n"
    )
    assert captured.err == ""


def test_validate_week_directory(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "20260713.md").write_text(
        "[First] [SUP]\nSupported.\n", encoding="utf-8"
    )
    (tmp_path / "20260716.md").write_text(
        "[Second] [DEV]\nDeveloped.\n", encoding="utf-8"
    )
    (tmp_path / "README.md").write_text("Ignored.\n", encoding="utf-8")

    assert main(["validate", str(tmp_path)]) == 0

    captured = capsys.readouterr()
    assert "DayNotes: 2\n" in captured.out
    assert "Events: 2\n" in captured.out
    assert "Date range: 2026-07-13 to 2026-07-16\n" in captured.out
    assert captured.out.endswith("Status: valid\n")
    assert captured.err == ""


def test_validate_json_has_stable_structure(
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = FIXTURES / "20260725.md"

    assert main(["validate", str(path), "--json"]) == 0

    assert json.loads(capsys.readouterr().out) == {
        "path": str(path),
        "valid": True,
        "daynotes": 1,
        "events": 2,
        "start_date": "2026-07-25",
        "end_date": "2026-07-25",
        "categories": ["DEV", "SUP"],
        "errors": [],
    }


def test_validate_malformed_daynote_reports_diagnostics(
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = FIXTURES / "20260724.md"

    assert main(["validate", str(path)]) == 1

    captured = capsys.readouterr()
    assert captured.out.endswith("Status: invalid\n")
    assert "malformed entry header" in captured.err


def test_validate_rejects_unsupported_category(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = tmp_path / "20260713.md"
    path.write_text("[Internal] [OPS]\nMaintenance.\n", encoding="utf-8")

    assert main(["validate", str(path), "--json"]) == 1

    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert report["valid"] is False
    assert report["categories"] == ["OPS"]
    assert report["errors"] == ["unsupported categories: OPS"]
    assert "unsupported categories: OPS" in captured.err


@pytest.mark.parametrize(
    ("kind", "expected_error"),
    [
        ("missing", "path does not exist"),
        ("invalid_file", "invalid file type"),
        ("empty_directory", "directory contains no DayNotes"),
        ("md_directory", "directory whose name ends in .md"),
    ],
)
def test_validate_rejects_invalid_inputs(
    kind: str,
    expected_error: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = tmp_path / "missing"
    if kind == "invalid_file":
        path = tmp_path / "notes.txt"
        path.write_text("not Markdown", encoding="utf-8")
    elif kind == "empty_directory":
        path = tmp_path / "week"
        path.mkdir()
    elif kind == "md_directory":
        path = tmp_path / "20260713.md"
        path.mkdir()

    assert main(["validate", str(path)]) == 1

    captured = capsys.readouterr()
    assert captured.out.endswith("Status: invalid\n")
    assert expected_error in captured.err


def test_validate_missing_path_argument_preserves_argparse_exit_two() -> None:
    with pytest.raises(SystemExit) as raised:
        main(["validate"])

    assert raised.value.code == 2
