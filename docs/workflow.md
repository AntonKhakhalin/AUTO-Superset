# How AUTO works

## Main components

| Component | Responsibility |
| --- | --- |
| `auto-muse-coordinator` | Select Free/Go, load project policy, stage TUI preferences and start the resident supervisor |
| `auto-muse-supervisor` | Follow the same Muse session and verify recovery on the exact Go route |
| `auto-policy-context` | Render coordinator/worker instructions and policy fingerprints |
| `auto-policy-ack`, `auto-policy-git-guard` | Acknowledge current project policy before guarded integration operations |
| `auto-dispatch`, native launcher, route resolver | Resolve a logical agent route, apply gates and create a worker through Superset |
| `auto-workspace-supervisor` | Own registered worker state, lifecycle events and native-resume coordination |
| `auto-worker-watch` | Collect worker events in the foreground and return control when attention is needed |
| `auto-lifecycle-tap`, `auto-hook-install` | Observe the Superset-managed notification hook; retain terminal fallback if its shape changes |
| `auto-present`, OpenCode plugins | Provide concise statuses and local coordinator text history |
| `auto-quota-status` and provider gates | Read supported/empirical quota sources without a model inference request |

The versioned native launcher and legacy watcher are active dependencies. Their filenames are preserved because runtime callers reference them. They are not disposable backups.

## Fast Fix

The coordinator classifies a localized task into MICRO, FAST WORKER or ESCALATED. A safe micro-fix may be performed directly. Otherwise, one eligible worker receives a narrow contract and relevant validation. A failed assumption, wider scope, or consequential design change moves the task to Feature in the same top-level session.

Fast Fix avoids mandatory strategic planning, pre-implementation independent review, and broad validation for every tiny change. Git safety, quota checks, worker ownership and recovery rules still apply.

## Feature

Choose an eligible strategist, preferring the configured Astra planning route when it is available. Use explicit PLAN ONLY contracts and divide implementation into bounded scopes. Parallel work is useful only when scopes are independent and quotas/capabilities support it. Select review and validation according to the task's actual risk.

The public installation policy overrides personal subscription assumptions and utilization targets embedded in the inherited runtime. The selected provider/route list is the routing boundary. Installed CLIs, free-tier labels and estimated quotas do not establish entitlement or authorize spending.

## Completion and recovery

The workspace supervisor is the authoritative state writer. `WAITING_INPUT` means an interaction needs attention. `NATIVE_RESUMING` protects the current logical writer while Superset recovery is active. Follow the updated terminal/session binding and do not start a competing writer.

Superset **1.28 native OpenCode identity and resurrection are the preferred recovery source**. The supervisor follows persisted successor lineage and verifies the same session, host, workspace, harness, definition and exclusive writer. A lifecycle hook alone cannot rebind ownership. After native grace, at most one explicit `--resume-session` fallback is allowed: recheck quota/ownership, retire the already-exited source through Superset, verify retirement, launch without a prompt, then verify the new binding before one continuation. Unconfirmed operations require ownership reconciliation. See the [full recovery contract](superset-1.28.md#recovery-contract).

The v9.9.4.1 Free → Go verification remains unchanged. Free → Go recovery requires fresh, reserve-safe Go telemetry and a verified completion on the expected provider/model in the same session. A different model's completion, a zero-token placeholder, an error record or an unrelated session is insufficient. Go must be selected during installation and authenticated locally.

Keep the user's original prompt separate from runtime policy transport. The OpenCode policy plugin supplies the coordinator bootstrap. A missing policy plugin/file is an error; do not work around it by running without policy enforcement.

The original workflow documents have been condensed into this guide and the project templates. Detailed runtime recovery contracts remain in the runtime source. Quota amounts, daily utilization targets and account-specific configuration are not requirements for public users.
