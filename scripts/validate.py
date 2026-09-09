#!/usr/bin/env python3
"""Validate the public package without providers, credentials or model calls."""
from pathlib import Path
import ast
import json
import subprocess
import sys
from scan_public import worktree_files

ROOT = Path(__file__).resolve().parents[1]


def main():
    subprocess.run([sys.executable, str(ROOT / "scripts/scan_public.py")], check=True)
    for path in worktree_files():
        text = path.read_text()
        first = text.splitlines()[0] if text else ""
        if path.suffix == ".py" or (first.startswith("#!") and "python" in first):
            ast.parse(text, filename=str(path))
        elif first.startswith("#!") and "sh" in first:
            shell = "zsh" if "zsh" in first else "bash" if "bash" in first else "sh"
            subprocess.run([shell, "-n", str(path)], check=True)
        if path.suffix == ".json":
            json.loads(text)
        if path.suffix == ".js":
            subprocess.run(["node", "--check", str(path)], check=True)
    subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", str(ROOT / "tests"), "-v"], cwd=ROOT, check=True)
    print("Validation passed. This is offline verification, not a live Superset/provider smoke test.")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print("Validation stopped; fix the reported check and rerun.", file=sys.stderr)
        raise SystemExit(exc.returncode)
