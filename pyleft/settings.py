import argparse
from typing import List, Optional

from pyleft.utils import cwd

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # pyright: ignore


class Settings:
    def __init__(self) -> None:
        self.__raw_files: List[str] = []
        self.__raw_exclude: List[str] = []
        self.__no_gitignore: bool = False
        self.__quiet: bool = False
        self.__verbose: bool = False

        self.load_pyproject_toml()
        self.load_args()

    @property
    def no_gitignore(self) -> bool:
        """
        Don't use the exclusions from the .gitignore file(s) in the current working directory.
        """
        return self.__no_gitignore

    @property
    def quiet(self) -> bool:
        """
        Don't print any output to STDOUT.
        """
        return self.__quiet

    @property
    def verbose(self) -> bool:
        """
        Print debugging information to STDERR.
        """
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

        # files
        files_value = self._get_toml_list_key(pyproject_pyleft_data, "files")
        if files_value is not None:
            self.__raw_files = files_value

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
            "files", nargs="+", help="Files/directories to recursively check."
        )
        parser.add_argument(
            "--exclude", nargs="+", help="Glob patterns of files/directories to exclude"
        )
        parser.add_argument(
            "--no-gitignore",
            action="store_true",
            help=self.no_gitignore.__doc__,
        )
        parser.add_argument("--quiet", action="store_true", help=self.quiet.__doc__)
        parser.add_argument("--verbose", action="store_true", help=self.verbose.__doc__)

        args = parser.parse_args()

        # combine these with config file
        self.__raw_files += args.files
        self.__raw_exclude += args.exclude

        # if these are explicitly set with args, override
        if args.no_gitignore:
            self.__no_gitignore = True

        if args.quiet:
            self.__quiet = True

        if args.verbose:
            self.__verbose = True
