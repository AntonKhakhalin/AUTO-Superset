#!/usr/bin/env python3
"""Build the public release from the committed, validated source tree."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    metadata = json.loads((ROOT / "release.json").read_text())
    tag = metadata["tag"]
    title = metadata["title"]
    if not isinstance(tag, str) or not re.fullmatch(r"v[0-9]+(?:\.[0-9]+){1,2}", tag):
        raise SystemExit("Release tag must be vMAJOR.MINOR or vMAJOR.MINOR.PATCH")
    if not isinstance(title, str) or not title or any(c in title for c in "\r\n"):
        raise SystemExit("Release title must be a single nonempty line")
    if metadata["runtime"] != (ROOT / "VERSION").read_text().strip():
        raise SystemExit("Release runtime does not match VERSION")
    if not (ROOT / "docs/releases" / (tag + ".md")).is_file():
        raise SystemExit("Release notes are missing")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if os.environ.get("SOURCE_SHA", head) != head:
        raise SystemExit("Checkout does not match the release source SHA")
    subprocess.run(["git", "diff", "--exit-code", "HEAD", "--"], cwd=ROOT, check=True)
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    archive = dist / ("AUTO-Superset-" + tag + ".zip")
    subprocess.run(["git", "archive", "--format=zip", "--prefix=AUTO-Superset/",
                    "--output", str(archive), head], cwd=ROOT, check=True)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (dist / "SHA256SUMS.txt").write_text(digest + "  " + archive.name + "\n")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as output:
            output.write("tag=" + tag + "\ntitle=" + title + "\n")
    print("Prepared " + archive.name + " from " + head)


if __name__ == "__main__":
    main()
