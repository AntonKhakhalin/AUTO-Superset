# AUTO-Superset maintenance

This repository packages the AUTO runtime; it is not Superset's application source.

- Keep public source free of credentials, personal paths, account state and raw input backups.
- Use `python3 -B scripts/validate.py` for offline checks. Do not claim a live macOS/provider check unless it ran.
- Preserve unrelated user configuration and Superset data. Installation changes need rollback and conflict handling.
- Preserve policy, quota, exact-route recovery and duplicate-writer protections.
- Keep documentation honest about source-reviewed versions and actual supported platforms.
- Public templates live under `templates/project/`; they are distinct from these maintenance instructions.
- Do not publish, push or modify remote state unless the current user request authorizes it.
