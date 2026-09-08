# Research Continuum experiment and evaluation contract

Status: accepted historical architecture requirements plus a separately frozen owner-authorized numerical 0.1 protocol. Actual execution evidence is in STATUS.md.

## Historical training programme question (later release)

Can a bounded proposal agent find a training change that improves a tiny language-model objective more reliably or efficiently than fixed random search under the same total resource budget, while preserving quality constraints and surviving untouched confirmation and independent reproduction?

This question is intentionally comparative. It does not assume that agent-guided search is better, that the selected training task represents general AI research, or that an optimization result is scientifically novel. A well-run null or negative result satisfies the first programme outcome.

## Evidence vocabulary

- **Source fact:** a statement traceable to an exact source version and location.
- **Assumption:** a declared premise used by a model or study, not established by this run.
- **Development evidence:** feedback used adaptively to propose or select candidates.
- **Confirmation evidence:** reserved evidence used only through a bounded evaluator under a frozen decision rule.
- **Reproduction:** another worker obtains the stated computational result using substantially the same artifacts and protocol.
- **Replication:** a new study tests the claim with meaningfully new data, conditions or implementation.
- **Interpretation:** a reasoned explanation linked to evidence; agent prose is never evidence by itself.
- **Supported claim:** a precise statement that passed its declared confirmation/reproduction contract and human review within a named applicability boundary.

`EVALUATED`, `CONFIRMED`, `REPRODUCED`, `REPLICATED` and `SUPPORTED` are separate states. A deterministic rerun does not establish external validity. A simulator can be numerically correct while its model is inapplicable.

## Question and hypothesis contract

Before a study is accepted, record:

| Field | Requirement |
| --- | --- |
| Question | One bounded answerable question, target workload/population and decision relevance |
| Alternatives | Null/comparison position and at least one competing explanation where meaningful |
| Hypothesis | Predicted outcome, mechanism, assumptions, sources, contradictions and falsifier |
| Domain | Adapter family, supported range, excluded uses and required expert review |
| Evidence map | Source, prior run and unresolved evidence linked by stable IDs |
| Exit | Observation that yields pass, redirect, descope, hold or terminate |

Hypothesis revisions are immutable. A post-result explanation is linked as a new interpretation or hypothesis revision and labelled exploratory; it is not backdated into the accepted study.

## Study-design contract

An accepted `StudyDesign` freezes these fields before candidate search:

1. Question and hypothesis revisions.
2. Unit of analysis, sampling frame or workload, inclusion/exclusion rules and intended applicability.
3. Transparent baseline and candidate arms under comparable resource accounting.
4. Positive control expected to produce a known signal, negative control expected not to, and one perturbation that should violate an invariant.
5. Search space, permitted code/data transformations and immutable evaluator/quality boundaries.
6. Development, calibration and confirmation partitions and their contamination checks.
7. Primary metric, direction, units, quality constraints, secondary diagnostics and minimum decision threshold.
8. Seeds, repeats or sample-size rationale; stochastic and hardware variance plan.
9. Planned ablations and alternate explanations for any selected finalist.
10. Family of comparisons, dependence/sequential structure, uncertainty estimator and error-control rule or an explicit reason descriptive evidence is all that is supported.
11. Finite limits for accepted trials, wall time, CPU/GPU, memory, disk, evaluator queries, agent inference and monetary cost.
12. Baseline, exploration, confirmation and reproduction reservations; stop/pivot outcomes and invalid states.
13. Exact source, code, environment, evaluator and allocation-policy revisions.
14. Required result bundle, independent-reproduction protocol and claim/publication boundary.

A study cannot be accepted with “improve the model” as its only hypothesis, one mutable metric as its entire protocol or an indefinite loop as its stop rule.

## Search, selection and confirmation

Development search is adaptive by design. The proposal policy may observe only feedback named by the accepted study. Every attempted candidate receives a durable record, including crashes, rejected proposals, regressions and no-effect results.

