import os
import warnings
from pathlib import Path
from typing import List

import pathspec

from pyleft.models import PathSpecDirectory

cwd = Path(os.getcwd())


def check_if_file_matches_exclusions(
    file: Path, exclusions: List[PathSpecDirectory]
) -> bool:
    """
    Check if the given file object matches the given exclusion patterns
    """

    # iterate through the exclusion patterns
    for exclusion in exclusions:
        # if the exlcusion comes from a directory this file is not in, skip
        if exclusion.working_directory not in file.parents:
            continue

        rel_file = file.relative_to(exclusion.working_directory)

        # if this exclusion matches this file relative to the directory
        if exclusion.path_spec.match_file(rel_file):
            return True

    # if no matches found
    return False


def load_gitignore(working_directory: Path, lines: List[str]) -> PathSpecDirectory:
    """
    Load a gitignore file with the ability to slice out invalid lines.
    """
    try:
        return PathSpecDirectory(
            working_directory=working_directory,
            path_spec=pathspec.GitIgnoreSpec.from_lines(
                lines,
            ),
        )

    except ValueError:
        # if we get a value error, manually slice out the invalid lines
        patterns = []

        for line in lines:
            try:
                # try to add the pattern
                patterns.append(
                    pathspec.patterns.gitwildmatch.GitWildMatchPattern(line)
                )
            except ValueError as e:
                # print a warning
                warnings.warn(str(e))

        # build spec with invalid lines sliced out
        return PathSpecDirectory(
            working_directory=working_directory,
            path_spec=pathspec.GitIgnoreSpec(patterns),
        )
