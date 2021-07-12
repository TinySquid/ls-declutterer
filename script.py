import os
import argparse
import json

from time import sleep
from dotenv import load_dotenv
from distutils.util import strtobool

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

# Ensure all environment variables are good to go.
load_dotenv()

GITHUB_USERNAME = os.getenv("GITHUB_USER", None)
PERSONAL_ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", None)
REPO_PREFIX = os.getenv("REPO_PREFIX", None)
SKIP_RENAME_STEP = bool(strtobool(os.getenv("SKIP_RENAME_STEP", "False")))
SKIP_ARCHIVE_STEP = bool(strtobool(os.getenv("SKIP_ARCHIVE_STEP", "False")))
LAMBDASCHOOL_ORG_ID = "MDEyOk9yZ2FuaXphdGlvbjI0NzgwMTE0"

if GITHUB_USERNAME is None or PERSONAL_ACCESS_TOKEN is None or REPO_PREFIX is None:
    print("Missing required .env vars. See README.md for instructions.")
    exit()

# GraphQL queries
fetch_repositories_query = gql(
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

rename_mutation = gql(
    """
    mutation($repository_id: String, $name: String) {
        updateRepository(input: {repositoryId: $repository_id, name: $name}) {
            repository {
                name
            }
        }
    }
    """
)

archive_mutation = gql(
    """
    mutation($repository_id: String) {
        archiveRepository(input: {repositoryId: $repository_id}) {
            repository {
                isArchived
            }
        }
    }
    """
)

unarchive_mutation = gql(
    """
    mutation($repository_id: String) {
        unarchiveRepository(input: {repositoryId: $repository_id}) {
            repository {
                isArchived
            }
        }
    }
    """
)

# Meat and potatos.
def prompt(message):
    """Creates a simple y/n prompt with custom message. Returns boolean value."""
    choice = input(message).split(" ")[0]

    if choice != "y":
        return False

    return True


def read_json_file(path):
    """Returns JSON parsed data from file."""
    with open(path, "r") as file:
        return json.load(file)


def write_json_file(path, data):
    """Stores dict as JSON object to file."""
    with open(path, "w") as file:
        file.write(json.dumps(data, indent=4))


def setup_gql_client():
    """Returns a graphql client instance authorized with github token."""
    transport = AIOHTTPTransport(
        url="https://api.github.com/graphql",
        headers={"Authorization": f"bearer {PERSONAL_ACCESS_TOKEN}"},
    )

    return Client(transport=transport)


def generate_list():
    """Creates a list.json file to store repositories to be modified for a given GITHUB_USER account."""

    print("List generation starting...")

    # Overwrite check
    if os.path.exists(f"{os.getcwd()}/data/list.json"):
        overwrite = prompt("Found previously generated list, overwrite? (y/n): ")

        if not overwrite:
            print("List generation skipped.")
            return

    print("...")

    # Build list of repositories from paginated query results
    repositories = []
    params = {"cursor": None}

    while True:
        result = client.execute(fetch_repositories_query, variable_values=params)

        params["cursor"] = result["viewer"]["repositories"]["pageInfo"]["endCursor"]
        additional_repositories = result["viewer"]["repositories"]["nodes"]

        if len(additional_repositories) == 0 or params["cursor"] == "null":
            break

        # Add only personal LambdaSchool forks
        for repo in additional_repositories:
            if (
                repo["parent"]["owner"]["id"] == LAMBDASCHOOL_ORG_ID
                and repo["owner"]["login"] == GITHUB_USERNAME
            ):
                repositories.append(repo)
                print(f"Repo found: {repo['name']}")

    # Save to list.json
    write_json_file("./data/list.json", repositories)

    print(f"\nTotal repositories found: {len(repositories)}\n")

    print(
        f"List generation complete. Verify and make any necessary changes to repositories in the list stored at: {os.getcwd()}/data/list.json"
    )


def generate_modified_list():
    """Creates a modified.json file to track changes made to repositories from list.json."""

    print("Creating modification progress file...", end=" ")

    modification_list = []

    # Build modification array from list.json.
    repo_list = read_json_file("./data/list.json")

    for repo in repo_list:
        # Shape:
        # { id: "hash", oldName: "Hooks-III", newName: "zls-Hooks-III", renamed: false, archived, false }
        repo_entry = {
            "id": repo["id"],
            "old_name": repo["name"],
            "new_name": f"{REPO_PREFIX}{repo['name']}",
            "renamed": False,
            "archived": False,
        }

        modification_list.append(repo_entry)

    # Save to modified.json
    write_json_file("./data/modified.json", modification_list)

    print("Done.")

    print(f"Total repositories to modify: {len(modification_list)}")

    resume_work()


def dummy_check():
    if SKIP_RENAME_STEP and SKIP_ARCHIVE_STEP:
        print(
            "You've set both steps to be skipped in the .env file. Nothing to do here..."
        )
        exit()


def rename_repo(repo):
    """Renames a passed in repository. See generate_modified_list()
    for repo param shape."""

    if SKIP_RENAME_STEP or repo["renamed"]:
        print(f"Skipping {repo['id']}")
    else:
        result = client.execute(
            rename_mutation,
            variable_values={"repository_id": repo["id"], "name": repo["new_name"]},
        )

        if result["updateRepository"]["repository"]["name"] == repo["new_name"]:
            print(f"Renamed: {repo['id']}")
            return True
        else:
            print(f"Update failed for repository with id: {repo['id']} (rename).")
            return False


def revert_repo_rename(repo):
    """Renames a passed in repository to its original name. See generate_modified_list()
    for repo param shape."""

    result = client.execute(
        rename_mutation,
        variable_values={"repository_id": repo["id"], "name": repo["old_name"]},
    )

    if result["updateRepository"]["repository"]["name"] == repo["old_name"]:
        print(f"Renamed: {repo['id']}")
        return True
    else:
        print(f"Update failed for repository with id: {repo['id']} (rename).")
        return False


def archive_repo(repo):
    """Archives a passed in repository. See generate_modified_list()
    for repo param shape. Returns True on success, False on failure."""

    if SKIP_ARCHIVE_STEP or repo["archived"]:
        print(f"Skipping {repo['id']}")
    else:
        result = client.execute(
            archive_mutation,
            variable_values={"repository_id": repo["id"]},
        )

        if result["archiveRepository"]["repository"]["isArchived"] == True:
            print(f"Archived: {repo['id']}")
            return True
        else:
            print(f"Update failed for repository with id: {repo['id']} (archive).")
            return False


def unarchive_repo(repo):
    """Unarchives a passed in repository. See generate_modified_list()
    for repo param shape. Returns True on success, False on failure."""

    result = client.execute(
        unarchive_mutation,
        variable_values={"repository_id": repo["id"]},
    )

    if result["unarchiveRepository"]["repository"]["isArchived"] == False:
        print(f"Unarchived: {repo['id']}")
        return True
    else:
        print(f"Update failed for repository with id: {repo['id']} (archive).")
        return False


def revert_repo_changes(repo):
    """Handles reverting modifications to a repository. See generate_modified_list()
    for repo param shape."""
    if repo["archived"]:
        # A repository must be un-archived before changing its name
        unarchive_repo(repo)
    revert_repo_rename(repo)


def resume_work(revert=False):
    """Performs the rename/archive steps to every repository listed in modified.json."""
    print("Using modified.json to edit repositories...")

    repo_list = read_json_file("./data/modified.json")

    # Bruh
    dummy_check()

    # Rename and archive iteratively (ignore previous work or global skip setting)
    for repo in repo_list:
        repo["renamed"] = rename_repo(repo, revert)
        sleep(0.05)
        repo["archived"] = archive_repo(repo, revert)
        sleep(0.05)

    # Save changes
    write_json_file("./data/modified.json", repo_list)

    print("Done.")


def revert_work():
    """Performs the work... in reverse :)"""
    resume_work(revert=True)


def main_start():
    """Starts the script from the beginning when no args are passed in."""
    generate_list()

    move_forward = prompt("Continue with modification? (y/n): ")

    if not move_forward:
        exit()

    generate_modified_list()

    resume_work()


# CLI options
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

# Init graphql client and auth with github
client = setup_gql_client()


# Run behaviour
if args.gen_list:
    generate_list()

elif args.resume:
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
