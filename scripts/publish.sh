#!/bin/bash
# Publishes only this curated checkout, using the user's existing GitHub login.
set -euo pipefail
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$repo_dir"
command -v gh >/dev/null || { echo 'Install GitHub CLI first: brew install gh' >&2; exit 1; }
gh auth status >/dev/null 2>&1 || { echo 'Sign in first: gh auth login' >&2; exit 1; }
owner=$(gh api user --jq .login)
python3 scripts/validate.py
if [[ ! -d .git ]]; then
  git init -b main
fi
if git remote get-url origin >/dev/null 2>&1; then
  echo 'origin already exists. Review it and publish manually; this script only creates a new repository.' >&2
  exit 1
fi
if [[ $(git branch --show-current) != main ]]; then
  echo 'Expected branch main; no branch was switched.' >&2
  exit 1
fi
if git rev-parse --verify HEAD >/dev/null 2>&1; then
  echo 'An existing Git history was found. Review it for secrets before publishing manually.' >&2
  exit 1
fi
git add -- .
python3 scripts/scan_public.py --tracked
if ! git var GIT_AUTHOR_IDENT >/dev/null 2>&1; then
  echo 'Set your Git author name and email locally, then rerun.' >&2
  exit 1
fi
git commit -m 'Publish portable AUTO-Superset runtime and setup'
gh repo create "$owner/AUTO-Superset" --public --source=. --remote=origin --push \
  --description 'Quota-aware AUTO coordination, worker supervision, and Fast Fix / Feature workflows for Superset.'
gh repo view "$owner/AUTO-Superset" --json nameWithOwner,url,isPrivate
