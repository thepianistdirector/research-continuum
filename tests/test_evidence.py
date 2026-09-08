"""Evidence attacks must fail even when an attacker recomputes file checksums."""

import copy
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from continuum import evidence, report, store
from continuum.numerical import Evaluator, Point
from continuum.study import DEFAULT_STUDY, Study


ROOT = Path(__file__).resolve().parents[1]
SCRATCH = ROOT / ".cache" / "tests"
SCRATCH.mkdir(parents=True, exist_ok=True)


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        data = copy.deepcopy(DEFAULT_STUDY)
        data.update(evaluations_per_policy=8, development_seeds=[11], confirmation_seeds=[101])
        self.study = Study.from_dict(data)
        self.path = self.root / "campaign.sqlite"
        self.initial = store.create(self.study, self.path)
        self.complete = store.run(self.path)

    def test_complete_campaign_derives_only_unreviewed_descriptive_claim(self):
        evidence.validate_snapshot(self.complete, require_complete=True)
        summary = evidence.summarize(self.complete)
        self.assertTrue(summary["campaign_complete"])
        self.assertNotEqual(summary["verdict"], "INCONCLUSIVE")
        self.assertEqual(summary["claim_status"], "UNREVIEWED")
        self.assertEqual(summary["independent_human_review"], "PENDING")
        self.assertEqual(summary["recorded_evaluations"], 64)
        self.assertEqual(summary["charged_evaluations"], 64)
        self.assertEqual(len(summary["reproductions"]), 4)
        self.assertTrue(all(r["status"] == "MATCH" for r in summary["reproductions"]))

    def test_partial_campaign_valid_for_inspection_but_not_export(self):
        evidence.validate_snapshot(self.initial)
        self.assertEqual(evidence.summarize(self.initial)["verdict"], "INCONCLUSIVE")
        with self.assertRaisesRegex(ValueError, "unfinished"):
            evidence.export_bundle(self.initial, self.root / "incomplete")
        self.assertFalse((self.root / "incomplete").exists())

    def test_missing_duplicate_and_wrong_raw_values_rejected(self):
        for mode in ("missing", "duplicate", "objective", "nan", "boolean", "valid-wrong-point"):
            damaged = copy.deepcopy(self.complete)
            observation = damaged["attempts"][0]["observations"][0]
            if mode == "missing":
                damaged["attempts"][0]["observations"].pop()
            elif mode == "duplicate":
                damaged["attempts"][0]["observations"][1]["index"] = 0
            elif mode == "objective":
                observation["value"] = 0.0
            elif mode == "nan":
                observation["value"] = float("nan")
            elif mode == "boolean":
                observation["point"][0] = True
            else:
                observation["point"] = [1.0, 1.0]
                observation["value"] = Evaluator(self.study).evaluate(Point(1.0, 1.0))
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                evidence.validate_snapshot(damaged)

    def test_schedule_evaluator_budget_and_lineage_tampering_rejected(self):
        mutations = [
            lambda s: s["trial_specs"].pop(),
            lambda s: s["trial_specs"].append(copy.deepcopy(s["trial_specs"][0])),
            lambda s: s["trial_specs"][0].update(seed=999),
            lambda s: s["allocations"][0].update(capacity=999999),
            lambda s: s.update(evaluator_digest="0" * 64),
            lambda s: s["study"].update(quality_threshold=1),
            lambda s: s["controls"].pop(),
            lambda s: s["attempts"][0].update(charged_evaluations=7),
            lambda s: s["attempts"][0].update(retry_of="unknown"),
            lambda s: s["attempts"].append(copy.deepcopy(s["attempts"][0])),
            lambda s: s["attempts"][0]["terminal"].update(best=0),
            lambda s: s["attempts"][0].update(staged=None),
            lambda s: s.update(extra="unknown"),
        ]
        for i, mutation in enumerate(mutations):
            damaged = copy.deepcopy(self.complete)
            mutation(damaged)
            with self.subTest(mutation=i), self.assertRaises(ValueError):
                evidence.validate_snapshot(damaged)

    def test_event_deletion_duplicate_and_terminal_disagreement_rejected(self):
        for mode in ("missing", "duplicate", "wrong-terminal", "wrong-attempt", "boolean", "causal-order"):
            damaged = copy.deepcopy(self.complete)
            if mode == "missing":
                damaged["events"].pop(2)
                for i, event in enumerate(damaged["events"], 1):
                    event["sequence"] = i
            elif mode == "duplicate":
                damaged["events"].append(copy.deepcopy(damaged["events"][-1]))
            elif mode == "wrong-terminal":
                damaged["events"][-1]["payload"]["status"] = "FAILED"
            elif mode == "wrong-attempt":
                damaged["events"][-1]["attempt_id"] = "unknown"
            elif mode == "boolean":
                damaged["events"][3]["payload"]["index"] = True
            else:
                second_admission = next(i for i, e in enumerate(damaged["events"])
                                        if e["kind"] == "ADMITTED" and e["attempt_id"] == damaged["attempts"][1]["id"])
                event = damaged["events"].pop(second_admission)
                damaged["events"].insert(2, event)
                for i, event in enumerate(damaged["events"], 1):
                    event["sequence"] = i
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                evidence.validate_snapshot(damaged)

    def test_exhausted_failures_export_with_inconclusive_claim_and_no_erased_cost(self):
        path = self.root / "failed.sqlite"
        store.create(self.study, path)
        with mock.patch("continuum.store.make_policy", side_effect=TimeoutError):
            failed = store.run(path)
        evidence.validate_snapshot(failed, require_complete=True)
        summary = evidence.summarize(failed)
        self.assertEqual(summary["verdict"], "INCONCLUSIVE")
        self.assertEqual(summary["charged_evaluations"], 128)
        self.assertEqual(summary["recorded_evaluations"], 0)
        self.assertEqual(summary["failed_attempts"], 16)
        bundle = evidence.export_bundle(failed, self.root / "failed-bundle")
        restored = evidence.verify_bundle(bundle)
        self.assertEqual(restored, failed)
        self.assertIn("TIMED_OUT", (bundle / "report.html").read_text())

    def test_bundle_roundtrip_retains_all_records_and_refuses_overwrite(self):
        bundle = evidence.export_bundle(self.complete, self.root / "bundle")
        self.assertEqual(evidence.verify_bundle(bundle), self.complete)
        before = {p.name: p.read_bytes() for p in bundle.iterdir()}
        with self.assertRaises(FileExistsError):
            evidence.export_bundle(self.complete, bundle)
        self.assertEqual(before, {p.name: p.read_bytes() for p in bundle.iterdir()})
        records = json.loads((bundle / "records.json").read_text())
        self.assertEqual(len(records["evaluations"]), len(self.complete["attempts"]))
        self.assertEqual(len(records["claim"]["all_evaluation_ids"]), len(self.complete["attempts"]))
        self.assertEqual(records["claim"]["status"], "UNREVIEWED")

    def _rewrite_checked_file(self, bundle, filename, data):
        (bundle / filename).write_bytes(data)
        manifest = json.loads((bundle / "manifest.json").read_text())
        manifest["files"][filename] = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
        (bundle / "manifest.json").write_bytes(evidence.canonical_bytes(manifest))

    def test_recomputed_checksums_do_not_make_false_claims_valid(self):
        for filename in ("evidence.json", "summary.json", "records.json", "report.html"):
            bundle = evidence.export_bundle(self.complete, self.root / filename)
            if filename == "report.html":
                data = (bundle / filename).read_bytes() + b"<script>alert('false claim')</script>"
            else:
                value = json.loads((bundle / filename).read_text())
                if filename == "evidence.json":
                    value["attempts"][0]["observations"][0]["value"] = 0
                elif filename == "summary.json":
                    value["claim_status"] = "APPROVED"
                else:
                    value["claim"]["independent_human_review"] = "PASSED"
                data = evidence.canonical_bytes(value)
            self._rewrite_checked_file(bundle, filename, data)
            with self.subTest(filename=filename), self.assertRaises(ValueError):
                evidence.verify_bundle(bundle)

    def test_extra_files_symlinks_duplicate_json_and_nonfinite_json_rejected(self):
        for mode in ("extra", "symlink", "fifo", "oversized", "duplicate-json", "nonfinite-json"):
            bundle = evidence.export_bundle(self.complete, self.root / mode)
            if mode == "extra":
                (bundle / "run-me.sh").write_text("exit 0")
            elif mode == "symlink":
                target = bundle / "summary.json"
                content = target.read_bytes()
                target.unlink()
                (self.root / "outside.json").write_bytes(content)
                target.symlink_to(self.root / "outside.json")
            elif mode == "fifo":
                target = bundle / "summary.json"
                target.unlink()
                os.mkfifo(target)
            elif mode == "oversized":
                with (bundle / "summary.json").open("wb") as stream:
                    stream.truncate(evidence.FILE_LIMIT + 1)
            else:
                data = b'{"schema_version":1,"schema_version":1}' if mode == "duplicate-json" else b'{"number":NaN}'
                self._rewrite_checked_file(bundle, "evidence.json", data)
            with self.subTest(mode=mode), self.assertRaises((ValueError, OSError)):
                evidence.verify_bundle(bundle)

    def test_failure_before_atomic_rename_does_not_publish_partial_bundle(self):
        destination = self.root / "interrupted"
        with mock.patch("continuum.evidence._rename_noreplace", side_effect=OSError("injected export failure")):
            with self.assertRaisesRegex(OSError, "injected"):
                evidence.export_bundle(self.complete, destination)
        self.assertFalse(destination.exists())
        self.assertEqual(list(self.root.glob(".interrupted.staging-*")), [])

    def test_racing_destination_is_never_overwritten(self):
        destination = self.root / "race"
        rename = evidence._rename_noreplace

        def race(source, target):
            target.mkdir()
            return rename(source, target)

        with mock.patch("continuum.evidence._rename_noreplace", side_effect=race):
            with self.assertRaises(FileExistsError):
                evidence.export_bundle(self.complete, destination)
        self.assertEqual(list(destination.iterdir()), [])

    def test_relabelled_source_attempts_cannot_be_a_fresh_reproduction(self):
        cloned = copy.deepcopy(self.complete)
        cloned["campaign_id"] = "renamed-source-copy"
        with self.assertRaises(ValueError):
            evidence.compare_reproduction(self.complete, cloned)
        cloned["source_records"].append({
            "id": "source-reproduction-" + self.complete["campaign_id"], "type": "SourceRecord",
            "schema_version": 1, "description": "Forged source binding for negative test",
            "license": "AGPL-3.0-only",
            "locator": "sha256:" + hashlib.sha256(evidence.canonical_bytes(self.complete)).hexdigest()})
        with self.assertRaisesRegex(ValueError, "reuse source attempt"):
            evidence.compare_reproduction(self.complete, cloned)

    def test_fresh_reproduction_rejects_reuse_and_records_runtime_deviations(self):
        with self.assertRaisesRegex(ValueError, "new campaign"):
            evidence.compare_reproduction(self.complete, self.complete)
        path = self.root / "fresh.sqlite"
        store.create(self.study, path, reproduction_source={
            "campaign_id": self.complete["campaign_id"],
            "evidence_digest": hashlib.sha256(evidence.canonical_bytes(self.complete)).hexdigest()})
        fresh = store.run(path)
        result = evidence.compare_reproduction(self.complete, fresh)
        self.assertEqual(result["status"], "MATCH")
        self.assertEqual(result["independent_human_review"], "PENDING")
        self.assertEqual(len(result["comparisons"]), 8)
        fresh["environment"]["runtime_digest"] = "0" * 64
        result = evidence.compare_reproduction(self.complete, fresh)
        self.assertEqual(result["status"], "INCONCLUSIVE")
        self.assertIn("environment runtime_digest differs", result["deviations"])

    def test_report_escapes_text_and_has_semantic_keyboard_navigation(self):
        hostile = copy.deepcopy(self.initial)
        hostile["study"]["question"] = '<script>alert("attack")</script> Read $(touch SHOULD_NOT_EXIST)'
        hostile["study_digest"] = Study.from_dict(hostile["study"]).digest
        hostile["events"][0]["payload"]["study_digest"] = hostile["study_digest"]
        rendered = report.render(hostile, evidence.summarize(hostile))
        self.assertIn("&lt;script&gt;", rendered)
        self.assertNotIn("<script>", rendered)
        self.assertNotIn("onclick=", rendered)
        self.assertIn("prefers-reduced-motion", rendered)

        class Elements(HTMLParser):
            def __init__(self):
                super().__init__()
                self.ids, self.anchors, self.tables, self.captions, self.scripts = set(), [], 0, 0, 0

            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if "id" in attrs:
                    self.ids.add(attrs["id"])
                if tag == "a" and attrs.get("href", "").startswith("#"):
                    self.anchors.append(attrs["href"][1:])
                self.tables += tag == "table"
                self.captions += tag == "caption"
                self.scripts += tag == "script"

        parsed = Elements()
        parsed.feed(rendered)
        self.assertEqual(parsed.scripts, 0)
        self.assertEqual(parsed.tables, parsed.captions)
        self.assertTrue(set(parsed.anchors) <= parsed.ids)
        self.assertIn('lang="en"', rendered)
        self.assertIn('name="viewport"', rendered)
        self.assertIn('scope="col"', rendered)
        self.assertIn('tabindex="0" role="region"', rendered)


if __name__ == "__main__":
    unittest.main()
