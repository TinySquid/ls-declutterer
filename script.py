import os
import argparse
import json

from dotenv import load_dotenv

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

load_dotenv()

github_username = os.getenv("GITHUB_USER", None)
personal_access_token = os.getenv("ACCESS_TOKEN", None)
repo_prefix = os.getenv("REPO_PREFIX", None)
lambda_school_org_id = "MDEyOk9yZ2FuaXphdGlvbjI0NzgwMTE0"

if personal_access_token is None or repo_prefix is None or github_username is None:
    print("Missing required .env vars. See README.md for instructions.")
    exit()


def prompt(message):
    """Creates a simple y/n prompt with custom message. Returns boolean value."""
    choice = input(message).split(" ")[0]

    if choice != "y":
        return False

    return True


def generate_list():
    """Creates a list.json file to store repositories to be modified for a given GITHUB_USER account."""

    print("List generation starting...")

    # Pre-check
    if os.path.exists(f"{os.getcwd()}/data/list.json"):
        overwrite = prompt("Found previously generated list, overwrite? (y/n): ")

        if not overwrite:
            print("List generation skipped.")
            return

    print("...")

    # gql setup
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

    # Build list of repositories from query results
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
                print(f"Repo found: {repo['name']}")

    # Save list in JSON format
    with open("./data/list.json", "w") as file:
        file.write(json.dumps(repositories, indent=4))

    print(f"\nTotal repositories found: {len(repositories)}\n")

    print(
        f"List generation complete. Verify and make any necessary changes to repositories in the list stored at: {os.getcwd()}/data/list.json"
    )


def generate_modified_list():
    """Creates a modified.json file to track changes made to repositories from list.json."""

    print("Creating modification progress file...", end=" ")

    modification_list = []

    # Build modification array from list.json.
    with open("./data/list.json", "r") as list_file:
        json_list = json.load(list_file)

        for repo in json_list:
            # Format:
            # { id: "hash", oldName: "Hooks-III", newName: "zls-Hooks-III", renamed: false, archived, false }
            repo_entry = {
                "id": repo["id"],
                "old_name": repo["name"],
                "new_name": f"{repo_prefix}{repo['name']}",
                "renamed": False,
                "archived": False,
            }

            modification_list.append(repo_entry)

    # Dump modification_list to json file.
    with open("./data/modified.json", "w") as mod_file:
        mod_file.write(json.dumps(modification_list, indent=4))

    print("Done.")

    print(f"Total repositories to modify: {len(modification_list)}")

    resume_work()


def resume_work():
    print("Using modified.json to edit repositories...")

    print("Done.")


def revert_work():
    print("Using modified.json to revert changes...")

    print("Done.")


def main_start():
    generate_list()

    move_forward = prompt("Continue with modification? (y/n): ")

    if not move_forward:
        exit()

    generate_modified_list()


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
    # Create / overwrite list.json.
    generate_list()

elif args.resume:
    # Work from modified.json.
    if os.path.exists(f"{os.getcwd()}/data/modified.json"):
        resume_work()
    else:
        print("modified.json file not found. Nothing to resume.")

elif args.revert:
    if os.path.exists(f"{os.getcwd()}/data/modified.json"):
        revert_work()
    else:
        print("modified.json file not found. Nothing to revert.")

else:
    if os.path.exists(f"{os.getcwd()}/data/modified.json"):
        resume = prompt("modified.json file found. Resume from there? (y/n): ")

        if not resume:
            warn_accept = prompt(
                "Overwriting modified.json is NOT recommended, only go forward if you know what you are doing.\nContinue? (y/n): "
            )

            if warn_accept:
                main_start()

        else:
            resume_work()
    else:
        main_start()
