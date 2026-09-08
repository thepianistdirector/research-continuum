"""Validate retained computation and derive bounded, unreviewed evidence records.

Bundles contain data, never executable instructions. Checksums detect accidental
or uncoordinated edits; they do not authenticate an author or confer review.
"""

from __future__ import annotations

import ctypes
import errno
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import stat
import statistics
import tempfile
from datetime import datetime, timedelta

from .study import Study
from .numerical import Evaluator, Point, controls, evaluator_identity, make_policy


FILE_LIMIT = 128 * 1024 * 1024
BUNDLE_LIMIT = 256 * 1024 * 1024
FILES = frozenset({"evidence.json", "summary.json", "records.json", "report.html"})
STATUSES = frozenset({"COMPLETED", "FAILED", "INVALID", "CANCELLED", "TIMED_OUT"})
LIMITATIONS = [
    "This is one public, known-answer numerical fixture, not a secret holdout.",
    "Grid and coordinate policy repeats are deterministic checks, not independent stochastic samples.",
    "Medians are descriptive; no significance, confidence interval, causal, novelty, or general superiority claim is made.",
    "Equal charged evaluation units do not imply equal CPU or elapsed time.",
    "Recorded observations can undercount calls lost at process death; full admitted allowance remains charged.",
    "Operator-invoked audits recompute objectives outside admitted search; campaign counts exclude that verification overhead.",
    "Reserved reproduction runs use the same coordinator and built-ins; independent external execution is a separate gate.",
    "Trusted built-ins share a process. Logical interfaces are not adversarial code isolation.",
    "Checksums detect integrity changes; they are not signatures or scientific validation.",
    "Independent human and qualified domain review are pending.",
]


def canonical_bytes(value):
    """Stable JSON bytes, also used to identify the exact exported snapshot."""
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2,
                       allow_nan=False) + "\n").encode("utf-8")


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _keys(value, names, label):
    _require(type(value) is dict and set(value) == set(names.split()),
             f"{label}: missing or unknown fields")


def _text(value, label, limit=4096, empty=False):
    _require(type(value) is str and (empty or bool(value)) and len(value) <= limit,
             f"{label}: invalid text")


def _integer(value, label, minimum=0):
    _require(type(value) is int and value >= minimum, f"{label}: invalid integer")


def _number(value, label):
    _require(type(value) in (int, float) and math.isfinite(value), f"{label}: non-finite or invalid number")


def _digest(value, label):
    _require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None,
             f"{label}: invalid SHA-256")


def _timestamp(value):
    _text(value, "timestamp", 64)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid timestamp") from exc
    _require(parsed.utcoffset() == timedelta(0), "timestamp must be UTC")


def _schedule(study):
    """Independent reconstruction, deliberately not imported from the store."""
    originals = []
    for phase, seeds in (("development", study.development_seeds),
                         ("confirmation", study.confirmation_seeds)):
        for policy in (study.baseline, study.candidate):
            for seed in seeds:
                originals.append({
                    "id": f"{phase}-{policy}-{seed}", "phase": phase,
                    "source_phase": phase, "policy": policy, "seed": seed,
                    "reproduces": None, "pool": f"{phase}:{policy}",
                    "allocation": study.evaluations_per_policy * study.max_attempts_per_trial,
                })
    return originals + [dict(row, id="reproduction-" + row["id"], phase="reproduction",
                             reproduces=row["id"], pool="reproduction:" + row["policy"])
                        for row in originals]


def _terminal(value, observations, study, *, staged=False):
    _keys(value, "status reason observed_evaluations best elapsed_seconds cpu_seconds ended_at", "terminal")
    _require(value["status"] in STATUSES, "unknown terminal status")
    _text(value["reason"], "terminal reason", empty=True)
    _integer(value["observed_evaluations"], "observed evaluations")
    _require(value["observed_evaluations"] == len(observations), "terminal observation count mismatch")
    expected_best = min((o["value"] for o in observations), default=None)
    if value["best"] is not None:
        _number(value["best"], "best")
    _require(value["best"] == expected_best, "terminal best disagrees with retained observations")
    for field in ("elapsed_seconds", "cpu_seconds"):
        if value[field] is not None:
            _number(value[field], field)
            _require(value[field] >= 0, "negative timing")
    _timestamp(value["ended_at"])
    if value["status"] == "COMPLETED":
        _require(len(observations) == study.evaluations_per_policy, "completed attempt has missing observations")
    if staged:
        _require(value["status"] == "COMPLETED", "only complete results may be staged")


