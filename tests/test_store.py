"""Falsifiers for actual coordinator transactions and process-death recovery."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from continuum import store
from continuum.study import DEFAULT_STUDY, Study
from continuum.numerical import Point

ROOT = Path(__file__).resolve().parents[1]
SCRATCH = ROOT / ".cache" / "tests"
SCRATCH.mkdir(parents=True, exist_ok=True)


def small_study() -> Study:
    data = copy.deepcopy(DEFAULT_STUDY)
    data.update(evaluations_per_policy=8, development_seeds=[11], confirmation_seeds=[101],
                study_id="transaction-falsifier", revision="1")
    return Study.from_dict(data)


def child_env() -> dict[str, str]:
    # Test workers receive only execution essentials, not developer credentials.
    return {"PATH": os.defpath, "PYTHONPATH": str(ROOT), "PYTHONDONTWRITEBYTECODE": "1",
            "TMPDIR": str(SCRATCH), "LANG": "C.UTF-8"}


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / "campaign.sqlite"
        self.study = small_study()
        self.initial = store.create(self.study, self.path)

    def test_finite_clean_campaign_has_every_call_and_reserve(self):
        result = store.run(self.path)
        self.assertEqual(len(result["trial_specs"]), 8)
        self.assertEqual(len(result["attempts"]), 8)
        self.assertTrue(all(a["terminal"]["status"] == "COMPLETED" for a in result["attempts"]))
        self.assertEqual(sum(len(a["observations"]) for a in result["attempts"]), 64)
        self.assertEqual(sum(a["charged_evaluations"] for a in result["attempts"]), 64)
        self.assertEqual(sum(p["capacity"] for p in result["allocations"]), 128)
        self.assertEqual(sum(c["objectiveCalls"] for c in result["controls"]), 2)
        before = json.dumps(result, sort_keys=True)
        self.assertEqual(before, json.dumps(store.run(self.path), sort_keys=True))

    def test_pause_resume_preserves_prior_evidence_exactly(self):
        partial = store.run(self.path, max_trials=1)
        self.assertEqual(len(partial["attempts"]), 1)
        self.assertEqual(partial["attempts"][0], store.run(self.path)["attempts"][0])

    def _kill_at(self, point: str):
        command = [sys.executable, "-c",
                   "import sys; from continuum.store import run; run(sys.argv[1], _crash_at=sys.argv[2])",
                   str(self.path), point]
        process = subprocess.run(command, cwd=ROOT, env=child_env(), capture_output=True, text=True, timeout=20)
        self.assertEqual(process.returncode, -signal.SIGKILL, process.stderr)

    def test_real_kill_after_admission_retains_cost_and_retry_identity(self):
        self._kill_at("after-admission")
        partial = store.inspect(self.path)
        self.assertEqual(len(partial["attempts"]), 1)
        self.assertIsNone(partial["attempts"][0]["terminal"])
        self.assertEqual(partial["attempts"][0]["charged_evaluations"], 8)
        result = store.run(self.path)
        first, retry = result["attempts"][:2]
        self.assertEqual(first["terminal"]["status"], "FAILED")
        self.assertEqual(first["terminal"]["observed_evaluations"], 0)
        self.assertIsNone(first["terminal"]["elapsed_seconds"])
        self.assertEqual(retry["retry_of"], first["id"])
        self.assertNotEqual(retry["id"], first["id"])
        self.assertEqual(sum(a["charged_evaluations"] for a in result["attempts"]), 72)
        from continuum.evidence import summarize
        self.assertIn("INCONCLUSIVE", json.dumps(summarize(result)))

    def test_real_kill_after_execution_retains_full_partial_trace(self):
        self._kill_at("after-execution")
        partial = store.inspect(self.path)
        self.assertEqual(len(partial["attempts"][0]["observations"]), 8)
        result = store.run(self.path)
        first = result["attempts"][0]
        self.assertEqual(first["observations"], partial["attempts"][0]["observations"])
        self.assertEqual(first["terminal"]["status"], "FAILED")
        self.assertEqual(first["terminal"]["observed_evaluations"], 8)
        self.assertEqual(sum(a["charged_evaluations"] for a in result["attempts"]), 72)

    def test_real_kill_after_staging_finalizes_once_without_retry(self):
        self._kill_at("after-staging")
        partial = store.inspect(self.path)
        staged = partial["attempts"][0]["staged"]
        self.assertIsNotNone(staged)
        self.assertIsNone(partial["attempts"][0]["terminal"])
        result = store.run(self.path)
        self.assertEqual(result["attempts"][0]["terminal"], staged)
        self.assertEqual(len(result["attempts"]), 8)
        self.assertEqual(sum(a["charged_evaluations"] for a in result["attempts"]), 64)
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM terminals").fetchone()[0], 8)
            self.assertEqual(db.execute("SELECT count(DISTINCT attempt_id) FROM terminals").fetchone()[0], 8)

    def test_two_kills_exhaust_only_their_trial_reserve(self):
        self._kill_at("after-admission")
        self._kill_at("after-admission")
        result = store.run(self.path)
        attempts = [a for a in result["attempts"] if a["trial_id"] == result["trial_specs"][0]["id"]]
        self.assertEqual(len(attempts), 2)
        self.assertTrue(all(a["terminal"]["status"] == "FAILED" for a in attempts))
        self.assertEqual(sum(a["charged_evaluations"] for a in attempts), 16)
        self.assertEqual(len([a for a in result["attempts"] if a["trial_id"].startswith("reproduction-")]), 4)
        self.assertEqual(result, store.run(self.path))

    def test_second_live_coordinator_cannot_assume_lock_owner_dead(self):
        code = """import sys,time
