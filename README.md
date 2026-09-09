# AUTO-Superset

**Give Superset a coordinator that can delegate work, track quota, supervise workers, and recover interrupted sessions.**

AUTO-Superset adds two workflows to [Superset](https://superset.sh): **Fast Fix** for small corrections and **Feature** for work that needs planning and coordinated implementation. It packages the AUTO runtime, OpenCode plugins, agent configuration, and project policies into a portable installer.

**Public preview · macOS · Superset 1.27.0+ · AUTO 9.9.4.1-public.1**

> This is an independent community project. Superset and each provider CLI are installed separately. Offline installation/recovery checks are included; a live macOS smoke test is still required before relying on unattended operation.

[Quick start](#quick-start) · [Setup guide](docs/setup.md) · [Workflow](docs/workflow.md) · [Troubleshooting](docs/troubleshooting.md) · [Source audit](docs/source-audit.md)

## What it adds

- **Two task profiles.** Fast Fix keeps small work narrow; Feature introduces a planner and scoped workers when useful.
- **Quota-aware routing.** Reads available quota information before dispatch, with provider-specific gates and explicit provider selection.
- **Worker supervision.** One local supervisor tracks registered workers, completion, permission prompts, failures, and native resume state.
- **Free → Go recovery.** Preserves the Muse session when the selected, authenticated Go route has sufficient quota. Recovery completion must match the exact session and model route.
- **Cleaner coordinator output.** Isolates OpenCode presentation preferences and supplies concise status messages.
- **Project-specific rules.** Loads your repository's `AGENTS.md` and `.superset/AUTO_PROJECT.md` with policy fingerprints and integration checks.

The coordinator currently uses **Muse Spark 1.3 through OpenCode**. It is not an interchangeable coordinator backend. Worker providers are optional, and model access depends on your accounts.

## Quick start

### 1. Prepare Superset and your CLIs

Install the [latest Superset desktop release](https://github.com/superset-sh/superset/releases/latest), sign in, and initialize a local workspace. Enable its CLI using the app's setup instructions.

Install Python 3.10+, Git, Node.js, jq, zsh, [OpenCode](https://opencode.ai/docs/), and the worker CLI you want to use. The default selection is OpenCode + Codex. Sign in to providers yourself; this project supplies no credentials or subscriptions.

From a Superset terminal, launch OpenCode and your selected worker CLI once. In OpenCode, verify that the Muse Free model is available and complete one small prompt. This initializes the local database used by quota telemetry. Then stop workers and quit Superset completely.

### 2. Install AUTO

```sh
git clone https://github.com/AntonKhakhalin/AUTO-Superset.git
cd AUTO-Superset
bash install.sh --dry-run
bash install.sh
```

The installer checks prerequisites, adds the selected agent rows, merges the AUTO OpenCode agent definitions, and saves a restore point. Existing Superset projects, sessions, settings, and native agent configurations are preserved. Conflicting custom agents or OpenCode values stop the install with an explanation.

To use a different selection, pass the same selection to preview and install:

```sh
bash install.sh --providers opencode,claude --dry-run
bash install.sh --providers opencode,claude
```

| Provider option | What it enables |
| --- | --- |
| `opencode` | Muse Free coordinator and leaf worker; required |
| `opencode-go` | Optional Go recovery and Go worker routes |
| `codex` | Codex worker routes and quota gate |
| `claude` | Claude worker routes and quota telemetry |
| `cursor` | Cursor worker routes and included-usage gates |
| `antigravity` | `agy` worker routes and quota telemetry |
| `azure` | Optional Azure OpenCode configuration; your own endpoint and key |

Start with one worker provider. Installing all providers is unnecessary. The installer does not enable billing or install permission-bypass flags. Existing native agent permissions remain yours to manage.

### 3. Set up your project

```sh
python3 scripts/setup.py init-project --project /path/to/your/repository
```

Review the generated `.superset/AUTO_PROJECT.md` and set the actual build, test, and release commands. Existing policy/setup files are preserved; merge the template into them when needed.

### 4. Start a task

Reopen Superset, open your project workspace, and choose **AUTO · Fast Fix** or **AUTO · Feature** from the agent picker.

```sh
python3 scripts/setup.py doctor
```

Use a small, reversible task first, such as a documentation correction. Follow the [live smoke test](docs/setup.md#live-smoke-test) to verify launch, completion, and your selected providers.

## Choose a workflow

| | Fast Fix | Feature |
| --- | --- | --- |
| Best for | Local bugs and small existing-feature changes | New features and changes across components |
| Planning | Short inspection; no mandatory planner for a small fix | Eligible strategic planner when needed |
| Execution | Direct micro-fix or one scoped worker | Scoped workers with explicit ownership |
| Validation | Focused checks for the affected behavior | Checks and review proportional to risk |
| Escalation | Moves to Feature when evidence warrants it | Preserves the task contract through recovery |

AUTO never schedules extra work just to consume subscription quota. Unselected providers are excluded from routing and telemetry, including cached quota records.

## Repository layout

| Path | Purpose |
| --- | --- |
| `runtime/bin/` | Coordinator, dispatch, quota, policy, and supervision commands |
| `runtime/opencode/` | Hidden-policy and conversation-mirror plugins |
| `config/` | Portable agent definitions, logical routes, and optional Azure example |
| `templates/project/` | Starter repository policy and setup hook |
| `scripts/setup.py` | Install, diagnose, initialize a project, and restore |
| `scripts/validate.py` | Offline syntax, configuration, and behavioral checks |
| `scripts/scan_public.py` | Secret-pattern and private-artifact scan |
| `docs/` | Setup, architecture, limitations, and source audit |
| `tests/` | Installation rollback and recovery-evidence regression tests |

## Updates and restore

Stop active AUTO workers and quit Superset before installing an update. Pull the reviewed changes and rerun the installer with your chosen providers. Changed files receive a new restore point; identical installs are no-ops.

```sh
python3 scripts/setup.py restore /path/to/restore-point --dry-run
python3 scripts/setup.py restore /path/to/restore-point
```

Restore points are printed after installation. Restore refuses to overwrite files or agent rows edited afterward. It removes only the agents added by that installation and restores the files that installation changed.

## Compatibility and limits

- Superset **1.27.0** is the source-reviewed baseline; its CLI exposes per-launch `--model`, `--effort`, and `--resume-session`. Newer releases require a smoke test. [Upstream implementation](https://github.com/superset-sh/superset/blob/desktop-v1.27.0/packages/cli/src/commands/agents/create/command.ts)
- The supplied runtime came from an **OpenCode 1.18.29** setup. It uses OpenCode plugin hooks, local session storage, and TUI preferences that can change between releases.
- The installer supports **macOS**. Linux CI checks portability of source and fixture behavior; it does not establish Linux desktop support. Windows is not supported by this installer.
- Some quota adapters use provider web endpoints or local databases. Unknown quota is not proof of available capacity. Muse Free thresholds are estimates, not a provider guarantee.
- Recovery, notifications, and chat rendering require live verification in your installation. See [troubleshooting](docs/troubleshooting.md).

## Contributing

Run `python3 -B scripts/validate.py` before opening a pull request. Add focused regression coverage for changes to installation, recovery, or policy enforcement. Share sanitized diagnostics; never upload your entire Superset directory.

See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and the [MIT license](LICENSE).
