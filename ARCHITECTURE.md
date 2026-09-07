# Research Continuum architecture

Status: proposed design, no implementation. Owner: Lucas Santana. Version: initial plan, 2026-09-07.

## Scientific boundary and adapters

Use a Python coordinator backed initially by SQLite, a filesystem artifact store and isolated subprocess workers. The durable research state machine tracks proposed, accepted, queued, running, evaluated, replicated, rejected, failed and cancelled experiments. Producer workspaces never mount evaluator source, hidden test data, credentials or the coordinator database. A narrow evaluator service returns permitted development feedback; final confirmation has a bounded query count and a separate worker. A typed domain adapter exposes prepare, run, evaluate and reproduce operations. Agents can suggest search-policy changes as a new research proposal but cannot mutate budgets, permissions, metric definitions or accepted evidence.

Karpathy's autoresearch is an inspiration and comparison baseline, not a dependency or claim of affiliation. Its public design centers on a compact training loop and fixed evaluation budget. This project proposes broader adapters, protected evaluation, replication and cost accounting; superiority must be demonstrated. Use simple local process orchestration before considering a workflow framework. No upstream code is copied in this planning release.

Referenced engines are candidates for a version-specific evaluation, not installed or approved production dependencies. Wave 1 records the exact official source/version/license, maintenance and advisory review, runtime/transitive behavior, telemetry/data implications, alternatives and rollback before adoption. Prefer the smallest viable local stack; do not introduce Kubernetes, a vector database, a workflow platform or a model provider merely to create infrastructure.

## Experiment flow

```mermaid
flowchart LR
  A[Approved public sources or synthetic inputs] --> B[Source and scenario validation]
  B --> C[Accepted experiment specification]
  H[Human or bounded proposal agent] --> C
  C --> D[Budget and scope gate]
  D --> E[Isolated domain adapter]
  E --> F[Protected numerical and quality evaluator]
  F --> G[Recorded results and limitations]
  G --> I[Independent reproduction]
  I --> J[Research report]
```

This diagram describes the planned system. A producer cannot edit its evaluator, overwrite accepted results or extend its own budget. Source text and model output are untrusted data, never permission to execute code or change project rules.

## Components and ownership

| Component | Owns | Does not own |
| --- | --- | --- |
| Input catalog | Exact public source reference, date/version, license, units and permitted transformations | Silent data scraping or access to private records |
| Scenario contract | Inputs, supported ranges, initial/boundary conditions, comparison arms and seeds | Numerical claims outside the model card |
| Coordinator | Scheduling, state transitions, cancellation and resource accounting | Scientific truth or automatic publication |
| Domain adapter | Engine-specific conversion, execution and raw diagnostics | Metric definitions and permission changes |
| Evaluator | Predeclared invariants, metrics, holdouts and invalidity decisions | Editing the candidate to make it pass |
| Artifact store | Immutable completed run bundles and explicit partial/failed results | Personal credentials or hidden data copies |
| Report/workbench | Inspectable comparisons, uncertainty, limitations and source links | Invented outcomes or unlabeled simulations |

Use a local Python command-line coordinator and filesystem bundles first. SQLite is appropriate when durable multi-run scheduling becomes necessary. Keep JSON for contracts and small metadata, CSV for simple numeric tables, and introduce a larger-array format only when the data warrants it. Numerical engines may use C/C++ or other languages behind process adapters. Select exact language/runtime versions in the first implementation task after compatibility checks.

## Planned repository map

```text
src/                 coordinator, contracts, evaluation and reports
adapters/            independently testable domain engines
scenarios/           lawful public or synthetic scenarios
benchmarks/          fixed numerical references and confirmation cases
tests/               behavior, failure and boundary checks
apps/workbench/      later local comparison interface
docs/                domain decisions and scientific interpretation
```

These directories are proposed owned scopes, not existing software. The project starts as documentation only. Early tasks establish an actual runnable skeleton and exact verification commands before downstream implementation begins.

## Shared data contracts

