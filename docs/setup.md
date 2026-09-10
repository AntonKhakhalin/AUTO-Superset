# Setup guide

## Prerequisites

Use macOS with the [latest Superset release](https://github.com/superset-sh/superset/releases/latest). The source-reviewed baseline is desktop/host/CLI 1.28.0; the runtime's supplied OpenCode baseline is 1.18.29. Install Python 3.10+, Git, Node.js, jq and zsh. Python uses only the standard library.

If Homebrew is already installed, the general utilities can be installed with:

```sh
brew install python git node jq
brew install anomalyco/tap/opencode
```

The OpenCode tap is the installation route recommended by its [official documentation](https://opencode.ai/docs/). macOS includes zsh. Install each selected worker CLI from its provider's official instructions, and authenticate locally. Superset's own setup must generate `~/.superset/bin/opencode`; Codex selections also require `~/.superset/bin/codex`.

Before installing AUTO, start Superset, create/open a local project workspace, and launch your selected CLIs from a Superset terminal. Configure your provider using OpenCode's `/connect` flow as appropriate. Confirm the exact Muse Free route appears in your model picker and complete one small prompt. Then stop all workers and quit the desktop app. The installer never sends a model request.

## Preview and install

```sh
bash install.sh --providers opencode,codex --dry-run
bash install.sh --providers opencode,codex
```

Add `opencode-go` only when you have configured Go and want it eligible for automatic recovery. Add other providers only after installing/authenticating their CLIs. A CLI's presence is not evidence of subscription entitlement.

If multiple Superset hosts exist, identify the intended local host and pass its database explicitly:

```sh
bash install.sh --host-db /path/to/the/intended/host.db --dry-run
bash install.sh --host-db /path/to/the/intended/host.db
```

The installer checks `host_agent_configs` and the 1.28 terminal-binding schema, including `resumed_into_terminal_id`. Open the updated Superset once to complete its own migrations before installing AUTO. It adds rows in a SQLite transaction and backs up changed files with owner-only permissions. It does not replace the host database. Do not restart Superset during installation.

## OpenCode configuration

The default path is `$XDG_CONFIG_HOME/opencode/opencode.json`, or `~/.config/opencode/opencode.json`. AUTO definitions are merged without silently replacing existing values. The rest of your config, including permissions, is preserved. The two Muse agent definitions are needed even if Go is disabled; provider selection prevents the unused Go route from being scheduled.

If you use JSONC, an alternate `OPENCODE_CONFIG`, or a conflicting agent definition, merge the contents of `config/opencode.json` into your chosen config manually. Preserve your other settings. If using Azure, also merge the Azure example. Then run:

```sh
bash install.sh --skip-opencode-config --dry-run
bash install.sh --skip-opencode-config
```

This option means **you have already completed the configuration merge**. It does not validate the alternate file. OpenCode documents config merging and environment/file substitutions in its [configuration guide](https://opencode.ai/docs/config/).

The managed Superset OpenCode wrapper supplies `OPENCODE_CONFIG_DIR` for the AUTO plugins. Launch the coordinator from Superset. Launching the underlying OpenCode binary directly may omit the policy plugin and will not establish an AUTO workspace.

## Azure (optional)

The public example contains only these environment references:

```json
{
  "baseURL": "{env:AUTO_AZURE_BASE_URL}",
  "apiKey": "{env:AUTO_AZURE_API_KEY}"
}
```

Supply your own Azure-compatible base URL and API key through your local environment or credential setup, then select `azure` when installing. Environment values must reach the Superset-launched process; shell startup configuration may be needed. Never commit actual values. No endpoint, deployment, quota, student credit or key belonging to another user is provided.

The example retains the imported model mapping. Verify it matches the deployments/models available at your endpoint. Enabling the `azure` setup option only installs the route; using API-billed work still requires authorization in the task/project policy.

## Project policy

```sh
python3 scripts/setup.py init-project --project /path/to/your/repository
```

This copies only missing files. Set the real project paths, test commands, generated-file rules, and release requirements in `.superset/AUTO_PROJECT.md`. If the project already has `AGENTS.md` or `.superset/setup.sh`, review the corresponding template and integrate any needed instructions yourself. Add your actual dependency installation steps to the setup hook; AUTO cannot infer them reliably for every project.

Commit the reviewed policy/setup files to your project so new worktrees inherit them.

## Live smoke test

1. Reopen Superset and run `python3 scripts/setup.py doctor` from this checkout. Resolve failures.
2. Run `superset agents list --local --json`. Confirm one row for each expected label, especially `AUTO · Fast Fix`, `AUTO · Feature`, and your selected worker. Do not post the full result without checking its `env` fields.
3. Read the quota summary with `"$HOME/.superset/bin/auto-quota-status" --force --summary`. Selected providers must show usable, fresh data before quota-gated work can proceed. Unselected providers remain unknown/disabled.
4. In a disposable project/worktree, use **AUTO · Fast Fix** for a small documentation correction. Confirm the coordinator provides a final response and the diff contains only the requested change.
5. Request a small worker-owned fix. Confirm that a worker launches, pauses visibly for any permission request, writes its completion handoff, and returns control to the coordinator.
6. Check Feature with a bounded planning/implementation task using your selected worker provider. Review the plan, ownership and final validation report.
7. If you selected Go, test it manually before relying on fallback. Actual automatic cap/recovery behavior remains a separate live acceptance item; do not exhaust a quota merely to test it.

Offline tests prove specific recovery-evidence checks with fixtures; they do not certify a real provider's billing, model availability, session recovery or TUI behavior.

For 1.28 native recovery, also follow the [recovery acceptance checklist](superset-1.28.md#upgrade-and-live-acceptance).

## Upgrade and uninstall

Stop workers and quit Superset. Update this checkout, review changes, preview, then install with the desired provider set. Existing custom-row conflicts require reconciliation instead of silent overwrite. To remove a provider, reinstall without it to disable routing/telemetry, then remove its unused custom agent rows in Superset if desired. The installer deliberately does not delete existing rows during upgrades.

Use the printed restore-point directory with `python3 scripts/setup.py restore PATH`. Undo multiple installations in reverse order. Restore preserves unrelated workspace/session data and refuses changed files or edited agent rows. Lifecycle taps added later by the runtime are best-effort observers; normal Superset startup regenerates its managed notify hook.
