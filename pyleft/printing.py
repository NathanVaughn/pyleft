import sys

from pyleft.settings import Settings


def verbose_print(message: str) -> None:
    """
    Verbose print function wrapped in if statement.
    Only prints if `verbose` is True.
    """
    if Settings.verbose:
        print(message, file=sys.stderr)


def quiet_print(message: str) -> None:
    """
    Quiet print function wrapped in if statement.
    Only prints if `quiet` is False.
    """
    if not Settings.quiet:
        print(message, file=sys.stdout)
