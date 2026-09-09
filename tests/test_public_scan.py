import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("public_scan", ROOT / "scripts/scan_public.py")
scanner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scanner)


class PublicScanTests(unittest.TestCase):
    def test_local_macos_metadata_is_skipped_but_auth_files_are_scanned(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = [".DS_Store", "runtime/.DS_Store", "._README.md", "__MACOSX/._file"]
            for rel in paths:
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"\x00\xff\xfeMac metadata fixture")
            (root / "README.md").write_text("Public source\n")
            (root / "auth.json").write_text("{}\n")
            with patch.object(scanner, "ROOT", root):
                selected = scanner.worktree_files()
                self.assertEqual({p.name for p in selected}, {"README.md", "auth.json"})
                self.assertIn(("auth.json", "private/generated file"), scanner.scan(selected))

    def test_forced_staged_metadata_is_still_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            shutil.copyfile(ROOT / "scripts/scan_public.py", root / "scripts/scan_public.py")
            shutil.copyfile(ROOT / ".gitignore", root / ".gitignore")
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            for name in (".DS_Store", "._README.md"):
                (root / name).write_bytes(b"\x00\xffmetadata fixture")
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            clean = subprocess.run([sys.executable, "-B", str(root / "scripts/scan_public.py"), "--tracked"], capture_output=True, text=True)
            self.assertEqual(clean.returncode, 0, clean.stdout + clean.stderr)
            subprocess.run(["git", "-C", str(root), "add", "-f", ".DS_Store", "._README.md"], check=True)
            blocked = subprocess.run([sys.executable, "-B", str(root / "scripts/scan_public.py"), "--tracked"], capture_output=True, text=True)
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("FAIL .DS_Store: private/generated file", blocked.stdout)
            self.assertIn("FAIL ._README.md: private/generated file", blocked.stdout)


if __name__ == "__main__":
    unittest.main()