def validate_snapshot(snapshot, require_complete=False):
    """Reject malformed accounting, evaluator drift and false computational evidence.

Partial local campaigns are valid. Complete exports need every logical trial
completed or exhausted, including all retained failed attempts and terminals.
"""
    try:
        _validate_snapshot(snapshot, require_complete)
    except (KeyError, TypeError, OverflowError, RecursionError) as exc:
        raise ValueError("malformed evidence snapshot") from exc


def _validate_snapshot(snapshot, require_complete):
    _keys(snapshot, "schema_version campaign_id study study_digest evaluator_digest environment created_at source_records trial_specs allocations controls attempts events", "snapshot")
    _require(type(snapshot["schema_version"]) is int and snapshot["schema_version"] == 1,
             "unsupported snapshot version")
    _text(snapshot["campaign_id"], "campaign id", 128)
    _timestamp(snapshot["created_at"])
    study = Study.from_dict(snapshot["study"])
    _require(snapshot["study"] == study.to_dict(), "non-canonical study")
    _require(snapshot["study_digest"] == study.digest, "study digest mismatch")
    _require(snapshot["evaluator_digest"] == evaluator_identity(), "evaluator digest mismatch: use original release")
    _keys(snapshot["environment"], "python implementation system machine sqlite package_version runtime_digest", "environment")
    for field, value in snapshot["environment"].items():
        _text(value, "environment " + field, 256)
    _digest(snapshot["environment"]["runtime_digest"], "runtime digest")
    _require(type(snapshot["source_records"]) is list and bool(snapshot["source_records"]), "missing source records")
    source_ids = set()
    for source in snapshot["source_records"]:
        _keys(source, "id type schema_version description license locator", "source record")
        _require(source["type"] == "SourceRecord" and type(source["schema_version"]) is int
                 and source["schema_version"] == 1, "invalid source record version/type")
        for field in ("id", "description", "license", "locator"):
            _text(source[field], "source " + field)
        _require(source["id"] not in source_ids, "duplicate source id")
        source_ids.add(source["id"])
    expected = {row["id"]: row for row in _schedule(study)}
    _require(type(snapshot["trial_specs"]) is list, "invalid trial schedule")
    actual = {}
    for spec in snapshot["trial_specs"]:
        _keys(spec, "id phase source_phase policy seed reproduces pool allocation", "trial specification")
        _integer(spec["seed"], "seed")
        _integer(spec["allocation"], "trial allocation", 1)
        _require(spec["id"] not in actual, "duplicate trial specification")
        actual[spec["id"]] = spec
    _require(actual == expected, "trial schedule differs from frozen study")
    reserves = {}
    for spec in expected.values():
        reserves[spec["pool"]] = reserves.get(spec["pool"], 0) + spec["allocation"]
    _require(type(snapshot["allocations"]) is list, "invalid allocations")
    observed_reserves = {}
    for row in snapshot["allocations"]:
        _keys(row, "pool capacity", "allocation")
        _integer(row["capacity"], "allocation capacity", 1)
        _require(row["pool"] not in observed_reserves, "duplicate pool allocation")
        observed_reserves[row["pool"]] = row["capacity"]
    _require(observed_reserves == reserves, "reserved budgets differ from frozen study")
    _require(type(snapshot["controls"]) is list, "invalid evaluator controls")
    for control in snapshot["controls"]:
        _keys(control, "name expected observed passed objectiveCalls", "control")
        _integer(control["objectiveCalls"], "control calls")
        _require(type(control["passed"]) is bool, "control verdict must be boolean")
    _require(snapshot["controls"] == controls(study), "evaluator controls missing or altered")
    _require(all(row["passed"] is True for row in snapshot["controls"]), "evaluator control failed")

    _require(type(snapshot["attempts"]) is list, "invalid attempts")
    _require(len(snapshot["attempts"]) <= len(expected) * study.max_attempts_per_trial, "too many attempts")
    by_id, by_trial, charges = {}, {key: [] for key in expected}, {key: 0 for key in reserves}
    evaluator = Evaluator(study, expected_identity=snapshot["evaluator_digest"])
    for attempt in snapshot["attempts"]:
        _keys(attempt, "id trial_id number retry_of charged_evaluations started_at observations terminal staged", "attempt")
        _text(attempt["id"], "attempt id", 128)
        _require(attempt["id"] not in by_id, "duplicate attempt id")
        _require(attempt["trial_id"] in expected, "unknown trial reference")
        _integer(attempt["number"], "attempt number", 1)
        _integer(attempt["charged_evaluations"], "attempt debit", 1)
        _require(attempt["charged_evaluations"] == study.evaluations_per_policy, "attempt charge differs from frozen allowance")
        _timestamp(attempt["started_at"])
        spec = expected[attempt["trial_id"]]
        prior = by_trial[attempt["trial_id"]]
        _require(attempt["number"] == len(prior) + 1 <= study.max_attempts_per_trial, "attempt order/limit invalid")
        _require(attempt["retry_of"] == (prior[-1]["id"] if prior else None), "retry lineage mismatch")
        if prior:
            _require(prior[-1]["terminal"] is not None and prior[-1]["terminal"]["status"] != "COMPLETED",
                     "cannot retry active or completed attempt")
        observations = attempt["observations"]
        _require(type(observations) is list and len(observations) <= study.evaluations_per_policy,
                 "observation allowance exceeded")
        policy = make_policy(spec["policy"], study, spec["seed"])
        for index, observation in enumerate(observations):
            _keys(observation, "index point value", "observation")
            _integer(observation["index"], "observation index")
            _require(observation["index"] == index, "missing or duplicate observation index")
            _require(type(observation["point"]) is list and len(observation["point"]) == 2, "invalid point")
            for coordinate in observation["point"]:
                _number(coordinate, "point coordinate")
            _number(observation["value"], "objective value")
            point = policy.propose()
            _require(point.to_list() == observation["point"], "observation differs from seeded policy replay")
            value = evaluator.evaluate(Point(*observation["point"]))
            _require(value == observation["value"], "raw objective disagrees with evaluator")
            policy.observe(point, value)
        if attempt["staged"] is not None:
            _terminal(attempt["staged"], observations, study, staged=True)
        if attempt["terminal"] is not None:
            _terminal(attempt["terminal"], observations, study)
            if attempt["terminal"]["status"] == "COMPLETED":
                _require(attempt["staged"] == attempt["terminal"], "completed terminal lacks identical staging")
            else:
                _require(attempt["staged"] is None, "noncomplete terminal cannot replace staged completion")
        charges[spec["pool"]] += attempt["charged_evaluations"]
        _require(charges[spec["pool"]] <= reserves[spec["pool"]], "reserved pool exhausted")
        by_id[attempt["id"]] = attempt
        prior.append(attempt)
    if require_complete:
        for attempts in by_trial.values():
            _require(bool(attempts) and all(a["terminal"] is not None for a in attempts), "campaign still has unfinished trials")
            _require(attempts[-1]["terminal"]["status"] == "COMPLETED"
                     or len(attempts) == study.max_attempts_per_trial, "campaign has retryable trials")

    _require(type(snapshot["events"]) is list and bool(snapshot["events"]), "missing event ledger")
    projections = {key: [] for key in by_id}
    active = None
    admission_order = []
    for sequence, event in enumerate(snapshot["events"], 1):
        _keys(event, "sequence kind attempt_id payload at", "event")
        _integer(event["sequence"], "event sequence", 1)
        _require(event["sequence"] == sequence, "event sequence gap or duplicate")
        _timestamp(event["at"])
        if sequence == 1:
            _require(event["kind"] == "CREATED" and event["attempt_id"] is None
                     and event["payload"] == {"study_digest": study.digest, "evaluator_digest": snapshot["evaluator_digest"]},
                     "invalid campaign creation event")
        else:
            _require(event["attempt_id"] in by_id, "event references unknown attempt")
            payload = event["payload"]
            if event["kind"] == "ADMITTED":
                _keys(payload, "trial_id number charged_evaluations", "admission event")
                _integer(payload["number"], "event attempt number", 1)
                _integer(payload["charged_evaluations"], "event charge", 1)
                _require(active is None, "attempt admitted before preceding attempt terminated")
                active = event["attempt_id"]
                admission_order.append(active)
            else:
                _require(active == event["attempt_id"], "event is outside its active attempt")
                if event["kind"] == "OBSERVED":
                    _keys(payload, "index", "observation event")
                    _integer(payload["index"], "event observation index")
                elif event["kind"] == "STAGED":
                    _keys(payload, "status", "staging event")
                elif event["kind"] == "TERMINATED":
                    _keys(payload, "status reason", "terminal event")
                    active = None
                else:
                    raise ValueError("unknown event kind")
            projections[event["attempt_id"]].append((event["kind"], event["payload"]))
    _require(admission_order == list(by_id), "attempt list disagrees with admission order")
    for attempt in by_id.values():
        expected_events = [("ADMITTED", {key: attempt[key] for key in ("trial_id", "number", "charged_evaluations")})]
        expected_events += [("OBSERVED", {"index": row["index"]}) for row in attempt["observations"]]
        if attempt["staged"] is not None:
            expected_events.append(("STAGED", {"status": "COMPLETED"}))
        if attempt["terminal"] is not None:
            expected_events.append(("TERMINATED", {key: attempt["terminal"][key] for key in ("status", "reason")}))
        _require(projections[attempt["id"]] == expected_events, "event ledger disagrees with attempt state")


