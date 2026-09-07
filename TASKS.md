# Research Continuum contributor tasks

All 24 tasks start **PLANNED**. [STATUS.md](STATUS.md) is the mutable progress authority; this file is the initial task contract. [plan/tasks.json](plan/tasks.json) is the machine-readable copy of that initial contract. Update both task descriptions together when scope changes. Tanduna publication/review and task execution are separate operations.

Before an implementation task starts, bind it to an actual repository branch/commit, inspect existing paths and dependencies, identify one primary owner and record the exact verification commands available in that checkout. Proposed directory names below are ownership boundaries to establish, not claims of existing modules. Later outcome packages may need decomposition at their wave gate; do not treat all 24 as one autonomous job.

Protected across every task: evaluator/holdouts outside the task's authority, accepted evidence, unrelated source, credentials, data rights, domain safety rules and resource ceilings. No production deploy, physical system connection, external outreach or paid compute is authorized by a task description. Do not commit, push or publish unless the specific contribution task authorizes it. The maintainer reviews source contributions and scientific claims separately.

## RC-001 — Analyze and scope the autoresearch baseline

- Wave: 1; status: **PLANNED**; owner: unassigned until accepted by Lucas Santana.
- Dependencies: none.
- Owned scope: `docs/baselines/`.
- Acceptance: Record the upstream reference, attribution, narrow reproduction target and proposed differences; no superiority claim without tests.
- Verification: reproduce the stated observable outcome; include one representative invalid/failure case when implementing behavior. Record exact commands and source revision after the harness exists; this plan makes no claim that those commands or tests currently exist.
- Delivery: focused diff, result/diagnostics, known limitations and a concise reproduction note. Preserve unrelated work.
## RC-002 — Define budgets, safety and evaluation boundaries

- Wave: 1; status: **PLANNED**; owner: unassigned until accepted by Lucas Santana.
- Dependencies: RC-001.
- Owned scope: `docs/decisions/`.
- Acceptance: Specify permitted edits/tools, total resource accounting, protected evaluator, holdout access and stop conditions.
- Verification: reproduce the stated observable outcome; include one representative invalid/failure case when implementing behavior. Record exact commands and source revision after the harness exists; this plan makes no claim that those commands or tests currently exist.
- Delivery: focused diff, result/diagnostics, known limitations and a concise reproduction note. Preserve unrelated work.
## RC-003 — Build the durable experiment skeleton

- Wave: 1; status: **PLANNED**; owner: unassigned until accepted by Lucas Santana.
- Dependencies: RC-001, RC-002.
- Owned scope: `src/`, `tests/`, `examples/`.
- Acceptance: A local synthetic campaign survives restart with unique experiment IDs and explicit invalid/failed states; no model or cloud dependency is required.
- Verification: reproduce the stated observable outcome; include one representative invalid/failure case when implementing behavior. Record exact commands and source revision after the harness exists; this plan makes no claim that those commands or tests currently exist.
- Delivery: focused diff, result/diagnostics, known limitations and a concise reproduction note. Preserve unrelated work.
## RC-004 — Implement bounded workspace execution

- Wave: 2; status: **PLANNED**; owner: unassigned until accepted by Lucas Santana.
- Dependencies: RC-001, RC-002, RC-003.
- Owned scope: `src/sandbox/`.
- Acceptance: Restrict owned paths, processes, network and resources; adversarial escape/write attempts fail under the supported threat model.
- Verification: reproduce the stated observable outcome; include one representative invalid/failure case when implementing behavior. Record exact commands and source revision after the harness exists; this plan makes no claim that those commands or tests currently exist.
- Delivery: focused diff, result/diagnostics, known limitations and a concise reproduction note. Preserve unrelated work.
## RC-005 — Implement the evaluator boundary

- Wave: 2; status: **PLANNED**; owner: unassigned until accepted by Lucas Santana.
- Dependencies: RC-001, RC-002, RC-003.
- Owned scope: `src/evaluator/`.
- Acceptance: Keep test data/code outside producer access and enforce development/final feedback separation and query limits.
- Verification: reproduce the stated observable outcome; include one representative invalid/failure case when implementing behavior. Record exact commands and source revision after the harness exists; this plan makes no claim that those commands or tests currently exist.
- Delivery: focused diff, result/diagnostics, known limitations and a concise reproduction note. Preserve unrelated work.
## RC-006 — Implement atomic result persistence

