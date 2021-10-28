import ast
import fnmatch
import os
import sys
from pathlib import Path
from typing import Dict, List, Union

import pathspec
import toml

type_comments = sys.version_info >= (3, 8)


def debug_print(verbose: bool, message: str) -> None:
    if verbose:
        print(message, file=sys.stderr)


def check_function(
    function: Union[ast.FunctionDef, ast.AsyncFunctionDef], inside_class: bool
) -> List[str]:
    """
    Check a single function for type annotations and return a list of strings of issues
    """
    function_issues = []
    function_name = f"{function.name}:{function.lineno}"

    has_classmethod = any(
        isinstance(decorator, ast.Name)
        and decorator.id == "classmethod"
        and isinstance(decorator.ctx, ast.Load)
        for decorator in function.decorator_list
    )

    has_property = any(
        isinstance(decorator, ast.Name)
        and decorator.id == "property"
        and isinstance(decorator.ctx, ast.Load)
        for decorator in function.decorator_list
    )

    for i, arg in enumerate(function.args.args):
        # if the function is inside a class, and is a class method
        if inside_class and i == 0 and arg.arg == "cls" and has_classmethod:
            continue

        # if the function is inside a class, and is a property
        if inside_class and i == 0 and arg.arg == "cls" and has_property:
            continue

        # if the function is the __new__ method
        if inside_class and i == 0 and arg.arg == "cls" and function.name == "__new__":
            continue

        # if the function is inside a class, and is a normal method
        if inside_class and i == 0 and arg.arg == "self":
            continue

        # static methods have no special treatment

        # check positional arguments for type annotations
        if arg.annotation is None:
            function_issues.append(
                f"Argument '{arg.arg}' of function '{function_name}' has no type annotation"
            )

    # check keyword arguments for type annotations
    for i, arg in enumerate(function.args.kwonlyargs):
        if arg.annotation is None:
            function_issues.append(
                f"Argument '{arg.arg}' of function '{function_name}' has no type annotation"
            )

    # check that function has a return type annotation
    # __init__ and __new__ functions are allowed to have no return type annotation
    if function.returns is None and function.name not in ["__init__", "__new__"]:
        function_issues.append(
            f"Function '{function_name}' has no return type annotation"
        )

    return function_issues


def walk_ast(
    node: Union[ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef],
    file_content: List[str],
    inside_class: bool = False,
) -> List[str]:
    """
    Walk an AST tree and check all functions inside recursively
    and return a list of strings of issues
    """
    ast_issues = []

    for sub_node in node.body:
        if isinstance(sub_node, ast.ClassDef):
            # walk children of class
            ast_issues.extend(walk_ast(sub_node, file_content, inside_class=True))
        elif isinstance(sub_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # skip the function if "noqa" in the same line as the function
            if "# noqa" not in file_content[sub_node.lineno - 1]:
                # check the function's type annotations
                ast_issues.extend(check_function(sub_node, inside_class=inside_class))

            # still, walk the children of the function as you can put
            # functions inside functions
            ast_issues.extend(walk_ast(sub_node, file_content))

    return ast_issues


def check_file(file: Path) -> List[str]:
    """
    Check a single file for type annotations and return a list of strings of issues
    """
    # read the contents of the file
    file_content = file.read_text(encoding="utf-8").splitlines()

    # not supported in Python 3.7 and below
    kwargs = {}
    if type_comments:
        kwargs["type_comments"] = True

    # parse the file
    ast_tree = ast.parse("\n".join(file_content), filename=file.name, **kwargs)
    # walk the ast
    return walk_ast(ast_tree, file_content=file_content)


def main(
    filenames: List[str],
    exclusions: List[str] = None,
    skip_gitignore: bool = False,
    verbose: bool = False,
) -> Dict[str, List[str]]:
    if exclusions is None:
        exclusions = []

    # try to load config from pyproject.toml file
    pyproject = os.path.join(os.getcwd(), "pyproject.toml")
    if os.path.isfile(pyproject):
        debug_print(verbose, f"Loading {pyproject}")
        with open(pyproject, "r", encoding="utf-8") as fp:
            pyproject_config = toml.load(fp)

        if "tool" in pyproject_config and "pyleft" in pyproject_config["tool"]:
            debug_print(verbose, "Loading tool.pyleft settings")
            config = pyproject_config["tool"]["pyleft"]

            # load extra files/dirs
            if "files" in config:
                assert isinstance(config["files"], (str, list))

                # accept space separated list
                if isinstance(config["files"], str):
                    config["files"] = config["files"].split(" ")

                filenames.extend(config["files"])

            # load exclusions
            if "exclude" in config:
                assert isinstance(config["exclude"], (str, list))

                # accept space separated list
                if isinstance(config["exclude"], str):
                    config["exclude"] = config["exclude"].split(" ")

                exclusions.extend(config["exclude"])

            # load skip gitignore setting
            if "no-gitignore" in config:
                assert isinstance(config["no-gitignore"], bool)
                skip_gitignore = config["no-gitignore"]

            # load quiet setting
            if "quiet" in config:
                assert isinstance(config["quiet"], bool)
                quiet = config["quiet"]

            # load verbose setting
            if "verbose" in config:
                assert isinstance(config["verbose"], bool)
                verbose = config["verbose"]

    # parse exclusions from gitignore
    if not skip_gitignore:
        gitignore = os.path.join(os.getcwd(), ".gitignore")
        if os.path.isfile(gitignore):
            debug_print(verbose, f"Loading {gitignore}")
            with open(gitignore, "r", encoding="utf-8") as fp:
                exclusions.extend(fp.readlines())

    # prepare match spec from all exclusions
    spec = pathspec.PathSpec.from_lines(
        pathspec.patterns.GitWildMatchPattern, exclusions
    )

    # create data object to hold all result da6a
    all_issues: Dict[str, List[str]] = {}

    # iterate through all files
    for filename in filenames:
        # if the filename is a directory, recursively walk it
        if os.path.isdir(filename):
            for sub_file in Path(filename).glob("**/*.py"):
                # skip files that are in the exclusions list
                # compute relative filename to parent directory so as to properly
                # match gitignore and other exclusion patterns
                if spec.match_file(sub_file.relative_to(filename)):
                    debug_print(verbose, f"Skipping {sub_file}")
                    continue

                debug_print(verbose, f"Checking {sub_file}")
                all_issues[str(sub_file.relative_to(filename))] = check_file(sub_file)

        # if the filename is a file, check only that
        elif os.path.isfile(filename):
            # also make sure file is not in exclusions
            if spec.match_file(filename):
                debug_print(verbose, f"Skipping {filename}")
                continue

            debug_print(verbose, f"Checking {filename}")
            all_issues[filename] = check_file(Path(filename))

    return all_issues
