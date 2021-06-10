import os
import sys
from dotenv import load_dotenv

load_dotenv()


def print_usage():
    print("usage: {0} [--dry-run] [--resume] [--undo]".format(sys.argv[0]))
    exit()


def missing_vars():
    print("Missing required .env vars. See README.md for instructions.")
    exit()


def prerun_warning():
    print(
        "It is recommended to first run this script with the '--dry-run' flag "
        "so you can inspect the changes that will be made."
    )
    print("Continue anyways? (y/n)")

    choice = str(sys.stdin.read(1))

    if choice == "n":
        exit()


accessToken = os.getenv("ACCESS_TOKEN", None)
repoPrefix = os.getenv("REPO_PREFIX", None)

if accessToken is None or repoPrefix is None:
    missing_vars()

# Prompt on full run
if len(sys.argv) == 1:
    prerun_warning()

print_usage()
