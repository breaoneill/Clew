import json
from pathlib import Path

import pytest

from clew.cli import main

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_defaults_to_human_readable_output(capsys: pytest.CaptureFixture[str]) -> None:
    main(["parse", str(FIXTURES / "20260723.md")])

    captured = capsys.readouterr()
    assert "2026-07-23 | Widgets Inc | SUP" in captured.out
    assert "Investigate SELinux log report error." in captured.out
    assert "Source: 20260723.md:5" in captured.out
    assert captured.err == ""


def test_parse_can_emit_json(capsys: pytest.CaptureFixture[str]) -> None:
    main(["parse", str(FIXTURES / "20260723.md"), "--json"])

    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result[0] == {
        "date": "2026-07-23",
        "subject": "Widgets Inc",
        "category": "SUP",
        "description": "Investigate SELinux log report error.",
        "source_filename": "20260723.md",
        "source_line_number": 5,
    }
    assert len(result) == 2
    assert captured.err == ""


def test_parse_reports_malformed_entries(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as raised:
        main(["parse", str(FIXTURES / "20260724.md")])

    captured = capsys.readouterr()
    assert raised.value.code == 2
    assert "20260724.md:1: malformed entry header" in captured.err
    assert "20260724.md:4: entry requires at least one description line" in captured.err
