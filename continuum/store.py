"""Single-writer, append-only SQLite campaign coordinator for trusted built-ins."""
from __future__ import annotations

from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import sqlite3
import time
from typing import Iterator
import uuid

from . import __version__
from .study import Study
from .numerical import Evaluator, Point, controls, evaluator_identity, make_policy


class CampaignError(ValueError):
    """A campaign cannot safely perform the requested transition."""


class CampaignBusy(CampaignError):
    """Another live local coordinator holds this campaign's OS lock."""


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _runtime_source_identity() -> str:
    digest = hashlib.sha256()
    for path in sorted(Path(__file__).parent.glob("*.py")):
        digest.update(path.name.encode() + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


_IMPORTED_RUNTIME_IDENTITY = _runtime_source_identity()


def runtime_identity() -> str:
    if _runtime_source_identity() != _IMPORTED_RUNTIME_IDENTITY:
        raise CampaignError("Runtime source changed since import; restart using one unchanged release")
    return _IMPORTED_RUNTIME_IDENTITY


def environment() -> dict:
    return {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "system": platform.system(),
        "machine": platform.machine(),
        "sqlite": sqlite3.sqlite_version,
        "package_version": __version__,
        "runtime_digest": runtime_identity(),
    }


def trial_specs(study: Study) -> list[dict]:
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
    return originals + [dict(t, id="reproduction-" + t["id"], phase="reproduction",
                             reproduces=t["id"], pool="reproduction:" + t["policy"])
                        for t in originals]


def allocations(study: Study) -> list[dict]:
    totals: dict[str, int] = defaultdict(int)
    for trial in trial_specs(study):
        totals[trial["pool"]] += trial["allocation"]
    return [{"pool": pool, "capacity": capacity} for pool, capacity in totals.items()]


def _path(value: str | Path) -> Path:
    path = Path(value).absolute()
    if path.is_symlink():
        raise CampaignError("Campaign database must not be a symbolic link")
    return path.resolve()


@contextmanager
def _writer_lock(path: Path) -> Iterator[None]:
    """Local liveness authority. Never unlink a lock file: that permits split locks."""
    lock_path = path.with_name(path.name + ".lock")
    descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise CampaignBusy("Another coordinator is active for this campaign") from exc
        yield
    finally:
        os.close(descriptor)


def _connect(path: Path, *, readonly: bool = False) -> sqlite3.Connection:
    if not path.is_file():
        raise CampaignError("Campaign database does not exist; use init first")
    uri = path.as_uri() + ("?mode=ro" if readonly else "?mode=rw")
    db = sqlite3.connect(uri, uri=True, timeout=5, isolation_level=None)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    if not readonly:
        db.execute("PRAGMA synchronous=FULL")
    return db


@contextmanager
def _transaction(db: sqlite3.Connection) -> Iterator[None]:
    db.execute("BEGIN IMMEDIATE")
    try:
        yield
        db.execute("COMMIT")
    except BaseException:
        if db.in_transaction:
            db.execute("ROLLBACK")
        raise


def _event(db: sqlite3.Connection, kind: str, attempt: str | None, payload: dict) -> None:
    db.execute("INSERT INTO events(kind,attempt_id,payload,at) VALUES(?,?,?,?)",
               (kind, attempt, canonical(payload), now()))


_SCHEMA = """
CREATE TABLE meta(id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL);
CREATE TABLE trials(id TEXT PRIMARY KEY, spec TEXT NOT NULL);
CREATE TABLE attempts(
 id TEXT PRIMARY KEY, trial_id TEXT NOT NULL REFERENCES trials(id),
 number INTEGER NOT NULL CHECK(number BETWEEN 1 AND 2),
 retry_of TEXT REFERENCES attempts(id), charged_evaluations INTEGER NOT NULL CHECK(charged_evaluations>0),
 started_at TEXT NOT NULL, UNIQUE(trial_id,number));
CREATE TABLE observations(
 attempt_id TEXT NOT NULL REFERENCES attempts(id), observation_index INTEGER NOT NULL CHECK(observation_index>=0),
 point TEXT NOT NULL, value REAL NOT NULL CHECK(value>=0), PRIMARY KEY(attempt_id,observation_index));
CREATE TABLE staged(attempt_id TEXT PRIMARY KEY REFERENCES attempts(id), payload TEXT NOT NULL);
CREATE TABLE terminals(attempt_id TEXT PRIMARY KEY REFERENCES attempts(id), payload TEXT NOT NULL);
CREATE TABLE events(sequence INTEGER PRIMARY KEY AUTOINCREMENT,
 kind TEXT NOT NULL CHECK(kind IN ('CREATED','ADMITTED','OBSERVED','STAGED','TERMINATED')),
 attempt_id TEXT REFERENCES attempts(id), payload TEXT NOT NULL, at TEXT NOT NULL);
CREATE TRIGGER observations_no_terminal BEFORE INSERT ON observations
 WHEN EXISTS(SELECT 1 FROM terminals WHERE attempt_id=NEW.attempt_id)
 BEGIN SELECT RAISE(ABORT,'terminal attempts cannot receive observations'); END;
CREATE TRIGGER observations_no_staging BEFORE INSERT ON observations
 WHEN EXISTS(SELECT 1 FROM staged WHERE attempt_id=NEW.attempt_id)
 BEGIN SELECT RAISE(ABORT,'staged attempts cannot receive observations'); END;
"""


def create(study: Study, database: str | Path, *, expected_evaluator: str | None = None,
           reproduction_source: dict | None = None, campaign_source: dict | None = None) -> dict:
    """Freeze a new campaign; refuse replacing any existing database, even a partial one."""
    path = _path(database)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _writer_lock(path):
        if path.exists():
            raise CampaignError("Database already exists; resume it or choose a new path")
        expected = expected_evaluator or evaluator_identity()
        # Validate the requested source identity before creating an accepted campaign.
        Evaluator(study, expected_identity=expected)
        control_results = controls(study)
        if not all(c.get("passed") is True for c in control_results):
            raise CampaignError("Evaluator controls failed; no campaign was admitted")
        meta = {
            "schema_version": 1, "campaign_id": uuid.uuid4().hex,
            "study": study.to_dict(), "study_digest": study.digest,
            "evaluator_digest": expected, "environment": environment(), "created_at": now(),
            "source_records": [{"id": "source-" + study.evaluator, "type": "SourceRecord",
                "schema_version": 1, "description": "Original implementation of public known-answer " + study.evaluator + " and reviewed search policies",
                "license": "AGPL-3.0-only", "locator": "docs/decisions/001-numerical-study.md" if study.schema_version == 1 else "docs/decisions/003-numerical-workbench.md"}],
            "trial_specs": trial_specs(study), "allocations": allocations(study),
            "controls": control_results,
        }
        if campaign_source is not None:
            if (type(campaign_source) is not dict or set(campaign_source) != {"id", "digest"}
                    or type(campaign_source["id"]) is not str or not campaign_source["id"]
                    or type(campaign_source["digest"]) is not str
                    or len(campaign_source["digest"]) != 64
                    or any(c not in "0123456789abcdef" for c in campaign_source["digest"])):
                raise CampaignError("Invalid workbench campaign binding")
            meta["source_records"].append({"id": "source-workbench-" + campaign_source["id"],
                "type": "SourceRecord", "schema_version": 1,
                "description": "Complete workbench inventory accepted before this study was admitted",
                "license": "AGPL-3.0-only", "locator": "sha256:" + campaign_source["digest"]})
        if reproduction_source is not None:
            if (set(reproduction_source) != {"campaign_id", "evidence_digest"}
                    or not isinstance(reproduction_source["campaign_id"], str)
                    or not isinstance(reproduction_source["evidence_digest"], str)):
                raise CampaignError("Invalid reproduction source binding")
            meta["source_records"].append({
                "id": "source-reproduction-" + reproduction_source["campaign_id"],
                "type": "SourceRecord", "schema_version": 1,
                "description": "Source campaign accepted before this fresh reproduction execution",
                "license": "AGPL-3.0-only", "locator": "sha256:" + reproduction_source["evidence_digest"],
            })
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_CLOEXEC, 0o600)
        os.close(descriptor)
        db = _connect(path)
        try:
            db.executescript(_SCHEMA)
            for table in ("meta", "trials", "attempts", "observations", "staged", "terminals", "events"):
                for operation in ("UPDATE", "DELETE"):
                    db.execute(f"CREATE TRIGGER immutable_{table}_{operation.lower()} BEFORE {operation} ON {table} "
                               "BEGIN SELECT RAISE(ABORT,'accepted records are append-only'); END")
            with _transaction(db):
                db.execute("INSERT INTO meta VALUES(1,?)", (canonical(meta),))
                db.executemany("INSERT INTO trials VALUES(?,?)", [(t["id"], canonical(t)) for t in meta["trial_specs"]])
                _event(db, "CREATED", None, {"study_digest": study.digest, "evaluator_digest": expected})
            # Persist the new directory entry as well as SQLite's committed file.
            parent_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(parent_fd)
            finally:
                os.close(parent_fd)
            return _snapshot(db)
        finally:
            db.close()