The first comparison uses the same total declared budget for agent-guided and fixed random search. Comparable budget includes successful and failed trial execution, proposal-agent inference, evaluator calls and setup charged by the study. Report component totals as well as the chosen aggregate; wall time, GPU time and money are not interchangeable.

Confirmation evidence is provisioned before search in a distinct trust domain. The proposal and execution workers cannot list, read, infer filenames for or mount confirmation data or evaluator code. A confirmation lease names the candidate, study revision, evaluator revision, permitted output and remaining query count. Every request consumes the ledger even if the candidate crashes or the response is lost, unless the accepted protocol defines and records a recoverable infrastructure exception.

Repeated adaptive comparisons increase false-positive risk. Before confirmation, the study defines which outcomes form one family and selects a method justified for that design. Benjamini–Hochberg is a useful primary reference for false-discovery-rate control under its stated conditions; it is not an automatic answer for arbitrary dependence or sequential adaptation. The reusable-holdout literature motivates guarded holdout reuse, but Research Continuum does not claim a valid reusable-holdout implementation. Until one is implemented and evaluated, use conservative one-shot or tightly bounded confirmation.

If confirmation feedback leads to a candidate change, the changed candidate is new. It cannot inherit the previous confirmation verdict. Exhausted or contaminated confirmation yields `HOLD` or a new reviewed study with new evidence; it does not unlock the raw holdout.

## Baselines, controls, ablations and reproduction

For the first campaign:

- establish the unchanged upstream-inspired training loop as an observable baseline after exact license/dependency/hardware review;
- include fixed random search over the same accepted search space and total resource budget;
- use paired inputs and seeds when this improves comparison without introducing dependence the analysis ignores;
- include a known-answer contract fixture before GPU work, and a deliberately invalid output the evaluator must reject;
- retain every accepted trial and protocol deviation;
- select finalists only from development evidence under the registered rule;
- run untouched confirmation within its fixed query budget;
- rebuild and rerun each claimed finalist from its retained bundle in a clean workspace by a separate worker;
- remove or neutralize each material change in planned ablations before attributing the effect to it.

The study must distinguish a failure to reproduce the number, a failure to reproduce its direction, a quality-constraint regression and an environment incompatibility. None may be silently collapsed into “close enough.” Tolerances come from numerical analysis, measurement precision or a declared domain reference before search.

## Trial acceptance and execution

Only an immutable accepted `TrialSpec` executes. It names owned candidate paths, adapter version, input bundle, seed, limits, required outputs and forbidden capabilities. Natural-language proposals are parsed into this contract and reviewed by policy; they are not shell scripts.

The planned worker uses a fresh workspace, explicit argument arrays, fixed environment, bounded scratch/output mounts and no network by default. It receives no personal credentials, browser/keychain state, SSH agent, cloud metadata access, coordinator database, evaluator source or unrelated repository paths. Dependencies and inputs are prepared through a trusted step and made read-only where supported. Candidate output remains untrusted until schema, type, size and safe-parser validation passes.

Trial terminal states:

- `EVALUATED`: valid declared outputs were scored on the named evidence partition;
- `INVALID`: outputs, model domain, invariants or protocol make the score unusable;
- `FAILED`: execution or infrastructure failed without a valid result;
- `CANCELLED`: a human, budget, policy or coordinator stop ended execution;
- `REJECTED`: the proposal never received authority to execute.

Metric direction comes from the accepted study: lower `val_bpb` is favorable in the first training study, while other adapters may maximize or constrain different metrics. An unfavorable valid estimate is retained as evidence; a valid but imprecise estimate may remain inconclusive under the predeclared decision rule. A crash, malformed output or invalid numerical result is not a zero-valued scientific observation. Invalid and failed attempts remain in cost and reliability reporting.

## Resource and allocation contract

Every accepted campaign defines hard resource ledgers and separate reservations. A future initial ceiling is proposed as one local worker, at most 20 trial attempts, at most two elapsed compute hours and 5 GiB of new artifacts. This is a planning bound, not execution or spending authority.

