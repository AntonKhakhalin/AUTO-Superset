# Troubleshooting

| Symptom | Next step |
| --- | --- |
| Installer asks you to quit Superset | Stop active workers and quit the desktop/host processes. Do not kill a worker mid-write just to install an update. |
| No host database found | Open Superset and initialize a local workspace once, then quit. |
| Multiple host databases | Pass the exact intended `--host-db`; do not guess or copy another machine's DB. |
| Unsupported database schema | Stop installation and review the new upstream schema. The installer does not create/migrate Superset tables. |
| Managed OpenCode/Codex wrapper missing | Launch that CLI from Superset, then quit and retry. Do not copy a generated wrapper from someone else's machine. |
| OpenCode config conflict | Reconcile the named key. For JSONC/alternate config, merge manually and use `--skip-opencode-config`. |
| Agent label conflict or duplicates | Rename/remove the obsolete conflicting row in Superset after reviewing it. AUTO resolves labels exactly and needs a unique match. |
| `CONTROL_PLANE_HANDOFF_REQUIRED` at first start | Initialize OpenCode with one completed Muse Free prompt, verify the model is available, and inspect scoped quota telemetry. Go must be selected and usable if Free is unavailable. |
| Provider not enabled | Reinstall with that provider after installing/authenticating its CLI; do not edit cached quota to make it look available. |
| Model or effort rejected | Check the installed provider/Superset model catalog and update the matching logical route. The shipped route names are a snapshot. |
| Worker shows `WAITING_INPUT` | Respond to the actual permission or input request. Public templates do not bypass permission prompts. |
| Worker shows `NATIVE_RESUMING` | Allow its protected same-session recovery; follow the supervisor's terminal binding. |
| Clean chat becomes noisy | Verify OpenCode version and isolated TUI preferences. Set `SUPERSET_AUTO_PRESENTATION_DEBUG=1` only for local diagnosis; review logs before sharing. |
| Missing lifecycle tap after a Superset update | The coordinator reapplies its observer when it recognizes the hook. Unknown hook shapes retain terminal fallback; inspect `auto-hook-install --check`. |
| Restore refuses a file or agent row | It was edited after installation. Preserve that work and reconcile it manually; do not force overwrite. |

Start with `python3 scripts/setup.py doctor`. It reports local prerequisite presence and Superset version; it does not certify authentication, every model or recovery behavior. The [live smoke test](setup.md#live-smoke-test) covers those next steps.

Never attach an entire Superset home directory to an issue. It can contain account credentials, workspace metadata, session text, terminal history, and cached quota. Share the command name, sanitized error, versions, and a small reproduction.

## Superset 1.28 recovery

- A missing `resumed_into_terminal_id` column means Superset has not completed its host migrations. Reopen the updated app, then quit it before reinstalling AUTO. Do not create the column yourself.
- A native claim without a successor, multiple same-session bindings, an unconfirmed source retirement, or an explicit launch timeout keeps ownership unresolved. Do not dispatch another writer or reset the attempt counter. Reconcile the intended host/session first.
- `terminalFailure.kind` distinguishes shell/PTY failure, daemon startup/timeout, attach cancellation and control disconnect when those diagnostics reach AUTO. Missing desktop IPC details are not supplied by the CLI snapshot contract.
- If a continuation timed out, inspect the adopted terminal before resubmitting: AUTO does not retry a possibly delivered prompt.
- If the doctor flags the native OpenCode plugin, launch OpenCode from Superset 1.28 to regenerate it. AUTO retains its own policy/mirror plugins and observes the managed notification hook.

See [the 1.28 review and live acceptance checklist](superset-1.28.md).
