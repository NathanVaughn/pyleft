import os
from pathlib import Path

import pytest

import pyleft.api

FILES_DIR = os.path.join(os.path.dirname(__file__), "files")


def test_pass():
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
def test_fail(filename: str, issue: str):
    assert issue in pyleft.api.check_file(Path(FILES_DIR, filename))[0].lower()
