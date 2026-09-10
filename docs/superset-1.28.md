# Superset 1.28 compatibility review

Reviewed 2026-09-10 for AUTO **9.9.5-public.1**. Live macOS/provider acceptance is pending.

The [1.28 release](https://github.com/superset-sh/superset/releases/tag/desktop-v1.28.0) spans **66 commits**, with **560 added/modified files and 27 deleted files** relative to desktop-v1.27.0. The complete recursive trees and individual commit file lists were checked; the compare API alone truncates at 300 files. [The inventory](upstream-1.28-inventory.json) records every net path and commit. Review depth is a complete change inventory plus focused code review of AUTO-facing contracts, rather than a line-by-line audit of all 587 application files.

Pinned source commits:

- Base: `a32cd9091928efe75cf9c1fbaeb4e87df60a91c0`
- Target: `a415227dc25f806dd3ef6bf05b464adba5ac08fb`

## Changes that affect AUTO

| Upstream change | AUTO consequence |
| --- | --- |
| [#7263: OpenCode identity and resume](https://github.com/superset-sh/superset/pull/7263) | Root `session_id` now travels through the notify hook. Child sessions and nested harnesses cannot replace the outer identity. Prefer this native identity over hook-only guesses. |
| [#7253: host account-switch relaunch](https://github.com/superset-sh/superset/pull/7253) | Native recovery can happen on the host without a mounted pane. Follow persisted successor links, including multi-hop relaunches. |
| [Native claim and successor persistence](https://github.com/superset-sh/superset/blob/desktop-v1.28.0/packages/host-service/src/terminal-agents/persistence.ts) | An atomic claim changes `end_reason` to `resumed`; `resumed_into_terminal_id` records the successor. AUTO reads this schema and verifies the original conversation and exclusive ownership. |
| [Native resume router](https://github.com/superset-sh/superset/blob/desktop-v1.28.0/packages/host-service/src/trpc/router/terminal-agents/terminal-agents.ts) | A definitely empty, never-prompted session can launch fresh upstream. A fresh conversation is not AUTO same-session recovery and will not be adopted. |
| [#7284: typed PTY failures](https://github.com/superset-sh/superset/pull/7284) | Classify available `SHELL_EXITED`, `PTY_SPAWN_FAILED`, and `PTY_SPAWN_TIMEOUT` causes separately. Keep numeric exit/signal facts, discard raw shell arguments/output. |
| [#7299: daemon readiness and timeout diagnostics](https://github.com/superset-sh/superset/pull/7299) | Startup failure, silence, in-flight requests and late replies describe control health. They do not establish worker death. |
| [#7309: attach/reap race](https://github.com/superset-sh/superset/pull/7309), [#7358: unresponsive clients](https://github.com/superset-sh/superset/pull/7358) | Attach cancellation, a reaped snapshot, a dropped client, and a living PTY are distinct. A readable old snapshot cannot cancel recovery for an exited binding. |
| [#7291](https://github.com/superset-sh/superset/pull/7291), [#7300: migration identity](https://github.com/superset-sh/superset/pull/7300) | Require the migrated 1.28 host schema. Let Superset perform migrations; AUTO never creates or patches upstream tables. |
| [#7264](https://github.com/superset-sh/superset/pull/7264), [#7314: reconnecting panes](https://github.com/superset-sh/superset/pull/7314) | An unreachable-host banner is not a failed worker. Keep recovery ownership protected. |
| [#7270: host versions](https://github.com/superset-sh/superset/pull/7270) | Check the local host and regenerated CLI as well as the desktop version. A desktop update alone does not prove host compatibility. |
| [#7277](https://github.com/superset-sh/superset/pull/7277), [#7286](https://github.com/superset-sh/superset/pull/7286), [#7329: intentional aborts](https://github.com/superset-sh/superset/pull/7329) | Do not convert deliberate worker/git cancellation into provider quota failure. |
| [#7278](https://github.com/superset-sh/superset/pull/7278), [#7279](https://github.com/superset-sh/superset/pull/7279), [#7280](https://github.com/superset-sh/superset/pull/7280), [#7303](https://github.com/superset-sh/superset/pull/7303), [#7327](https://github.com/superset-sh/superset/pull/7327) | Environment, transcript, diff, descriptor and nested-repository fixes do not replace AUTO's handoff, quota, or policy checks. |
| [#7306](https://github.com/superset-sh/superset/pull/7306), [#7326](https://github.com/superset-sh/superset/pull/7326), [#7328](https://github.com/superset-sh/superset/pull/7328) | Host process startup and diagnostics changed. AUTO does not ingest or publish full crash tails, account data or oversized worker output. |

The remaining inventory covers Changes/reviewer panes, workspace creation/navigation, Pages, cloud workspace UI, mobile terminal caching/status, marketing, billing, Linear/automation delivery, updater behavior, integrations skills, tests and generated assets. These do not justify changing AUTO's provider entitlements, workflow scope, billing rules, or project policy. No upstream application code is vendored by this update.

## Recovery contract

1. Learn the provider-native root session from the original terminal's persisted binding. Pin the host database, workspace, agent identity and definition.
2. On terminal/control loss, retain `NATIVE_RESUMING` and give Superset automatic resurrection its grace (default 30 seconds). No competing dispatch is permitted.
3. Follow native `resumed_into_terminal_id` links, bounded to 16 hops. Adopt only a live, unambiguously owned terminal with the same provider session. A native claim with no successor yet remains protected.
4. If native recovery does not appear, recheck the unexpected-exit predicate and the normal scoped quota gate. Before the one explicit fallback, retire the already-exited source with `superset terminals close`. The upstream close marks a binding disposed before killing it; an earlier native `resumed` claim is sticky. Verify the result: if native won, follow it; if retirement is unconfirmed, do not launch.
5. Launch at most one `superset agents create --resume-session` for that logical worker, retaining explicit model/effort overrides. Launch without a prompt. A returned `sessionId` identifies a terminal, not the provider conversation; require the persisted binding before adopting it.
6. Send at most one bounded continuation after ownership verification. Do not retry an unconfirmed send. Keep the original worker ID, task and durable handoff.
7. A known explicit duplicate can be closed only after matching its ownership; confirm its exit before adopting another writer. An unknown launch, native claim, database, or cleanup outcome becomes `SUPERVISION_LOST` for reconciliation, never permission to dispatch a replacement.

The supported close-before-launch step prevents a stale original candidate from resurrecting again after an explicit fallback. AUTO never writes to `host.db`. Manual launches outside AUTO remain outside its lock; concurrent same-session terminals stop adoption.

## Failure information and its limits

Superset's new typed PTY causes are defined on the **desktop terminal IPC** path. The [CLI terminal read command](https://github.com/superset-sh/superset/blob/desktop-v1.28.0/packages/cli/src/commands/terminals/read/command.ts) calls the host-service snapshot API; it does **not promise** to expose every desktop `error.cause` field. AUTO consumes a structured cause or its rendered message when a failed control command actually supplies it. Missing diagnostics remain unknown. No new log-scraping or private IPC bridge is assumed.

`terminalFailure` retains a sanitized kind, available numeric exit/signal values, and available daemon timing facts. It never treats successful terminal screen text as a PTY diagnostic. Confirmed PTY failure can become `FAILED_TERMINAL` only after native recovery has had its chance, the source is retired, and no unresolved launch or live competing binding exists. Explicit launch uncertainty and daemon failures remain `SUPERVISION_LOST`.

Existing provider quota/busy/model classifications remain separate. A quota gate still blocks explicit recovery; if native ownership could remain, the supervisor requests reconciliation instead of authorizing a replacement writer.

## Preserved behavior

- `auto-workspace-supervisor`, `NATIVE_RESUMING` and duplicate-writer checks remain active.
- `auto-muse-supervisor` and its **v9.9.4.1 Free→Go verifier are unchanged**: exact session, expected provider/model, fresh completed assistant turn, no error, nonzero output tokens. Native terminal adoption is not Go recovery success.
- Durable handoffs, quota supervision, `AUTO_PROJECT` inheritance, hidden policy, Clean Coordinator Chat, and integration ownership checks remain required.
- This release changes neither subscriptions nor permission/billing settings.

## Upgrade and live acceptance

1. Stop AUTO work, upgrade Superset to **1.28.0**, reopen it to finish local/host migrations, and launch OpenCode once to regenerate the native wrapper/plugin. Then quit Superset and stop AUTO supervisors.
2. Update this checkout. Run `bash install.sh --providers YOUR_EXISTING_SELECTION --dry-run`, then the same command without `--dry-run`. The installer preserves existing settings and prints a restore point.
3. Reopen Superset, run `python3 scripts/setup.py doctor`, and follow the [setup smoke test](setup.md#live-smoke-test).
4. In a disposable worker task, verify root session identity, an unexpected-terminal-loss recovery, the same task/handoff after native adoption, and no duplicate writer. Deliberately closing a pane must not resurrect it. Check a naturally encountered account-switch recovery separately if you use that feature.
5. Verify the explicit fallback under controlled conditions, including source retirement and one attempt, plus your selected route/model/effort after recovery. Do not exhaust paid quotas merely to test Free→Go.

No additional private project-source files are needed for this update. Superset supplies its generated wrappers, native plugin and migrated host database locally; users must supply their own authenticated providers and project policy. Live macOS recovery, model restoration, account switching and provider behavior remain unverified in this Linux fixture environment.