def _snapshot(db: sqlite3.Connection) -> dict:
    row = db.execute("SELECT payload FROM meta WHERE id=1").fetchone()
    if row is None:
        raise CampaignError("Campaign initialization is incomplete; preserve it and choose a new database")
    result = json.loads(row["payload"])
    stored_specs = [json.loads(r["spec"]) for r in db.execute("SELECT spec FROM trials ORDER BY rowid")]
    if stored_specs != result.get("trial_specs"):
        raise CampaignError("Stored trial schedule differs from the accepted contract")
    attempts = []
    for row in db.execute("SELECT * FROM attempts ORDER BY rowid"):
        attempt = dict(row)
        attempt["observations"] = [
            {"index": r["observation_index"], "point": json.loads(r["point"]), "value": r["value"]}
            for r in db.execute("SELECT * FROM observations WHERE attempt_id=? ORDER BY observation_index", (row["id"],))
        ]
        for table, key in (("staged", "staged"), ("terminals", "terminal")):
            record = db.execute(f"SELECT payload FROM {table} WHERE attempt_id=?", (row["id"],)).fetchone()
            attempt[key] = json.loads(record["payload"]) if record else None
        attempts.append(attempt)
    result["attempts"] = attempts
    result["events"] = [dict(r, payload=json.loads(r["payload"])) for r in db.execute("SELECT * FROM events ORDER BY sequence")]
    return result