- `SourceRecord`: human-readable ID, provider URL, version/date, license, permitted use, transformations, coverage, quality limitations and whether redistribution is allowed.
- `ModelCard`: engine/version, governing assumptions, variables/units, supported ranges, calibration evidence, validation cases, numerical tolerances, invalid states and prohibited interpretations.
- `ExperimentSpec`: ID, question, model/scenario versions, source references, parameters, seeds, baseline/candidate, metrics, quality constraints, acceptance/falsification rule, allowed adapter and compute/storage limits.
- `RunResult`: spec ID, repository commit, environment, actual seed, start/end, raw artifact paths, diagnostics, measured/modelled status, metrics, uncertainty, cost and terminal state.
- `ResearchClaim`: exact statement, supporting and contradicting run/source references, applicability, limitations, reproduction status and reviewer decision.

The persisted contract uses explicit schema versions and rejects unknown execution fields. Units are machine-readable and must be converted at a named boundary. A run records seeds, solver settings, thread count, hardware and tolerances: stochastic reproducibility and floating-point equivalence are distinct from bitwise determinism.

## Execution and recovery

Lifecycle: `PROPOSED -> ACCEPTED -> QUEUED -> RUNNING -> EVALUATED -> REPLICATED` with `REJECTED`, `INVALID`, `FAILED` and `CANCELLED` terminal alternatives. A low score is a valid negative result; a numerical failure is invalid evidence and must not become a favorable score.

Write outputs into a run-specific temporary directory and publish the result atomically only when required outputs validate. Preserve partial diagnostics after interruption. Retries use the same logical run ID and cannot overwrite a completed result. At restart, reconcile running subprocesses, recorded costs and worker ownership before scheduling. Cancellation must terminate the subprocess tree and mark its artifacts and cost state explicitly.

Workers receive only the accepted scenario, pinned engine environment and bounded scratch/output locations. Deny network by default after input preparation, omit personal credentials and limit CPU/GPU time, memory, disk and subprocess count. Use process argument arrays rather than shell interpolation. Model weights and serialized objects require safe loading; no arbitrary remote-code trust. Separate contributor code from evaluator and release credentials.

## Evaluation and domain invariants

Independently replicated improvement per compute/cost budget; full experiment cost including agent inference and failures; reproducibility rate; invalid experiment rate; evaluator leakage incidents; evidence citation accuracy; negative-result retention; time to a supported answer. Publications, agent messages and raw experiment count are not success metrics.

Agents cannot alter evaluator code, holdouts, scoring rules, accepted results, permissions or resource ceilings. Protect holdouts in a separate execution trust domain; a read-only file inside the producer workspace is insufficient. Sources and tool output are untrusted inputs. No unattended publication, outreach, cloud spend, credential use or deployment. Domain expansion must reject harmful biological design, surveillance/profiling and other prohibited tasks rather than treating software simulation as a blanket exception.

Tolerances are justified from numerical analysis, source precision or a domain reference before candidate search. Calibrate on development evidence and confirm on reserved cases. Save all candidate attempts, including failure, and report comparison uncertainty; do not tune repeatedly against a supposedly independent final holdout.

## Scale and integration decisions

Prove one local experiment first. Add batch workers only after replay, cancellation and duplicate prevention pass; add distributed runs only when measured elapsed time justifies the complexity. No cloud resource is provisioned by this plan. Future Tanduna contributions remain ordinary reviewed GitHub changes. An optional Research Continuum integration uses versioned experiment contracts and cannot bypass this project's evaluator or safety policy.

## Risks and cut order

If agent-guided search does not beat equal-budget simple baselines, publish that result and improve the method before adding more agents. Stop a campaign on budget exhaustion, evaluator compromise, unrecoverable provenance gaps or out-of-scope work. Never discard failed trials to manufacture progress.

Cut photorealism and polished dashboards first, distributed execution second, and additional scientific domains third. Preserve the first reproducible experiment, source rights, evaluation integrity and bounded claims. Revisit architecture only when a measured limitation or failed benchmark justifies it.