def _completed(attempts):
    return next((a for a in attempts if a["terminal"] is not None
                 and a["terminal"]["status"] == "COMPLETED"), None)


def _compare_sequences(original, fresh, tolerance):
    if original is None or fresh is None:
        return "INCONCLUSIVE"
    left, right = original["observations"], fresh["observations"]
    if len(left) != len(right):
        return "MISMATCH"
    for a, b in zip(left, right):
        values = zip(a["point"] + [a["value"]], b["point"] + [b["value"]])
        if a["index"] != b["index"] or not all(math.isclose(x, y, rel_tol=tolerance, abs_tol=tolerance) for x, y in values):
            return "MISMATCH"
    return "MATCH"


def summarize(snapshot):
    """Return descriptive outcomes only; scientific review remains unfulfilled."""
    validate_snapshot(snapshot)
    study = Study.from_dict(snapshot["study"])
    grouped = {spec["id"]: [] for spec in snapshot["trial_specs"]}
    for attempt in snapshot["attempts"]:
        grouped[attempt["trial_id"]].append(attempt)
    trial_results, reproductions = [], []
    for spec in snapshot["trial_specs"]:
        attempts = grouped[spec["id"]]
        done = _completed(attempts)
        last = attempts[-1] if attempts else None
        exhausted = bool(last and last["terminal"] is not None
                         and len(attempts) == study.max_attempts_per_trial and done is None)
        result = {
            "trial_id": spec["id"], "phase": spec["phase"], "source_phase": spec["source_phase"],
            "policy": spec["policy"], "seed": spec["seed"],
            "status": "COMPLETED" if done else "EXHAUSTED" if exhausted else "PENDING",
            "attempt_ids": [a["id"] for a in attempts], "completed_attempt_id": done["id"] if done else None,
            "best": done["terminal"]["best"] if done else None,
            "quality_met": done["terminal"]["best"] <= study.quality_threshold if done else None,
            "charged_evaluations": sum(a["charged_evaluations"] for a in attempts),
            "recorded_evaluations": sum(len(a["observations"]) for a in attempts),
            "failed_attempts": sum(a["terminal"] is not None and a["terminal"]["status"] != "COMPLETED" for a in attempts),
        }
        trial_results.append(result)
        if spec["reproduces"]:
            source = _completed(grouped[spec["reproduces"]])
            reproductions.append({"id": "reproduction-record-" + spec["id"], "schema_version": 1,
                "type": "ReproductionRecord", "source_trial_id": spec["reproduces"], "trial_id": spec["id"],
                "source_attempt_id": source["id"] if source else None,
                "attempt_id": done["id"] if done else None,
                "status": _compare_sequences(source, done, study.to_dict()["reproduction_tolerance"]),
                "tolerance": study.to_dict()["reproduction_tolerance"],
                "context": "reserved fresh execution in the same coordinator; no independent human review"})
    groups = []
    for phase in ("development", "confirmation", "reproduction"):
        for policy in (study.baseline, study.candidate):
            rows = [r for r in trial_results if r["phase"] == phase and r["policy"] == policy]
            bests = [r["best"] for r in rows if r["status"] == "COMPLETED"]
            groups.append({"phase": phase, "policy": policy, "scheduled_trials": len(rows),
                           "completed_trials": len(bests), "median_best": statistics.median(bests) if bests else None,
                           "quality_met_trials": sum(r["quality_met"] is True for r in rows),
                           "charged_evaluations": sum(r["charged_evaluations"] for r in rows),
                           "recorded_evaluations": sum(r["recorded_evaluations"] for r in rows),
                           "failed_attempts": sum(r["failed_attempts"] for r in rows)})
    reasons = []
    for phase in ("development", "confirmation"):
        baseline, candidate = [g for g in groups if g["phase"] == phase]
        if any(g["completed_trials"] != g["scheduled_trials"] for g in (baseline, candidate)):
            reasons.append(f"{phase}: some original trials are missing or ineligible")
        if baseline["charged_evaluations"] != candidate["charged_evaluations"]:
            reasons.append(f"{phase}: charged evaluation costs differ between policies")
    if any(r["status"] != "MATCH" for r in reproductions):
        reasons.append("reserved reproduction is missing, ineligible, or mismatched")
    baseline, candidate = [g for g in groups if g["phase"] == "confirmation"]
    verdict, relation = "INCONCLUSIVE", "inconclusive"
    if not reasons:
        difference = candidate["median_best"] - baseline["median_best"]
        verdict = "CANDIDATE_LOWER" if difference < 0 else "BASELINE_LOWER" if difference > 0 else "TIE"
        relation = "consistent" if difference < 0 else "contradicted"
    complete = all(r["status"] in ("COMPLETED", "EXHAUSTED") for r in trial_results)
    result = {"schema_version": 1, "campaign_id": snapshot["campaign_id"], "study_digest": study.digest,
            "campaign_complete": complete, "verdict": verdict, "hypothesis_relation": relation,
            "claim_status": "UNREVIEWED", "independent_human_review": "PENDING",
            "inconclusive_reasons": reasons, "groups": groups, "trials": trial_results,
            "reproductions": reproductions, "charged_evaluations": sum(g["charged_evaluations"] for g in groups),
            "recorded_evaluations": sum(g["recorded_evaluations"] for g in groups),
            "reserved_evaluations": sum(r["capacity"] for r in snapshot["allocations"]),
            "control_objective_calls": sum(row["objectiveCalls"] for row in snapshot["controls"]),
            "failed_attempts": sum(g["failed_attempts"] for g in groups), "limitations": LIMITATIONS.copy()}
    if study.schema_version == 2:
        from .analysis import study_uncertainty
        result["uncertainty"] = study_uncertainty(study, result)
        result["limitations"][2] = "The frozen verdict is descriptive. Seed resampling intervals are conditional summaries, not population confidence or significance guarantees."
    return result


