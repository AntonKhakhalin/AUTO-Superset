#!/bin/sh
# Add this repository's actual dependency/setup commands after the checks.
set -eu
for command in auto-dispatch auto-worker-watch auto-policy-context; do
  if [ ! -x "$HOME/.superset/bin/$command" ]; then
    printf 'AUTO runtime missing: %s. Install AUTO-Superset on this machine first.\n' "$command" >&2
    exit 1
  fi
done
printf 'AUTO runtime found. Configure project dependency setup in .superset/setup.sh.\n'