def inspect(database: str | Path, *, validate: bool = True) -> dict:
    """Read one committed snapshot. Inspection never starts or reconciles work."""
    db = _connect(_path(database), readonly=True)
    try:
        db.execute("BEGIN")
        result = _snapshot(db)
        db.execute("COMMIT")
    except sqlite3.DatabaseError as exc:
        raise CampaignError("Database is incomplete or corrupt; preserve it for review") from exc
    finally:
        db.close()
    if validate:
        from .evidence import validate_snapshot
        validate_snapshot(result)
    return result


def _terminal(db: sqlite3.Connection, attempt_id: str, record: dict) -> None:
    # The unique key rejects duplicate publication; never silently replace a result.
    with _transaction(db):
        db.execute("INSERT INTO terminals VALUES(?,?)", (attempt_id, canonical(record)))
        _event(db, "TERMINATED", attempt_id, {"status": record["status"], "reason": record["reason"]})


def _result(db: sqlite3.Connection, attempt_id: str, status: str, reason: str,
            started_wall: float | None = None, started_cpu: float | None = None) -> dict:
    row = db.execute("SELECT count(*) n,min(value) best FROM observations WHERE attempt_id=?", (attempt_id,)).fetchone()
    return {
        "status": status, "reason": reason, "observed_evaluations": row["n"], "best": row["best"],
        "elapsed_seconds": max(0.0, time.monotonic() - started_wall) if started_wall is not None else None,
        "cpu_seconds": max(0.0, time.process_time() - started_cpu) if started_cpu is not None else None,
        "ended_at": now(),
    }


