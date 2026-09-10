import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("auto_setup", ROOT / "scripts/setup.py")
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name).resolve() / "A User Home"
        self.db = self.home / ".superset/host/example/host.db"
        self.db.parent.mkdir(parents=True)
        con = sqlite3.connect(self.db)
        types = {"display_order": "integer", "created_at": "integer", "updated_at": "integer"}
        con.execute("create table host_agent_configs (" + ",".join(k + " " + types.get(k, "text") + (" primary key" if k == "id" else "") for k in setup.COLS) + ")")
        con.execute("create table terminal_agent_bindings (terminal_id text, workspace_id text, agent_id text, agent_session_id text, definition_id text, ended_at integer, end_reason text, resumed_into_terminal_id text)")
        con.execute("create table terminal_sessions (id text, status text, dispose_requested_at integer, ended_at integer)")
        con.execute("create table workspaces (id text, branch text)")
        con.execute("insert into workspaces values ('local-test', 'preserve-me')")
        con.commit()
        con.close()
        self.cfg = self.home / ".config/opencode/opencode.json"
        self.cfg.parent.mkdir(parents=True)
        self.before = b'{"theme":"system","permission":{"bash":"ask"}}\n'
        self.cfg.write_bytes(self.before)
        self.addCleanup(patch.stopall)
        patch.dict(setup.os.environ, {"XDG_CONFIG_HOME": str(self.home / ".config"), "OPENCODE_CONFIG": ""}).start()

    def rows(self, table="host_agent_configs"):
        with sqlite3.connect(self.db) as con:
            return con.execute("select * from " + table).fetchall()

    def test_install_idempotence_restore_and_unrelated_state(self):
        backup = setup.install(self.home, self.db, {"opencode", "codex"})
        first = self.rows()
        self.assertGreater(len(first), 2)
        merged = json.loads(self.cfg.read_text())
        self.assertEqual(merged["permission"], {"bash": "ask"})
        self.assertNotIn("provider", merged)
        self.assertIsNone(setup.install(self.home, self.db, {"opencode", "codex"}))
        self.assertEqual(first, self.rows())
        self.assertEqual((backup / "manifest.json").stat().st_mode & 0o777, 0o600)
        settings = json.loads((self.home / ".superset/auto/public-settings.json").read_text())
        self.assertIn("Codex · Astra Planner XHigh", settings["allowedLabels"])
        self.assertNotIn("Claude · Opus 5 High", settings["allowedLabels"])
        setup.restore(backup)
        self.assertEqual(self.cfg.read_bytes(), self.before)
        self.assertEqual(self.rows(), [])
        self.assertEqual(self.rows("workspaces"), [("local-test", "preserve-me")])

    def test_dry_run_is_read_only(self):
        before = self.db.read_bytes()
        setup.install(self.home, self.db, {"opencode"}, dry_run=True)
        self.assertEqual(before, self.db.read_bytes())
        self.assertEqual(self.cfg.read_bytes(), self.before)
        self.assertFalse((self.home / ".superset/bin").exists())

    def test_mid_install_failure_rolls_back_files_and_rows(self):
        original = setup.atomic
        def fail(path, data, mode=0o600):
            if path.name == "auto-policy-ack":
                raise OSError("injected write failure")
            return original(path, data, mode)
        with patch.object(setup, "atomic", fail):
            with self.assertRaises(OSError):
                setup.install(self.home, self.db, {"opencode", "codex"})
        self.assertEqual(self.rows(), [])
        self.assertEqual(self.cfg.read_bytes(), self.before)
        self.assertFalse((self.home / ".superset/bin/auto-agent-id").exists())

    def test_restore_refuses_later_user_changes(self):
        backup = setup.install(self.home, self.db, {"opencode"})
        self.cfg.write_text('{"user_change":true}')
        with self.assertRaisesRegex(RuntimeError, "Changed since install"):
            setup.restore(backup)
        self.assertEqual(self.cfg.read_text(), '{"user_change":true}')

    def test_config_conflict_fails_before_mutation(self):
        self.cfg.write_text('{"agent":{"muse-auto":{"model":"user-choice"}}}')
        with self.assertRaisesRegex(RuntimeError, "configuration conflict"):
            setup.install(self.home, self.db, {"opencode"})
        self.assertEqual(self.rows(), [])
        self.assertFalse((self.home / ".superset/bin").exists())

    def test_unknown_schema_fails_without_creating_tables(self):
        with sqlite3.connect(self.db) as con:
            con.execute("drop table host_agent_configs")
        with self.assertRaisesRegex(RuntimeError, "Unsupported"):
            setup.install(self.home, self.db, {"opencode"})
        self.assertEqual(self.rows("workspaces"), [("local-test", "preserve-me")])

    def test_unmigrated_127_host_fails_before_install(self):
        with sqlite3.connect(self.db) as con:
            con.execute("alter table terminal_agent_bindings drop column resumed_into_terminal_id")
        before = self.db.read_bytes()
        with self.assertRaisesRegex(RuntimeError, "1.28 recovery schema"):
            setup.install(self.home, self.db, {"opencode"})
        self.assertEqual(self.db.read_bytes(), before)
        self.assertFalse((self.home / ".superset/bin").exists())

    def test_duplicate_labels_are_rejected(self):
        _, rows, _ = setup.plan(self.home, {"opencode"}, self.db)
        with sqlite3.connect(self.db) as con:
            for ident in ("duplicate-a", "duplicate-b"):
                row = dict(rows[0], id=ident)
                con.execute("insert into host_agent_configs values (" + ",".join("?" for _ in setup.COLS) + ")", tuple(row[k] for k in setup.COLS))
        with self.assertRaisesRegex(RuntimeError, "Duplicate"):
            setup.install(self.home, self.db, {"opencode"})


if __name__ == "__main__":
    unittest.main()
