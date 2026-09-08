"""The public command workflow must execute fresh work and preserve accepted files."""
import copy
import hashlib
import json
import os
import signal
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from continuum import store
from continuum.evidence import canonical_bytes, export_bundle
from continuum.study import DEFAULT_STUDY, Study

ROOT = Path(__file__).resolve().parents[1]
SCRATCH = ROOT / ".cache" / "tests"
SCRATCH.mkdir(parents=True, exist_ok=True)


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        data = copy.deepcopy(DEFAULT_STUDY)
        data.update(evaluations_per_policy=8, development_seeds=[11], confirmation_seeds=[101])
        self.study = Study.from_dict(data)
        self.source_db = self.root / "source.sqlite"
        store.create(self.study, self.source_db)
        self.source = store.run(self.source_db)
        self.bundle = export_bundle(self.source, self.root / "bundle")

    def cli(self, *arguments):
        env = {"PATH": os.defpath, "PYTHONPATH": str(ROOT), "PYTHONDONTWRITEBYTECODE": "1",
               "TMPDIR": str(SCRATCH), "LANG": "C.UTF-8"}
        return subprocess.run([sys.executable, "-m", "continuum", *map(str, arguments)],
                              cwd=self.root, env=env, capture_output=True, text=True, timeout=30)

    def test_reproduce_executes_a_new_campaign_and_record(self):
        fresh, record = self.root / "fresh.sqlite", self.root / "reproduction.json"
        result = self.cli("reproduce", "--bundle", self.bundle, "--db", fresh, "--record", record)
        self.assertEqual(result.returncode, 0, result.stderr)
        proof = json.loads(record.read_text())
        self.assertEqual(proof["status"], "MATCH")
        self.assertEqual(proof["source_campaign_id"], self.source["campaign_id"])
        self.assertNotEqual(proof["source_campaign_id"], proof["fresh_campaign_id"])
        self.assertEqual(len(store.inspect(fresh)["attempts"]), 8)
        before = record.read_bytes()
        again = self.cli("reproduce", "--bundle", self.bundle, "--db", fresh, "--record", record)
        self.assertEqual(again.returncode, 2)
        self.assertEqual(record.read_bytes(), before)

    def test_cached_completed_campaign_cannot_be_relabelled_fresh(self):
        old = self.root / "old.sqlite"
        store.create(self.study, old)
        store.run(old)
        record = self.root / "forged-fresh.json"
        result = self.cli("reproduce", "--bundle", self.bundle, "--db", old, "--record", record)
        self.assertEqual(result.returncode, 2)
        self.assertIn("not created for reproducing", result.stderr)
        self.assertFalse(record.exists())

    def test_unbound_partial_campaign_cannot_be_adopted_as_reproduction(self):
        old = self.root / "old-partial.sqlite"
        store.create(self.study, old)
        before = store.run(old, max_trials=1)
        record = self.root / "forged-partial.json"
        result = self.cli("reproduce", "--bundle", self.bundle, "--db", old, "--record", record)
        self.assertEqual(result.returncode, 2)
        self.assertIn("not created for reproducing", result.stderr)
        self.assertFalse(record.exists())
        self.assertEqual(before, store.inspect(old))

    def test_bound_interrupted_reproduction_resumes(self):
        fresh = self.root / "interrupted-reproduction.sqlite"
        store.create(self.study, fresh, expected_evaluator=self.source["evaluator_digest"],
                     reproduction_source={"campaign_id": self.source["campaign_id"],
                       "evidence_digest": hashlib.sha256(canonical_bytes(self.source)).hexdigest()})
        partial = store.run(fresh, max_trials=1)
        record = self.root / "resumed-reproduction.json"
        result = self.cli("reproduce", "--bundle", self.bundle, "--db", fresh, "--record", record)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(record.read_text())["status"], "MATCH")
        self.assertEqual(partial["attempts"][0], store.inspect(fresh)["attempts"][0])

    def test_record_parent_failure_is_detected_before_any_fresh_trials(self):
        parent = self.root / "regular-file"
        parent.write_text("preserve")
        fresh = self.root / "not-admitted.sqlite"
        result = self.cli("reproduce", "--bundle", self.bundle, "--db", fresh,
                          "--record", parent / "record.json")
        self.assertEqual(result.returncode, 2)
        self.assertFalse(fresh.exists())
        self.assertEqual(parent.read_text(), "preserve")

    def test_reproduction_outputs_cannot_mutate_the_input_bundle(self):
        before = sorted(p.name for p in self.bundle.iterdir())
        result = self.cli("reproduce", "--bundle", self.bundle, "--db", self.root / "outside.sqlite",
                          "--record", self.bundle / "record.json")
        self.assertEqual(result.returncode, 2)
        self.assertIn("outside the accepted input bundle", result.stderr)
        self.assertEqual(before, sorted(p.name for p in self.bundle.iterdir()))
        self.assertFalse((self.root / "outside.sqlite").exists())

    def test_real_kill_after_final_reproduction_before_record_is_recoverable(self):
        fresh, record = self.root / "late-crash.sqlite", self.root / "late-record.json"
        script = """import os,signal,sys
import continuum.__main__ as cli
def kill_before_publish(*args):
 os.kill(os.getpid(),signal.SIGKILL)
cli.write_new_json=kill_before_publish
cli.main(sys.argv[1:])
"""
        env = {"PATH": os.defpath, "PYTHONPATH": str(ROOT), "PYTHONDONTWRITEBYTECODE": "1",
               "TMPDIR": str(SCRATCH), "LANG": "C.UTF-8"}
        killed = subprocess.run([sys.executable, "-c", script, "reproduce", "--bundle", str(self.bundle),
                                 "--db", str(fresh), "--record", str(record)], cwd=self.root, env=env,
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(killed.returncode, -signal.SIGKILL, killed.stderr)
        self.assertFalse(record.exists())
        completed = store.inspect(fresh)
        self.assertTrue(all(a["terminal"] for a in completed["attempts"]))
        resumed = self.cli("reproduce", "--bundle", self.bundle, "--db", fresh, "--record", record)
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        proof = json.loads(record.read_text())
        self.assertEqual(proof["status"], "MATCH")
        self.assertIn("no new execution claimed", proof["publication_context"])
        self.assertEqual(completed, store.inspect(fresh))

    def test_invalid_study_fails_before_creating_database(self):
        invalid = self.root / "invalid.json"
        invalid.write_text(json.dumps(self.study.to_dict() | {"evaluator": "eval(user_code)"}))
        database = self.root / "invalid.sqlite"
        result = self.cli("init", "--study", invalid, "--db", database)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(database.exists())


if __name__ == "__main__":
    unittest.main()
