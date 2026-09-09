import argparse
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    loader = importlib.machinery.SourceFileLoader(name.replace("-", "_"), str(ROOT / "runtime/bin" / name))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


class RuntimeTests(unittest.TestCase):
    def test_go_recovery_requires_exact_session_route_and_completed_tokens(self):
        supervisor = load("auto-muse-supervisor")
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "fixture.sqlite"
            con = sqlite3.connect(db)
            con.execute("create table message (session_id text, time_created integer, data text)")
            good = {"role": "assistant", "providerID": supervisor.GO_PROVIDER_ID,
                    "modelID": supervisor.GO_MODEL_ID, "finish": "stop", "tokens": {"output": 1}}
            cases = [dict(good, providerID="wrong-provider"), dict(good, modelID="wrong-model"),
                     dict(good, error={"message": "failed"}), dict(good, finish=None), dict(good, tokens={"output": 0})]
            with patch.object(supervisor, "db_path", return_value=db):
                for data in cases:
                    con.execute("insert into message values ('fixture-session', 200, ?)", (json.dumps(data),))
                    con.commit()
                    self.assertFalse(supervisor.completed_go_turn_in_session("fixture-session", 100))
                con.execute("insert into message values ('different-session', 200, ?)", (json.dumps(good),))
                con.commit()
                self.assertFalse(supervisor.completed_go_turn_in_session("fixture-session", 100))
                con.execute("insert into message values ('fixture-session', 200, ?)", (json.dumps(good),))
                con.commit()
                self.assertTrue(supervisor.completed_go_turn_in_session("fixture-session", 100))
                self.assertFalse(supervisor.completed_go_turn_in_session("fixture-session", 300))
            con.close()

    def test_disabled_providers_cannot_reuse_cached_quota(self):
        quota = load("auto-quota-status")
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            cfg = home / ".superset/auto/public-settings.json"
            cfg.parent.mkdir(parents=True)
            cfg.write_text('{"providers":["opencode","codex"]}')
            old = {"pools": {"opencodeGo": {"availability": "available", "reserveSafe": True},
                             "codex": {"availability": "available"}}}
            args = argparse.Namespace()
            with patch.object(quota.Path, "home", return_value=home):
                filtered, disabled = quota.public_provider_filter(args, old)
            self.assertIn("opencodeGo", disabled)
            self.assertNotIn("opencodeGo", filtered["pools"])
            self.assertIn("codex", filtered["pools"])
            self.assertTrue(args.no_opencode_go)
            self.assertIn("opencodeGo", old["pools"])

    def test_route_catalog_and_template_references_are_complete(self):
        agents = json.loads((ROOT / "config/agents.json").read_text())
        labels = {a["label"] for a in agents}
        self.assertEqual(len(labels), len(agents))
        for label, route in json.loads((ROOT / "config/routes.json").read_text())["routes"].items():
            self.assertIn(route["baseAgentLabel"], labels, label)
        for agent in agents:
            cmd = agent["command"]
            if cmd.startswith("{auto_bin}/auto-"):
                self.assertTrue((ROOT / "runtime/bin" / cmd.split("/")[-1]).is_file(), cmd)
            self.assertFalse(any("--dangerously-" in x for x in agent["args"]))
            self.assertNotIn("--force", agent["promptArgs"])


if __name__ == "__main__":
    unittest.main()