The first allocation baseline is fixed round-robin or fixed random allocation after reserving baseline, confirmation and reproduction capacity. Each accepted hypothesis receives a small exploration floor unless it violates an early stop. Remaining exploration may follow a versioned transparent policy. Successive halving, bandit methods, learned allocation or agent-written scheduler policies are later hypotheses evaluated against simple baselines on fresh campaigns. They never directly edit the active coordinator or increase its budget.

Stop one trial on unsafe behavior, missing rights, invalid input, limit breach, evaluator protocol violation or missing declared output. Stop or hold the campaign on:

- total budget exhaustion;
- evaluator or confirmation compromise;
- unrecoverable lineage/provenance gaps;
- confirmation query exhaustion or evidence contamination;
- repeated infrastructure failure above the study's declared tolerance;
- domain, safety, licensing or privacy boundary violation;
- no remaining hypothesis capable of changing the stated decision within the remaining budget.

`REDIRECT` creates a new question or study revision. `DESCOPE` narrows the domain or search space while preserving the core question. Neither rewrites the accepted protocol after results are known.

## Result and lineage bundle

Each attempt retains:

- accepted question, hypothesis, study and trial revision IDs;
- source/model/data records and permitted transformation lineage;
- baseline/candidate code reference and patch or generated artifact;
- pinned environment/dependencies, operating system, hardware, threads and determinism settings;
- actual seed, inputs and declared outputs;
- raw output, diagnostics, failure traces and protocol deviations;
- evaluator revision, evidence partition, valid/invalid decision and metrics with units;
- uncertainty/comparison calculation and multiple-comparison family membership;
- complete resource usage including proposal, failed execution and evaluator costs;
- worker/lease/attempt identity, timestamps and terminal state;
- parent/child derivation edges and reproduction/ablation links.

Completed bundles publish atomically after validation. Interrupted or oversized outputs are stored, when safe and useful, as explicitly partial diagnostics. A retry creates a new attempt and cannot overwrite a terminal result. Evidence lineage follows the semantics in [ARCHITECTURE.md](ARCHITECTURE.md); an artifact integrity digest may detect bundle mutation but does not establish scientific validity.

## Claim and publication contract

A `ResearchClaim` contains one exact claim, its target scope, support, contradictions, missing evidence, confirmation status, reproduction/replication status, limitations and reviewer decision. Claims must resolve to the complete applicable outcome set rather than a curated success subset.

A `PublicationBundle` is eligible for human review only when it includes:

1. the accepted question/hypothesis/study protocol and dated deviations;
2. complete baseline, candidate, null, negative, invalid and failed outcomes appropriate to the design;
3. search and confirmation separation, query counts and repeated-comparison treatment;
4. effect/metric estimates, uncertainty and quality constraints without selective endpoints;
5. ablations, independent reproduction and unresolved alternate explanations;
6. source/data/model/code rights and artifact inventory;
7. exact reproduction instructions and environment limits;
8. bounded claims, contradictions, negative outcomes and nonclaims;
9. named human scientific and release review.

The exporter may draft tables and prose only from graph-backed records. It cannot add unsupported novelty, causal, superiority, safety or real-world-effectiveness language. Manuscript generation never starts a campaign and publication count never allocates research resources. No publication is automatic.

## Domain-specific requirements

The common contract does not replace domain validity:

- **Training:** lawful corpus/tokenizer, train/development/confirmation separation, data contamination checks, seeds, compute parity and quality/performance metrics.
- **Inference:** fixed model/task quality, warmup, measurement repetitions, device/software identity, tail latency, memory and throughput tradeoffs.
- **Retrieval:** lawful corpus/query/judgment records, query-level split, index lineage, leakage controls and relevance uncertainty.
- **Data research:** provenance for every record/transformation, deduplication and benchmark-contamination checks, coverage/subgroup limitations and privacy review.
- **Numerical optimization:** governing objective/constraints, known-answer controls, residual/convergence checks, conditioning, precision, justified tolerance and invalid numerical states.

