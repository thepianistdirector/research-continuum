# Local research workbench

The 0.5 workbench runs a frozen inventory of numerical studies and keeps every
result, failed attempt and cost. It uses Python's standard library and works
without network access, accounts, model services or a package installation.

## First campaign

From the extracted source directory, use Linux and Python 3.12 or newer:

```bash
python3 -m continuum --version
python3 -m continuum campaign --out my-campaign.json
```

Read the draft before accepting it. The default has nine studies: Rosenbrock,
sphere and ellipsoid, each comparing coordinate refinement with uniform random
search, a fixed-step coordinate ablation against the same random baseline, and a
coordinate-versus-grid comparison. Each study uses 128 evaluations per policy,
three development seeds and three disjoint confirmation seeds. Fresh reserved
reproduction trials repeat every original trial. The complete campaign has 216
logical trials, 27,648 clean search evaluations, and 55,296 reserved units including
one retry per trial. Eighteen initial control evaluations are additional.

```bash
python3 -m continuum campaign-init --plan my-campaign.json --dir runs/my-campaign
python3 -m continuum campaign-run --dir runs/my-campaign --pause-after 2
python3 -m continuum campaign-inspect --dir runs/my-campaign
python3 -m continuum campaign-resume --dir runs/my-campaign
python3 -m continuum campaign-export --dir runs/my-campaign --out evidence/my-campaign
python3 -m continuum campaign-verify --bundle evidence/my-campaign
```

Open `evidence/my-campaign/index.html` directly in a browser. No web server is
needed. Search by study, question or policy; filter objectives and outcomes; sort
by charged cost; inspect a study, choose a trial, and open an attempt's complete
point/value table. The best-so-far curve describes only that selected attempt.
Selections have stable local URL fragments; the trial link can be bookmarked or copied. Every card links to a standalone study report with its complete ledger, protocol,
controls, provenance and evidence-linked claim. Without JavaScript, study cards,
ablations, limitations and full-report links remain available.

The browser is a read-only view of exported evidence. Filtering never changes the
frozen inventory, accounting totals, computed verdicts or ablation contrasts.
Missing outcomes remain missing. A failed partial trace can be inspected but does
not contribute to a completed-policy comparison. `INCONCLUSIVE` is a first-class
outcome, not an error to remove from the report.

## Portable reproduction

Copy the complete exported directory and the exact matching source release to
another supported Linux environment. Retain all nested member bundles. Then run:

```bash
python3 -m continuum campaign-verify --bundle evidence/my-campaign
python3 -m continuum campaign-reproduce --bundle evidence/my-campaign --dir runs/fresh-reproduction --record evidence/campaign-reproduction.json
```

The command executes all source studies in a new campaign, bound to the exact
source evidence before the first admission. It cannot adopt a cached unrelated
campaign. It records new campaign/attempt identities, objective traces, accounting
and actual runtime metadata. `MATCH` requires all traces and runtime fields to
agree. Runtime differences remain in the record and make the formal result
`INCONCLUSIVE` even if `numerical_sequences_match` is true. `MISMATCH` means at
least one eligible trace differed. The process returns 0 for MATCH, 1 for a
retained non-MATCH result, and 2 for invalid input or an operational failure.

If reproduction is interrupted, repeat the same command with the same directory
and an unused record path. A completed, source-bound reproduction can republish a
missing record without rerunning or claiming additional execution. Output paths
must remain outside the accepted bundle. Existing records are never overwritten.
The bundle contains data; no imported commands, scripts or plug-ins are executed.

## Recovery and frozen state

The campaign directory contains `campaign.json` and one SQLite ledger per study
under `studies/`. Every ledger binds to the whole frozen inventory, so replacing a
study, shrinking the inventory or editing the accepted question invalidates the
binding. Draft edits require a new campaign directory. Do not hand-edit accepted
JSON or SQLite files.

