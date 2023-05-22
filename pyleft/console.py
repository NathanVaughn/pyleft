import sys

from pyleft import api
from pyleft.settings import Settings
from pyleft.utils import quiet_print


def run() -> None:
    settings = Settings()

    all_issues = api.main(files=settings.files, verbose=settings.verbose)

    # print results
    if len(all_issues):
        [quiet_print(settings.quiet, i) for i in all_issues]
        exit_code = 1
    else:
        quiet_print(settings.quiet, "No issues found")
        exit_code = 0

    # exit with exit code if issues found
    sys.exit(exit_code)


if __name__ == "__main__":
    run()
