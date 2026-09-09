# Contributing

Describe the problem, the resulting behavior, and checks that establish the fix. Keep unrelated formatting, route churn and model recommendations out of behavioral patches.

```sh
python3 -B scripts/validate.py
```

Tests use temporary SQLite/filesystem fixtures and make no provider calls. For changes to Superset integration, record the upstream source tag and complete the macOS smoke test in `docs/setup.md`. Report live checks separately from fixture tests.

Preserve native resume ownership, exact recovery evidence, fresh quota gates, policy fingerprints, user configuration, rollback and clear failure messages. Do not weaken a gate to make a test pass.

Update `VERSION`, `CHANGELOG.md`, and relevant documentation for a release. Do not commit generated Superset wrappers, model credentials, machine IDs, personal settings, databases, logs or backup archives.
