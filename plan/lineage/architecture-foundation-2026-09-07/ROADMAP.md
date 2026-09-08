# Research Continuum roadmap

Wave 0 is **DONE**: its three architecture-foundation tasks were accepted by the authorized root after independent review and reproduced checks. All 24 original scientific/build tasks remain **PLANNED** across Waves 1–8. The programme now contains nine waves and 27 tasks; no scientific result or runtime is claimed.

## Product objective

Build a general software research system, starting with AI, that can read approved sources, formulate hypotheses, design experiments, modify bounded code, execute under budgets, challenge its findings and preserve a usable body of evidence. Advance from a single optimization loop to multiple research questions and domains without allowing agents to rewrite the rules that judge them.

## First research milestone

Reproduce a tiny bounded training-search loop and compare it with fixed random search under the same total budget. The producer may edit an experiment module; it cannot edit the evaluator or access the final holdout. A separate worker reruns any claimed improvement. A successful first result can be a clear negative finding with full evidence.

Wave 0 makes the programme executable without pretending the research runtime exists. Waves 1–3 then establish the first integrated experiment. Wave 4 tests whether its evidence is robust. Later waves expand domains, add research memory and allocation, improve inspection and prepare an independently reproduced research-system preview. Wave order is an integration dependency, not a calendar. The explicit task dependencies are in [TASKS.md](TASKS.md).

## Capacity and next planning window

Assume one maintainer and one implementation owner per coherent surface. Human reviewer availability, suitable GPU hardware and paid-compute budget are currently unallocated. No date forecast has a local throughput basis yet. Measure RC-001 and the first local skeleton packet before forecasting Waves 1–2; later tasks are outcome packages to split when prerequisites exist. The conservative dependency graph waits for the previous wave's accepted gate. Within a wave, use disjoint work only when dependencies, trust separation and shared resources permit it.

Proposed initial experiment ceiling for future approval: one local worker, at most 20 trial runs, at most two elapsed compute hours and 5 GiB of new artifacts per campaign. Agent inference costs count toward an explicitly approved budget. These are draft limits, not permission to start or spend. Reduce the workload if the first benchmark cannot fit. GPU, cloud, domain-review time and additional workers need an explicit allocation before execution.

Reserve baseline, confirmation and independent-reproduction capacity before exploration starts. Exploration cannot borrow those reserves. Scale beyond one local worker only after cancellation, restart reconciliation, duplicate prevention, fencing and aggregate resource accounting pass and measured queue time justifies concurrency. Remote workers additionally require a reproducible environment package, narrow revocable identity, partition recovery and explicit hardware/spend approval.

## Executable next work packet after Wave 0 review

**Packet:** RC-001 autoresearch baseline record.

- Baseline: foundation candidate on `main` descended from `f558f21830246d4732bc1e590a83214d480cd94b`; verify exact source identity and clean/dirty state again at start.
- Owned output: `docs/baselines/autoresearch.md` and source-link corrections strictly required by that record.
- Inputs: official `karpathy/autoresearch` revision `228791fb499afffb54b46200aca536f79142f117`, its README, `program.md`, fixed/mutable code boundary and dependency metadata. Re-resolve the official branch before work and record any drift.
- Outcome: an attributed, version-specific baseline describing the observable five-minute `val_bpb` loop, hardware/data/dependency assumptions, what a later reproduction would and would not establish, exact proposed differences and unresolved license/reuse questions.
- Acceptance: the record can be reviewed without running training; it labels claims from source inspection, identifies the smallest later reproducible outcome, and makes no affiliation, superiority or scientific-validity claim.
- Checks: `python3 tools/validate_plan.py`, local-link inspection and a diff against the accepted Wave 0 baseline. No install, model weight, dataset download, GPU, paid service, commit, push or publication is required.
- Stop/escalate: hold code reuse on unclear license terms; hold the runtime reproduction until compatible hardware, data rights, dependency review and a bounded compute allocation are approved.

The next throughput reforecast occurs after RC-001 is accepted and again after RC-003 proves a restartable synthetic skeleton. The first replaces document-effort guesses; the second supplies actual implementation, review and defect data.

## Waves and tasks

## Wave 0: Architecture and research-programme foundation

Outcome/gate: The proposed scientific contract, programme dependencies and exact next packet are coherent, source-grounded and reviewable without implying a research runtime.

Entry: Documentation-only repository at `f558f21830246d4732bc1e590a83214d480cd94b`; no implementation, data or compute prerequisite.
- **RC-F01: Define the research-system architecture contract.** Distinguish the inspected autoresearch baseline from proposed Research Continuum extensions; define the question–hypothesis–evidence graph, study and publication contracts, protected evaluation, domain-adapter seams, durable campaign/recovery model, isolation boundaries, allocation rules, local-first scale gates, cross-lab portability and explicit nonclaims with primary-source grounding.
- **RC-F02: Convert the vision into an outcome and dependency roadmap.** Prepend Wave 0, preserve all original Waves 1–8 and their 24 task IDs, acceptance text, dependency logic and gates, identify capacity and human/hardware/licensing decisions, and define stop, pivot, scale and replan conditions without speculative dates.
- **RC-F03: Make the next work packet executable and validate the repository plan.** Provide a standard-library validation command that checks task identity, status, documentation parity, dependency existence/order, DAG acyclicity, wave coverage and navigation links; prove its negative self-test detects an invalid plan; specify one RC-001 packet that can run locally without paid compute, model weights or dataset downloads.

Gate decision: The active root may mark Wave 0 accepted under Lucas Santana's delegated implementation instruction after reviewing the complete foundation diff and reproducing the validator results. Otherwise revise or hold; `READY_FOR_REVIEW` is not acceptance.

## Wave 1: Research contract and baseline

Outcome/gate: One question, budget and falsification protocol are fixed.

Entry: Wave 0 accepted; inspect the official baseline and current repository state again.
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