Research Continuum's generic evaluator can validate contracts and route evidence. A domain adapter and qualified reviewer decide whether a metric and model support the intended interpretation.

## Security and integrity tests required before claims

RC-004 and RC-005 must test representative attempts to read/write evaluator paths, traverse or symlink outside the workspace, enumerate credentials, reach the network/cloud metadata, spawn excess processes, exceed resource/output limits, smuggle executable serialized objects, probe confirmation data and alter accepted records or query counts. Tests must run against the supported platform isolation mechanism. A mocked denial or instruction-following demonstration is not containment evidence.

Evaluator errors fail closed. Any suspected leak marks affected confirmation evidence contaminated until reviewed. Workers never receive publication credentials, and no research task authorizes deployment, outreach, data acquisition or spending.

## Evidence limits

Primary methodological sources in [SOURCES.md](SOURCES.md) motivate provenance, guarded adaptive analysis, multiple-comparison planning, transparent ML reporting and independent artifact review. They do not validate this architecture or prescribe one universal statistical method. Every future result is limited by its study, data, evaluator, implementation, hardware and reviewer evidence.


## Numerical 0.1 protocol — frozen before execution

The executable example is [rosenbrock-study.json](examples/rosenbrock-study.json), explained in [decision 001](docs/decisions/001-numerical-study.md). The baseline is seeded uniform random search and the candidate is deterministic coordinate refinement. The public Rosenbrock objective has a directly checked zero at (1,1). Both arms receive 128 observations per attempt, with three development seeds and three different confirmation seeds. No state carries between trials. Reproduction capacity reruns both phases. Threshold and descriptive median comparison are frozen; no significance or generality is claimed. Candidate repetitions are identical deterministic checks.

All attempts, including failures, consume their entire admitted allowance conservatively; actual durable observations are counted separately. Recovery never refunds costs. Unequal charged costs or missing/invalid trials makes the comparison inconclusive. The complete ledger and report retain every outcome. A valid random-search advantage falsifies the candidate hypothesis and must remain visible.

The logical built-in evaluator API does not satisfy the protected hostile-code/holdout obligations of the original training programme. Public known-answer seeds are not secret confirmation data. Human/domain review and externally obtained release reproduction remain separately required evidence, never replaced by an agent walkthrough.

## Numerical 0.5 campaign protocol

The [workbench campaign](examples/workbench-campaign.json) freezes all nine
comparisons before execution. Rosenbrock, sphere and anisotropic quadratic each
receive random-baseline, fixed-step-ablation and grid-baseline studies. The
coordinate ablation removes only step halving, with identical objective, baseline,
seed plan, observation allowance and comparison rule. These are three numerical
fixtures, not evidence of three independent scientific domains.

Each study preserves the original development/confirmation/reserved-reproduction
separation. The whole campaign reserves 55,296 evaluation units for 27,648 clean
search observations and their permitted retries. All original failed attempts
remain charged and in the evidence. There is no adaptive selection between studies
or pooled ranking across objectives with different scales.

The frozen verdict remains the difference in confirmation medians at matched
aggregate costs. The additional uncertainty estimand is the median paired
candidate-minus-baseline best objective over the same confirmation seeds. A
2,000-resample, fixed-seed percentile interval describes resampling of eligible
observed pairs; it makes no population-coverage or significance guarantee.
Deterministic policy pairs receive no sampling interval. Incomplete or ineligible
comparisons keep their observations without an interval. Exact choices and
limitations are in [Decision 003](docs/decisions/003-numerical-workbench.md).

The [default evidence](evidence/workbench/default-campaign/index.html),
[fresh reproduction](evidence/workbench/reproduced-campaign/index.html) and
[retained recovery case](evidence/workbench/recovery-campaign/index.html) expose
all frozen studies. A baseline advantage, null outcome or cost-invalid comparison
is retained. These demonstrations do not satisfy the broader human-review,
training/agent-search, sandbox or independent scientific-validity contracts above.
