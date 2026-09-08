"""Original reviewed numerical built-ins; logical interfaces, not a sandbox."""

from dataclasses import dataclass
import hashlib
import math
from pathlib import Path
import random

from . import study as study_module
from .study import Study


@dataclass(frozen=True, slots=True)
class Point:
    x: float
    y: float

    def to_list(self) -> list[float]:
        return [self.x, self.y]


class EvaluatorMismatch(RuntimeError):
    """Accepted evaluator identity differs from this execution."""


def objective(point: Point) -> float:
    """Rosenbrock's dimensionless sum of nonnegative square terms."""
    return 100.0 * (point.y - point.x * point.x) ** 2 + (1.0 - point.x) ** 2


_ORIGINAL_OBJECTIVE = objective
_ORIGINAL_CODE = objective.__code__


def _source_identity() -> str:
    digest = hashlib.sha256()
    for name, path in (("numerical.py", Path(__file__)), ("study.py", Path(study_module.__file__))):
        digest.update(name.encode("ascii") + b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


_IMPORTED_SOURCE_IDENTITY = _source_identity()


def evaluator_identity() -> str:
    # Bind acceptance to this imported release, not to subsequently edited disk bytes.
    if _source_identity() != _IMPORTED_SOURCE_IDENTITY:
        raise EvaluatorMismatch("source changed since import; restart using one unchanged release")
    return _IMPORTED_SOURCE_IDENTITY


def _finite_number(value: object, name: str) -> float:
    if type(value) not in (int, float):
        raise ValueError(f"{name} must be a finite number, not a boolean")
    try:
        result = float(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{name} must be finite") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _valid_point(point: object, domain: tuple) -> Point:
    if type(point) is not Point:
        raise ValueError("proposal must be a typed Point with exactly two coordinates")
    x = _finite_number(point.x, "x")
    y = _finite_number(point.y, "y")
    if any(not low <= value <= high for value, (low, high) in zip((x, y), domain)):
        raise ValueError("proposal is outside the accepted closed domain")
    return Point(x, y)


class Evaluator:
    """Only validated proposals cross the reviewed objective boundary."""

    __slots__ = ("_domain", "_identity", "_objective_calls")

    def __init__(self, study: Study, expected_identity: str | None = None):
        if type(study) is not Study:
            raise ValueError("evaluator requires a validated Study")
        self._domain = study.domain
        self._identity = evaluator_identity() if expected_identity is None else expected_identity
        self._objective_calls = 0
        self.verify_identity()

    @property
    def objective_calls(self) -> int:
        return self._objective_calls

    def verify_identity(self) -> None:
        if (objective is not _ORIGINAL_OBJECTIVE or objective.__code__ is not _ORIGINAL_CODE
                or evaluator_identity() != self._identity):
            raise EvaluatorMismatch("frozen evaluator identity changed; use the accepted original release")

    def evaluate(self, point: Point) -> float:
        self.verify_identity()
        accepted = _valid_point(point, self._domain)
        self._objective_calls += 1
        result = _finite_number(objective(accepted), "objective")
        if result < 0.0:
            raise ValueError("objective violated its nonnegative invariant")
        return result


class _Policy:
    __slots__ = ("_domain", "_limit", "_count", "_pending")

    def __init__(self, domain: tuple, limit: int):
        self._domain = domain
        self._limit = limit
        self._count = 0
        self._pending = None

    def propose(self) -> Point:
        if self._pending is not None:
            raise RuntimeError("observe the pending proposal before requesting another")
        if self._count >= self._limit:
            raise StopIteration("policy's finite observation allowance exhausted")
        self._pending = self._next()
        return self._pending

    def observe(self, point: Point, value: float | None) -> None:
        accepted = _valid_point(point, self._domain)
        if self._pending is None or accepted != self._pending:
            raise RuntimeError("feedback must name the exact pending proposal")
        if value is not None:
            value = _finite_number(value, "objective feedback")
            if value < 0.0:
                raise ValueError("objective feedback must be nonnegative")
        self._accept(accepted, value)
        self._count += 1
        self._pending = None

    def _next(self) -> Point:
        raise NotImplementedError

    def _accept(self, point: Point, value: float | None) -> None:
        pass


class UniformRandom(_Policy):
    __slots__ = ("_random",)

    def __init__(self, domain: tuple, limit: int, seed: int):
        super().__init__(domain, limit)
        self._random = random.Random(seed)

    def _next(self) -> Point:
        values = [low + (high - low) * self._random.random() for low, high in self._domain]
        return Point(*values)


class CoordinateRefinement(_Policy):
    __slots__ = ("_incumbent", "_best", "_step", "_direction", "_sweep_improved")

    def __init__(self, domain: tuple, limit: int, start: tuple, step: float):
        super().__init__(domain, limit)
        self._incumbent = Point(*start)
        self._best = math.inf
        self._step = step
        self._direction = 0
        self._sweep_improved = False

    def _next(self) -> Point:
        if self._count == 0:
            return self._incumbent
        axis, sign = ((0, 1), (0, -1), (1, 1), (1, -1))[self._direction]
        values = self._incumbent.to_list()
        low, high = self._domain[axis]
        values[axis] = min(high, max(low, values[axis] + sign * self._step))
        return Point(*values)

    def _accept(self, point: Point, value: float | None) -> None:
        if value is not None and value < self._best:
            self._incumbent = point
            self._best = value
            if self._count > 0:
                self._sweep_improved = True
        if self._count > 0:
            self._direction += 1
            if self._direction == 4:
                if not self._sweep_improved:
                    self._step *= 0.5
                self._direction = 0
                self._sweep_improved = False


def make_policy(name: str, study: Study, seed: int) -> _Policy:
    if type(study) is not Study:
        raise ValueError("policy requires a validated Study")
    if type(seed) is not int or not 0 <= seed <= 2**32 - 1:
        raise ValueError("seed must be an integer from zero to 2^32-1")
    if name == "uniform_random":
        return UniformRandom(study.domain, study.evaluations_per_policy, seed)
    if name == "coordinate_refinement":
        return CoordinateRefinement(study.domain, study.evaluations_per_policy, study.start, study.initial_step)
    raise ValueError("only uniform_random and coordinate_refinement policies are supported")


def controls(study: Study) -> list[dict]:
    evaluator = Evaluator(study)
    records = []
    for name, point, expected in (
        ("known_minimum", Point(1.0, 1.0), 0.0),
        ("known_nonzero", Point(0.0, 0.0), 1.0),
    ):
        before = evaluator.objective_calls
        observed = evaluator.evaluate(point)
        records.append({"name": name, "expected": expected, "observed": observed,
                        "passed": observed == expected, "objectiveCalls": evaluator.objective_calls - before})
    for name, invalid in (
        ("reject_nan", Point(math.nan, 1.0)),
        ("reject_infinity", Point(1.0, math.inf)),
        ("reject_boolean", Point(True, 1.0)),
        ("reject_shape", (1.0, 1.0)),
        ("reject_out_of_domain", Point(study.domain[0][1] + 1.0, 1.0)),
    ):
        before = evaluator.objective_calls
        try:
            evaluator.evaluate(invalid)
        except ValueError:
            observed = "rejected"
        else:
            observed = "accepted"
        records.append({"name": name, "expected": "rejected", "observed": observed,
                        "passed": observed == "rejected", "objectiveCalls": evaluator.objective_calls - before})
    try:
        Evaluator(study, expected_identity="0" * 64)
    except EvaluatorMismatch:
        observed = "rejected"
    else:
        observed = "accepted"
    records.append({"name": "reject_evaluator_mutation", "expected": "rejected", "observed": observed,
                    "passed": observed == "rejected", "objectiveCalls": 0})
    return records
