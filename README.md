![Cover](./assets/cover.png)
<sub>Banner image by [@aznbokchoy](https://unsplash.com/@aznbokchoy) on Unsplash</sub>

<h1 align="center">Lambda Forked Repo Declutterer</h1>

## Problem:

100+ repositories forked while in Lambda School causing:

- A cluttered repository list.
- Dependabot alert spam.

## Solution:

Rename and archive all of them so:

- Existing work is still available.
- No more notifications from alerts.
- Repos become read-only.
- Repos show up at the bottom of lists with prefixing on places like Netlify, Heroku, etc.

## Process:

Using Github's GraphQL API, we can fetch a list of a user's repositories and modify them. The steps are relatively straightforward:

- Fetch all _public_, _non-archived_, _forked_ repositories.
- Build a list to store references to repositories where the fork parent is from Lambda School.
- Iteratively rename and archive each repository.

To make the script more intelligent, we can create a progress file to track the state for each repository we are modifying. Then, if errors happen, we can resume where we left off at a later time.