A deliberate pause stops after the requested number of remaining logical trials,
across study boundaries. Ctrl+C and process termination preserve admitted costs.
Resume reconciles the interrupted ledger: a validated staged completion is
finalized once; an un-staged attempt remains failed and may consume its separately
reserved retry. Exhausted trials remain visible. A second active campaign
coordinator is refused. Individual ledgers also retain their coordinator locks.

A campaign's inspection reads its member snapshots in sequence. During execution
it is a progress observation, not an assertion of one simultaneous wall-clock
snapshot. Export requires all members to be terminal. The resulting bundle is a
fixed complete inventory with checksums and independently recomputed derivations.

Source and runtime identities are strict. Finish or resume using the unchanged
release that froze the campaign. Keep 0.1 databases and bundles with version 0.1.0;
0.5 does not silently migrate or relabel their evidence. Process-death tests do not
establish hardware power-loss durability. Native macOS and Windows are not claimed.

## New supported studies

For one study, choose reviewed built-ins explicitly:

```bash
python3 -m continuum study --objective sphere-2d-v1 --baseline grid_search --candidate coordinate_refinement --out sphere-study.json
python3 -m continuum init --study sphere-study.json --db runs/sphere.sqlite
python3 -m continuum run --db runs/sphere.sqlite
python3 -m continuum export --db runs/sphere.sqlite --out evidence/sphere
```

Supported objectives: `rosenbrock-2d-v1`, `sphere-2d-v1`, `ellipsoid-2d-v1`.
Supported policies: `uniform_random`, `grid_search`, `coordinate_refinement`,
`coordinate_fixed_step`. Baseline and candidate must differ. Explicit selections
create schema-2 drafts. With no selection flags, `study` still emits the exact
schema-1 default protocol and its narrower restrictions.

All studies retain bounded domain/start/step/threshold, disjoint development and
confirmation seed lists, finite evaluation allowances, fixed retries and timeout,
and the original own-scalar-feedback rule. There is no cross-study policy feedback.
The domain must remain in `[-10,10]²` and contain (0,0) and (1,1). Each phase has
1–16 seeds, with equal phase counts. Each run has 8–4096 evaluations. A study's
clean original-plus-reproduction budget cannot exceed 65,536 evaluations. A
campaign has 1–32 studies and at most 1,048,576 clean evaluations. Its retry reserve
is twice the clean budget. Oversized studies/bundles fail closed; no outcomes are
silently truncated.

To create a campaign variant, edit an unaccepted draft. Each entry has a unique
`id`, the full `study`, and nullable `ablation_of` and `factor` fields. An ablation
must reference an earlier entry and change exactly one computational field:
`candidate` (coordinate step halving only), `initial_step`, or `start`. All other
protocol fields stay identical; question/hypothesis/falsifier text and study
identity may describe the changed experiment. A changed allowance, objective,
seed set or baseline is a separate study, not a matched ablation.

## Read uncertainty and ablations

A study's frozen verdict compares confirmation **medians of best objective** at
equal charged costs, with complete original trials and matching reserved replay.
The extra uncertainty view describes **paired candidate-minus-baseline best
values** at the same confirmation seeds. The median paired difference need not
equal the difference of medians; it does not replace the frozen verdict.

With at least three eligible pairs involving uniform random search, a fixed
2,000-resample bootstrap reports a descriptive 2.5%–97.5% empirical interval.
This summarizes sensitivity to resampling the chosen seeds. It is not a validated
population confidence interval, significance test or guarantee about other
workloads. Small samples are labelled insufficient. Grid and coordinate repeats
are deterministic checks, so comparisons involving only those policies receive
no sampling interval. Ineligible comparisons retain available pairs but no interval.

Ablation contrasts compare the reference and variant candidates at identical
confirmation seeds. They require eligible source studies and equal paired costs.
A negative difference favours the variant on that fixture. The fixed-step variant
isolates removing coordinate step halving; it does not establish broad causality
or optimizer superiority. Different objective scales are never pooled into a
single winner. See [Decision 003](decisions/003-numerical-workbench.md) for exact
formulas, policy rules and resampling choices.

Independent human accessibility observations and qualified scientific review remain
separate requirements. Agent tests and browser checks do not satisfy them.