- Wave: 2; status: **PLANNED**; owner: unassigned until accepted by Lucas Santana.
- Dependencies: RC-001, RC-002, RC-003.
- Owned scope: `src/store/`.
- Acceptance: Crash and duplicate-event tests preserve one terminal result and complete cost accounting without overwriting accepted evidence.
- Verification: reproduce the stated observable outcome; include one representative invalid/failure case when implementing behavior. Record exact commands and source revision after the harness exists; this plan makes no claim that those commands or tests currently exist.
- Delivery: focused diff, result/diagnostics, known limitations and a concise reproduction note. Preserve unrelated work.
## RC-007 — Integrate one small training domain

- Wave: 3; status: **PLANNED**; owner: unassigned until accepted by Lucas Santana.
- Dependencies: RC-004, RC-005, RC-006.
- Owned scope: `adapters/training/`.
- Acceptance: Use lawful data and a pinned baseline; run/reproduce contracts capture exact code, environment, seeds and metrics.
- Verification: reproduce the stated observable outcome; include one representative invalid/failure case when implementing behavior. Record exact commands and source revision after the harness exists; this plan makes no claim that those commands or tests currently exist.
- Delivery: focused diff, result/diagnostics, known limitations and a concise reproduction note. Preserve unrelated work.
## RC-008 — Add hypothesis and patch proposals

- Wave: 3; status: **PLANNED**; owner: unassigned until accepted by Lucas Santana.
- Dependencies: RC-004, RC-005, RC-006, RC-007.
- Owned scope: `src/agents/`.
- Acceptance: Each proposal includes evidence, control, predicted outcome and falsifier; only accepted bounded patches execute.
- Verification: reproduce the stated observable outcome; include one representative invalid/failure case when implementing behavior. Record exact commands and source revision after the harness exists; this plan makes no claim that those commands or tests currently exist.
- Delivery: focused diff, result/diagnostics, known limitations and a concise reproduction note. Preserve unrelated work.
## RC-009 — Compare autonomous and random search

- Wave: 3; status: **PLANNED**; owner: unassigned until accepted by Lucas Santana.
- Dependencies: RC-004, RC-005, RC-006, RC-008.
- Owned scope: `experiments/first-campaign/`.
- Acceptance: Run equal-total-budget campaigns, retain all failures and independently rerun every claimed finalist improvement.
- Verification: reproduce the stated observable outcome; include one representative invalid/failure case when implementing behavior. Record exact commands and source revision after the harness exists; this plan makes no claim that those commands or tests currently exist.
- Delivery: focused diff, result/diagnostics, known limitations and a concise reproduction note. Preserve unrelated work.
## RC-010 — Add independent replication and ablations

- Wave: 4; status: **PLANNED**; owner: unassigned until accepted by Lucas Santana.
- Dependencies: RC-007, RC-008, RC-009.
- Owned scope: `src/replication/`.
- Acceptance: A fresh worker reruns candidates and removes individual changes to test attribution; report failures.
- Verification: reproduce the stated observable outcome; include one representative invalid/failure case when implementing behavior. Record exact commands and source revision after the harness exists; this plan makes no claim that those commands or tests currently exist.
- Delivery: focused diff, result/diagnostics, known limitations and a concise reproduction note. Preserve unrelated work.
## RC-011 — Control repeated selection and leakage

- Wave: 4; status: **PLANNED**; owner: unassigned until accepted by Lucas Santana.
- Dependencies: RC-007, RC-008, RC-009.
- Owned scope: `src/evaluation/`.
- Acceptance: Limit final holdout queries, separate selection from confirmation and report uncertainty after repeated search.
- Verification: reproduce the stated observable outcome; include one representative invalid/failure case when implementing behavior. Record exact commands and source revision after the harness exists; this plan makes no claim that those commands or tests currently exist.
- Delivery: focused diff, result/diagnostics, known limitations and a concise reproduction note. Preserve unrelated work.
## RC-012 — Build evidence-linked research reports

