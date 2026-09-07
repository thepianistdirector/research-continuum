#!/usr/bin/env python3
"""Validate the documentation-only Research Continuum task contract.

This checks plan structure and navigation. It does not run an experiment or
validate an architecture or scientific claim.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "plan" / "tasks.json"
TASK_ID_PATTERN = re.compile(r"RC-(?:F\d{2}|\d{3}(?:-[A-Z0-9]+)?)")
FOUNDATION_IDS = ["RC-F01", "RC-F02", "RC-F03"]
ORIGINAL_IDS = [f"RC-{number:03d}" for number in range(1, 25)]
REQUIRED_SEED_IDS = FOUNDATION_IDS + ORIGINAL_IDS

STATUS_VOCABULARY = {
    "PLANNED",
    "READY_FOR_REVIEW",
    "IN_PROGRESS",
    "IMPLEMENTED",
    "AUTOMATED_PASS",
    "RUNTIME_VERIFIED",
    "USER_VALIDATED",
    "RELEASE_VERIFIED",
    "BLOCKED",
    "FAILED",
    "NOT_TESTED",
    "DONE",
}

# These are the original dependency edges, plus the reviewed Wave 0 entry edge.
# Later task decomposition may add prerequisite edges and new tasks, but cannot
# silently remove the seed programme's dependency logic.
REQUIRED_DEPENDENCIES = {
    "RC-F01": [],
    "RC-F02": ["RC-F01"],
    "RC-F03": ["RC-F02"],
    "RC-001": ["RC-F03"],
    "RC-002": ["RC-001"],
    "RC-003": ["RC-001", "RC-002"],
    "RC-004": ["RC-001", "RC-002", "RC-003"],
    "RC-005": ["RC-001", "RC-002", "RC-003"],
    "RC-006": ["RC-001", "RC-002", "RC-003"],
    "RC-007": ["RC-004", "RC-005", "RC-006"],
    "RC-008": ["RC-004", "RC-005", "RC-006", "RC-007"],
    "RC-009": ["RC-004", "RC-005", "RC-006", "RC-008"],
    "RC-010": ["RC-007", "RC-008", "RC-009"],
    "RC-011": ["RC-007", "RC-008", "RC-009"],
    "RC-012": ["RC-007", "RC-008", "RC-009"],
    "RC-013": ["RC-010", "RC-011", "RC-012"],
    "RC-014": ["RC-010", "RC-011", "RC-012"],
    "RC-015": ["RC-010", "RC-011", "RC-012"],
    "RC-016": ["RC-013", "RC-014", "RC-015"],
    "RC-017": ["RC-013", "RC-014", "RC-015"],
    "RC-018": ["RC-013", "RC-014", "RC-015"],
    "RC-019": ["RC-016", "RC-017", "RC-018"],
    "RC-020": ["RC-016", "RC-017", "RC-018"],
    "RC-021": ["RC-016", "RC-017", "RC-018"],
    "RC-022": ["RC-019", "RC-020", "RC-021"],
    "RC-023": ["RC-019", "RC-020", "RC-021"],
    "RC-024": ["RC-019", "RC-020", "RC-021"],
}


def is_nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def normalize(value: str) -> str:
    return " ".join(value.split())


def is_repository_relative_path(value: str) -> bool:
    path = PurePosixPath(value)
    return (
        bool(value.strip())
        and not value.startswith("/")
        and "\\" not in value
        and all(part not in {"", ".", ".."} for part in path.parts)
    )


def validate_metadata(plan: Any) -> list[str]:
    if not isinstance(plan, dict):
        return ["plan root must be a JSON object"]

    errors: list[str] = []
    schema_version = plan.get("schemaVersion")
    if isinstance(schema_version, bool) or not isinstance(schema_version, int):
        errors.append("plan.schemaVersion must be an integer")
    elif schema_version != 1:
        errors.append(f"unsupported plan.schemaVersion {schema_version!r}; expected 1")

    if plan.get("project") != "research-continuum":
        errors.append("plan.project must be the non-empty repository identifier 'research-continuum'")
    if not is_nonempty_text(plan.get("contractVersion")):
        errors.append("plan.contractVersion must be non-empty text")

    state_authority = plan.get("stateAuthority")
    if not is_nonempty_text(state_authority):
        errors.append("plan.stateAuthority must be non-empty text")
    elif state_authority != "../STATUS.md":
        errors.append("plan.stateAuthority must be '../STATUS.md'")
    elif not (ROOT / "STATUS.md").is_file():
        errors.append("plan.stateAuthority target does not exist")
    return errors


def validate_plan_dict(plan: Any) -> list[str]:
    errors = validate_metadata(plan)
    if not isinstance(plan, dict):
        return errors

    tasks = plan.get("tasks")
    if not isinstance(tasks, list):
        return errors + ["plan.tasks must be a list"]
    if not tasks:
        errors.append("plan.tasks must not be empty")

    valid_tasks: list[tuple[str, dict[str, Any]]] = []
    ids: list[str] = []
    seen_ids: set[str] = set()
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            errors.append(f"task[{index}] must be a JSON object")
            continue
        task_id = task.get("id")
        if not is_nonempty_text(task_id):
            errors.append(f"task[{index}].id must be non-empty text")
            continue
        if TASK_ID_PATTERN.fullmatch(task_id) is None:
            errors.append(f"task[{index}].id has unsupported format {task_id!r}")
            continue
        if task_id in seen_ids:
            errors.append(f"task ID {task_id} is duplicated")
            continue
        seen_ids.add(task_id)
        ids.append(task_id)
        valid_tasks.append((task_id, task))

    if ids[: len(FOUNDATION_IDS)] != FOUNDATION_IDS:
        errors.append("the three Wave 0 foundation tasks must remain first and ordered")
    missing_seed_ids = [task_id for task_id in REQUIRED_SEED_IDS if task_id not in seen_ids]
    if missing_seed_ids:
        errors.append(f"required seed task IDs are missing: {missing_seed_ids}")
    original_positions = [ids.index(task_id) for task_id in ORIGINAL_IDS if task_id in seen_ids]
    if original_positions != sorted(original_positions):
        errors.append("the original RC-001 through RC-024 order changed")

    by_id = dict(valid_tasks)
    position = {task_id: index for index, task_id in enumerate(ids)}
    dependency_map: dict[str, list[str]] = {}
    required_fields = {"id", "wave", "title", "status", "dependsOn", "ownedPaths", "acceptance"}

    for task_id, task in valid_tasks:
        missing_fields = sorted(required_fields - task.keys())
        if missing_fields:
            errors.append(f"{task_id} missing fields: {', '.join(missing_fields)}")

        if not is_nonempty_text(task.get("title")):
            errors.append(f"{task_id} title must be non-empty text")
        status = task.get("status")
        if not isinstance(status, str) or status not in STATUS_VOCABULARY:
            errors.append(f"{task_id} uses unknown status {status!r}")
        wave = task.get("wave")
        valid_wave = isinstance(wave, int) and not isinstance(wave, bool) and wave >= 0
        if not valid_wave:
            errors.append(f"{task_id} wave must be a non-negative integer, not a boolean")
        if not is_nonempty_text(task.get("acceptance")):
            errors.append(f"{task_id} acceptance must be non-empty text")

        dependencies_value = task.get("dependsOn")
        dependencies: list[str] = []
        if not isinstance(dependencies_value, list):
            errors.append(f"{task_id} dependsOn must be a list")
        else:
            seen_dependencies: set[str] = set()
            for dependency_index, dependency in enumerate(dependencies_value):
                if not is_nonempty_text(dependency):
                    errors.append(
                        f"{task_id} dependency entries must be non-empty text; "
                        f"entry {dependency_index} is {dependency!r}"
                    )
                    continue
                if TASK_ID_PATTERN.fullmatch(dependency) is None:
                    errors.append(f"{task_id} dependency has unsupported format {dependency!r}")
                    continue
                if dependency in seen_dependencies:
                    errors.append(f"{task_id} repeats dependency {dependency}")
                    continue
                seen_dependencies.add(dependency)
                dependencies.append(dependency)
        dependency_map[task_id] = dependencies

        owned_paths_value = task.get("ownedPaths")
        if not isinstance(owned_paths_value, list) or not owned_paths_value:
            errors.append(f"{task_id} ownedPaths must be a non-empty list")
        else:
            seen_paths: set[str] = set()
            for path_index, owned_path in enumerate(owned_paths_value):
                if not isinstance(owned_path, str):
                    errors.append(
                        f"{task_id} ownedPaths entries must be text; "
                        f"entry {path_index} is {owned_path!r}"
                    )
                    continue
                if not is_repository_relative_path(owned_path):
                    errors.append(f"{task_id} owned path is not repository-relative: {owned_path!r}")
                    continue
                if owned_path in seen_paths:
                    errors.append(f"{task_id} repeats owned path {owned_path!r}")
                    continue
                seen_paths.add(owned_path)

        if task_id in REQUIRED_SEED_IDS:
            expected_wave = 0 if task_id in FOUNDATION_IDS else (int(task_id[-3:]) - 1) // 3 + 1
            if valid_wave and wave != expected_wave:
                errors.append(f"{task_id} must remain in Wave {expected_wave}")
            required_dependencies = REQUIRED_DEPENDENCIES[task_id]
            if task_id in FOUNDATION_IDS and dependencies != required_dependencies:
                errors.append(f"{task_id} foundation dependencies must remain {required_dependencies}")
            elif not all(dependency in dependencies for dependency in required_dependencies):
                errors.append(f"{task_id} dropped required dependencies {required_dependencies}")

        for dependency in dependencies:
            if dependency not in by_id:
                errors.append(f"{task_id} has missing dependency {dependency}")
            elif position[dependency] >= position[task_id]:
                errors.append(f"{task_id} dependency {dependency} is not earlier in plan order")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str) -> None:
        if task_id in visiting:
            errors.append(f"dependency cycle reaches {task_id}")
            return
        if task_id in visited:
            return
        visiting.add(task_id)
        for dependency in dependency_map.get(task_id, []):
            if dependency in by_id:
                visit(dependency)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in ids:
        visit(task_id)
    return errors


def parse_task_contract(markdown: str) -> dict[str, dict[str, Any]]:
    id_pattern = TASK_ID_PATTERN.pattern
    headings = list(re.finditer(rf"^## ({id_pattern}) — (.+)$", markdown, re.MULTILINE))
    parsed: dict[str, dict[str, Any]] = {}
    for index, match in enumerate(headings):
        task_id = match.group(1)
        end = headings[index + 1].start() if index + 1 < len(headings) else len(markdown)
        block = markdown[match.end() : end]
        status_match = re.search(r"^- Wave: (\d+); status: \*\*([^*]+)\*\*;", block, re.MULTILINE)
        dependencies_match = re.search(r"^- Dependencies: (.+)$", block, re.MULTILINE)
        acceptance_match = re.search(r"^- Acceptance: (.+)$", block, re.MULTILINE)
        dependencies = []
        if dependencies_match:
            dependencies = re.findall(id_pattern, dependencies_match.group(1))
        parsed[task_id] = {
            "title": match.group(2).strip(),
            "wave": int(status_match.group(1)) if status_match else None,
            "status": status_match.group(2).strip() if status_match else None,
            "dependsOn": dependencies,
            "acceptance": acceptance_match.group(1).strip() if acceptance_match else None,
        }
    return parsed


def validate_documents(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    try:
        tasks_markdown = (ROOT / "TASKS.md").read_text(encoding="utf-8")
        roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
        status = (ROOT / "STATUS.md").read_text(encoding="utf-8")
    except OSError as error:
        return [f"cannot read required planning document: {error}"]

    tasks = plan["tasks"]
    plan_ids = [task["id"] for task in tasks]
    plan_by_id = {task["id"]: task for task in tasks}
    parsed = parse_task_contract(tasks_markdown)

    if list(parsed) != plan_ids:
        errors.append("TASKS.md task identity/order differs from plan/tasks.json")
    for task_id, plan_task in plan_by_id.items():
        if task_id not in parsed:
            continue
        document_task = parsed[task_id]
        for field in ("title", "wave", "status", "dependsOn"):
            if document_task[field] != plan_task[field]:
                errors.append(f"{task_id} {field} differs between TASKS.md and plan/tasks.json")
        if normalize(document_task.get("acceptance") or "") != normalize(plan_task["acceptance"]):
            errors.append(f"{task_id} acceptance differs between TASKS.md and plan/tasks.json")

    declared_waves = sorted({task["wave"] for task in tasks})
    roadmap_waves = [int(value) for value in re.findall(r"^## Wave (\d+):", roadmap, re.MULTILINE)]
    if roadmap_waves != declared_waves:
        errors.append(
            f"ROADMAP.md wave headers {roadmap_waves} differ from declared waves {declared_waves}"
        )
    roadmap_ids = re.findall(rf"\*\*({TASK_ID_PATTERN.pattern}):", roadmap)
    if roadmap_ids != plan_ids:
        errors.append("ROADMAP.md task identity/order differs from plan/tasks.json")
    if roadmap.count("Gate decision:") != len(declared_waves):
        errors.append("ROADMAP.md must have one gate decision for every declared wave")

    for task_id in FOUNDATION_IDS:
        status_value = re.escape(str(plan_by_id[task_id]["status"]))
        status_pattern = rf"\|\s*{re.escape(task_id)}\s*\|\s*\*\*{status_value}\*\*"
        if not re.search(status_pattern, status):
            errors.append(f"STATUS.md does not match the plan status for {task_id}")

    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for document in sorted(ROOT.glob("*.md")):
        try:
            contents = document.read_text(encoding="utf-8")
        except OSError as error:
            errors.append(f"cannot inspect links in {document.name}: {error}")
            continue
        for target in link_pattern.findall(contents):
            if "://" in target or target.startswith("#") or target.startswith("mailto:"):
                continue
            relative_target = target.split("#", 1)[0]
            if relative_target:
                try:
                    target_exists = (document.parent / relative_target).exists()
                except OSError:
                    target_exists = False
                if not target_exists:
                    errors.append(f"broken local link in {document.name}: {target}")
    return errors


def run_self_tests(plan: dict[str, Any]) -> list[str]:
    failures: list[str] = []

    missing_dependency = copy.deepcopy(plan)
    missing_dependency["tasks"][2]["dependsOn"] = ["RC-999"]
    dependency_errors = validate_plan_dict(missing_dependency)
    if not any("missing dependency RC-999" in error for error in dependency_errors):
        failures.append("missing-dependency self-test did not reject RC-999")

    malformed = copy.deepcopy(plan)
    malformed["schemaVersion"] = True
    malformed["project"] = []
    malformed["stateAuthority"] = {}
    malformed["tasks"][0]["id"] = ["RC-F01"]
    malformed["tasks"][1]["wave"] = True
    malformed["tasks"][1]["title"] = ""
    malformed["tasks"][1]["dependsOn"] = [{}]
    malformed["tasks"][1]["ownedPaths"] = [42]
    malformed_errors = validate_plan_dict(malformed)
    expected_fragments = [
        "schemaVersion",
        "plan.project",
        "plan.stateAuthority",
        "task[0].id",
        "title must be non-empty text",
        "wave must be a non-negative integer",
        "dependency entries must be non-empty text",
        "ownedPaths entries must be text",
    ]
    for fragment in expected_fragments:
        if not any(fragment in error for error in malformed_errors):
            failures.append(f"malformed-plan self-test did not report {fragment!r}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="also prove missing-dependency and malformed-plan rejection",
    )
    args = parser.parse_args()

    try:
        plan: Any = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"FAIL: cannot load {PLAN_PATH}: {error}", file=sys.stderr)
        return 1

    errors = validate_plan_dict(plan)
    if not errors and isinstance(plan, dict):
        errors.extend(validate_documents(plan))
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    if args.self_test:
        self_test_failures = run_self_tests(plan)
        if self_test_failures:
            for failure in self_test_failures:
                print(f"FAIL: {failure}", file=sys.stderr)
            return 1
        print("PASS: missing-dependency self-test rejected an unknown dependency")
        print("PASS: malformed-plan self-test rejected invalid metadata and task fields without crashing")

    print(
        f"PASS: {len(plan['tasks'])} task contracts, metadata, wave order, DAG, "
        "document parity, and local links are valid"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
