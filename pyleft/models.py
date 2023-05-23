import dataclasses
from pathlib import Path

import pathspec
import pathspec.patterns


@dataclasses.dataclass
class PathSpecDirectory:
    """
    Class to hold a pathspec, and the directory it came from.
    """

    working_directory: Path
    path_spec: pathspec.PathSpec