def _records(snapshot, summary):
    """Small versioned graph. Raw values remain in the single evidence snapshot."""
    study = Study.from_dict(snapshot["study"])
    study_id = "study-" + snapshot["study_digest"]
    question_id, hypothesis_id = "question-" + snapshot["study_digest"], "hypothesis-" + snapshot["study_digest"]
    evaluations = [{"id": "evaluation-" + a["id"], "schema_version": 1, "type": "EvaluationRecord",
                    "trial_id": a["trial_id"], "run_id": "run-" + a["id"], "evaluator_digest": snapshot["evaluator_digest"],
                    "eligible": a["terminal"] is not None and a["terminal"]["status"] == "COMPLETED",
                    "result": a["terminal"], "observation_source": {"file": "evidence.json", "attempt_id": a["id"]}}
                   for a in snapshot["attempts"]]
    by_trial = {r["trial_id"]: r for r in summary["trials"]}
    confirmation_ids = ["evaluation-" + r["completed_attempt_id"] for r in summary["trials"]
                        if r["phase"] == "confirmation" and r["completed_attempt_id"] is not None]
    support, contradiction = [], []
    for spec in snapshot["trial_specs"]:
        if spec["phase"] == "confirmation" and spec["policy"] == study.candidate:
            candidate = by_trial[spec["id"]]
            baseline = by_trial[f"confirmation-{study.baseline}-{spec['seed']}"]
            if candidate["best"] is not None and baseline["best"] is not None:
                refs = ["evaluation-" + r["completed_attempt_id"] for r in (baseline, candidate)]
                (support if candidate["best"] < baseline["best"] else contradiction).extend(refs)
    return {"schema_version": 1, "source_records": snapshot["source_records"],
            "question": {"id": question_id, "type": "QuestionRevision", "schema_version": 1,
                         "text": snapshot["study"]["question"], "source_ids": [r["id"] for r in snapshot["source_records"]]},
            "hypothesis": {"id": hypothesis_id, "type": "HypothesisRevision", "schema_version": 1,
                           "question_id": question_id, "text": snapshot["study"]["hypothesis"], "falsifier": snapshot["study"]["falsifier"]},
            "study": {"id": study_id, "type": "StudyDesign", "schema_version": 1,
                      "question_id": question_id, "hypothesis_id": hypothesis_id, "design": snapshot["study"]},
            "trials": [dict(spec, type="TrialSpec", schema_version=1, study_id=study_id) for spec in snapshot["trial_specs"]],
            "runs": [{"id": "run-" + a["id"], "type": "RunResult", "schema_version": 1,
                      "trial_id": a["trial_id"], "attempt_id": a["id"], "retry_of": a["retry_of"],
                      "charged_evaluations": a["charged_evaluations"], "terminal": a["terminal"]} for a in snapshot["attempts"]],
            "evaluations": evaluations, "reproductions": summary["reproductions"],
            "claim": {"id": "claim-" + snapshot["campaign_id"], "type": "ResearchClaim", "schema_version": 1,
                      "question_id": question_id, "hypothesis_id": hypothesis_id, "study_id": study_id,
                      "status": "UNREVIEWED", "verdict": summary["verdict"], "hypothesis_relation": summary["hypothesis_relation"],
                      "comparison_evaluation_ids": confirmation_ids, "support_evaluation_ids": support,
                      "contradiction_evaluation_ids": contradiction,
                      "all_evaluation_ids": [r["id"] for r in evaluations],
                      "reproduction_ids": [r["id"] for r in summary["reproductions"]],
                      "scope": "descriptive median for this frozen fixture only", "limitations": summary["limitations"],
                      "independent_human_review": "PENDING"},
            "report_design": {"audience": "technical", "surface": "offline semantic HTML",
                "structure": "answer; frozen definitions; findings and exact trial lookup; methods; controls and recovery; limitations; next steps and questions",
                "chart_omission": "The single-study report prioritizes exact per-trial evidence. The campaign browser plots recorded attempt traces and separates descriptive seed resampling from the frozen verdict.",
                "dependencies": "Python standard library only; no external runtime resources"}}


