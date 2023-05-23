import pytest

from pyleft.api import does_arg_have_default, does_kwarg_have_default


@pytest.mark.parametrize(
    "arg_position, arg_count, defaults, output",
    [
        (0, 5, [3, 4, 5], False),
        (1, 5, [3, 4, 5], False),
        (2, 5, [3, 4, 5], True),
        (3, 5, [3, 4, 5], True),
        (4, 5, [3, 4, 5], True),
        (0, 3, [1, 2, 3], True),
        (1, 3, [1, 2, 3], True),
        (2, 3, [1, 2, 3], True),
    ],
)
def test_does_arg_have_default(
    arg_position: int, arg_count: int, defaults: list, output: bool
) -> None:
    assert does_arg_have_default(arg_position, arg_count, defaults) == output


@pytest.mark.parametrize(
    "arg_position, defaults, output",
    [
        (0, [1, None, 3], True),
        (1, [1, None, 3], False),
        (2, [1, None, 3], True),
    ],
)
def test_does_kwarg_have_default(
    arg_position: int, defaults: list, output: bool
) -> None:
    assert does_kwarg_have_default(arg_position, defaults) == output