- Wave: 4; status: **PLANNED**; owner: unassigned until accepted by Lucas Santana.
- Dependencies: RC-007, RC-008, RC-009.
- Owned scope: `src/reports/`.
- Acceptance: Every conclusion resolves to sources and experiments; contradictions, null findings and resource totals remain visible.
- Verification: reproduce the stated observable outcome; include one representative invalid/failure case when implementing behavior. Record exact commands and source revision after the harness exists; this plan makes no claim that those commands or tests currently exist.
- Delivery: focused diff, result/diagnostics, known limitations and a concise reproduction note. Preserve unrelated work.
## RC-013 — Add an inference-efficiency domain

- Wave: 5; status: **PLANNED**; owner: unassigned until accepted by Lucas Santana.
- Dependencies: RC-010, RC-011, RC-012.
- Owned scope: `adapters/inference/`.
- Acceptance: Use quality-constrained latency/memory objectives and a protected evaluator; integrate Lean Model Lab only through a versioned contract when available.
- Verification: reproduce the stated observable outcome; include one representative invalid/failure case when implementing behavior. Record exact commands and source revision after the harness exists; this plan makes no claim that those commands or tests currently exist.
- Delivery: focused diff, result/diagnostics, known limitations and a concise reproduction note. Preserve unrelated work.
## RC-014 — Add retrieval or data-selection research

- Wave: 5; status: **PLANNED**; owner: unassigned until accepted by Lucas Santana.
- Dependencies: RC-010, RC-011, RC-012.
- Owned scope: `adapters/retrieval/`.
- Acceptance: Use lawful corpora, train/development/holdout separation and relevance/quality checks without prompt leakage.
- Verification: reproduce the stated observable outcome; include one representative invalid/failure case when implementing behavior. Record exact commands and source revision after the harness exists; this plan makes no claim that those commands or tests currently exist.
- Delivery: focused diff, result/diagnostics, known limitations and a concise reproduction note. Preserve unrelated work.
## RC-015 — Add a numerical optimization domain

- Wave: 5; status: **PLANNED**; owner: unassigned until accepted by Lucas Santana.
- Dependencies: RC-010, RC-011, RC-012.
- Owned scope: `adapters/optimization/`.
- Acceptance: Reproduce a non-LLM numerical benchmark to test genuine adapter generality and domain safety boundaries.
- Verification: reproduce the stated observable outcome; include one representative invalid/failure case when implementing behavior. Record exact commands and source revision after the harness exists; this plan makes no claim that those commands or tests currently exist.
- Delivery: focused diff, result/diagnostics, known limitations and a concise reproduction note. Preserve unrelated work.
## RC-016 — Build the question-evidence graph

- Wave: 6; status: **PLANNED**; owner: unassigned until accepted by Lucas Santana.
- Dependencies: RC-013, RC-014, RC-015.
- Owned scope: `src/knowledge/`.
- Acceptance: Track source versions, hypotheses and contradiction links; reject unsupported citations and stale evidence reuse.
- Verification: reproduce the stated observable outcome; include one representative invalid/failure case when implementing behavior. Record exact commands and source revision after the harness exists; this plan makes no claim that those commands or tests currently exist.
- Delivery: focused diff, result/diagnostics, known limitations and a concise reproduction note. Preserve unrelated work.
## RC-017 — Add bounded campaign allocation

- Wave: 6; status: **PLANNED**; owner: unassigned until accepted by Lucas Santana.
- Dependencies: RC-013, RC-014, RC-015.
- Owned scope: `src/scheduling/`.
- Acceptance: Allocate fixed budgets across hypotheses with simple baselines, starvation controls and explicit stop/pivot decisions.
- Verification: reproduce the stated observable outcome; include one representative invalid/failure case when implementing behavior. Record exact commands and source revision after the harness exists; this plan makes no claim that those commands or tests currently exist.
- Delivery: focused diff, result/diagnostics, known limitations and a concise reproduction note. Preserve unrelated work.
## RC-018 — Evaluate research-policy improvements

