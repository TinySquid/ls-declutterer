import os
import sys
import argparse
from dotenv import load_dotenv


load_dotenv()


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

# Setup command parser
parser = argparse.ArgumentParser()
groupFlags = parser.add_mutually_exclusive_group()
groupFlags.add_argument("--dry-run", help="assemble a list of repositories to be modified", action="store_true")
groupFlags.add_argument("--resume", help="continue from previous run", action="store_true")
groupFlags.add_argument("--undo", help="reverses repo modifications", action="store_true")

args = parser.parse_args()

# Full run prompt
if len(sys.argv) == 1:
    prerun_warning()