def _admit(db: sqlite3.Connection, trial: dict, study: Study) -> str:
    with _transaction(db):
        prior = db.execute("SELECT * FROM attempts WHERE trial_id=? ORDER BY number", (trial["id"],)).fetchall()
        if len(prior) >= study.max_attempts_per_trial:
            raise CampaignError("Trial attempt reserve exhausted")
        for attempt in prior:
            terminal = db.execute("SELECT payload FROM terminals WHERE attempt_id=?", (attempt["id"],)).fetchone()
            if terminal is None:
                raise CampaignError("Unreconciled attempt prevents admission")
            if json.loads(terminal["payload"])["status"] == "COMPLETED":
                raise CampaignError("Completed trial cannot receive another attempt")
        if sum(a["charged_evaluations"] for a in prior) + study.evaluations_per_policy > trial["allocation"]:
            raise CampaignError("Trial allocation exhausted")
        attempt_id = uuid.uuid4().hex
        number = len(prior) + 1
        db.execute("INSERT INTO attempts VALUES(?,?,?,?,?,?)", (
            attempt_id, trial["id"], number, prior[-1]["id"] if prior else None,
            study.evaluations_per_policy, now()))
        _event(db, "ADMITTED", attempt_id, {"trial_id": trial["id"], "number": number,
                                           "charged_evaluations": study.evaluations_per_policy})
        return attempt_id


def _observe(db: sqlite3.Connection, attempt_id: str, index: int, point: Point, value: float,
             study: Study) -> None:
    with _transaction(db):
        count = db.execute("SELECT count(*) FROM observations WHERE attempt_id=?", (attempt_id,)).fetchone()[0]
        if index != count or count >= study.evaluations_per_policy:
            raise CampaignError("Observation order or allowance violated")
        db.execute("INSERT INTO observations VALUES(?,?,?,?)", (attempt_id, index, canonical(point.to_list()), value))
        _event(db, "OBSERVED", attempt_id, {"index": index})


def _fault(point: str, requested: str | None) -> None:
    """Internal fault-injection seam used by real subprocess recovery tests."""
    if requested == point:
        os.kill(os.getpid(), signal.SIGKILL)


