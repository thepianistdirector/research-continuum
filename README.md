# Research Continuum

**Run a bounded computational study. Keep the entire evidence trail.**

Research Continuum 0.1 compares seeded uniform random search with fixed coordinate refinement on a public, known-answer two-dimensional Rosenbrock objective. You freeze a question and protocol, run finite trials, inspect failures and costs, recover interruptions, and export a report with replayable raw evidence.

Created and maintained by **Lucas Santana** ([thepianistdirector](https://github.com/thepianistdirector)). [Tanduna campaign](https://tanduna.com/projects/research-continuum) · [Source repository](https://github.com/thepianistdirector/research-continuum)

**Release status:** [0.1.0 is publicly available](https://github.com/thepianistdirector/research-continuum/releases/tag/v0.1.0). All four release assets were downloaded without credentials and match the approved checksums. Independent external-host execution, human/qualified review, and native Tanduna publication remain pending. See [STATUS.md](STATUS.md) for the separate evidence levels.

Download the [source archive](https://github.com/thepianistdirector/research-continuum/releases/download/v0.1.0/research-continuum-0.1.0.tar.gz) and [SHA256SUMS](https://github.com/thepianistdirector/research-continuum/releases/download/v0.1.0/SHA256SUMS). The archive's SHA-256 is `72027ecd84a06d20445e9fd6d604dee2393b03d78255f679652e2f331585bc3b`. Extract it and follow the commands below from `research-continuum-0.1.0`. The immutable archive retains the preparation-time status; this repository records subsequent publication evidence.

## Run a study

Use Linux and Python 3.12 or newer. The currently verified environment is Linux x86_64 with Python 3.12.14 and SQLite 3.53.1. Other environments are unverified. There is no pip install, model, dataset, network or paid compute requirement. Run these commands from the source archive's extracted directory:

```bash
python3 -m continuum --version
python3 -m continuum study --out my-study.json
```

Read `my-study.json` before accepting it. The [protocol decision](docs/decisions/001-numerical-study.md) explains every field, the hypothesis and its falsifier. The default freezes 128 objective evaluations per policy, development seeds 11/22/33 and confirmation seeds 101/202/303. Reserved reproduction runs replay both phases.

```bash
python3 -m continuum init --study my-study.json --db runs/study.sqlite
python3 -m continuum run --db runs/study.sqlite --pause-after 1
python3 -m continuum resume --db runs/study.sqlite
python3 -m continuum inspect --db runs/study.sqlite
python3 -m continuum evaluate --db runs/study.sqlite
```

The deliberate pause gives you a chance to inspect progress. You can also interrupt with Ctrl+C and resume the same database. Every admitted attempt retains its full charge. A process killed before validated staging becomes a failed attempt and may receive one separately charged retry; a validated staged result is finalized exactly once. Exhausted retries remain visible. Another active coordinator cannot take the same campaign lock.

```bash
python3 -m continuum inspect --db runs/study.sqlite --json > full-ledger.json
python3 -m continuum export --db runs/study.sqlite --out evidence/my-study
python3 -m continuum verify --bundle evidence/my-study
python3 -m continuum reproduce --bundle evidence/my-study --db runs/reproduced.sqlite --record evidence/reproduction.json
```

Open `evidence/my-study/report.html` in a browser. The standalone report uses no remote assets or scripts. The bundle includes the frozen protocol, every trial/attempt/observation/event, derived evaluations, contradiction links, reproduction records, limitations and a checksummed manifest. `reproduce` executes the study in a new campaign and writes a new record; it does not reuse a cached verdict. If interrupted, repeat the reproduction command with its pre-bound database. If trials already finished but record publication failed, this reconciles the missing record and explicitly claims no additional execution. An unrelated cached campaign cannot be adopted as reproduction; choose a new database for a new run.

Commands refuse to overwrite accepted databases, bundles or output records. Keep interrupted evidence and choose a new output name when an existing artifact must be preserved. Database corruption, evaluator changes and runtime changes fail closed; use the original unchanged release to resume. A bundle is data, never a source of shell commands or executable plugins.

## Read the answer honestly

The descriptive verdict can be `CANDIDATE_LOWER`, `BASELINE_LOWER`, `TIE` or `INCONCLUSIVE`. A baseline advantage is a valid outcome against the candidate hypothesis. The quality threshold (best objective at most 0.01) is a separate proximity diagnostic. Unequal charged costs, incomplete trials or failed reproduction prevent a complete comparison.

The included [default study report](evidence/runtime/default-study/report.html) records **BASELINE_LOWER**: confirmation median best objective 0.25900796897177875 for random search and 4.655312582291663 for coordinate refinement. Neither reaches the 0.01 threshold. All 24 trials complete, including 12 reserved reproduction runs, with 3,072 search evaluations and matching reproduction traces. This is evidence against the frozen candidate hypothesis for this fixture.

The fixture is public. Its minimum at (1,1) is directly checkable from two nonnegative square terms. Confirmation uses fresh frozen seeds, not secret holdout data. Coordinate refinement is deterministic: repeated candidate runs are implementation checks, not independent stochastic samples. These results do not establish statistical significance, novelty, general optimizer superiority, performance versus autoresearch, or an autonomous scientist.

Counts distinguish reserved allowance, conservatively charged attempt units, recorded search evaluations and initial controls. Validation and report generation recompute evidence as operator-requested audit work; they are not additional adaptive policy feedback. Trial CPU/wall measurements are separate from command startup and audit overhead. Unknown interrupted duration stays unknown.

## Create a different supported study

Edit a **new draft** and use a new study revision/database. Version 1 permits bounded question text, domain/start/step, threshold, evaluation allowance and seed lists. The rectangle stays within `[-10,10]²` and contains the controls; each phase has 1–16 disjoint seeds and each run has 8–4096 evaluations. Aggregate clean search work, including reproduction, cannot exceed 65,536 evaluations. Policies, objective, retry limit, timeout, feedback and comparison rules are fixed. Unknown fields, expressions, booleans as numbers and non-finite values are rejected.

Reviewed built-ins run in one trusted local process. The API supplies no ledger or evaluator-mutation capability to policies. This is **not an adversarial sandbox**. Arbitrary contributed code, protected holdouts, remote workers, LLMs and credential access are outside 0.1.

## Build and verify the source package

```bash
python3 tools/validate_plan.py --self-test
python3 -m unittest discover -s tests -v
python3 tools/build_release.py --out .build/research-continuum-0.1.0.tar.gz
```

The tests include actual killed coordinator processes and forged-evidence rejection. They do not replace independent scientific review, human accessibility observations or publicly obtained artifact verification. Build into a new filename if a previous archive exists.

## The longer programme

The [canonical roadmap](ROADMAP.md) and [task contracts](TASKS.md) retain training/inference/retrieval research, protected evaluation, agent proposals, ablations, research memory, finite allocation, accessible workbench, remote workers and multi-domain evaluation as later outcomes. [Architecture](ARCHITECTURE.md) and [experiment requirements](EXPERIMENTS.md) preserve those boundaries.

The original 27 source entries remain mapped with immutable lineage; the three completed foundation entries describe documentation/tooling. Historical RC-001–RC-024 remain PLANNED. The numerical 0.1 does not complete historical training/agent-search, hostile-code isolation, or broad numerical adapter-generality requirements. [Autoresearch source analysis](docs/baselines/autoresearch-2026-09-07.md) preserves the exact inspiration and unresolved code-reuse rights. No upstream implementation is reused.

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SOURCES.md](SOURCES.md). Original material is **AGPL-3.0-only**, with the full [license](LICENSE). No third-party runtime binaries, weights, datasets or upstream source are bundled. Research Continuum owns no sibling project's roadmap or infrastructure.
