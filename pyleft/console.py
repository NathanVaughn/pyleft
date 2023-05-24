import sys

import pyleft.api
from pyleft.printing import quiet_print
from pyleft.settings import Settings


def run() -> None:
    # load arguments when called from command line
    Settings.load_args()

    # run
    all_issues = pyleft.api.main()

    # print results
    if len(all_issues):
        [quiet_print(i) for i in all_issues]
        exit_code = 1
    else:
        quiet_print("No issues found")
        exit_code = 0

    # exit with exit code if issues found
    sys.exit(exit_code)


if __name__ == "__main__":
    run()