from pathlib import Path
from continuum.store import _writer_lock
with _writer_lock(Path(sys.argv[1])):
 print('locked',flush=True)
 time.sleep(20)
"""
        process = subprocess.Popen([sys.executable, "-c", code, str(self.path)], cwd=ROOT,
                                   env=child_env(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            self.assertEqual(process.stdout.readline().strip(), "locked")
            with self.assertRaises(store.CampaignBusy):
                store.run(self.path)
            self.assertEqual(store.inspect(self.path)["attempts"], [])
        finally:
            process.terminate()
            process.communicate(timeout=5)

    def test_duplicate_terminal_and_mutations_are_rejected_by_sqlite(self):
        result = store.run(self.path, max_trials=1)
        attempt = result["attempts"][0]
        with sqlite3.connect(self.path) as db:
            for statement, params in [
                ("UPDATE meta SET payload='{}'", ()),
                ("DELETE FROM events", ()),
                ("UPDATE observations SET value=0", ()),
                ("INSERT INTO terminals VALUES(?,?)", (attempt["id"], json.dumps(attempt["terminal"]))),
                ("INSERT INTO observations VALUES(?,?,?,?)", (attempt["id"], 8, '[1,1]', 0.0)),
            ]:
                with self.subTest(statement=statement), self.assertRaises(sqlite3.IntegrityError):
                    db.execute(statement, params)
        self.assertEqual(result, store.inspect(self.path))

    def test_refuses_overwrite_and_missing_database_has_no_side_effect(self):
        before = self.path.read_bytes()
        with self.assertRaises(store.CampaignError):
            store.create(self.study, self.path)
        self.assertEqual(before, self.path.read_bytes())
        absent = self.root / "missing.sqlite"
        with self.assertRaises(store.CampaignError):
            store.run(absent)
        self.assertFalse(absent.exists())
        self.assertFalse(Path(str(absent) + ".lock").exists())

    def test_cancelled_attempt_keeps_full_debit(self):
        with mock.patch("continuum.store.make_policy", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                store.run(self.path)
        attempt = store.inspect(self.path)["attempts"][0]
        self.assertEqual(attempt["terminal"]["status"], "CANCELLED")
        self.assertEqual(attempt["charged_evaluations"], 8)
        self.assertEqual(attempt["terminal"]["observed_evaluations"], 0)
        self.assertEqual(store.run(self.path)["attempts"][1]["retry_of"], attempt["id"])

    def test_timeout_is_explicit_and_finite(self):
        with mock.patch("continuum.store.make_policy", side_effect=TimeoutError):
            result = store.run(self.path, max_trials=1)
        self.assertEqual(len(result["attempts"]), 2)
        self.assertTrue(all(a["terminal"]["status"] == "TIMED_OUT" for a in result["attempts"]))
        self.assertEqual(sum(a["charged_evaluations"] for a in result["attempts"]), 16)

    def test_deliberately_bad_candidate_is_invalid_not_a_zero(self):
        class BadPolicy:
            def propose(self):
                return Point(float("nan"), 1.0)
        with mock.patch("continuum.store.make_policy", return_value=BadPolicy()):
            with self.assertRaises(store.CampaignError):
                store.run(self.path)
        attempt = store.inspect(self.path)["attempts"][0]
        self.assertEqual(attempt["terminal"]["status"], "INVALID")
        self.assertIsNone(attempt["terminal"]["best"])
        self.assertEqual(attempt["observations"], [])
        self.assertEqual(attempt["charged_evaluations"], 8)

    def test_new_identity_cannot_stamp_source_changed_since_import(self):
        with mock.patch("continuum.store._runtime_source_identity", return_value="0" * 64):
            with self.assertRaisesRegex(store.CampaignError, "source changed since import"):
                store.runtime_identity()

    def test_changed_environment_blocks_without_admission(self):
        env = store.environment()
        env["runtime_digest"] = "0" * 64
        with mock.patch("continuum.store.environment", return_value=env):
            with self.assertRaisesRegex(store.CampaignError, "Runtime identity changed"):
                store.run(self.path)
        self.assertEqual(store.inspect(self.path)["attempts"], [])


if __name__ == "__main__":
    unittest.main()
