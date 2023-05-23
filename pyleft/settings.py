import argparse
import dataclasses
from pathlib import Path
from typing import List, Optional

import pathspec
import pathspec.patterns

from pyleft.utils import (
    check_if_file_matches_exclusions,
    cwd,
    load_gitignore,
    verbose_print,
)

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # pyright: ignore


@dataclasses.dataclass
class PathSpecDirectory:
    """
    Class to hold a pathspec, and the directory it came from.
    """

    working_directory: Path
    path_spec: pathspec.PathSpec


class Settings:
    """
    Class to hold and process user settings.
    """

    def __init__(self) -> None:
        self.__raw_paths: List[str] = []
        self.__raw_exclude: List[str] = []
        self.__no_gitignore: bool = False
        self.__quiet: bool = False
        self.__verbose: bool = False

        self.load_pyproject_toml()
        self.load_args()

    def load_exclusions(self) -> List[PathSpecDirectory]:
        """
        Load all of the exclusion patterns.
        """
        path_spec_directories: List[PathSpecDirectory] = []

        if not self.no_gitignore:
            # find all of the gitignore files
            for gitignore in cwd.glob("**/.gitignore"):
                # recursively evaluate exclusions
                # this way gitignored gitignores are not evaluated

                if not check_if_file_matches_exclusions(
                    gitignore, path_spec_directories
                ):
                    verbose_print(self.verbose, f"Loading {gitignore.absolute()}")
                    # record the directory it came from, and build the pattern
                    path_spec_directories.append(
                        load_gitignore(
                            gitignore.parent, gitignore.read_text().splitlines()
                        )
                    )

        # include anything defined by the user or settings
        if self.__raw_exclude:
            path_spec_directories.append(load_gitignore(cwd, self.__raw_exclude))

        return path_spec_directories

    def load_files(self) -> List[Path]:
        """
        Build a list of the file objects that need to be checked.
        """
        all_files: List[Path] = []

        for raw_path in self.__raw_paths:
            # build the path object
            raw_path_obj = Path(raw_path)

            # if it's a file, add it to our list
            if raw_path_obj.is_file():
                all_files.append(raw_path_obj)

            # if it's a directory, find all python files inside
            if raw_path_obj.is_dir():
                all_files.extend(raw_path_obj.glob("**/*.py"))

        # make all paths absolute
        all_files = [a.absolute() for a in all_files]
        return all_files

    @property
    def files(self) -> List[Path]:
        """
        Return a list of filenames that need to be processed after exclusions
        have been applied.
        """
        exclusions = self.load_exclusions()
        all_files = self.load_files()

        # empty list to hold items that pass
        out_files: List[Path] = []

        # iterate through all of the files
        for file in all_files:
            matched = check_if_file_matches_exclusions(file, exclusions)

            # if no matches found, add it to final output
            if not matched:
                out_files.append(file)

        return out_files

    @property
    def no_gitignore(self) -> bool:
        return self.__no_gitignore

    @property
    def quiet(self) -> bool:
        return self.__quiet

    @property
    def verbose(self) -> bool:
        return self.__verbose

    def _get_toml_boolean_key(
        self, pyproject_pyleft_data: dict, key: str
    ) -> Optional[bool]:
        """
        Return the value of a boolean key in toml data
        """
        if key in pyproject_pyleft_data:
            assert isinstance(pyproject_pyleft_data[key], bool)
            return pyproject_pyleft_data[key]

    def _get_toml_list_key(
        self, pyproject_pyleft_data: dict, key: str
    ) -> Optional[List[str]]:
        """
        Return the value of a list key in toml data
        """
        if key in pyproject_pyleft_data:
            assert isinstance(pyproject_pyleft_data[key], (str, list))

            # accept space separated list
            if isinstance(pyproject_pyleft_data[key], str):
                pyproject_pyleft_data[key] = pyproject_pyleft_data[key].split(" ")

            return pyproject_pyleft_data[key]

    def load_pyproject_toml(self) -> None:
        """
        Load settings data from pyproject.toml. This should be called first.
        """

        # create pathlib object for pyproject file
        pyproject_file = cwd.joinpath("pyproject.toml")

        # if it does not exist, cancel
        if not pyproject_file.exists():
            return

        # parse the file
        pyproject_file_data = tomllib.loads(pyproject_file.read_text())

        # check if we have any settings in it
        if (
            "tool" not in pyproject_file_data
            or "pyleft" not in pyproject_file_data["tool"]
        ):
            return

        # reference to our config
        pyproject_pyleft_data = pyproject_file_data["tool"]["pyleft"]

        # extract data into this object
        # =============================

        # paths
        paths_value = self._get_toml_list_key(pyproject_pyleft_data, "paths")
        if paths_value is not None:
            self.__raw_paths = paths_value

        # exclude
        exclude_value = self._get_toml_list_key(pyproject_pyleft_data, "exclude")
        if exclude_value is not None:
            self.__raw_exclude = exclude_value

        # no-gitignore
        no_gitignore_value = self._get_toml_boolean_key(
            pyproject_pyleft_data, "no-gitignore"
        )
        if no_gitignore_value is not None:
            self.__no_gitignore = no_gitignore_value

        # quiet
        quiet_value = self._get_toml_boolean_key(pyproject_pyleft_data, "quiet")
        if quiet_value is not None:
            self.__no_gitignore = quiet_value

        # verbose
        verbose_value = self._get_toml_boolean_key(pyproject_pyleft_data, "verbose")
        if verbose_value is not None:
            self.__no_gitignore = verbose_value

    def load_args(self) -> None:
        """
        Load settings from arguments. This should be called second.
        """

        parser = argparse.ArgumentParser(
            prog="pyleft", description="Python Type Annotation Existence Checker"
        )
        parser.add_argument(
            "paths",
            nargs="+",
            help="File and directory names to recursively check.",
        )
        parser.add_argument(
            "--exclude",
            nargs="+",
            help="Pattern(s) of files/directories to exclude in gitignore format.",
            default=[],
        )
        parser.add_argument(
            "--no-gitignore",
            action="store_true",
            help="Don't use the exclusions from the .gitignore file(s) in the current working directory.",
        )
        parser.add_argument(
            "--quiet", action="store_true", help="Don't print any output to STDOUT."
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Print debugging information to STDERR.",
        )

        args = parser.parse_args()

        # combine these with config file
        self.__raw_paths += args.paths
        self.__raw_exclude += args.exclude

        # if these are explicitly set with args, override
        if args.no_gitignore:
            self.__no_gitignore = True

        if args.quiet:
            self.__quiet = True

        if args.verbose:
            self.__verbose = True
