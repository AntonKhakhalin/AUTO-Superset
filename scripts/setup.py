#!/usr/bin/env python3
"""Local, backed-up AUTO installation. No downloads, logins, or model calls."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
PROVIDERS = {"opencode", "opencode-go", "codex", "claude", "cursor", "antigravity", "azure"}
COLS = ["id", "preset_id", "icon_id", "label", "command", "args_json", "prompt_transport",
        "prompt_args_json", "resume_args_json", "fork_args_json", "env_json", "display_order",
        "created_at", "updated_at"]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encode(data) -> bytes:
    return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode()


def read_json(path: Path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def atomic(path: Path, data: bytes, mode=0o600):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".auto-tmp-" + uuid.uuid4().hex)
    try:
        tmp.write_bytes(data)
        tmp.chmod(mode)
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def check_stopped():
    result = subprocess.run(["ps", "-axo", "command="], text=True, capture_output=True, check=True)
    for line in result.stdout.splitlines():
        if re.search(r"/Superset\.app/Contents/|(?:^|/)auto-(?:muse|workspace)-supervisor(?:\s|$)|superset[^\n]*host-service", line):
            raise RuntimeError("Quit Superset and stop active AUTO workers before installing or restoring.")


def preflight(home, providers):
    required = {"git", "python3", "jq", "zsh", "node", "superset", "opencode"}
    for provider, binary in {"codex": "codex", "claude": "claude", "cursor": "cursor-agent", "antigravity": "agy"}.items():
        if provider in providers:
            required.add(binary)
    for binary in sorted(required):
        if not (shutil.which(binary) or os.access(home / ".superset/bin" / binary, os.X_OK)):
            raise RuntimeError(f"Required command missing: {binary}. See docs/setup.md.")
    for binary in ["opencode"] + (["codex"] if "codex" in providers else []):
        if not os.access(home / ".superset/bin" / binary, os.X_OK):
            raise RuntimeError(f"Launch {binary} once from Superset to generate its managed wrapper, then quit Superset.")
    cli = shutil.which("superset") or str(home / ".superset/bin/superset")
    cp = subprocess.run([cli, "--version"], text=True, capture_output=True, timeout=15)
    version = re.search(r"(\d+)\.(\d+)\.(\d+)", cp.stdout + cp.stderr)
    if cp.returncode or not version or tuple(map(int, version.groups())) < (1, 27, 0):
        raise RuntimeError("Superset CLI 1.27.0+ is required; update Superset and regenerate its CLI wrapper.")


def find_db(home: Path, explicit=None) -> Path:
    if explicit:
        candidates = [Path(explicit).expanduser().resolve()]
    else:
        candidates = sorted((home / ".superset/host").glob("*/host.db"))
    if len(candidates) != 1 or not candidates[0].is_file():
        raise RuntimeError("Open Superset once, then quit it. If several hosts exist, pass --host-db PATH.")
    return candidates[0]


def validate_schema(con):
    columns = {r[1] for r in con.execute("pragma table_info(host_agent_configs)")}
    if not set(COLS) <= columns:
        raise RuntimeError("Unsupported Superset host-agent schema; no changes were made.")


def merge_dict(old, new, path=""):
    """Add missing leaves; refuse to silently replace user configuration."""
    result = dict(old)
    for key, value in new.items():
        if key not in result:
            result[key] = value
        elif isinstance(value, dict) and isinstance(result[key], dict):
            result[key] = merge_dict(result[key], value, path + "." + key)
        elif result[key] != value:
            raise RuntimeError(f"OpenCode configuration conflict at {path}.{key}; reconcile it before installing.")
    return result


def render(value, home):
    if isinstance(value, str):
        return value.replace("{auto_bin}", str(home / ".superset/bin"))
    if isinstance(value, list):
        return [render(v, home) for v in value]
    if isinstance(value, dict):
        return {k: render(v, home) for k, v in value.items()}
    return value


def plan(home: Path, providers: set[str], db: Path, skip_opencode_config=False):
    if "opencode" not in providers or providers - PROVIDERS:
        raise RuntimeError("Select opencode plus any of: " + ", ".join(sorted(PROVIDERS - {"opencode"})))
    managed = home / ".superset"
    files = {}
    for src in (ROOT / "runtime/bin").iterdir():
        if src.is_file():
            files[managed / "bin" / src.name] = (src.read_bytes(), 0o755)
    files[managed / "auto-runtime-shims/git"] = ((ROOT / "runtime/git-shim").read_bytes(), 0o755)
    for src in (ROOT / "runtime/opencode").glob("*.js"):
        files[managed / "hooks/opencode/plugin" / src.name] = (src.read_bytes(), 0o644)
    files[managed / "auto/runtime/auto-coordinator-mirror.js"] = (
        (ROOT / "runtime/opencode/auto-coordinator-mirror.js").read_bytes(), 0o644)
    specs = [render(a, home) for a in read_json(ROOT / "config/agents.json") if a["provider"] in providers]
    labels = {a["label"] for a in specs}
    routes = read_json(ROOT / "config/routes.json")
    routes["routes"] = {label: r for label, r in routes["routes"].items() if r["baseAgentLabel"] in labels}
    files[managed / "auto/routes.json"] = (encode(routes), 0o600)
    settings = {"version": (ROOT / "VERSION").read_text().strip(), "providers": sorted(providers),
                "allowedLabels": sorted(labels | set(routes["routes"]))}
    files[managed / "auto/public-settings.json"] = (encode(settings), 0o600)
    config_home = Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config")
    cfg = config_home / "opencode/opencode.json"
    # JSONC and an explicit alternate config require conscious local integration.
    if not skip_opencode_config and ((cfg.parent / "opencode.jsonc").exists() or os.environ.get("OPENCODE_CONFIG")):
        raise RuntimeError("Alternate OpenCode config detected. Merge config/opencode.json there first; see docs/setup.md.")
    if not skip_opencode_config:
        merged = merge_dict(read_json(cfg, {}), read_json(ROOT / "config/opencode.json"))
        if "azure" in providers:
            merged = merge_dict(merged, read_json(ROOT / "config/opencode-azure.example.json"))
        files[cfg] = (encode(merged), 0o600)
    con = sqlite3.connect(f"{db.as_uri()}?mode=ro", uri=True)
    try:
        validate_schema(con)
        existing = [dict(zip(COLS, r)) for r in con.execute("select " + ",".join(COLS) + " from host_agent_configs")]
    finally:
        con.close()
    now = int(time.time() * 1000)
    order = max((r["display_order"] for r in existing), default=-1) + 1
    additions = []
    reused = []
    for spec in specs:
        found = [r for r in existing if r["label"] == spec["label"]]
        if len(found) > 1:
            raise RuntimeError(f"Duplicate agent label: {spec['label']}; resolve it in Superset first.")
        row = dict(zip(COLS, [str(uuid.uuid4()), spec["presetId"], spec.get("iconId"), spec["label"],
            spec["command"], json.dumps(spec["args"]), spec["promptTransport"], json.dumps(spec["promptArgs"]),
            json.dumps(spec["resumeArgs"]), json.dumps(spec["forkArgs"]), json.dumps(spec["env"]), order, now, now]))
        if found:
            old = found[0]
            # Native built-ins belong to Superset/the user and are reused, never rewritten.
            native = spec["label"] in {"Codex", "Claude", "Cursor"} and old["preset_id"] == spec["presetId"] and old["command"] == spec["command"]
            same = all((json.loads(old[k]) == json.loads(row[k])) if k.endswith("_json") else old[k] == row[k]
                       for k in COLS if k not in {"id", "created_at", "updated_at", "display_order"})
            if not (native or same):
                raise RuntimeError(f"Agent configuration conflict: {spec['label']}. Rename the existing row or reconcile launch settings.")
            reused.append(old["label"])
        else:
            additions.append(row)
            order += 1
    # Replacing an existing AUTO runtime is deliberate, and every byte is backed up.
    # Refuse links so external targets cannot be overwritten by installation.
    for path in files:
        if path.is_symlink() or any(p.is_symlink() for p in path.parents if p != home.parent):
            raise RuntimeError(f"Symlink installation target requires manual integration: {path}")
    return files, additions, reused


def install(home, db, providers, dry_run=False, skip_opencode_config=False):
    files, additions, reused = plan(home, providers, db, skip_opencode_config)
    changed = {p: item for p, item in files.items() if not p.is_file() or p.read_bytes() != item[0] or (p.stat().st_mode & 0o777) != item[1]}
    print(f"Plan: {len(changed)} files, {len(additions)} new agents, {len(reused)} existing agents reused.")
    if dry_run:
        return None
    if not changed and not additions:
        print("Already installed; no changes.")
        return None
    backup = home / ".superset/auto/install-backups" / (time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8])
    backup.mkdir(parents=True, mode=0o700)
    records = []
    for i, (path, (data, mode)) in enumerate(changed.items()):
        rec = {"path": str(path), "before": None, "afterSha256": digest(data), "beforeMode": None}
        if path.exists():
            copy = backup / f"file-{i:03d}"
            atomic(copy, path.read_bytes())
            rec.update(before=copy.name, beforeMode=path.stat().st_mode & 0o777)
        records.append(rec)
    manifest = {"version": 1, "home": str(home), "db": str(db), "files": records, "addedAgents": additions}
    atomic(backup / "manifest.json", encode(manifest))
    con = sqlite3.connect(f"{db.as_uri()}?mode=rw", uri=True, timeout=5)
    written = []
    try:
        con.execute("begin immediate")
        validate_schema(con)
        for row in additions:
            if con.execute("select 1 from host_agent_configs where label=?", (row["label"],)).fetchone():
                raise RuntimeError("Agent rows changed since planning; rerun with Superset stopped.")
            con.execute("insert into host_agent_configs (" + ",".join(COLS) + ") values (" + ",".join("?" for _ in COLS) + ")", [row[k] for k in COLS])
        for path, (data, mode) in changed.items():
            atomic(path, data, mode)
            written.append(path)
        con.commit()
    except Exception:
        con.rollback()
        for rec in reversed(records):
            path = Path(rec["path"])
            if path in written:
                if rec["before"]:
                    atomic(path, (backup / rec["before"]).read_bytes(), rec["beforeMode"])
                else:
                    path.unlink(missing_ok=True)
        raise
    finally:
        con.close()
    print(f"Installed. Restore point: {backup}")
    print("Reopen Superset; run: python3 scripts/setup.py doctor")
    return backup


def restore(backup: Path, dry_run=False):
    manifest = read_json(backup / "manifest.json")
    if not manifest or manifest.get("version") != 1:
        raise RuntimeError("Invalid restore point")
    for rec in manifest["files"]:
        path = Path(rec["path"])
        if not path.is_file() or path.is_symlink() or digest(path.read_bytes()) != rec["afterSha256"]:
            raise RuntimeError(f"Changed since install; refusing to overwrite: {path}")
    db = Path(manifest["db"])
    con = sqlite3.connect(f"{db.as_uri()}?mode=rw", uri=True, timeout=5)
    originals = {}
    try:
        con.execute("begin immediate")
        for row in manifest["addedAgents"]:
            current = con.execute("select " + ",".join(COLS) + " from host_agent_configs where id=?", (row["id"],)).fetchone()
            if current != tuple(row[k] for k in COLS):
                raise RuntimeError("An installed agent was edited or removed; reconcile it before restoring.")
        if dry_run:
            con.rollback()
            print("Restore plan verified; no changes.")
            return
        for rec in manifest["files"]:
            path = Path(rec["path"])
            originals[path] = (path.read_bytes(), path.stat().st_mode & 0o777)
            if rec["before"]:
                atomic(path, (backup / rec["before"]).read_bytes(), rec["beforeMode"])
            else:
                path.unlink()
        for row in manifest["addedAgents"]:
            con.execute("delete from host_agent_configs where id=?", (row["id"],))
        con.commit()
    except Exception:
        con.rollback()
        for path, (data, mode) in originals.items():
            atomic(path, data, mode)
        raise
    finally:
        con.close()
    print("Restored installation files and added agents. Other Superset data was preserved.")


def doctor(home):
    failures = []
    def check(ok, text):
        print(("OK   " if ok else "FAIL ") + text)
        if not ok:
            failures.append(text)
    check(sys.version_info >= (3, 10), "Python 3.10+")
    for command in ("git", "jq", "zsh", "node", "superset", "opencode"):
        check(bool(shutil.which(command) or (home / ".superset/bin" / command).is_file()), command + " installed")
    binary = shutil.which("superset") or str(home / ".superset/bin/superset")
    try:
        cp = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=10)
        match = re.search(r"(\d+)\.(\d+)\.(\d+)", cp.stdout + cp.stderr)
        check(cp.returncode == 0 and bool(match) and tuple(map(int, match.groups())) >= (1, 27, 0), "Superset CLI 1.27.0+")
    except (OSError, subprocess.TimeoutExpired):
        check(False, "Superset CLI version")
    settings = read_json(home / ".superset/auto/public-settings.json", {})
    check(bool(settings), "AUTO installed")
    for src in (ROOT / "runtime/bin").iterdir():
        if src.is_file():
            path = home / ".superset/bin" / src.name
            check(path.is_file() and os.access(path, os.X_OK), src.name)
    for name in ("opencode", "codex"):
        if name == "opencode" or name in settings.get("providers", []):
            check(os.access(home / ".superset/bin" / name, os.X_OK), "Superset managed " + name + " wrapper")
    check((home / ".superset/hooks/opencode/plugin/auto-coordinator-policy.js").is_file(), "hidden policy plugin")
    check(os.access(home / ".superset/auto-runtime-shims/git", os.X_OK), "Git policy guard")
    data_home = Path(os.environ.get("XDG_DATA_HOME") or home / ".local/share")
    check((data_home / "opencode/opencode.db").is_file(), "OpenCode initialized (run one Muse Free prompt manually first)")
    print("Doctor checks local setup only. Provider login, quota, model access and live recovery require the smoke test in docs/setup.md.")
    return 1 if failures else 0


def init_project(project: Path, dry_run=False):
    cp = subprocess.run(["git", "-C", str(project), "rev-parse", "--show-toplevel"], text=True, capture_output=True)
    if cp.returncode or Path(cp.stdout.strip()).resolve() != project.resolve():
        raise RuntimeError("--project must be the root of an existing Git worktree")
    pairs = [(src, project / src.relative_to(ROOT / "templates/project"))
             for src in (ROOT / "templates/project").rglob("*") if src.is_file()]
    for src, dest in pairs:
        if dest.exists():
            print("Preserved existing " + str(dest))
        elif not dry_run:
            atomic(dest, src.read_bytes(), 0o755 if dest.suffix == ".sh" else 0o644)
    print("Review .superset/AUTO_PROJECT.md and set your real build/test commands before starting AUTO.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    ins = sub.add_parser("install")
    ins.add_argument("--providers", default="opencode,codex")
    ins.add_argument("--host-db")
    ins.add_argument("--dry-run", action="store_true")
    ins.add_argument("--skip-opencode-config", action="store_true", help="Use an already manually merged OpenCode config")
    res = sub.add_parser("restore")
    res.add_argument("backup", type=Path)
    res.add_argument("--dry-run", action="store_true")
    sub.add_parser("doctor")
    ini = sub.add_parser("init-project")
    ini.add_argument("--project", type=Path, required=True)
    ini.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    home = Path.home()
    try:
        if args.command == "doctor":
            return doctor(home)
        if args.command == "init-project":
            init_project(args.project.expanduser().resolve(), args.dry_run)
        else:
            check_stopped()
            if args.command == "restore":
                restore(args.backup.expanduser().resolve(), args.dry_run)
            else:
                if sys.platform != "darwin":
                    raise RuntimeError("The public installer currently supports macOS only. Linux is used for fixture tests.")
                providers = set(args.providers.split(","))
                preflight(home, providers)
                install(home, find_db(home, args.host_db), providers, args.dry_run, args.skip_opencode_config)
        return 0
    except (RuntimeError, ValueError, OSError, sqlite3.Error, subprocess.SubprocessError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
