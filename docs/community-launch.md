# AUTO-Superset Community Launch Kit

Use this page as the maintained copy source for public announcements. Keep claims synchronized with the README and current release notes.

## Core positioning

**AUTO-Superset is a community add-on for existing Superset installations.** It adds a top-level coordinator that can route work to supported coding agents, supervise workers, observe quota gates, and recover supported interrupted sessions.

Current public baseline: **v1.0 · AUTO 9.9.4.1-public.1 · macOS · Superset 1.27.0+**.

Do not describe AUTO-Superset as an official Superset feature, a Superset fork, or a provider subscription. It is an independent community project.

## Discord announcement

### Suggested title

**I built AUTO-Superset — a multi-agent coordinator for Superset**

### Post

I built an add-on for Superset called **AUTO-Superset**.

I like using several coding agents in Superset, but I wanted one top-level coordinator that could decide how to handle a task, delegate useful work, supervise the workers, track provider quota gates, and recover supported interrupted sessions without turning the coordinator chat into a wall of terminal output.

It adds two workflows to an existing Superset install:

- **AUTO · Fast Fix** — optimized for small/local fixes
- **AUTO · Feature** — for changes that benefit from planning and coordinated workers

It can work with supported routes from OpenCode, Codex, Claude Code, Cursor, Antigravity/Gemini, and optional Azure configuration. You choose which providers to install; it does not require all of them.

The installer has a dry-run, preserves existing Superset projects/sessions/settings/native agents, detects conflicts instead of blindly overwriting them, and creates restore points.

**v1.0 public preview:** macOS, Superset 1.27.0+, AUTO 9.9.4.1-public.1.

GitHub / install / docs:
https://github.com/AntonKhakhalin/AUTO-Superset

Release:
https://github.com/AntonKhakhalin/AUTO-Superset/releases/tag/v1.0

If you already use Superset heavily, I would especially appreciate feedback on installation compatibility, worker supervision/recovery, and how the Fast Fix vs Feature split feels in real projects.

## GitHub Discussions announcement

### Suggested title

**AUTO-Superset v1.0: community multi-agent coordinator for Superset — looking for testers**

### Post

I have published the first public preview of **AUTO-Superset**, an independent community add-on for Superset.

The goal is to add a lightweight control layer above the coding agents people already use in Superset. Instead of manually choosing and supervising every worker, AUTO provides two top-level workflows:

- **AUTO · Fast Fix** for localized bugs and small existing-feature changes.
- **AUTO · Feature** for larger changes that may benefit from planning, scoped workers, supervision, and broader validation.

The current runtime includes provider-aware routing/gates, worker supervision, supported native same-session recovery, optional Muse Free → OpenCode Go continuity, cleaner coordinator presentation, and repository-specific `AGENTS.md` / `.superset/AUTO_PROJECT.md` policy support.

For existing Superset users, the project is intended to install alongside the current setup rather than replace it. The installer supports `--dry-run`, installs only selected provider routes, preserves existing projects/sessions/settings/native agents, fails on conflicting custom values rather than silently overwriting them, and creates restore points.

**Current public baseline**

- AUTO-Superset **v1.0**
- AUTO runtime **9.9.4.1-public.1**
- **macOS** installer
- **Superset 1.27.0+**; 1.27.0 is the source-reviewed baseline
- OpenCode-based Muse Spark 1.3 coordinator

Repository:
https://github.com/AntonKhakhalin/AUTO-Superset

Release:
https://github.com/AntonKhakhalin/AUTO-Superset/releases/tag/v1.0

I am particularly looking for feedback from existing Superset users on:

1. installation alongside customized agent configurations;
2. Fast Fix vs Feature task selection;
3. worker completion, permission, failure, and recovery behavior;
4. provider-route compatibility across real accounts;
5. documentation or diagnostics that would make adoption easier.

This is not an official Superset project. Provider CLIs/accounts/subscriptions are installed and authenticated separately.

## Short social post

I released **AUTO-Superset v1.0** — a community add-on that gives Superset a top-level coordinator for **Fast Fix** and **Feature** workflows, worker delegation/supervision, quota-aware routing, and supported session recovery.

Built for existing Superset installs; dry-run + restore points included.

macOS · Superset 1.27.0+
https://github.com/AntonKhakhalin/AUTO-Superset

## Demo video / GIF storyboard

Target length: **30–60 seconds**. Avoid terminal-heavy footage; show the Superset experience.

1. **Opening (3–5 s):** Existing Superset project is open. Show the agent picker.
2. **Choose AUTO (3–5 s):** Select `AUTO · Feature`.
3. **Prompt (5 s):** Use a real but safe task, e.g. “Add validation for X and update the tests.”
4. **Coordinator (5–10 s):** Show clean natural-language routing/dispatch status.
5. **Workers (8–15 s):** Show two useful worker tabs/workspaces executing scoped work. Do not expose credentials, quota tokens, private paths, or customer code.
6. **Completion (5–10 s):** Return to coordinator and show worker completion plus the final summary.
7. **End card (3–5 s):** `AUTO · Fast Fix` / `AUTO · Feature` + `github.com/AntonKhakhalin/AUTO-Superset`.

For an initial demo, use a disposable public/sample repository so the recording can be shared without redaction.

## Recommended GitHub topics

Add these repository topics through GitHub's **About → Settings gear**:

`superset`, `superset-sh`, `coding-agents`, `ai-agents`, `agent-orchestration`, `multi-agent`, `codex`, `claude-code`, `opencode`, `gemini-cli`, `cursor-agent`, `developer-tools`, `macos`

Use only topics that remain accurate as provider support changes.

## Release asset checklist

For each public release, attach an explicitly named reviewed package rather than relying only on GitHub's generic source archives:

- `AUTO-Superset-vX.Y.zip`
- `SHA256SUMS.txt`

Release notes should state:

- public AUTO version;
- source-reviewed Superset baseline;
- supported installer platform;
- tested OpenCode baseline when relevant;
- major changes;
- known limitations;
- upgrade/restore guidance.

## Suggested launch order

1. Publish/verify the GitHub Release and assets.
2. Confirm the README first screen and installation path.
3. Record the short demo GIF/video.
4. Post to the Superset Discord/community channel most appropriate for projects/showcase.
5. Post the longer GitHub Discussions announcement if the upstream community permits project/showcase posts there.
6. Share the short social post with the demo attached.
7. Collect installation/recovery feedback from the first 5–10 external users before broadening platform/support claims.
