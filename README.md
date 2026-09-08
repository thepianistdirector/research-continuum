# Research Continuum

**Run bounded numerical campaigns. Keep the entire evidence trail.**

Research Continuum 0.5 is a local research workbench for frozen numerical studies:
three known-answer objectives, random and grid baselines, coordinate-search
ablations, explicit seed uncertainty, interruption recovery, and portable evidence
that another execution can reproduce. An offline browser connects each question
to its outcomes, trials, attempts, costs and recorded points.

Created and maintained by **Lucas Santana**
([thepianistdirector](https://github.com/thepianistdirector)).
[Tanduna campaign](https://tanduna.com/projects/research-continuum) ·
[Source repository](https://github.com/thepianistdirector/research-continuum).

**0.5 status:** the local candidate is implemented and runtime verified: 76 tests,
the complete nine-study packaged workflow, fresh MATCH reproduction, real process-death
recovery and eleven browser interaction checks. [Open the included workbench](evidence/workbench/default-campaign/index.html)
or read the [verification record](evidence/workbench/packaged-preflight.json).
The owner-approved [0.5.0 release](https://github.com/thepianistdirector/research-continuum/releases/tag/v0.5.0) is public; [all four assets were anonymously downloaded and verified](evidence/public-release-0.5.json). The [public 0.1.0 release](https://github.com/thepianistdirector/research-continuum/releases/tag/v0.1.0)
remains available and immutable. Independent human/qualified review and native
Tanduna publication remain separate unfinished gates. See [STATUS.md](STATUS.md)
and the [owner-selected 0.5 goal](docs/GOAL-0.5.md).

## Run a campaign

Use **Linux and Python 3.12 or newer**, from this source directory. There is no pip
install, network access, account, model, dataset or paid compute requirement. The
current local execution environment is Linux x86_64, Python 3.12.14 and SQLite
3.53.1. Claimed environments and actual verification are recorded separately in
STATUS.md; native macOS and Windows are not supported.

```bash
python3 -m continuum --version
python3 -m continuum campaign --out my-campaign.json
```

Read the draft before accepting it. Its nine studies cover Rosenbrock, sphere and
ellipsoid. For each objective, coordinate refinement is compared with random
search; a fixed-step variant removes step halving; a separate study compares with
grid search. The entire campaign freezes **216 trials**, **27,648 clean search
evaluations** and **55,296 reserved units**, including separately charged retries.

```bash
python3 -m continuum campaign-init --plan my-campaign.json --dir runs/my-campaign
python3 -m continuum campaign-run --dir runs/my-campaign --pause-after 2
python3 -m continuum campaign-inspect --dir runs/my-campaign
python3 -m continuum campaign-resume --dir runs/my-campaign
python3 -m continuum campaign-export --dir runs/my-campaign --out evidence/my-campaign
python3 -m continuum campaign-verify --bundle evidence/my-campaign
```

Open `evidence/my-campaign/index.html` in your browser. Search and filter studies,
inspect a trial, compare attempts, and expand every recorded point and value.
Campaign totals always include the whole inventory. Full study reports, ablation
contrasts and raw evidence remain linked. No web server or remote asset is used.

```bash
python3 -m continuum campaign-reproduce --bundle evidence/my-campaign --dir runs/fresh-reproduction --record evidence/campaign-reproduction.json
```

This executes fresh work bound to the exact source bundle. It rejects unrelated
cached campaigns and retains unsuccessful outcomes and runtime differences.
If interrupted, repeat the command with the same directory. Accepted inputs and
output records are never overwritten. Keep every source-bound database and bundle
with its original unchanged release; use 0.1.0 to inspect or resume 0.1 evidence.

See the [complete workbench guide](docs/workbench.md) for recovery, command exit
codes, protocol limits, single-study commands and new campaign drafts.
[Decision 003](docs/decisions/003-numerical-workbench.md) documents the formulas,
policies, ablation controls and uncertainty method.

## Read results within their limits

The descriptive verdict is `CANDIDATE_LOWER`, `BASELINE_LOWER`, `TIE` or
`INCONCLUSIVE`. It compares confirmation medians at equal retained costs and
requires complete original trials and matching reserved replay. The quality
threshold is a separate diagnostic. Failures and null results stay in the ledger.

Uncertainty describes paired differences over the chosen confirmation seeds. A
fixed bootstrap provides a **descriptive resampling interval**, not a population
confidence or significance guarantee. Repeated grid and coordinate runs are
deterministic checks; they do not become independent stochastic samples. Different
objective scales are never pooled into a single winner.

Ablations freeze one computational change and retain the same baseline, objective,
budget and seeds. Every study receives only its own observations. Reviewed
built-ins execute in one trusted local process; this is not an adversarial sandbox.
The system does not run LLM agents, training workloads, arbitrary plug-ins or remote
workers, and it makes no general optimizer-superiority or autonomous-scientist claim.

## Verify and package

```bash
python3 tools/validate_plan.py --self-test
python3 -m unittest discover -s tests -v
python3 tools/build_release.py --out .build/research-continuum-0.5.0.tar.gz
```

The archive builder refuses an existing destination. Tests cover real process
kills, retained costs, frozen-inventory tampering, derived-evidence forgery and
cached-reproduction rejection. They do not replace independent scientific review,
human accessibility observations or public-download verification.

## Programme and history

The [roadmap](ROADMAP.md), [task contracts](TASKS.md) and [canonical plan](plan/tasks.json)
retain 228 outcomes and all 27 original source identities. The selected 0.5 workbench
makes bounded progress on later numerical, ablation, reporting, reproduction and
interface outcomes; it does not silently complete their broader historical
training, adaptive-search or independent-review requirements.

[Architecture](ARCHITECTURE.md) · [Experiment contracts](EXPERIMENTS.md) ·
[0.1 documentation](docs/releases/0.1.0.md) · [Contribution guide](CONTRIBUTING.md) ·
[Sources](SOURCES.md).

Original material is **AGPL-3.0-only**, with the full [license](LICENSE). No
third-party runtime binaries, models, weights, datasets or upstream implementation
are bundled. Research Continuum owns no sibling project's infrastructure or plan.
