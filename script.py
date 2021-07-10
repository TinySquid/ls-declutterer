import os
import sys
import argparse
import json

from dotenv import load_dotenv

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

load_dotenv()


def missing_vars():
    print("Missing required .env vars. See README.md for instructions.")
    exit()


def prompt(message):
    """Creates a simple y/n prompt with custom message"""
    choice = input(message).split(" ")[0]

    if choice != "y":
        exit()


def generate_list():
    # Pre-check
    if os.path.exists(f"{os.getcwd()}/data/list.json"):
        prompt("Found previously generated list, overwrite? (y/n): ")

    print("List generation starting...\n")

    transport = AIOHTTPTransport(
        url="https://api.github.com/graphql",
        headers={"Authorization": f"bearer {personal_access_token}"},
    )

    client = Client(transport=transport)

    query = gql(
        """
        query($cursor: String) {
            viewer {
                repositories(isFork: true, first: 100, after: $cursor, privacy: PUBLIC) {
                    pageInfo {
                        endCursor
                    }
                    nodes {
                        id
                        name
                        url
                        owner {
                            login
                        }
                        parent {
                            owner {
                                id
                                login
                            }
                        }
                    }
                }
            }
        }
        """
    )

    params = {"cursor": None}
    repositories = []

    # Build list of repositories
    while True:
        result = client.execute(query, variable_values=params)

        params["cursor"] = result["viewer"]["repositories"]["pageInfo"]["endCursor"]
        additional_repositories = result["viewer"]["repositories"]["nodes"]

        if len(additional_repositories) == 0 or params["cursor"] == "null":
            break

        # Add only personal LambdaSchool forks
        for repo in additional_repositories:
            if (
                repo["parent"]["owner"]["id"] == lambda_school_org_id
                and repo["owner"]["login"] == github_username
            ):
                repositories.append(repo)

    # Write list to file
    with open("./data/list.json", "w") as file:
        file.write(json.dumps(repositories, indent=4))

    # Print repo names
    for repo in repositories:
        print(f"Repo: {repo['name']}")

    print(
        f"\nList generation complete. Verify repositories in the list stored at: {os.getcwd()}/data/list.json"
    )


def resume_work():
    print("Resuming work from modified.json...\n")
    print("Done.")


def revert_work():
    print("Reverting changes from modified.json...\n")
    print("Done.")


def main_start():
    generate_list()
    prompt("Continue? (y/n): ")


github_username = os.getenv("GITHUB_USER", None)
personal_access_token = os.getenv("ACCESS_TOKEN", None)
repo_prefix = os.getenv("REPO_PREFIX", None)
lambda_school_org_id = "MDEyOk9yZ2FuaXphdGlvbjI0NzgwMTE0"  # Lambda org ID

if personal_access_token is None or repo_prefix is None or github_username is None:
    missing_vars()

# Setup command parser
parser = argparse.ArgumentParser()
group_flags = parser.add_mutually_exclusive_group()
group_flags.add_argument(
    "--gen-list",
    help="assemble a list of repositories to be modified",
    action="store_true",
)
group_flags.add_argument(
    "--resume", help="continue from previous run", action="store_true"
)
group_flags.add_argument("--revert", help="reverses modifications", action="store_true")

args = parser.parse_args()

# Run chosen methods

if args.gen_list:
    """
    create / overwrite list.json
    """
    generate_list()

elif args.resume:
    """ """
    resume_work()

elif args.revert:
    """
    - Check pre-existing modified.json
    * file exists:
    - Revert modifications to repositores from the modified.json list.
    * file does not exist:
    - inform user.
    """
    revert_work()

else:
    """
    Full execution
    - Check for pre-existing modified.json, run resume_work() if found.
    * no modified.json:
    - generate_list().
    - Wait for user input (verification).
    - Create modified.json.
    - Modify repositories, updating modified.json in sync.
    """
    if os.path.exists(f"{os.getcwd()}/data/modified.json"):
        resume_work()
    else:
        main_start()
