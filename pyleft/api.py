import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Union, Tuple

import pathspec
from pathspec.pathspec import PathSpec
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
    for arg in function.args.kwonlyargs:
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


def load_config(verbose: bool) -> Tuple[List[str], List[str], bool]:
    # try to load config from pyproject.toml file
    pyproject = os.path.join(os.getcwd(), "pyproject.toml")
    if not os.path.isfile(pyproject):
        return [], [], False

    debug_print(verbose, f"Loading {pyproject}")
    with open(pyproject, "r", encoding="utf-8") as fp:
        pyproject_config = toml.load(fp)

    if "tool" not in pyproject_config or "pyleft" not in pyproject_config["tool"]:
        return [], [], False

    debug_print(verbose, "Loading tool.pyleft settings")
    config = pyproject_config["tool"]["pyleft"]

    # load extra files/dirs
    if "files" in config:
        assert isinstance(config["files"], (str, list))

        # accept space separated list
        if isinstance(config["files"], str):
            config["files"] = config["files"].split(" ")

        filenames = config["files"]
    else:
        filenames = []

    # load exclusions
    if "exclude" in config:
        assert isinstance(config["exclude"], (str, list))

        # accept space separated list
        if isinstance(config["exclude"], str):
            config["exclude"] = config["exclude"].split(" ")

        exclusions = config["exclude"]
    else:
        exclusions = []

    # load skip gitignore setting
    if "no-gitignore" in config:
        assert isinstance(config["no-gitignore"], bool)
        no_gitignore = config["no-gitignore"]
    else:
        no_gitignore = False

    return filenames, exclusions, no_gitignore


def does_file_match_exclusion(
    fileobj: Path, specifications: List[Tuple[Path, PathSpec]]
) -> bool:
    for spec in specifications:
        # if the specification is from a directory not a parent to this file, skip
        if spec[0] not in fileobj.parents:
            continue

        # if the speficiaction matches this file relative to the specification,
        # return True
        if spec[1].match_file(fileobj.relative_to(spec[0])):
            return True

    # no matches
    return False


def main(
    filenames: List[str],
    exclusions: List[str] = None,
    no_gitignore: bool = False,
    verbose: bool = False,
) -> Dict[str, List[str]]:

    cwd = Path(os.getcwd())

    # prevent using mutable type
    if exclusions is None:
        exclusions = []

    # load config
    cfg_filenames, cfg_exclusions, cfg_no_gitignore = load_config(verbose)

    # extend cli options
    filenames.extend(cfg_filenames)
    exclusions.extend(cfg_exclusions)
    no_gitignore = no_gitignore or cfg_no_gitignore

    # list of matching specifications, with the directory it came from,
    # and the specification itself
    specifications: List[Tuple[Path, PathSpec]] = []

    # parse exclusions from gitignore
    if not no_gitignore:
        for gitignore in cwd.glob("**/.gitignore"):
            debug_print(verbose, f"Loading {gitignore.absolute()}")
            with open(gitignore, "r", encoding="utf-8") as fp:
                specifications.append(
                    (
                        gitignore.parent.absolute(),
                        pathspec.PathSpec.from_lines(
                            pathspec.patterns.GitWildMatchPattern, fp.readlines()
                        ),
                    )
                )

    # prepare match spec from given exclusions
    specifications.append(
        (
            cwd.absolute(),
            pathspec.PathSpec.from_lines(
                pathspec.patterns.GitWildMatchPattern, exclusions
            ),
        )
    )

    # create data object to hold all result da6a
    all_issues: Dict[str, List[str]] = {}

    # build a list of all files
    all_files = []
    for filename in filenames:
        if os.path.isdir(filename):
            all_files.extend(Path(filename).glob("**/*.py"))
        elif os.path.isfile(filename):
            all_files.append(Path(filename))

    all_files = [p.absolute() for p in all_files]

    # go through all files
    for fileobj in all_files:
        rel_filename = fileobj.relative_to(cwd)

        if does_file_match_exclusion(fileobj, specifications):
            debug_print(verbose, f"Skipping {rel_filename}")
            continue

        debug_print(verbose, f"Checking {rel_filename}")
        all_issues[rel_filename] = check_file(fileobj)

    return all_issues
