import argparse
import os
from datetime import date

from common import get_workspace_paths

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    today = date.today().strftime("%y%m%d")
    parser.add_argument('-d', '--date', type=int, help='Date', default=today)
    args = vars(parser.parse_args())

    if args["date"] < 100000 or args["date"] > 999999:
        print("Invalid date value, exiting.")
        exit(1)

    directories = get_workspace_paths(os.getcwd() + os.sep + "qrgrading-" + str(args["date"]))

    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    print(f"Workspace 'qrgrading-{args["date"]}' created successfully.")
