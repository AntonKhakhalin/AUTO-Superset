# Security and privacy

Do not post credentials, private keys, API tokens, provider auth files, session transcripts, databases or full Superset backups in issues or pull requests. Revoke/rotate a credential through its provider if it has actually been exposed.

Use provider login tools or local environment/file references. The optional Azure example accepts `AUTO_AZURE_BASE_URL` and `AUTO_AZURE_API_KEY`; it contains no usable credentials. Existing user permissions are preserved. Public custom-agent templates do not install approval/sandbox bypass flags.

AUTO reads local quota/auth/session sources for its selected providers and can contact their usage endpoints. The conversation-mirror plugin stores coordinator user/assistant text locally beneath Superset's AUTO state. Treat that state and installation restore points as private. No telemetry upload service is added by this package.

The coordinator-only Git guard is a policy checkpoint, not an OS sandbox or a substitute for repository permissions. Agent instructions do not make arbitrary untrusted repositories safe.

To report a vulnerability, use GitHub's private vulnerability reporting when enabled. If it is unavailable, open an issue asking for a private contact without disclosing exploit details or sensitive data.

Before publishing changes, run `python3 -B scripts/validate.py` and inspect the staged files. The scanner reports file paths and finding categories, never matched secret values. A clean scan is not a guarantee that all secrets are absent.
