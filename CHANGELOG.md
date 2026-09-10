# Changelog

## 9.9.5-public.1 — 2026-09-10

- Target Superset desktop/host/CLI 1.28.0; check the native successor schema before installation.
- Prefer native OpenCode session identity and persisted successor lineage; keep the workspace supervisor and protected `NATIVE_RESUMING` state.
- Require host/workspace/agent/definition/session ownership and one live writer before adoption. Hooks can no longer rewrite terminal ownership.
- Retain one quota-gated explicit fallback after native grace; retire the exited source through Superset before launching so it cannot resurrect again. Confirm native identity before sending work.
- Preserve uncertain launches/cleanup as supervision loss; record one continuation attempt so timeouts cannot duplicate prompts.
- Consume available PTY/daemon failure details without retaining shell arguments, output or crash tails.
- Keep v9.9.4.1 Free→Go exact-session verification, durable handoffs, quotas, AUTO_PROJECT inheritance, Clean Coordinator Chat and policy ownership checks.
- Add recovery/installation regression coverage, the complete upstream change inventory and a live upgrade checklist. Live macOS/provider acceptance remains pending.

## 9.9.4.1-public.1 — 2026-09-09

- Fixed macOS extraction metadata blocking validation: skip local Finder/AppleDouble metadata while keeping the staged-file scan strict; added regression tests.
- Packaged the current AUTO runtime with portable paths and explicit source selection.
- Added macOS installation previews, provider selection, configuration conflict checks, private restore points, and rollback.
- Added project templates, setup diagnostics, GitHub documentation, CI and offline behavioral checks.
- Excluded account/session state and personal settings; replaced the private Azure endpoint/key-file reference with environment placeholders.
- Disabled permission-bypass flags in new custom-agent templates and personal quota-utilization targets in public routing.
- Made disabled providers ineligible even when old quota cache data exists.
- Retained native model/effort launch, policy checkpoints, worker supervision, and exact-route same-session recovery checks.
- Status: public preview; live macOS/provider acceptance remains outstanding.
