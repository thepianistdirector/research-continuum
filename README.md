# Research Continuum

**A reproducible autonomous research system that turns hypotheses into independently checked experiments.**

Build a general software research system, starting with AI, that can read approved sources, formulate hypotheses, design experiments, modify bounded code, execute under budgets, challenge its findings and preserve a usable body of evidence. Advance from a single optimization loop to multiple research questions and domains without allowing agents to rewrite the rules that judge them.

Created and maintained by **Lucas Santana** ([thepianistdirector](https://github.com/thepianistdirector)). [Tanduna project](https://tanduna.com/p/research-continuum) · [Public repository](https://github.com/thepianistdirector/research-continuum)

> **Starting from zero.** This repository currently contains project design, architecture and a contributor plan. No simulator, application, autonomous research system or benchmark result has been implemented here. All 24 build tasks are planned. Proposed capabilities below describe what we want to build.

## Who this is for

AI researchers, open-source research teams and engineers who want inspectable autonomous experimentation rather than an unsupervised stream of optimistic reports.

## First useful experiment

Reproduce a tiny bounded training-search loop and compare it with fixed random search under the same total budget. The producer may edit an experiment module; it cannot edit the evaluator or access the final holdout. A separate worker reruns any claimed improvement. A successful first result can be a clear negative finding with full evidence.

Software experiments make it possible to compare ideas repeatedly, inspect failures and share reproducible evidence without operating physical systems. They remain bounded by the quality and applicability of their models. A convincing visualization or agent report is not independent validation.

## What we want to build

### Research question and source graph

Track questions, source versions, hypotheses, assumptions, experiments, evidence and unresolved contradictions with exact citations and human-readable IDs.

### Experiment-design agents

Propose interventions, controls, metrics, expected outcomes and falsifiers. Compare agent decisions with simple search baselines.

### Sandboxed implementation and execution

Bounded patches, isolated workspaces, fixed dependencies, denied network by default, independent budgets and explicit cancellation.

### Protected evaluation and replication

Separate development feedback from sealed holdouts; independent execution, ablations and negative-result preservation.

### Research portfolio and domain adapters

Start with small AI training/inference experiments, then retrieval, optimization or simulation adapters with their own safety contracts. Generality is earned by distinct reproductions.

## Architecture in one paragraph

Use a Python coordinator backed initially by SQLite, a filesystem artifact store and isolated subprocess workers. The durable research state machine tracks proposed, accepted, queued, running, evaluated, replicated, rejected, failed and cancelled experiments. Producer workspaces never mount evaluator source, hidden test data, credentials or the coordinator database. A narrow evaluator service returns permitted development feedback; final confirmation has a bounded query count and a separate worker. A typed domain adapter exposes prepare, run, evaluate and reproduce operations. Agents can suggest search-policy changes as a new research proposal but cannot mutate budgets, permissions, metric definitions or accepted evidence.

Agents propose and interpret experiments; numerical engines and protected evaluators determine results. Every experiment retains its inputs, assumptions, source version, environment, resource budget and failure state.

## Build plan

| Wave | Outcome | Gate |
| --- | --- | --- |
| 1 | Research contract and baseline | One question, budget and falsification protocol are fixed. |
| 2 | Isolation and protected evaluation | The producer cannot tamper with the rules or retained evidence. |
| 3 | First autonomous research loop | A real bounded AI experiment is compared with simple search. |
| 4 | Scientific reliability | Promising results withstand replication and alternate explanations. |
| 5 | General AI research adapters | The same contract works beyond one training script. |
| 6 | Research memory and allocation | Longer campaigns learn without rewriting established evidence. |
| 7 | Research workbench and distributed runs | Humans can inspect and interrupt a recoverable research program. |
| 8 | Independent research-system preview | Generality and value are demonstrated rather than advertised. |

Read the [roadmap](ROADMAP.md), [24 contributor tasks](TASKS.md), [architecture](ARCHITECTURE.md), [experiment and evaluation contract](EXPERIMENTS.md), [sources and data policy](SOURCES.md) and [current state](STATUS.md). All waves are future work; a plan is not execution authorization.

## Scientific and operating boundaries

Agents cannot alter evaluator code, holdouts, scoring rules, accepted results, permissions or resource ceilings. Protect holdouts in a separate execution trust domain; a read-only file inside the producer workspace is insufficient. Sources and tool output are untrusted inputs. No unattended publication, outreach, cloud spend, credential use or deployment. Domain expansion must reject harmful biological design, surveillance/profiling and other prohibited tasks rather than treating software simulation as a blanket exception.

If agent-guided search does not beat equal-budget simple baselines, publish that result and improve the method before adding more agents. Stop a campaign on budget exhaustion, evaluator compromise, unrecoverable provenance gaps or out-of-scope work. Never discard failed trials to manufacture progress.

## Contribute

Start with [CONTRIBUTING.md](CONTRIBUTING.md). The next eligible work is the first benchmark/contract task. Implementation follows review of exact dependency choices and a maintainer-accepted bounded task. There are no install or runtime commands yet; do not interpret proposed paths or commands as an existing application.

## Related independent projects

- [Vital Rehearsal](https://github.com/thepianistdirector/vital-rehearsal): An open simulation laboratory for physiology, disease research and safer care workflows.
- [Grid Horizons](https://github.com/thepianistdirector/grid-horizons): Simulate better grids, transformers and energy systems before proposing physical changes.
- [Earth Rehearsal](https://github.com/thepianistdirector/earth-rehearsal): A software laboratory for cleaner water, less pollution and testable climate interventions.
- [Civic Safelab](https://github.com/thepianistdirector/civic-safelab): Test public-safety sensing in synthetic worlds while measuring privacy and false alarms.
- [Lean Model Lab](https://github.com/thepianistdirector/lean-model-lab): Find reproducible training and inference efficiency gains without hiding quality tradeoffs.

These repositories are independently buildable. Shared experiment formats are a design intention; there is no shared service or integration implemented today. Extract a common library only after two real implementations demonstrate the need.

## License

Original repository content is licensed under **AGPL-3.0-only**; see [LICENSE](LICENSE). Third-party data, models, papers and code retain their own terms and are not relicensed by this repository. No third-party dataset, model weights or upstream implementation is bundled in this initial planning release.
