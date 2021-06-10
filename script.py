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


def prerun_warning():
    print(
        "It is recommended to first run this script with the '--dry-run' flag "
        "so you can inspect the changes that will be made."
    )
    print("Continue anyways? (y/n)")

    choice = str(sys.stdin.read(1))

    if choice == "n":
        exit()


githubUser = os.getenv("GITHUB_USER", None)
accessToken = os.getenv("ACCESS_TOKEN", None)
repoPrefix = os.getenv("REPO_PREFIX", None)
lambdaSchoolUser = "MDEyOk9yZ2FuaXphdGlvbjI0NzgwMTE0"  # Lambda org ID

if accessToken is None or repoPrefix is None or githubUser is None:
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

# Dry run mode will fetch the repositories and write them to a file but won't modify them.
# Useful to make sure everything looks right before going through with the changes.
if args.dry_run:
    print("Dry run starting...\n")

    transport = AIOHTTPTransport(
        url="https://api.github.com/graphql", headers={"Authorization": "bearer {0}".format(accessToken)}
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
        additionalRepositories = result["viewer"]["repositories"]["nodes"]

        if len(additionalRepositories) == 0 or params["cursor"] == "null":
            break

        # Add only personal LambdaSchool forks
        for repo in additionalRepositories:
            if repo["parent"]["owner"]["id"] == lambdaSchoolUser and repo["owner"]["login"] == githubUser:
                repositories.append(repo)

    # Write list to file
    with open("./data/dry-run.json", "w") as file:
        file.write(json.dumps(repositories, indent=4))

    # Print repo names
    for repo in repositories:
        print(repo["name"])

    print(
        "\nDry run complete. Verify repositories in the list stored at: {0}".format(os.getcwd() + "/data/dry-run.json")
    )
