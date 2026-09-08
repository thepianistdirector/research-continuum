"""Strict immutable contracts for the trusted versioned numerical adapters."""

from dataclasses import asdict, dataclass, fields
import hashlib
import json
import math
from pathlib import Path
import re


OBJECTIVES = ("rosenbrock-2d-v1", "sphere-2d-v1", "ellipsoid-2d-v1")
POLICIES = ("uniform_random", "grid_search", "coordinate_refinement", "coordinate_fixed_step")


class StudyError(ValueError):
    """A study is outside the explicitly supported finite protocol."""


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _number(value: object, name: str) -> float:
    if type(value) not in (int, float):
        raise StudyError(f"{name} must be a finite number, not a boolean")
    try:
        result = float(value)
    except (ValueError, OverflowError) as exc:
        raise StudyError(f"{name} must be finite") from exc
    if not math.isfinite(result):
        raise StudyError(f"{name} must be finite")
    return result


def _integer(value: object, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise StudyError(f"{name} must be an integer from {minimum} to {maximum}")
    return value


def _sequence(value: object, name: str, length: int | None = None) -> tuple:
    if type(value) not in (list, tuple) or (length is not None and len(value) != length):
        raise StudyError(f"{name} must be an array" + (f" of length {length}" if length else ""))
    return tuple(value)


def _text(value: object, name: str, maximum: int = 2000) -> str:
    if type(value) is not str or not value.strip() or len(value) > maximum:
        raise StudyError(f"{name} must be nonempty text of at most {maximum} characters")
    if any(ord(char) < 32 and char not in "\n\t" for char in value):
        raise StudyError(f"{name} contains unsupported control characters")
    return value


@dataclass(frozen=True, slots=True)
class Study:
    schema_version: int
    study_id: str
    revision: str
    question: str
    hypothesis: str
    falsifier: str
    evaluator: str
    baseline: str
    candidate: str
    domain: tuple[tuple[float, float], tuple[float, float]]
    start: tuple[float, float]
    initial_step: float
    quality_threshold: float
    evaluations_per_policy: int
    development_seeds: tuple[int, ...]
    confirmation_seeds: tuple[int, ...]
    feedback: str
    comparison: str
    reproduction_tolerance: float
    max_attempts_per_trial: int
    attempt_timeout_seconds: int

    def __post_init__(self) -> None:
        _integer(self.schema_version, "schema_version", 1, 2)
        for name in ("study_id", "revision"):
            value = _text(getattr(self, name), name, 80)
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", value):
                raise StudyError(f"{name} must contain only letters, digits, dot, underscore or hyphen")
        for name in ("question", "hypothesis", "falsifier"):
            _text(getattr(self, name), name)
        constants = {
            "evaluator": "rosenbrock-2d-v1",
            "baseline": "uniform_random",
            "candidate": "coordinate_refinement",
            "feedback": "own-scalar-only-fresh-policy-per-run",
            "comparison": "descriptive-confirmation-median-best-v1",
        }
        if self.schema_version == 2:
            for name, choices in (("evaluator", OBJECTIVES), ("baseline", POLICIES), ("candidate", POLICIES)):
                value = getattr(self, name)
                if type(value) is not str or value not in choices:
                    raise StudyError(f"{name} must be a reviewed built-in: {choices}")
                del constants[name]
            if self.baseline == self.candidate:
                raise StudyError("baseline and candidate must be distinct policies")
        for name, expected in constants.items():
            if type(getattr(self, name)) is not str or getattr(self, name) != expected:
                raise StudyError(f"{name} must be {expected!r}")
        domain = tuple(
            tuple(_number(v, "domain bound") for v in _sequence(axis, "domain axis", 2))
            for axis in _sequence(self.domain, "domain", 2)
        )
        for low, high in domain:
            if not (-10.0 <= low <= 0.0 and 1.0 <= high <= 10.0):
                raise StudyError("domain must lie in [-10,10]^2 and contain controls (0,0) and (1,1)")
        object.__setattr__(self, "domain", domain)
        start = tuple(_number(v, "start coordinate") for v in _sequence(self.start, "start", 2))
        if any(not low <= value <= high for value, (low, high) in zip(start, domain)):
            raise StudyError("start must be inside the closed domain")
        object.__setattr__(self, "start", start)
        step = _number(self.initial_step, "initial_step")
        if not 1e-6 <= step <= max(high - low for low, high in domain):
            raise StudyError("initial_step must be between 1e-6 and the widest domain side")
        object.__setattr__(self, "initial_step", step)
        threshold = _number(self.quality_threshold, "quality_threshold")
        if not 0.0 <= threshold <= 1.0:
            raise StudyError("quality_threshold must be between zero and one")
        object.__setattr__(self, "quality_threshold", threshold)
        _integer(self.evaluations_per_policy, "evaluations_per_policy", 8, 4096)
        for name in ("development_seeds", "confirmation_seeds"):
            seeds = _sequence(getattr(self, name), name)
            if not 1 <= len(seeds) <= 16:
                raise StudyError(f"{name} must contain one to sixteen seeds")
            for seed in seeds:
                _integer(seed, "seed", 0, 2**32 - 1)
            if len(set(seeds)) != len(seeds):
                raise StudyError(f"{name} contains duplicate seeds")
            object.__setattr__(self, name, seeds)
        if len(self.development_seeds) != len(self.confirmation_seeds):
            raise StudyError("development and confirmation must have equal repetition counts")
        if set(self.development_seeds) & set(self.confirmation_seeds):
            raise StudyError("development and confirmation seeds must be disjoint")
        if self.total_clean_evaluations > 65536:
            raise StudyError("aggregate original and reproduction search allowance exceeds 65536 evaluations")
        tolerance = _number(self.reproduction_tolerance, "reproduction_tolerance")
        if tolerance != 1e-12:
            raise StudyError("reproduction_tolerance must remain 1e-12 in schema version 1")
        object.__setattr__(self, "reproduction_tolerance", tolerance)
        _integer(self.max_attempts_per_trial, "max_attempts_per_trial", 2, 2)
        _integer(self.attempt_timeout_seconds, "attempt_timeout_seconds", 10, 10)

    @classmethod
    def from_dict(cls, data: object) -> "Study":
        if type(data) is not dict:
            raise StudyError("study must be a JSON object")
        expected = {field.name for field in fields(cls)}
        if set(data) != expected:
            missing = sorted(expected - set(data))
            unknown = sorted(set(data) - expected, key=str)
            raise StudyError(f"study fields differ: missing={missing}, unknown={unknown}")
        return cls(**data)

    def to_dict(self) -> dict:
        # Round-tripping detaches nested containers and represents tuples as JSON arrays.
        return json.loads(canonical_json(asdict(self)))

    @property
    def digest(self) -> str:
        return hashlib.sha256(canonical_json(self.to_dict()).encode("ascii")).hexdigest()

    @property
    def total_clean_evaluations(self) -> int:
        return 4 * self.evaluations_per_policy * (len(self.development_seeds) + len(self.confirmation_seeds))

    @property
    def total_reserved_evaluations(self) -> int:
        return self.total_clean_evaluations * self.max_attempts_per_trial


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise StudyError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise StudyError(f"non-finite JSON constant: {value}")


def load_study(path: str | Path) -> Study:
    with Path(path).open("rb") as handle:
        raw = handle.read(65537)
    if len(raw) > 65536:
        raise StudyError("study JSON exceeds 65536 bytes")
    try:
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object, parse_constant=_reject_constant)
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise StudyError("study must be valid bounded UTF-8 JSON") from exc
    return Study.from_dict(data)


