# Research Continuum roadmap

All eight waves and 24 tasks are **PLANNED**. No delivery date, compute allocation or completed research is promised.

## Product objective

Build a general software research system, starting with AI, that can read approved sources, formulate hypotheses, design experiments, modify bounded code, execute under budgets, challenge its findings and preserve a usable body of evidence. Advance from a single optimization loop to multiple research questions and domains without allowing agents to rewrite the rules that judge them.

## First milestone

Reproduce a tiny bounded training-search loop and compare it with fixed random search under the same total budget. The producer may edit an experiment module; it cannot edit the evaluator or access the final holdout. A separate worker reruns any claimed improvement. A successful first result can be a clear negative finding with full evidence.

Waves 1–3 establish the first integrated experiment. Wave 4 tests whether its evidence is robust. Later waves expand domains, add agents, improve collaboration and prepare an independently reproduced research preview. Wave order is an integration dependency, not a calendar. The explicit task dependencies are in [TASKS.md](TASKS.md).

## Capacity and next planning window

Assume one maintainer and one implementation owner per coherent surface. Human reviewer availability, hardware and paid-compute budget are currently unallocated. Plan the next one or two weeks around Waves 1–2 only after measuring the first task's throughput; later tasks are outcome packages to split when prerequisites exist. The conservative dependency graph waits for the previous wave's accepted gate. Within a wave, use disjoint work only when dependencies and shared resources permit it.

Proposed initial experiment ceiling for future approval: one local worker, at most 20 trial runs, at most two elapsed compute hours and 5 GiB of new artifacts per campaign. Agent inference costs count toward an explicitly approved budget. These are draft limits, not permission to start or spend. Reduce the workload if the first benchmark cannot fit. GPU, cloud, domain-review time and additional workers need an explicit allocation before execution.

## Waves and tasks

## Wave 1: Research contract and baseline

Outcome/gate: One question, budget and falsification protocol are fixed.

Entry: No implementation prerequisite; inspect the initial plan.
- **RC-001: Analyze and scope the autoresearch baseline.** Record the upstream reference, attribution, narrow reproduction target and proposed differences; no superiority claim without tests.
- **RC-002: Define budgets, safety and evaluation boundaries.** Specify permitted edits/tools, total resource accounting, protected evaluator, holdout access and stop conditions.
- **RC-003: Build the durable experiment skeleton.** A local synthetic campaign survives restart with unique experiment IDs and explicit invalid/failed states; no model or cloud dependency is required.

Gate decision: continue when the outcome is reproduced and reviewed at its appropriate evidence level; otherwise repair, reduce scope or hold. No later wave may weaken this gate.
## Wave 2: Isolation and protected evaluation

Outcome/gate: The producer cannot tamper with the rules or retained evidence.

Entry: Wave 1 accepted with its evidence recorded.
- **RC-004: Implement bounded workspace execution.** Restrict owned paths, processes, network and resources; adversarial escape/write attempts fail under the supported threat model.
- **RC-005: Implement the evaluator boundary.** Keep test data/code outside producer access and enforce development/final feedback separation and query limits.
- **RC-006: Implement atomic result persistence.** Crash and duplicate-event tests preserve one terminal result and complete cost accounting without overwriting accepted evidence.

Gate decision: continue when the outcome is reproduced and reviewed at its appropriate evidence level; otherwise repair, reduce scope or hold. No later wave may weaken this gate.
## Wave 3: First autonomous research loop

Outcome/gate: A real bounded AI experiment is compared with simple search.

Entry: Wave 2 accepted with its evidence recorded.
- **RC-007: Integrate one small training domain.** Use lawful data and a pinned baseline; run/reproduce contracts capture exact code, environment, seeds and metrics.
- **RC-008: Add hypothesis and patch proposals.** Each proposal includes evidence, control, predicted outcome and falsifier; only accepted bounded patches execute.
- **RC-009: Compare autonomous and random search.** Run equal-total-budget campaigns, retain all failures and independently rerun every claimed finalist improvement.

Gate decision: continue when the outcome is reproduced and reviewed at its appropriate evidence level; otherwise repair, reduce scope or hold. No later wave may weaken this gate.
## Wave 4: Scientific reliability

Outcome/gate: Promising results withstand replication and alternate explanations.

Entry: Wave 3 accepted with its evidence recorded.
- **RC-010: Add independent replication and ablations.** A fresh worker reruns candidates and removes individual changes to test attribution; report failures.
- **RC-011: Control repeated selection and leakage.** Limit final holdout queries, separate selection from confirmation and report uncertainty after repeated search.
- **RC-012: Build evidence-linked research reports.** Every conclusion resolves to sources and experiments; contradictions, null findings and resource totals remain visible.

