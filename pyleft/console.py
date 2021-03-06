import argparse
import sys

from . import api


def run() -> None:
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
        help="Do not read the .gitignore to ignore files",
    )
    parser.add_argument("--quiet", action="store_true", help="Do not print issues")
    parser.add_argument(
        "--verbose", action="store_true", help="Verbose debugging output"
    )

    args = parser.parse_args()

    all_issues = api.main(
        filenames=args.files,
        exclusions=args.exclude,
        no_gitignore=args.no_gitignore,
        verbose=args.verbose,
    )

    # print results in nice format
    if not args.quiet:
        if len(all_issues):
            [print(i) for i in all_issues]
        else:
            print("No issues found")

    # exit with exit code if issues found
    sys.exit(int(len(all_issues) > 0))


if __name__ == "__main__":
    run()