DEFAULT_STUDY = {
    "schema_version": 1,
    "study_id": "rosenbrock-coordinate-v-random",
    "revision": "1",
    "question": "On this bounded Rosenbrock fixture, does fixed coordinate refinement obtain a lower confirmation median best objective than seeded uniform random search at equal evaluation allowance?",
    "hypothesis": "Fixed coordinate refinement will obtain a lower median best objective in the reserved confirmation runs.",
    "falsifier": "The candidate confirmation median is greater than or equal to the baseline median; invalid or missing runs or unequal charged costs make the comparison inconclusive.",
    "evaluator": "rosenbrock-2d-v1",
    "baseline": "uniform_random",
    "candidate": "coordinate_refinement",
    "domain": [[-2.0, 2.0], [-1.0, 3.0]],
    "start": [-1.2, 1.0],
    "initial_step": 0.5,
    "quality_threshold": 0.01,
    "evaluations_per_policy": 128,
    "development_seeds": [11, 22, 33],
    "confirmation_seeds": [101, 202, 303],
    "feedback": "own-scalar-only-fresh-policy-per-run",
    "comparison": "descriptive-confirmation-median-best-v1",
    "reproduction_tolerance": 1e-12,
    "max_attempts_per_trial": 2,
    "attempt_timeout_seconds": 10,
}


def builtin_study(evaluator="rosenbrock-2d-v1", baseline="uniform_random", candidate="coordinate_refinement") -> Study:
    """New schema-2 draft; no accepted schema-1 study is silently upgraded."""
    data = dict(DEFAULT_STUDY, schema_version=2, evaluator=evaluator, baseline=baseline, candidate=candidate,
                study_id=f"{evaluator}-{candidate}-v-{baseline}",
                question=f"On {evaluator}, does {candidate} obtain a lower confirmation median best objective than {baseline} at equal evaluation allowance?",
                hypothesis=f"{candidate} will obtain a lower confirmation median best objective than {baseline}.")
    if evaluator != "rosenbrock-2d-v1":
        data.update(domain=[[-2.0, 2.0], [-2.0, 2.0]], start=[-1.2, 1.0])
    return Study.from_dict(data)