Gate decision: continue when the outcome is reproduced and reviewed at its appropriate evidence level; otherwise repair, reduce scope or hold. No later wave may weaken this gate.
## Wave 5: General AI research adapters

Outcome/gate: The same contract works beyond one training script.

Entry: Wave 4 accepted with its evidence recorded.
- **RC-013: Add an inference-efficiency domain.** Use quality-constrained latency/memory objectives and a protected evaluator; integrate Lean Model Lab only through a versioned contract when available.
- **RC-014: Add retrieval or data-selection research.** Use lawful corpora, train/development/holdout separation and relevance/quality checks without prompt leakage.
- **RC-015: Add a numerical optimization domain.** Reproduce a non-LLM numerical benchmark to test genuine adapter generality and domain safety boundaries.

Gate decision: continue when the outcome is reproduced and reviewed at its appropriate evidence level; otherwise repair, reduce scope or hold. No later wave may weaken this gate.
## Wave 6: Research memory and allocation

Outcome/gate: Longer campaigns learn without rewriting established evidence.

Entry: Wave 5 accepted with its evidence recorded.
- **RC-016: Build the question-evidence graph.** Track source versions, hypotheses and contradiction links; reject unsupported citations and stale evidence reuse.
- **RC-017: Add bounded campaign allocation.** Allocate fixed budgets across hypotheses with simple baselines, starvation controls and explicit stop/pivot decisions.
- **RC-018: Evaluate research-policy improvements.** Compare new orchestration policies on fresh campaigns with equal cost; keep evaluators and accepted records immutable.

Gate decision: continue when the outcome is reproduced and reviewed at its appropriate evidence level; otherwise repair, reduce scope or hold. No later wave may weaken this gate.
## Wave 7: Research workbench and distributed runs

Outcome/gate: Humans can inspect and interrupt a recoverable research program.

Entry: Wave 6 accepted with its evidence recorded.
- **RC-019: Build a local campaign inspection view.** Show question-to-evidence lineage, full costs, failures and stop controls with accessible navigation.
- **RC-020: Add isolated remote workers.** Use scoped jobs with no inherited personal credentials, explicit budgets and verified cancellation/recovery.
- **RC-021: Export portable research packages.** Another researcher can inspect and reproduce accepted evidence without the original agent conversation.

Gate decision: continue when the outcome is reproduced and reviewed at its appropriate evidence level; otherwise repair, reduce scope or hold. No later wave may weaken this gate.
## Wave 8: Independent research-system preview

Outcome/gate: Generality and value are demonstrated rather than advertised.

Entry: Wave 7 accepted with its evidence recorded.
- **RC-022: Run a blind multi-domain evaluation.** Independent evaluators test at least two distinct domains against equal-budget simple baselines and publish all outcomes.
- **RC-023: Audit safety and scientific integrity.** Test evaluator tampering, prompt injection, runaway cost and unsupported conclusions; resolve material defects.
- **RC-024: Prepare a bounded autonomous-research release.** State supported domains, actual comparative results, known limitations and maintainer-approved release scope.

Gate decision: continue when the outcome is reproduced and reviewed at its appropriate evidence level; otherwise repair, reduce scope or hold. No later wave may weaken this gate.


## Acceptance and release

Numerical benchmarks, source rights, failure behavior and an end-to-end reproduction take precedence over task counts. Scientific extensions need their own applicability evidence; domain reviewer availability is a real dependency. High-risk interpretations require an independent qualified reviewer. A software preview can pass without demonstrating a novel scientific improvement; state the distinction explicitly.

All source and clinical/environmental/privacy/performance claims stay within [EXPERIMENTS.md](EXPERIMENTS.md). A final release needs the exact candidate, clean reproducibility instructions, lawful inputs, resolved material defects and maintainer approval. No production deploy, physical action or unrestricted autonomous execution is included.

## Stop and reduce-scope rules

If agent-guided search does not beat equal-budget simple baselines, publish that result and improve the method before adding more agents. Stop a campaign on budget exhaustion, evaluator compromise, unrecoverable provenance gaps or out-of-scope work. Never discard failed trials to manufacture progress.

Stop a campaign when its approved budget is exhausted, the evaluator is compromised, required provenance is missing or the task crosses its safety boundary. Do not keep adding agents to rescue an unsupported hypothesis. Cut rich visuals, distributed compute and additional domains before the initial benchmark. Reforecast after accepted task evidence, not from speculative agent throughput.