def compare_reproduction(original_snapshot, fresh_snapshot):
    """Compare genuinely new execution; caller records the actual observer identity."""
    validate_snapshot(original_snapshot, require_complete=True)
    validate_snapshot(fresh_snapshot, require_complete=True)
    _require(original_snapshot["campaign_id"] != fresh_snapshot["campaign_id"], "reproduction requires a new campaign identity")
    source_digest = hashlib.sha256(canonical_bytes(original_snapshot)).hexdigest()
    bindings = [row for row in fresh_snapshot["source_records"]
                if row["id"] == "source-reproduction-" + original_snapshot["campaign_id"]]
    _require(len(bindings) == 1 and bindings[0]["locator"] == "sha256:" + source_digest,
             "fresh campaign was not accepted for reproducing this exact source evidence")
    _require(not ({a["id"] for a in original_snapshot["attempts"]}
                  & {a["id"] for a in fresh_snapshot["attempts"]}),
             "reproduction cannot reuse source attempt identities")
    for field in ("study_digest", "evaluator_digest"):
        _require(original_snapshot[field] == fresh_snapshot[field], "reproduction contract differs: " + field)
    grouped = []
    for snapshot in (original_snapshot, fresh_snapshot):
        rows = {spec["id"]: [] for spec in snapshot["trial_specs"]}
        for attempt in snapshot["attempts"]:
            rows[attempt["trial_id"]].append(attempt)
        grouped.append(rows)
    comparisons = []
    tolerance = original_snapshot["study"]["reproduction_tolerance"]
    for spec in original_snapshot["trial_specs"]:
        left, right = (_completed(group[spec["id"]]) for group in grouped)
        comparisons.append({"trial_id": spec["id"], "source_attempt_id": left["id"] if left else None,
                            "fresh_attempt_id": right["id"] if right else None,
                            "status": _compare_sequences(left, right, tolerance)})
    deviations = [f"environment {key} differs" for key in original_snapshot["environment"]
                  if original_snapshot["environment"][key] != fresh_snapshot["environment"][key]]
    status = "MISMATCH" if any(c["status"] == "MISMATCH" for c in comparisons) else (
        "INCONCLUSIVE" if deviations or any(c["status"] != "MATCH" for c in comparisons) else "MATCH")
    return {"schema_version": 1, "type": "ReproductionRecord", "status": status,
            "source_campaign_id": original_snapshot["campaign_id"], "fresh_campaign_id": fresh_snapshot["campaign_id"],
            "source_evidence_digest": hashlib.sha256(canonical_bytes(original_snapshot)).hexdigest(),
            "fresh_evidence_digest": hashlib.sha256(canonical_bytes(fresh_snapshot)).hexdigest(),
            "study_digest": original_snapshot["study_digest"], "evaluator_digest": original_snapshot["evaluator_digest"],
            "fresh_environment": fresh_snapshot["environment"], "tolerance": tolerance,
            "comparisons": comparisons, "deviations": deviations,
            "review_status": "UNREVIEWED", "independent_human_review": "PENDING",
            "observation_context": "fresh local execution; independence not established"}