def run(database: str | Path, *, max_trials: int | None = None, _crash_at: str | None = None) -> dict:
    """Reconcile process death and execute finite built-in work under the campaign lock.

    max_trials pauses after that many logical trials without changing frozen budgets.
    _crash_at is a test seam, never accepted from a study or an exported bundle.
    """
    if max_trials is not None and (type(max_trials) is not int or max_trials < 1):
        raise CampaignError("Pause count must be a positive integer")
    if _crash_at not in (None, "after-admission", "after-execution", "after-staging"):
        raise CampaignError("Unknown internal crash point")
    path = _path(database)
    if not path.is_file():
        raise CampaignError("Campaign database does not exist; use init first")
    with _writer_lock(path):
        db = _connect(path)
        try:
            from .evidence import validate_snapshot
            snapshot = _snapshot(db)
            validate_snapshot(snapshot)
            study = Study.from_dict(snapshot["study"])
            if study.digest != snapshot["study_digest"]:
                raise CampaignError("Accepted study identity changed")
            evaluator = Evaluator(study, expected_identity=snapshot["evaluator_digest"])
            if environment() != snapshot["environment"]:
                raise CampaignError("Runtime identity changed; resume using the original release and environment")
            # Only a process holding flock can reconcile. A live owner cannot be presumed dead.
            for attempt in snapshot["attempts"]:
                if attempt["terminal"] is None:
                    if attempt["staged"] is not None:
                        _terminal(db, attempt["id"], attempt["staged"])
                    else:
                        _terminal(db, attempt["id"], _result(db, attempt["id"], "FAILED",
                            "Coordinator interrupted before validated result staging; full allowance retained"))
            processed = 0
            for trial in snapshot["trial_specs"]:
                prior = db.execute("SELECT a.id,t.payload FROM attempts a LEFT JOIN terminals t ON t.attempt_id=a.id "
                                   "WHERE a.trial_id=? ORDER BY a.number", (trial["id"],)).fetchall()
                if any(r["payload"] and json.loads(r["payload"])["status"] == "COMPLETED" for r in prior):
                    continue
                remaining = study.max_attempts_per_trial - len(prior)
                if remaining <= 0:
                    continue
                for _ in range(remaining):
                    attempt_id = _admit(db, trial, study)
                    start_wall, start_cpu = time.monotonic(), time.process_time()
                    _fault("after-admission", _crash_at)
                    try:
                        policy = make_policy(trial["policy"], study, trial["seed"])
                        for index in range(study.evaluations_per_policy):
                            if time.monotonic() - start_wall >= study.attempt_timeout_seconds:
                                raise TimeoutError("Attempt elapsed-time limit reached")
                            point = policy.propose()
                            value = evaluator.evaluate(point)
                            _observe(db, attempt_id, index, point, value, study)
                            policy.observe(point, value)
                        if time.monotonic() - start_wall >= study.attempt_timeout_seconds:
                            raise TimeoutError("Attempt elapsed-time limit reached")
                        _fault("after-execution", _crash_at)
                        record = _result(db, attempt_id, "COMPLETED", "Full frozen observation allowance evaluated",
                                         start_wall, start_cpu)
                        with _transaction(db):
                            db.execute("INSERT INTO staged VALUES(?,?)", (attempt_id, canonical(record)))
                            _event(db, "STAGED", attempt_id, {"status": "COMPLETED"})
                        _fault("after-staging", _crash_at)
                        _terminal(db, attempt_id, record)
                        break
                    except KeyboardInterrupt:
                        # If interruption follows staging, leave the valid staged artifact for resume.
                        existing = db.execute("SELECT 1 FROM terminals WHERE attempt_id=?", (attempt_id,)).fetchone()
                        staged = db.execute("SELECT 1 FROM staged WHERE attempt_id=?", (attempt_id,)).fetchone()
                        if not existing and not staged:
                            _terminal(db, attempt_id, _result(db, attempt_id, "CANCELLED", "Interrupted by operator",
                                                             start_wall, start_cpu))
                        raise
                    except TimeoutError:
                        _terminal(db, attempt_id, _result(db, attempt_id, "TIMED_OUT", "Attempt elapsed-time limit reached",
                                                         start_wall, start_cpu))
                    except (ValueError, RuntimeError, StopIteration):
                        _terminal(db, attempt_id, _result(db, attempt_id, "INVALID", "Built-in proposal or evaluator contract rejected",
                                                         start_wall, start_cpu))
                        # Contract rejection is a fail-closed campaign stop, not another exploratory query.
                        raise CampaignError("Built-in contract rejected; retained invalid attempt, review before resuming") from None
                    except sqlite3.DatabaseError:
                        # Storage ambiguity must remain recoverable. Never invent a terminal after a failed commit.
                        raise CampaignError("Storage write failed; preserve database and resume after resolving the cause") from None
                processed += 1
                if max_trials is not None and processed >= max_trials:
                    break
            result = _snapshot(db)
            validate_snapshot(result)
            return result
        finally:
            db.close()
