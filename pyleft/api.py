import ast
import sys
from pathlib import Path
from typing import List, Tuple, Union

from pyleft.path_utils import cwd
from pyleft.printing import verbose_print
from pyleft.settings import Settings

try:
    pass
except ImportError:
    pass  # pyright: ignore

type_comments = sys.version_info >= (3, 8)


def does_arg_have_default(arg_position: int, arg_count: int, defaults: list) -> bool:
    """
    For positional arguments, the defaults list provided by the ast, lists
    defaults for the last X arguments.

    So if there are 5 arguments, and 3 defaults, only the last 3 have defaults.
    """
    return arg_count - (arg_position + 1) < len(defaults)


def does_kwarg_have_default(arg_position: int, defaults: list) -> bool:
    """
    For keyword arguments, the defaults list provided by the ast, lists
    defaults for all arguments. If a value is None, then there is no default.

    So if there are 5 arguments, and 3 defaults, only the last 3 have defaults.
    """
    return defaults[arg_position] is not None


def check_function(
    function: Union[ast.FunctionDef, ast.AsyncFunctionDef],
    inside_class: bool,
) -> List[Tuple[str, int]]:
    """
    Check a single function for type annotations and return a list of tuples of issues.
    The first item in the tuple is the issue, the second item is the line number.
    """
    function_issues: List[Tuple[str, int]] = []

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
            # see if argument has a default value, and if so, if the user is okay with this
            if Settings.ignore_if_has_default and does_arg_have_default(
                i, len(function.args.args), function.args.defaults
            ):
                continue

            function_issues.append(
                (
                    f"Argument '{arg.arg}' of function '{function.name}' has no type annotation",
                    function.lineno,
                )
            )

    # check keyword arguments for type annotations
    for j, arg in enumerate(function.args.kwonlyargs):
        if arg.annotation is None:
            # see if argument has a default value, and if so, if the user is okay with this
            if Settings.ignore_if_has_default and does_kwarg_have_default(
                j, function.args.kw_defaults
            ):
                continue

            function_issues.append(
                (
                    f"Argument '{arg.arg}' of function '{function.name}' has no type annotation",
                    function.lineno,
                )
            )

    # check that function has a return type annotation
    # __init__ and __new__ functions are allowed to have no return type annotation
    if function.returns is None and function.name not in ["__init__", "__new__"]:
        function_issues.append(
            (
                f"Function '{function.name}' has no return type annotation",
                function.lineno,
            )
        )

    return function_issues


def walk_ast(
    node: Union[ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef],
    file_content: List[str],
    inside_class: bool = False,
) -> List[Tuple[str, int]]:
    """
    Walk an AST tree and check all functions inside recursively
    and return a list of strings of issues
    """
    # list of messages and line number tuples
    ast_issues: List[Tuple[str, int]] = []

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
    results = walk_ast(ast_tree, file_content=file_content)

    return [f'"{file.absolute()}:{r[1]}" {r[0]}' for r in results]


def main() -> List[str]:
    # record all the issues we find
    all_issues: List[str] = []

    # start looping
    for file in Settings.files:
        verbose_print(f"Checking {file.relative_to(cwd)}")
        all_issues.extend(check_file(file))

    return all_issues
