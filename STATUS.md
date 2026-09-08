# Current state

Last updated: 2026-09-08. Maintainer: Lucas Santana ([thepianistdirector](https://github.com/thepianistdirector)). The current task ledger is plan/tasks.json; generated task/roadmap views derive from it. This file records the current evidence and handoff, not a second task ledger.

## Architecture foundation accepted

The active root accepted the three foundation tasks in dependency order under Lucas Santana's explicit instruction to complete and publish this first architecture round. The reviewed source is the foundation commit on `main` containing this file, whose parent is `f558f21830246d4732bc1e590a83214d480cd94b`. This acceptance covers documentation and executable repository-plan tooling. It does not establish scientific validity, implemented simulation, user validation or a released product.

| Task | State | Acceptance evidence |
| --- | --- | --- |
| RC-F01 | **DONE** | Architecture, experiment and source contracts reviewed; scientific boundaries, evaluator isolation and explicit failure semantics accepted as design requirements. |
| RC-F02 | **DONE** | Roadmap and task graph reviewed; all 24 original contracts and eight scientific gates preserved, with only the foundation entry dependency added. |
| RC-F03 | **DONE** | Next-work packet reviewed; python3 tools/validate_plan.py and eight root negative probes passed on the accepted foundation diff. |

## Reproduced verification

- `python3 tools/validate_plan.py` — **PASS** on the accepted foundation: 27 tasks, nine waves and 71 dependency edges.
- Root negative probes in disposable copies — **PASS**: missing dependency, cycle, malformed dependency, Boolean wave, empty owned paths, wrong project, non-object root and TASKS.md status drift were all rejected cleanly.
- Original-plan comparison against the parent revision — **PASS**: all 24 original task objects retain their IDs, title, wave, acceptance, owned paths, PLANNED state and prior dependencies; RC-001 adds only RC-F03.
- All eight original scientific gates — **PRESERVED**.
- `git diff --check` — **PASS**.

These checks verify plan consistency and failure handling. They do not prove the architecture's scientific validity or any simulation result.

## Numerical 0.1 candidate

The owner-authorized narrow 0.1 is implemented: a standard-library Python CLI freezes one bounded Rosenbrock study, runs fixed coordinate refinement and seeded random search, retains all trials/costs, recovers interruption, derives evidence-linked claims, and exports/reproduces a versioned bundle. It runs one trusted built-in worker on the verified Linux x86_64 / Python 3.12.14 / SQLite 3.53.1 environment. No production dependencies, models, paid compute or network service were added.

The native Goal remains **incomplete** under task `01a07e1d-3d0e-7061-9637-9791078bd20d`. Actual runtime metadata confirmed `gpt-6-astra`. Root owns the integrated result; bounded Astra implementation and critic work has finished. Startup was clean `main` at `c127193dacea9915e848b9492816787aa2490bb7`. The owner approved the concrete publication packet on September 8. Source commit `cb34650eb69df0769222623d515daef91aac0e20` and annotated tag `v0.1.0` were pushed atomically; the exact approved release assets are public. Subsequent changes record publication evidence. The authorized Mac helper has created/reconciled native drafts and submitted the saved plan; no native publication has occurred.

| Evidence dimension | Actual observation |
| --- | --- |
| Implemented | Immutable study/schedule, finite reserves and retries, append-only SQLite ledger, fixed policies/evaluator, complete CLI, accessible static report, atomic bundle export, fresh reproduction and deterministic source packager |
| Automated | **AUTOMATED PASS**: 53 discovered product tests; 25 negative plan probes; 228 tasks / 28 waves / 27 source mappings; generated-view parity. Tests include real process kills, source drift before first freeze, forged evidence, cache-relabel rejection and reproduction-record recovery. |
| Packaged runtime | **RUNTIME VERIFIED**: corrected source preflight in a new extraction and minimal environment passes 16 commands, including the full test suite, new study, run/pause/resume/inspect/evaluate/export/verify and fresh reproduction. A modified study survives SIGKILL after admission with costs retained. Same host/runtime; not external or human evidence. |
| Browser observations | Agent keyboard/focus, expandable ledger, 320/390-width layouts, 2× CSS zoom, reduced motion and axe checks; no automated violations in the tested report. Human accessibility observations remain pending. |
| Human/domain review | **NOT TESTED**: no independent participant or qualified reviewer observation supplied. Agent critics and walkthroughs are identified separately. |
| Public release | **RELEASE VERIFIED**: [0.1.0](https://github.com/thepianistdirector/research-continuum/releases/tag/v0.1.0), release ID 384701002, published September 8 at 12:14:06 UTC. All four assets downloaded anonymously and matched approved hashes. |
| Public-download runtime / external use | **RUNTIME VERIFIED**: 18 same-host commands plus 19 commands on a separate Mac-hosted Linux ARM64 container. Root revalidated returned bundles, matching database snapshots, distinct attempt IDs and fresh reproduction. Python/SQLite/architecture differences are explicit; no native macOS, external x86_64 parity, full ARM64 suite or human claim. |
| Tanduna native publication | **BLOCKED / not published**: 228 selected outcomes, 28 saved waves and 538 dependencies are submitted as revision 1. Platform review failed twice with an input error, including one supported retry. Anonymous pages still show zero tasks and no published plan. |

[Decision 001](docs/decisions/001-numerical-study.md) records the protocol before results; [decision 002](docs/decisions/002-durable-local-campaign.md) records ownership, recovery and critic fixes. Runtime source identity is `74245e190f1a711677ec38dce61401ba1bd475bfeaa72895b8a5c50b1bb95fe0`; study hash is `625cea9555008c0de81ccf3e7f790027ffb6ccb0f7285b910d10ddc184337ddf`. These identify the executed runtime/protocol. Public source commit `cb34650eb69df0769222623d515daef91aac0e20` has the approved Git tree `ff7f345d6ab300fea5345f3fa3a74b5416263848`.

## Retained findings and verification evidence

The [default report](evidence/runtime/default-study/report.html) answers the frozen comparison with **BASELINE_LOWER**. Confirmation median best objective is 0.25900796897177875 for random search and 4.655312582291663 for coordinate refinement; neither reaches 0.01. All 24 trials complete, including 12 reserved reproduction runs, using 3,072 search evaluations plus two initial controls. This contradicts the candidate hypothesis for this fixture. Deterministic candidate repetition is not independent stochastic evidence. No significance, novelty, generality, autoresearch superiority or autonomous-scientist claim follows.

The [automated record](evidence/runtime/automated-checks.json) retains discovered tests and real output. The [packaged preflight summary](evidence/runtime/packaged-summary.json) records fresh execution and matching reproduction. Its killed eight-evaluation variant retains one failed attempt, 192 recorded evaluations and 200 charged units; the verdict is INCONCLUSIVE. The first package preflight failed because its allowlist omitted the generated CSV. That defect was fixed, and the failed archive/extraction remain local. The final candidate's exact-archive verification is retained as a separate sidecar to avoid a self-referential package hash.

The [browser record](evidence/runtime/browser-verification.json) distinguishes agent interaction, automated accessibility checks and CSS zoom from human observations. Verification tools and extracted browser support libraries remain project-local and are excluded from distribution. Process-death tests do not establish hardware power-loss durability. Reviewed built-ins and filesystem hashes do not establish adversarial isolation or cryptographic authentication against a malicious operator.

## Long-term plan and immutable history

`plan/tasks.json` is the sole current task ledger. Its generated roadmap and contracts contain 228 outcomes across 28 waves: three historical foundation outcomes, 50 narrow 0.1 outcomes and 175 conditional later/exploratory outcomes. Current statuses refer to actual implementation, automated or runtime evidence. Three remaining 0.1 outcomes require human review and native-plan publication/read-back. External-host workflow evidence is recorded with its precise ARM64 limits; an additional source-bound check against the original bundled VPS campaign is queued separately. The owner-reviewed publication decision and public release now have their own evidence; neither advances the independent human-review task. The owner approved public distribution with the missing human review explicitly disclosed. The retained T07 → T08 dependency is still unmet; observed publication evidence does not establish completion of that prerequisite or the full release programme.

All 27 original source entries map to successors. Eight exact historical lineage files retain the accepted and predecessor contracts. Historical RC-F01–RC-F03 stay DONE for foundation documentation/tooling only; RC-001–RC-024 remain PLANNED in source history. No broader training, agent search, hostile-code isolation, numerical generality or multi-domain acceptance is silently narrowed or marked complete.

## Current public state and remaining gates

Public reads at 2026-09-08 15:37 UTC confirm that the [roadmap](https://tanduna.com/projects/research-continuum/roadmap) still has no published plan and the [tasks page](https://tanduna.com/p/research-continuum/tasks) still exposes zero tasks. The original public proposal `prp_d83436915d973e65338f4a367f70541f` remains Discussion. The new [submitted plan](https://tanduna.com/p/research-continuum/proposals/prp_df7f3bd9e870117e57f01e5c8937764c/tasks) requires sign-in; it is not publicly published.

[Native reconciliation](evidence/tanduna-submission.json) records 228 selected outcomes, 28 waves and 538 exact dependency edges in saved/submitted revision 1, option `yes`. The authenticated Mac inventory contains 252 records: 27 original records preserved plus 225 new drafts; three original foundations are reused in the 228-outcome plan. Root checked every new task's embedded JSON contract and mapped lineage against the approved export, all returned task/wave IDs, saved order and graph. Canonical task IDs and wave IDs now retain those real platform mappings. The historical source records still describe their original observation; newly discovered original native IDs are recorded separately.

The reviewer returned “The review did not complete (input).” One supported retry failed the same way. The specific cause is not exposed in current evidence, and no further unchanged retry, task recreation or resubmission is warranted. A read-only Mac diagnostic request is queued. A passing platform review and the owner's approval of the exact frozen `yes` option are still required. That exact-option question is already pending in the Mac task; the general publication approval is not substituted for it. The frozen native revision retains the submitted export's statuses; subsequent Git evidence updates do not rewrite that history.

The [external ARM64 record](evidence/external-mac-arm64/verification.json) covers a genuinely separate Mac-hosted Linux container using the exact public archive. It retained 24 clean trials / 3,072 recorded and charged evaluations, BASELINE_LOWER, a new matching reproduction, and a real SIGKILL recovery with one failed attempt / 192 recorded / 200 charged units / INCONCLUSIVE. Root independently validated both bundles against returned SQLite snapshots and recomputed the new reproduction record; all 24 VPS/Mac point/value traces also match exactly. The environment was Linux aarch64, Python 3.12.13, SQLite 3.46.1. These results are external-host agent evidence, not native macOS support, external x86_64 parity, a full ARM64 test-suite pass or human review. The fresh MATCH record is bound to the Mac-created bundle; a separate formal reproduction of the original VPS bundle is queued to retain any runtime deviations honestly.

The Mac helper's native 15-minute schedule was read back as ACTIVE and an actual scheduled wake was observed at 15:30 UTC. Queue read/upload round trips and the executing Darwin ARM64 / GPT-6 Astra identity were recorded. The native tool did not expose the next execution timestamp. The helper stays available for bounded follow-ups; its existence does not replace scientific or platform review. The human worksheet remains unfilled and actual human observations are already requested in that Mac task.

The existing GitHub account `thepianistdirector` published the approved source and assets using Lucas Santana's existing author identity. [Owner approval](evidence/publication-approval.json), [public read-back](evidence/public-release.json), and [public-download workflow](evidence/public-download-runtime.json) retain separate proof. Archive SHA-256 is `72027ecd84a06d20445e9fd6d604dee2393b03d78255f679652e2f331585bc3b`. Its immutable documents preserve preparation-time status; the current repository records later evidence. No archive or tag replacement has occurred.

The pinned autoresearch README declares MIT but the refreshed pinned tree still has no standalone root license file. [Source audit](docs/baselines/autoresearch-2026-09-07.md) retains that uncertainty. No upstream code was reused. Original runtime/fixture and repository documents ship with AGPL-3.0-only; raw third-party downloads, browser binaries and private local inputs are excluded.

## Next outcome

Complete native-plan publication and independent-observation gates without weakening them. After 0.1 is publicly verified and its native plan is published, the next later-0.x outcome is Wave 06: reproduce the actual pinned autoresearch baseline under separately approved distribution rights, workload/resources and comparison rules. It does not become a prerequisite for this narrow numerical release or authorize training compute now.
