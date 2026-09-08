#!/usr/bin/env python3
"""Run discovered tests and plan falsifiers, retaining their actual exit evidence."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    from continuum.store import environment
    commands = [[sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
                [sys.executable, "tools/validate_plan.py", "--self-test"],
                [sys.executable, "tools/render_plan.py", "--check"],
                ["git", "diff", "--check"]]
    scratch = ROOT / ".cache" / "tests"
    scratch.mkdir(parents=True, exist_ok=True)
    env = {"PATH": os.environ.get("PATH", os.defpath), "TMPDIR": str(scratch),
           "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1"}
    results = []
    for command in commands:
        start = time.monotonic()
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=180)
        output = (result.stdout + result.stderr).replace(str(ROOT), "$PROJECT")
        results.append({"command": ["python3" if part == sys.executable else part for part in command],
                        "exit_code": result.returncode, "elapsed_seconds": time.monotonic() - start,
                        "output": output})
        print("PASS" if result.returncode == 0 else "FAIL", " ".join(results[-1]["command"]))
    match = re.search(r"Ran (\d+) tests", results[0]["output"])
    count = int(match.group(1)) if match else 0
    passed = count > 0 and all(r["exit_code"] == 0 for r in results)
    record = {"schema_version": 1, "observed_at": datetime.now(timezone.utc).isoformat(),
              "evidence_level": "AUTOMATED PASS" if passed else "FAILED", "environment": environment(),
              "discovered_tests": count, "checks": results,
              "limitations": ["Agent automated checks; no independent human review or public-release verification.",
                              "Process-death recovery does not prove hardware power-loss durability."]}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump(record, handle, indent=2)
        handle.write("\n")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
