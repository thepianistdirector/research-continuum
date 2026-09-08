"""Falsifiers for the frozen numerical contract and proposal boundary."""

import copy
from dataclasses import FrozenInstanceError
import json
import math
import random
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from continuum import numerical
from continuum.numerical import Evaluator, EvaluatorMismatch, Point, controls, evaluator_identity, make_policy
from continuum.study import DEFAULT_STUDY, Study, StudyError, load_study


PROJECT = Path(__file__).resolve().parents[1]


class StudyTests(unittest.TestCase):
    def setUp(self):
        self.data = copy.deepcopy(DEFAULT_STUDY)

    def test_example_is_exact_default_and_roundtrips(self):
        study = load_study(PROJECT / "examples/rosenbrock-study.json")
        self.assertEqual(study.to_dict(), DEFAULT_STUDY)
        self.assertEqual(Study.from_dict(study.to_dict()), study)
        self.assertEqual(study.total_clean_evaluations, 3072)
        self.assertEqual(study.total_reserved_evaluations, 6144)

    def test_immutable_and_detached_from_input_and_output(self):
        study = Study.from_dict(self.data)
        digest = study.digest
        self.data["domain"][0][0] = -8.0
        detached = study.to_dict()
        detached["confirmation_seeds"].append(44)
        with self.assertRaises(FrozenInstanceError):
            study.quality_threshold = 1.0
        with self.assertRaises(TypeError):
            study.domain[0][0] = -8.0
        self.assertEqual(study.digest, digest)
        self.assertNotEqual(Study.from_dict(self.data).digest, digest)

    def test_oversized_integer_parser_failure_is_normalized(self):
        cache = PROJECT / ".cache" / "tests"
        cache.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache) as temporary:
            path = Path(temporary) / "large-integer.json"
            path.write_text('{"schema_version":' + '1' * 5000 + '}')
            with self.assertRaises(StudyError):
                load_study(path)

    def test_invalid_contracts_fail_closed(self):
        changes = [
            {"schema_version": True}, {"schema_version": 2}, {"revision": "../escape"},
            {"question": ""}, {"evaluations_per_policy": True}, {"evaluations_per_policy": 7},
            {"evaluations_per_policy": 4097}, {"max_attempts_per_trial": 3},
            {"attempt_timeout_seconds": 100}, {"domain": [[-2, 2], [1, 3]]},
            {"domain": [[-11, 2], [-1, 3]]}, {"domain": [[-2, True], [-1, 3]]},
            {"domain": [[-2, math.inf], [-1, 3]]}, {"start": [3, 1]},
            {"start": [1, math.nan]}, {"start": [1, 10**500]}, {"initial_step": 0},
            {"quality_threshold": -0.01}, {"quality_threshold": math.nan},
            {"development_seeds": [11, 11, 33]}, {"confirmation_seeds": [11, 202, 303]},
            {"development_seeds": [True, 22, 33]}, {"development_seeds": [11]},
            {"development_seeds": []}, {"candidate": "arbitrary_script"},
            {"feedback": "all-confirmation-results"}, {"reproduction_tolerance": 0.01},
            {"extra": "ignored?"},
        ]
        for change in changes:
            with self.subTest(change=change):
                with self.assertRaises(StudyError):
                    Study.from_dict(self.data | change)
        missing = self.data.copy()
        del missing["falsifier"]
        with self.assertRaises(StudyError):
            Study.from_dict(missing)
        for invalid in (None, [], "study", True):
            with self.subTest(invalid=invalid), self.assertRaises(StudyError):
                Study.from_dict(invalid)

    def test_aggregate_limit_and_new_supported_revision(self):
        maximum = self.data | {"revision": "2", "evaluations_per_policy": 4096,
                               "development_seeds": [1, 2], "confirmation_seeds": [3, 4]}
        self.assertEqual(Study.from_dict(maximum).total_clean_evaluations, 65536)
        with self.assertRaises(StudyError):
            Study.from_dict(maximum | {"development_seeds": [1, 2, 3], "confirmation_seeds": [4, 5, 6]})

    def test_json_rejects_duplicates_nonfinite_and_oversize(self):
        cache = PROJECT / ".cache" / "tests"
        cache.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache) as temporary:
            path = Path(temporary) / "study.json"
            for raw in ('{"schema_version":1,"schema_version":1}', '{"x":NaN}',
                        '{"x":Infinity}', " " * 65537, "[" * 2000):
                path.write_text(raw, encoding="utf-8")
                with self.subTest(raw=raw[:70]), self.assertRaises(StudyError):
                    load_study(path)
            path.write_bytes(b"\xff")
            with self.assertRaises(StudyError):
                load_study(path)