def _read_json(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            _require(key not in result, "duplicate JSON field")
            result[key] = value
        return result

    def nonfinite(value):
        raise ValueError("non-finite JSON number: " + value)

    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=unique, parse_constant=nonfinite)
    except (UnicodeError, RecursionError) as exc:
        raise ValueError("invalid UTF-8 JSON") from exc


def _payloads(snapshot):
    from .report import render
    summary = summarize(snapshot)
    return {"evidence.json": canonical_bytes(snapshot), "summary.json": canonical_bytes(summary),
            "records.json": canonical_bytes(_records(snapshot, summary)),
            "report.html": render(snapshot, summary).encode("utf-8")}


def verify_bundle(path):
    """Verify a strict regular-file inventory and replay all trusted computation."""
    path = Path(path)
    _require(path.is_dir() and not path.is_symlink(), "bundle must be a real directory")
    _require({p.name for p in path.iterdir()} == FILES | {"manifest.json"}, "bundle file inventory differs")
    data, total = {}, 0
    for name in FILES | {"manifest.json"}:
        target = path / name
        # Nonblocking open prevents an imported FIFO from hanging verification;
        # fstat validates the actual opened object, including replacement races.
        fd = os.open(target, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            _require(stat.S_ISREG(info.st_mode), "bundle contains a non-regular file")
            _require(info.st_size <= FILE_LIMIT, "bundle file exceeds 128 MiB limit; use a smaller frozen study")
            total += info.st_size
            _require(total <= BUNDLE_LIMIT, "bundle exceeds 256 MiB limit; use a smaller frozen study")
            data[name] = stream.read(FILE_LIMIT + 1)
            _require(len(data[name]) == info.st_size, "bundle changed during read")
    manifest = _read_json(data["manifest.json"])
    _keys(manifest, "schema_version type campaign_id study_digest evaluator_digest files", "manifest")
    _require(type(manifest["schema_version"]) is int and manifest["schema_version"] == 1
             and manifest["type"] == "PublicationBundle", "unsupported bundle version/type")
    _require(type(manifest["files"]) is dict and set(manifest["files"]) == FILES, "manifest inventory differs")
    for name in FILES:
        entry = manifest["files"][name]
        _keys(entry, "sha256 bytes", "manifest file")
        _digest(entry["sha256"], "file digest")
        _integer(entry["bytes"], "file bytes")
        _require(entry == {"sha256": hashlib.sha256(data[name]).hexdigest(), "bytes": len(data[name])}, "bundle checksum/size mismatch: " + name)
    snapshot = _read_json(data["evidence.json"])
    validate_snapshot(snapshot, require_complete=True)
    _require(all(manifest[field] == snapshot[field] for field in ("campaign_id", "study_digest", "evaluator_digest")), "manifest evidence identity mismatch")
    expected = _payloads(snapshot)
    for name in FILES:
        _require(data[name] == expected[name], "derived or canonical bundle evidence differs: " + name)
    return snapshot


def _rename_noreplace(source, destination):
    """Linux atomic directory publication without replacing a racing destination."""
    libc = ctypes.CDLL(None, use_errno=True)
    try:
        rename = libc.renameat2
    except AttributeError as exc:
        raise OSError(errno.ENOSYS, "atomic non-overwriting export requires Linux renameat2") from exc
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    rename.restype = ctypes.c_int
    if rename(-100, os.fsencode(source), -100, os.fsencode(destination), 1) != 0:
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code), str(destination))


