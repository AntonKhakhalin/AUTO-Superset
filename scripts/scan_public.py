#!/usr/bin/env python3
"""Fail on secret-like values and private runtime artifacts. Never print values."""
from pathlib import Path
import argparse
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "provider token": re.compile(r"\b(?:sk-(?:proj-|ant-)?[A-Za-z0-9_-]{25,}|gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[A-Z0-9]{16})\b"),
    "JWT": re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{12,}\b"),
    "personal home": re.compile(r"/Users/" + r"(?!example\b|USERNAME\b)[A-Za-z0-9_-]+"),
    "credential URL": re.compile(r"https?://[^\s/:]+:[^\s/@]+@"),
}
PRIVATE_NAMES = {"auth.json", "auth-token.enc", "terminal-host.token", ".DS_Store", ".zsh_history", "local.db", "host.db", "quota-status.json"}
PRIVATE_DIRS = {"sessions", "backups", "node_modules", "__MACOSX", "recovery-transcripts", "install-backups"}
SENSITIVE_KEYS = re.compile(r"^(?:api[_-]?key|access[_-]?token|refresh[_-]?token|password|client[_-]?secret|authorization)$", re.I)


def is_macos_metadata(path):
    return path.name == ".DS_Store" or path.name.startswith("._") or "__MACOSX" in path.parts


def worktree_files():
    """Skip only known local metadata/caches, not arbitrary gitignored files.

    Git's staged-file scan below deliberately does not use this filter.
    """
    return [p for p in ROOT.rglob("*")
            if (p.is_file() or p.is_symlink())
            and not {".git", "__pycache__"}.intersection(p.relative_to(ROOT).parts)
            and (p.is_symlink() or not is_macos_metadata(p.relative_to(ROOT)))]


def json_findings(value, trail=""):
    errors = []
    if isinstance(value, dict):
        for key, v in value.items():
            if SENSITIVE_KEYS.match(key) and isinstance(v, str) and v and not v.startswith(("{env:", "{file:", "${", "YOUR_", "EXAMPLE_")):
                errors.append("literal credential field " + trail + "." + key)
            errors.extend(json_findings(v, trail + "." + key))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            errors.extend(json_findings(v, trail + f"[{i}]"))
    return errors


def scan(paths):
    findings = []
    for path in paths:
        rel = path.relative_to(ROOT)
        if path.is_symlink():
            findings.append((str(rel), "symlink"))
            continue
        if is_macos_metadata(rel) or path.name in PRIVATE_NAMES or PRIVATE_DIRS.intersection(rel.parts) or path.suffix in {".db", ".sqlite", ".enc", ".log", ".pem", ".key", ".pyc"}:
            findings.append((str(rel), "private/generated file"))
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeError, OSError):
            findings.append((str(rel), "unreviewed binary"))
            continue
        for label, pattern in PATTERNS.items():
            if pattern.search(text):
                findings.append((str(rel), label))
        if path.suffix == ".json":
            try:
                findings.extend((str(rel), x) for x in json_findings(json.loads(text)))
            except json.JSONDecodeError:
                findings.append((str(rel), "invalid JSON"))
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tracked", action="store_true")
    args = parser.parse_args()
    if args.tracked:
        cp = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z"], check=True, capture_output=True)
        paths = [ROOT / s for s in cp.stdout.decode().split("\0") if s]
    else:
        paths = worktree_files()
    findings = scan(paths)
    for path, reason in findings:
        print(f"FAIL {path}: {reason}")
    print(f"Scanned {len(paths)} files; {len(findings)} findings. Values are never printed.")
    return bool(findings)


if __name__ == "__main__":
    raise SystemExit(main())
