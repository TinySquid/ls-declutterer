![Cover](./assets/cover.png)
<sub>Banner image by [@aznbokchoy](https://unsplash.com/@aznbokchoy) on Unsplash</sub>

<h1 align="center">Lambda Forked Repo Declutterer</h1>

## Problem:

100+ repositories forked while in Lambda School causing:

- A cluttered repository list.
- Dependabot alert spam.

## Solution:

Rename and archive all of them so:

- Existing work is still available for reference.
- No more notifications from alerts.
- Repos become read-only.
- Repos prefixed, so on places like Netlify and Heroku they will appear at the bottom of the list.

## Process:

Using Github's GraphQL API, we can fetch a list of a user's repositories and modify them. The steps are relatively straightforward:

- Fetch all _public_, _non-archived_, _forked_ repositories.
- Build a list to store references to repositories where the fork parent is from Lambda School.
- Iteratively rename and archive each repository.

To make the script more intelligent, I made a progress system that uses a file to track the state for each repository it modifies. Then, if errors happen, it can resume where it left off at a later time, or be used to revert changes.

## Env:

The script requires a `.env` file with some variables, so copy the `.env.example` file as a template:

```
> cp .env.example .env
```

- `GITHUB_USER` - This needs to be your login username. Used to match repository ownership when fetching.

- `ACCESS_TOKEN` - This is a personal access token with a `public_repo` scope that you will need from Github.

See Github's [adding a personal access token guide](https://docs.github.com/en/github/authenticating-to-github/keeping-your-account-and-data-secure/creating-a-personal-access-token) for instructions.

- `REPO_PREFIX` - A prefix for the renamer to use. I use `zls` so I know its from LambdaSchool and `z` as first char so it pushes all the repos to the bottom of the list, but you can use anything.

## Running locally:

This project is managed with pipenv so you'll need that installed first.

```
> pip install pipenv
```

You will also need a `.env` file setup from the above section.

Install project dependencies and enter the virtualenv shell using the commands:

```
> pipenv install
> pipenv shell
```

On vscode make sure you are using the virtualenv interpreter (`ctrl + shift + p` -> `Python: Select Interpreter`)

On the left of the status bar, you should see something like:

![status bar](assets/virtualenv-vscode.png)

## Commands:

![program usage](assets/usage.png)

A full run of the script (no arguments) will go through the whole process of generating the list of repositories, and then the modified list, and then the actual modification steps.

```
> python script.py
```

I'd recommend running the script with `--gen-list` first to see _what_ repositories it will be modifying, so you can make changes (delete entries) if necessary. Running in full mode will pause and wait for input after generating the list anyways but I prefer the 2 step process.

```
> python script.py --gen-list
```

It will output a file to the `/data` directory called `list.json`. From there, you can verify that you own the repositories and that the parent repository owner is LambdaSchool. With all the checks implemented in the script, I don't believe there will be issues, but it's best to be safe before mass modification.

If you have a `list.json` setup then you can run the script with `--resume` to move on to the modification steps. The prompts are straightforward and if there is a network failure or api issue, it will _always_ save the changes it has made to `data/modified.json` and you can resume or revert with that.

```
> python script.py --resume
```

You can easily undo changes with the `--revert` argument and it will use `modified.json` to restore the listed repositories to their pre-modification state.

```
> python script.py --revert
```

The main thing is DO NOT DELETE `modified.json` as that is the only way for the script to know what repositories to revert or resume work.
