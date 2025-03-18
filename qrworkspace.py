import argparse
import os
from datetime import date

from common import get_workspace_paths

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    today = date.today().strftime("%Y%m%d")
    parser.add_argument('-d', '--date', type=int, help='Date', default=today)
    args = vars(parser.parse_args())

    if args["date"] < 20200101 or args["date"] > 21000101:
        print("Invalid date value")
        exit(1)

    directories = get_workspace_paths(os.getcwd() + os.sep + "qrgrading-" + str(args["date"]))

    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    print("Workspace created successfully.")