class NumericalTests(unittest.TestCase):
    def setUp(self):
        self.study = Study.from_dict(copy.deepcopy(DEFAULT_STUDY))

    def test_known_values_and_independent_polynomial_form(self):
        evaluator = Evaluator(self.study)
        for point, expected in ((Point(1, 1), 0), (Point(0, 0), 1),
                                (Point(-1, 1), 4), (Point(2, 3), 101)):
            self.assertEqual(evaluator.evaluate(point), expected)
        for x in (-2.0, -0.5, 0.0, 0.25, 1.5, 2.0):
            for y in (-1.0, 0.0, 0.25, 1.0, 3.0):
                expanded = 100 * y**2 - 200 * y * x**2 + 100 * x**4 + x**2 - 2 * x + 1
                self.assertAlmostEqual(evaluator.evaluate(Point(x, y)), expanded, places=10)

    def test_bad_candidate_and_invalid_numbers_do_not_call_objective(self):
        evaluator = Evaluator(self.study)
        for invalid in (Point(20, 20), Point(True, 1), Point(math.nan, 1), Point(1, math.inf),
                        Point(1, -math.inf), Point(1, "1"), Point(10**500, 1), [1, 1], (1, 1), None):
            with self.subTest(invalid=repr(invalid)), self.assertRaises(ValueError):
                evaluator.evaluate(invalid)
        self.assertEqual(evaluator.objective_calls, 0)

    def test_controls_have_explicit_real_call_accounting(self):
        records = controls(self.study)
        self.assertEqual(len(records), 8)
        self.assertTrue(all(row["passed"] for row in records))
        self.assertEqual(sum(row["objectiveCalls"] for row in records), 2)
        json.dumps(records, allow_nan=False)

    def test_objective_replacement_and_code_mutation_detected(self):
        evaluator = Evaluator(self.study)
        with patch.object(numerical, "objective", lambda point: 0.0):
            with self.assertRaises(EvaluatorMismatch):
                evaluator.evaluate(Point(0, 0))
        original_code = numerical.objective.__code__
        try:
            numerical.objective.__code__ = (lambda point: 0.0).__code__
            with self.assertRaises(EvaluatorMismatch):
                evaluator.evaluate(Point(0, 0))
        finally:
            numerical.objective.__code__ = original_code
        self.assertEqual(evaluator.objective_calls, 0)

    def test_mutation_before_initial_identity_capture_is_rejected(self):
        cache = PROJECT / ".cache" / "tests"
        cache.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache) as temporary:
            altered = Path(temporary) / "numerical.py"
            altered.write_text(Path(numerical.__file__).read_text().replace("return 100.0 *", "return 200.0 *"))
            with patch.object(numerical, "__file__", str(altered)):
                with self.assertRaises(EvaluatorMismatch):
                    evaluator_identity()
                with self.assertRaises(EvaluatorMismatch):
                    Evaluator(self.study)

    def test_random_trace_matches_independent_affine_draws(self):
        reference = random.Random(101)
        policy = make_policy("uniform_random", self.study, 101)
        for _ in range(self.study.evaluations_per_policy):
            expected = Point(-2.0 + 4.0 * reference.random(), -1.0 + 4.0 * reference.random())
            point = policy.propose()
            self.assertEqual(point, expected)
            policy.observe(point, 1.0)

    def test_source_mutation_and_wrong_expected_identity_detected(self):
        expected = evaluator_identity()
        evaluator = Evaluator(self.study, expected_identity=expected)
        cache = PROJECT / ".cache" / "tests"
        cache.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache) as temporary:
            altered = Path(temporary) / "numerical.py"
            altered.write_bytes(Path(numerical.__file__).read_bytes() + b"\n# deliberate mutation\n")
            with patch.object(numerical, "__file__", str(altered)):
                with self.assertRaises(EvaluatorMismatch):
                    evaluator.evaluate(Point(1, 1))
                with self.assertRaises(EvaluatorMismatch):
                    Evaluator(self.study, expected_identity=expected)
        with self.assertRaises(EvaluatorMismatch):
            Evaluator(self.study, expected_identity="0" * 64)

    def trace(self, name, seed):
        evaluator = Evaluator(self.study)
        policy = make_policy(name, self.study, seed)
        observations = []
        for _ in range(self.study.evaluations_per_policy):
            point = policy.propose()
            value = evaluator.evaluate(point)
            policy.observe(point, value)
            observations.append((point, value))
        with self.assertRaises(StopIteration):
            policy.propose()
        self.assertEqual(evaluator.objective_calls, self.study.evaluations_per_policy)
        return observations

    def test_equal_finite_allowance_and_deterministic_replay(self):
        baseline = self.trace(self.study.baseline, 11)
        candidate = self.trace(self.study.candidate, 11)
        self.assertEqual(len(baseline), len(candidate))
        self.assertEqual(baseline, self.trace(self.study.baseline, 11))
        self.assertNotEqual(baseline, self.trace(self.study.baseline, 22))
        self.assertEqual(candidate, self.trace(self.study.candidate, 303))

    def test_policy_rejects_wrong_feedback_and_missing_feedback(self):
        for name in (self.study.baseline, self.study.candidate):
            policy = make_policy(name, self.study, 11)
            with self.assertRaises(RuntimeError):
                policy.observe(Point(0, 0), 1)
            point = policy.propose()
            with self.assertRaises(RuntimeError):
                policy.propose()
            with self.assertRaises(RuntimeError):
                policy.observe(Point(1, 1), 0)
            for invalid in (True, math.inf, math.nan, -1.0):
                with self.subTest(name=name, invalid=invalid), self.assertRaises(ValueError):
                    policy.observe(point, invalid)
            policy.observe(point, None)
            with self.assertRaises(RuntimeError):
                policy.observe(point, 1.0)
            policy.propose()

    def test_coordinate_sweep_uses_immediate_improvement_and_halves_only_after_failed_sweep(self):
        data = copy.deepcopy(DEFAULT_STUDY)
        data["start"] = [0, 0]
        policy = make_policy("coordinate_refinement", Study.from_dict(data), 11)
        expected = [(Point(0, 0), 10), (Point(0.5, 0), 9), (Point(0, 0), 10),
                    (Point(0.5, 0.5), 8), (Point(0.5, 0), 9),
                    (Point(1, 0.5), 8), (Point(0, 0.5), 8),
                    (Point(0.5, 1), 8), (Point(0.5, 0), 8)]
        for point, feedback in expected:
            self.assertEqual(policy.propose(), point)
            policy.observe(point, feedback)
        self.assertEqual(policy.propose(), Point(0.75, 0.5))

    def test_clipped_duplicate_and_failed_initial_observation_still_consume_slots(self):
        data = copy.deepcopy(DEFAULT_STUDY)
        data.update(start=[2, 3], evaluations_per_policy=8)
        policy = make_policy("coordinate_refinement", Study.from_dict(data), 11)
        points = []
        for _ in range(8):
            point = policy.propose()
            points.append(point)
            policy.observe(point, None)
        self.assertEqual(points[0], points[1])
        with self.assertRaises(StopIteration):
            policy.propose()


if __name__ == "__main__":
    unittest.main()
