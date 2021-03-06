# PyLeft

[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![GitHub license](https://img.shields.io/github/license/NathanVaughn/pyleft)](https://github.com/NathanVaughn/pyleft/blob/main/LICENSE)
[![PyPi versions](https://img.shields.io/pypi/pyversions/pyleft)](https://pypi.org/project/pyleft)
[![PyPi downloads](https://img.shields.io/pypi/dm/pyleft)](https://pypi.org/project/pyleft)

Python type annotation existence checker

---

`pyleft` is a complement to Microsoft's [pyright](https://github.com/microsoft/pyright)
tool. While `pyright` does an excellent job at type checking your Python code,
it doesn't check to make sure type hints exist. If you forget to add type hints
to a function, `pyright` will usually see no problems with it. This tool checks
to make sure all of your code _has_ type hints, while leaving it to `pyright` to make
sure they are actually correct.

## Installation

PyLeft requires Python 3.6.2+.

`pip install pyleft`

## Usage

PyLeft is a Python module that can be run via `python -m`. Just provide the directories
or files to recursively check.

`python -m pyleft .`

The module will exit with an exit code of 0 if all type hints are present, or 1
if there are any issues.

### Example

```bash
> pyleft .
- tests\files\fail_1.py
        Argument 'two' of function 'add:1' has no type annotation
- tests\files\fail_2.py
        Function 'add:1' has no return type annotation
- tests\files\fail_3.py
        Function 'drive:2' has no return type annotation
- tests\files\fail_4.py
        Argument 'one' of function 'wheels:4' has no type annotation
```

## Options

- `files`: List of filenames and/or directories to recursively check.
- `--exclude`: (optional) List of patterns to exclude, in `.gitignore` format. Takes predecence over `files`.
- `--no-gitignore`: (optional) Don't use the exclusions from the .gitignore from the current working directory.
- `--quiet`: (optional) Don't print any output to STDOUT.
- `--verbose`: (optional) Print debugging information to STDERR.

## Configuration

Configuration is done through the `pyproject.toml` file.

```toml
[tool.pyleft]
# "files" in the configuration file are added to the option given on the command line
# This can either be a list, or a space separated string
files = ["extra/directory/"]
# This can either be a list, or a space separated string
exclude = ["*_pb2.py"]
no-gitignore = true
```

The `quiet` and `verbose` options can only be specified from the command line.

## Design Decisions

Only files with a `.py` extension are checked. Currently, `.pyi` files are not checked.

The `__init__` and `__new__` methods of a class are not required to
have return type hints. `pyright` automatically assumes this to be `None`.

The first (`self`) argument of any class method is not required to have a type hint.

The first (`cls`) argument of any class `@property` or `@classmethod` or `__new__`
method is not required to have a type hint.

Any variable argument list (`*arg`) or keyword argument dict (`**kwarg`)
is not required to have a type hint.

Types of types, such as `List` or `Tuple` are not required. For example,
a type hint of just `list` is allowed, although you should normally be as specific
as possible with a better type hint like `List[int]`.

## Disclaimer

This project is not affiliated in any way with Microsoft.
