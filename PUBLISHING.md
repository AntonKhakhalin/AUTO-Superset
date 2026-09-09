# Publish the prepared package to GitHub

The package is prepared locally. Creating the remote repository requires a GitHub login with repository-creation rights. This file does not indicate that publication has already happened.

## First publication

Extract the package, open Terminal, and enter its `AUTO-Superset` directory. Install GitHub CLI if needed and sign in to the account that should own the repository:

```sh
brew install gh
gh auth login
bash scripts/publish.sh
```

The script runs offline validation and the public-content scan, initializes a fresh `main` branch, commits the curated package, and creates **AUTO-Superset as a public repository** under the signed-in GitHub account. It then prints the repository URL and visibility. It never uploads the original project-source ZIP or the Superset home directory.

Git needs your author name/email configured. Use GitHub's no-reply email if you do not want your personal email in commit metadata. Configure those values yourself; the script does not choose or expose an email for you.

The script refuses an existing `origin` or existing commit history. If repository creation/push fails after the commit is made, inspect the error and use normal `gh repo create` / `git push` commands to finish that reviewed checkout. Do not delete or rewrite history just to rerun the helper.

If the repository already exists, review its contents and visibility first. Do not overwrite another repository to reuse its name. GitHub may require granting the connected app access to a newly created repository before tools in ChatGPT can edit it.

After publication, confirm the README and Actions checks render correctly. Complete the macOS/provider smoke test before describing this preview as an end-to-end validated release.
