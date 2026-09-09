# Changelog

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