- Wave: 6; status: **PLANNED**; owner: unassigned until accepted by Lucas Santana.
- Dependencies: RC-013, RC-014, RC-015.
- Owned scope: `experiments/policy/`.
- Acceptance: Compare new orchestration policies on fresh campaigns with equal cost; keep evaluators and accepted records immutable.
- Verification: reproduce the stated observable outcome; include one representative invalid/failure case when implementing behavior. Record exact commands and source revision after the harness exists; this plan makes no claim that those commands or tests currently exist.
- Delivery: focused diff, result/diagnostics, known limitations and a concise reproduction note. Preserve unrelated work.
## RC-019 — Build a local campaign inspection view

- Wave: 7; status: **PLANNED**; owner: unassigned until accepted by Lucas Santana.
- Dependencies: RC-016, RC-017, RC-018.
- Owned scope: `apps/workbench/`.
- Acceptance: Show question-to-evidence lineage, full costs, failures and stop controls with accessible navigation.
- Verification: reproduce the stated observable outcome; include one representative invalid/failure case when implementing behavior. Record exact commands and source revision after the harness exists; this plan makes no claim that those commands or tests currently exist.
- Delivery: focused diff, result/diagnostics, known limitations and a concise reproduction note. Preserve unrelated work.
## RC-020 — Add isolated remote workers

- Wave: 7; status: **PLANNED**; owner: unassigned until accepted by Lucas Santana.
- Dependencies: RC-016, RC-017, RC-018.
- Owned scope: `src/workers/`.
- Acceptance: Use scoped jobs with no inherited personal credentials, explicit budgets and verified cancellation/recovery.
- Verification: reproduce the stated observable outcome; include one representative invalid/failure case when implementing behavior. Record exact commands and source revision after the harness exists; this plan makes no claim that those commands or tests currently exist.
- Delivery: focused diff, result/diagnostics, known limitations and a concise reproduction note. Preserve unrelated work.
## RC-021 — Export portable research packages

- Wave: 7; status: **PLANNED**; owner: unassigned until accepted by Lucas Santana.
- Dependencies: RC-016, RC-017, RC-018.
- Owned scope: `src/export/`.
- Acceptance: Another researcher can inspect and reproduce accepted evidence without the original agent conversation.
- Verification: reproduce the stated observable outcome; include one representative invalid/failure case when implementing behavior. Record exact commands and source revision after the harness exists; this plan makes no claim that those commands or tests currently exist.
- Delivery: focused diff, result/diagnostics, known limitations and a concise reproduction note. Preserve unrelated work.
## RC-022 — Run a blind multi-domain evaluation

- Wave: 8; status: **PLANNED**; owner: unassigned until accepted by Lucas Santana.
- Dependencies: RC-019, RC-020, RC-021.
- Owned scope: `benchmarks/replication/`.
- Acceptance: Independent evaluators test at least two distinct domains against equal-budget simple baselines and publish all outcomes.
- Verification: reproduce the stated observable outcome; include one representative invalid/failure case when implementing behavior. Record exact commands and source revision after the harness exists; this plan makes no claim that those commands or tests currently exist.
- Delivery: focused diff, result/diagnostics, known limitations and a concise reproduction note. Preserve unrelated work.
## RC-023 — Audit safety and scientific integrity

- Wave: 8; status: **PLANNED**; owner: unassigned until accepted by Lucas Santana.
- Dependencies: RC-019, RC-020, RC-021.
- Owned scope: `docs/review/`.
- Acceptance: Test evaluator tampering, prompt injection, runaway cost and unsupported conclusions; resolve material defects.
- Verification: reproduce the stated observable outcome; include one representative invalid/failure case when implementing behavior. Record exact commands and source revision after the harness exists; this plan makes no claim that those commands or tests currently exist.
- Delivery: focused diff, result/diagnostics, known limitations and a concise reproduction note. Preserve unrelated work.
## RC-024 — Prepare a bounded autonomous-research release

- Wave: 8; status: **PLANNED**; owner: unassigned until accepted by Lucas Santana.
- Dependencies: RC-019, RC-020, RC-021.
- Owned scope: `docs/releases/`.
- Acceptance: State supported domains, actual comparative results, known limitations and maintainer-approved release scope.
- Verification: reproduce the stated observable outcome; include one representative invalid/failure case when implementing behavior. Record exact commands and source revision after the harness exists; this plan makes no claim that those commands or tests currently exist.
- Delivery: focused diff, result/diagnostics, known limitations and a concise reproduction note. Preserve unrelated work.
