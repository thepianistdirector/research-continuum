# Research Continuum

**A local-first research system for turning questions into bounded studies, independently checked experiments and durable evidence.**

Research Continuum is an ambitious general software research project, starting with AI training, inference, retrieval, data and numerical optimization. It is designed to let people and coding agents explore hypotheses without letting the same agent rewrite the budget, evaluator, confirmation evidence or research record that judges its work.

Created and maintained by **Lucas Santana** ([thepianistdirector](https://github.com/thepianistdirector)). [Tanduna project](https://tanduna.com/p/research-continuum) · [Public repository](https://github.com/thepianistdirector/research-continuum)

> **Architecture foundation completed.** The three Wave 0 tasks are **DONE**: the architecture contract, outcome/dependency roadmap, and executable next-work packet with a standard-library plan validator. The original 24 scientific/build tasks remain **PLANNED**. No simulator, model integration, application, autonomous research runtime or scientific result is implemented. Acceptance and reproduced checks are recorded in [STATUS.md](STATUS.md).

## The research programme

The core object is a research question, not a patch loop or a manuscript. A future campaign should connect:

```text
sources -> question -> competing hypotheses -> accepted study design
        -> controlled trials -> development search -> bounded confirmation
        -> independent reproduction and ablation -> qualified claim package
```

Each link is versioned and inspectable. The study declares its baseline, controls, search space, falsifier, metrics, uncertainty method, multiple-comparison policy, quality constraints and finite resource budget before confirmation. Negative, inconclusive, invalid and failed outcomes remain visible. A generated explanation is an interpretation, not evidence.

## Inspired by autoresearch, designed for a broader question

[Karpathy's autoresearch](https://github.com/karpathy/autoresearch/tree/228791fb499afffb54b46200aca536f79142f117) is the first comparison baseline and an important design inspiration. Its current official repository uses a compact single-GPU nanochat setup: an agent changes one `train.py`, fixed `prepare.py` code supplies data/evaluation, every trial receives five minutes, lower validation bits per byte wins, and results are kept, discarded or marked as crashes. That is a sharp, reviewable optimization loop.

Research Continuum proposes to retain that small-loop discipline while testing a different system around it:

- multiple versioned questions and competing hypotheses rather than one cumulative branch alone;
- study designs with baselines, controls, ablations and reproduction contracts;
- development search separated from protected, query-limited confirmation;
- adapters for training, inference, retrieval, data research and numerical optimization;
- durable campaign state, atomic results, cost accounting, cancellation and restart recovery;
- untrusted proposal/code/data isolation from evaluators, credentials and unrelated networks/files;
- explicit allocation, stop, pivot and scale policies under finite budgets;
- evidence packages that can support a reviewed publication later, rather than paper generation as the objective.

These are proposed extensions. The project has not reproduced autoresearch, shown a superior method, demonstrated generality or produced research evidence. The inspected upstream revision and licensing unknowns are recorded in [SOURCES.md](SOURCES.md).

## First useful experiment

The first integrated milestone is to reproduce a tiny bounded training-search loop and compare it with fixed random search under the same total budget. A proposal worker may edit one accepted experiment module. It cannot access or change the final evaluator, confirmation cases, accepted evidence or resource ceilings. A separately prepared worker reruns every claimed finalist.

The result can be “agent-guided search showed no confirmed advantage.” That is a successful research-system exercise if the controls, complete outcome record, costs, limitations and reproduction are credible.

Before any GPU experiment, Wave 1 must resolve the exact upstream source/license, dependency/data terms, compatible hardware, resource allocation and evaluator boundary. No GPU, cloud resource, paid model or dataset download is authorized by this plan.

## Planned architecture

The bounded local-first design begins with Python standard-library contracts, filesystem bundles and one coordinator writer. SQLite becomes a likely local index only when durable scheduling needs transactions. A candidate runs in a fresh bounded workspace with network denied by default and no evaluator source, confirmation data, personal credentials, coordinator database or unrelated files mounted. A distinct evaluator identity returns only protocol-approved development or confirmation results.

The planned registry tracks immutable revisions and events for questions, hypotheses, studies, trials, evaluations, reproductions and claims. Completed result bundles publish atomically; interrupted attempts retain clearly labelled partial diagnostics. Finite campaign budgets cover trial count, wall time, CPU/GPU, storage, evaluator queries, agent inference and monetary cost. Exploration cannot consume confirmation or reproduction reserves.

Remote workers, workflow platforms and distributed storage are deliberately later decisions. They require evidence that local replay, cancellation, isolation, fencing, budget accounting and concurrent scheduling work and that measured workload justifies the operational cost. See [ARCHITECTURE.md](ARCHITECTURE.md) for the trust zones, state machines, adapter interface and scale gates.

## Build plan

| Wave | Outcome | Gate |
| --- | --- | --- |
| 0 | Architecture and research-programme foundation | The proposed contract, outcome roadmap and next local packet are coherent and accepted by the active root under delegated authority. |
| 1 | Research contract and baseline | One question, budget and falsification protocol are fixed. |
| 2 | Isolation and protected evaluation | The producer cannot tamper with the rules or retained evidence under the supported threat model. |
| 3 | First autonomous research loop | A real bounded AI experiment is compared with simple search. |
| 4 | Scientific reliability | Promising results withstand protected confirmation, reproduction and alternate explanations. |
| 5 | General AI research adapters | The same contract works beyond one training script without erasing domain constraints. |
| 6 | Research memory and allocation | Longer campaigns learn from retained evidence without rewriting it or self-allocating resources. |
| 7 | Research workbench and distributed runs | Humans can inspect, pause and recover a research programme before remote scale. |
| 8 | Independent research-system preview | Generality, safety and value are demonstrated on exact evidence rather than advertised. |

Wave order expresses dependencies, not dates. Read the [outcome roadmap](ROADMAP.md), [27 task contracts](TASKS.md), [experiment and evaluation contract](EXPERIMENTS.md), [sources and data policy](SOURCES.md) and [current state](STATUS.md).

## Executable next packet

After maintainer acceptance of Wave 0, RC-001 is a documentation and source-analysis packet that can run without paid compute, model weights or dataset downloads. It will create a precise autoresearch baseline record from the pinned official revision, inventory its mutable/fixed boundaries and observable protocol, resolve or escalate licensing ambiguity, and define the smallest later reproduction target. It will not run the GPU benchmark.

The current planning contract can be checked with the system Python:

```bash
python3 tools/validate_plan.py
python3 tools/validate_plan.py --self-test
```

The second command proves the validator rejects a syntactically valid but missing dependency and a malformed in-memory plan without crashing. These commands validate repository planning consistency only; they do not validate the proposed architecture or any scientific claim.

## Scientific and operating boundaries

Agents cannot alter evaluator code, confirmation evidence, scoring rules, accepted records, permissions or resource ceilings. Source text, model output, candidate code, datasets and serialized artifacts are untrusted inputs. No unattended publication, outreach, cloud spend, credential use, production deployment or physical-system action is permitted.

Repeated development selection is accounted for; untouched confirmation is query-limited and separate. Statistical choices depend on each study's sampling and dependency structure. No generic significance threshold or correction establishes validity. The system must preserve null and adverse outcomes and stop on budget exhaustion, evaluator compromise, unrecoverable provenance, missing rights or out-of-domain work.

No autonomous recursion is unlimited. Proposed scheduler or “research org” changes are versioned hypotheses evaluated on fresh campaigns under a declared budget. Publication export follows supported claims and human review; publication count is not a success metric.

## Six independent laboratories

Research Continuum may eventually exchange versioned experiment and evidence bundles with [Lean Model Lab](https://github.com/thepianistdirector/lean-model-lab), [Vital Rehearsal](https://github.com/thepianistdirector/vital-rehearsal), [Grid Horizons](https://github.com/thepianistdirector/grid-horizons), [Earth Rehearsal](https://github.com/thepianistdirector/earth-rehearsal) and [Civic Safelab](https://github.com/thepianistdirector/civic-safelab).

They remain six independently buildable repositories with their own evaluators, safety rules, source rights and claims. There is no shared service, monorepo, database or package dependency today. A common library is considered only after two real implementations expose the same costly duplication and maintainers accept the coupling.

## Contribute

Start with [CONTRIBUTING.md](CONTRIBUTING.md). The next implementation/research task is gated on Wave 0 review and RC-001. There are no install or experiment-runtime commands yet; proposed paths and interfaces are not existing software.

Original repository content is licensed under **AGPL-3.0-only**; see [LICENSE](LICENSE). Third-party data, models, papers and code retain their own terms and are not relicensed here. No third-party dataset, weights or upstream code is bundled in this foundation candidate.
