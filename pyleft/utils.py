import os
import sys
from pathlib import Path

cwd = Path(os.getcwd())


def verbose_print(verbose: bool, message: str) -> None:
    """
    Verbose print function wrapped in if statement.
    Only prints if `verbose` is True.
    """
    if verbose:
        print(message, file=sys.stderr)


def quiet_print(quiet: bool, message: str) -> None:
    """
    Quiet print function wrapped in if statement.
    Only prints if `quiet` is False.
    """
    if not quiet:
        print(message, file=sys.stdout)
