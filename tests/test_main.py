import os
from pathlib import Path

import pytest

import pyleft.api
from pyleft.settings import Settings

FILES_DIR = os.path.join(os.path.dirname(__file__), "files")


def test_pass() -> None:
    print(pyleft.api.check_file(Path(FILES_DIR, "pass.py")))
    assert len(pyleft.api.check_file(Path(FILES_DIR, "pass.py"))) == 0


@pytest.mark.parametrize(
    "filename, issue",
    [
        ("fail_1.py", "two"),
        ("fail_2.py", "return"),
        ("fail_3.py", "return"),
        ("fail_4.py", "one"),
    ],
)
def test_fail(filename: str, issue: str) -> None:
    assert issue in pyleft.api.check_file(Path(FILES_DIR, filename))[0].lower()


def test_ignore_if_has_default() -> None:
    Settings._ignore_if_has_default = True
    assert len(pyleft.api.check_file(Path(FILES_DIR, "options_1.py"))) == 0

    Settings._ignore_if_has_default = False
    assert len(pyleft.api.check_file(Path(FILES_DIR, "options_1.py"))) > 0
