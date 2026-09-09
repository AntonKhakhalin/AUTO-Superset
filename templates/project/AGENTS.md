# Project instructions

Read the current user request, this file, and `.superset/AUTO_PROJECT.md` before changing this repository. Derive commands and project structure from the actual source; never invent validation results.

## Work and Git safety

- Work in the assigned worktree. Preserve unrelated staged, unstaged and untracked files.
- Do not discard changes, reset/clean/stash work, force checkout, rewrite history, or force push without explicit authorization.
- Keep write ownership clear. Do not create a competing writer while another worker or native recovery owns the same scope.
- Do not commit, push, deploy, publish, purchase, enable billing, or send messages unless the current task authorizes it.
- Run checks that establish the changed behavior. Report exactly what ran and any remaining limitations.

## AUTO behavior

When `SUPERSET_AUTO=1`, use the installed runtime policy and selected route catalog. The coordinator must distinguish its role from worker roles. Respect fresh quota gates, interactive permission requests, and the provider allowlist.

Fast Fix supports a direct micro-fix or one scoped worker; escalate when complexity or risk warrants it. Feature uses an eligible planner and scoped workers. Choose useful work for the task, never work solely to consume quota.

Use `auto-dispatch` for durable workers and `auto-worker-watch` for foreground collection. The workspace supervisor owns worker state. `WAITING_INPUT` needs attention; `NATIVE_RESUMING` is protected recovery, not permission to launch a replacement. Completion requires the task's durable handoff and validation evidence.

Workers follow the explicit contract, remain inside their scope, and do not create child AUTO workers. Planning-only workers do not implement. Preserve partial work and hand off blockers instead of pretending success.

Before coordinator-owned integration actions, refresh policy and acknowledge the current fingerprint using `auto-policy-ack --phase integration --cwd "$PWD"` when required by the Git guard. An acknowledgement does not itself authorize publication.

Keep user updates concise and natural. Finish with the outcome, material changes, checks performed, and unresolved blockers.
