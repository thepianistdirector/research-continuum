"""Offline command line for frozen numerical campaigns and their evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import uuid

from . import __version__
from .study import DEFAULT_STUDY, Study, load_study


def write_new_json(path: str | Path, value: object) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.staging")
    try:
        with staging.open("x", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        # A hard link publishes a complete regular file and refuses a racing destination.
        os.link(staging, destination)
        parent_fd = os.open(destination.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
    finally:
        staging.unlink(missing_ok=True)


def emit(value: object) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, allow_nan=False))


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python3 -m continuum", description=__doc__)
    p.add_argument("--version", action="version", version=f"Research Continuum {__version__}")
    commands = p.add_subparsers(dest="command", required=True)
    study = commands.add_parser("study", help="Inspect the default protocol, or create an editable study draft")
    study.add_argument("--out", help="New JSON draft path; never replaces an existing file")
    init = commands.add_parser("init", help="Validate and freeze a study in a new campaign database")
    init.add_argument("--study", required=True)
    init.add_argument("--db", required=True)
    for name in ("run", "resume"):
        run = commands.add_parser(name, help="Reconcile interruptions and execute remaining finite trials")
        run.add_argument("--db", required=True)
        run.add_argument("--pause-after", type=int, metavar="N", help="Pause after N remaining logical trials")
    inspect = commands.add_parser("inspect", help="Inspect every trial/attempt and its retained cost")
    inspect.add_argument("--db", required=True)
    inspect.add_argument("--json", action="store_true", help="Return the full snapshot, including every observation/event")
    evaluate = commands.add_parser("evaluate", help="Validate and derive the bounded comparison from retained evidence")
    evaluate.add_argument("--db", required=True)
    export = commands.add_parser("export", help="Atomically export a terminal campaign into a new evidence directory")
    export.add_argument("--db", required=True)
    export.add_argument("--out", required=True)
    verify = commands.add_parser("verify", help="Check bundle inventory, raw policy replay and derived claims")
    verify.add_argument("--bundle", required=True)
    reproduce = commands.add_parser("reproduce", help="Execute a verified bundle's study in a fresh database")
    reproduce.add_argument("--bundle", required=True)
    reproduce.add_argument("--db", required=True, help="New database, or an interrupted reproduction of this study")
    reproduce.add_argument("--record", required=True, help="New reproduction record JSON path")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if sys.platform != "linux" or sys.version_info < (3, 12):
        print("ERROR: This release requires Linux and Python 3.12 or newer; see verified environment limits.", file=sys.stderr)
        return 2
    from . import store
    from .evidence import canonical_bytes, compare_reproduction, export_bundle, summarize, verify_bundle
    try:
        if args.command == "study":
            study = Study.from_dict(DEFAULT_STUDY)
            if args.out:
                write_new_json(args.out, study.to_dict())
                print("Created study draft. Inspect bounded fields before init freezes a campaign.")
            else:
                emit(study.to_dict())
        elif args.command == "init":
            snapshot = store.create(load_study(args.study), args.db)
            emit({"campaign_id": snapshot["campaign_id"], "study_digest": snapshot["study_digest"],
                  "reserved_evaluations": sum(a["capacity"] for a in snapshot["allocations"]),
                  "trial_count": len(snapshot["trial_specs"]), "status": "FROZEN"})
        elif args.command in ("run", "resume"):
            snapshot = store.run(args.db, max_trials=args.pause_after)
            emit(summarize(snapshot))
        elif args.command == "inspect":
            snapshot = store.inspect(args.db)
            if args.json:
                emit(snapshot)
            else:
                print("Campaign:", snapshot["campaign_id"])
                print("Question:", snapshot["study"]["question"])
                print("Trial | attempt | status | charged evaluations | recorded evaluations | best (partial if not completed)")
                attempted = set()
                for attempt in snapshot["attempts"]:
                    attempted.add(attempt["trial_id"])
                    terminal = attempt["terminal"]
                    status = terminal["status"] if terminal else "STARTED"
                    best = terminal["best"] if terminal else None
                    print(f"{attempt['trial_id']} | {attempt['number']} | {status} | {attempt['charged_evaluations']} | "
                          f"{len(attempt['observations'])} | {best}")
                    if terminal and status != "COMPLETED":
                        print("  Reason:", terminal["reason"])
                for trial in snapshot["trial_specs"]:
                    if trial["id"] not in attempted:
                        print(f"{trial['id']} | — | NOT STARTED | 0 | 0 | —")
                print("Use --json for every point/value, source link and event.")
        elif args.command == "evaluate":
            emit(summarize(store.inspect(args.db)))
        elif args.command == "export":
            destination = export_bundle(store.inspect(args.db), Path(args.out))
            print("Exported verified evidence bundle:", destination)
        elif args.command == "verify":
            snapshot = verify_bundle(Path(args.bundle))
            emit({"verified": True, "campaign_id": snapshot["campaign_id"], "summary": summarize(snapshot)})
        elif args.command == "reproduce":
            original = verify_bundle(Path(args.bundle))
            record_path, database_path, bundle_path = (Path(p).resolve() for p in (args.record, args.db, args.bundle))
            if record_path == database_path:
                raise ValueError("Reproduction record and database must have different paths")
            if any(p == bundle_path or bundle_path in p.parents for p in (record_path, database_path)):
                raise ValueError("Reproduction outputs must stay outside the accepted input bundle")
            if os.path.lexists(args.record):
                raise ValueError("Reproduction record already exists; choose a new record path")
            record_path.parent.mkdir(parents=True, exist_ok=True)
            # Fail before admitting work when the output parent cannot accept a record.
            with tempfile.TemporaryFile(dir=record_path.parent):
                pass
            resumed_terminal = False
            source_digest = hashlib.sha256(canonical_bytes(original)).hexdigest()
            source_id = "source-reproduction-" + original["campaign_id"]
            if Path(args.db).exists():
                fresh = store.inspect(args.db)
                resumed_terminal = summarize(fresh)["campaign_complete"]
                bindings = [r for r in fresh["source_records"] if r["id"] == source_id]
                if len(bindings) != 1 or bindings[0]["locator"] != "sha256:" + source_digest:
                    raise ValueError("Existing database was not created for reproducing this exact bundle")
                if fresh["campaign_id"] == original["campaign_id"]:
                    raise ValueError("Reproduction requires a fresh campaign, not the producer database")
                if (fresh["study_digest"], fresh["evaluator_digest"]) != (original["study_digest"], original["evaluator_digest"]):
                    raise ValueError("Existing reproduction database does not match this bundle")
            else:
                store.create(Study.from_dict(original["study"]), args.db,
                             expected_evaluator=original["evaluator_digest"],
                             reproduction_source={"campaign_id": original["campaign_id"], "evidence_digest": source_digest})
            fresh = store.run(args.db)
            record = compare_reproduction(original, fresh)
            record["publication_context"] = ("reconciled record for a completed, source-bound reproduction; no new execution claimed"
                                             if resumed_terminal else "record from this new or resumed source-bound execution")
            record["execution_created_at"] = fresh["created_at"]
            write_new_json(args.record, record)
            emit(record)
            return 0 if record["status"] == "MATCH" else 1
        return 0
    except KeyboardInterrupt:
        print("Interrupted. The campaign and charged costs are retained; use resume with the same database.", file=sys.stderr)
        return 130
    except (ValueError, RuntimeError, OSError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