def _sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def export_bundle(snapshot, destination):
    """Stage, fsync, verify and atomically reveal a complete, immutable-by-policy bundle."""
    validate_snapshot(snapshot, require_complete=True)
    destination = Path(destination).absolute()
    if os.path.lexists(destination):
        raise FileExistsError(errno.EEXIST, "bundle destination already exists", str(destination))
    _require(destination.parent.is_dir(), "bundle parent directory must already exist")
    payloads = _payloads(snapshot)
    _require(all(len(value) <= FILE_LIMIT for value in payloads.values())
             and sum(map(len, payloads.values())) <= BUNDLE_LIMIT, "bundle size exceeds supported limits")
    manifest = {"schema_version": 1, "type": "PublicationBundle",
                **{field: snapshot[field] for field in ("campaign_id", "study_digest", "evaluator_digest")},
                "files": {name: {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
                          for name, data in payloads.items()}}
    payloads["manifest.json"] = canonical_bytes(manifest)
    staging = Path(tempfile.mkdtemp(prefix="." + destination.name + ".staging-", dir=destination.parent))
    try:
        for name, data in payloads.items():
            with (staging / name).open("xb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        _sync_directory(staging)
        verify_bundle(staging)
        _rename_noreplace(staging, destination)
        _sync_directory(destination.parent)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return destination
