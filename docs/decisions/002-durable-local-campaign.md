# RC decision 002: one durable trusted numerical campaign

Date: 2026-09-07; evidence updated 2026-09-08. Authority: Lucas's owner launch, narrow 0.1 recommendation. Status: implemented and locally verified; external and human evidence pending. See [current state](../../STATUS.md).

## Observed facts

The clean main checkout was c127193dacea9915e848b9492816787aa2490bb7 with origin thepianistdirector/research-continuum. Foundation plan validation and its negative probes pass. Python 3.12.14 and its standard-library SQLite 3.53.1 run on Linux x86_64. Startup showed 32 logical CPUs, 171 GiB available RAM, 1.6 TiB free disk and load 3.48. Process visibility is limited to this execution environment. No competing Research Continuum owner appeared in the available task inventory. The active turn's runtime metadata reported gpt-6-astra; no settings were changed.

The native Goal is active under task 01a07e1d-3d0e-7061-9637-9791078bd20d. The tool exposes a thread identity, not a separate Goal ID. Root owns runtime/integration. Leaf Astra owners handle the canonical roadmap and numerical adapter in disjoint paths. No sibling or shared-parent changes are authorized.

## Adopted slice and alternatives

Use Python's already available standard library and SQLite transactions with FULL synchronous writes. No production package installation or transitive graph is introduced. SQLite solves transactional admission, immutable observations, unique terminals and restart reconciliation with lower operational cost than a server database. Files alone would require a custom transactional journal. No graph database, generic plugin loader, network service, arbitrary executable study or LLM is included.

One OS flock per campaign prevents two live coordinators. The lock is released by process death; it is the local liveness authority, avoiding PID-reuse guesses or stale time-based leases. This supports one verified Linux environment only. Remote leases and distributed fencing remain deferred. Readers inspect committed snapshots.

Before execution, persist the exact strict StudyDesign, source/evaluator digest, policy rules, questions, seeds, thresholds, trial schedule, total reserves and runtime identity. Reject later evaluator or study drift. Records are append-only and database triggers reject updates/deletes through ordinary SQL. The trusted local operator can still replace files or alter software; this is tamper detection and logical API separation, not adversarial isolation.

Each scheduled trial has at most two attempts. Admission transaction allocates a unique attempt, consumes its entire fixed evaluation allowance, and emits an event. Every actual evaluation is retained independently before further proposals. Recorded calls and conservatively charged allowance are separate totals: death between evaluation and durable observation leaves unknown usage bounded by the charged allowance. Failed/cancelled/timed-out attempts never refund their allowance. Retry identity references its predecessor and cannot exceed its trial reserve or borrow another phase/arm's capacity.

At each trial's end, validate observations and stage its full result inside SQLite; then commit the unique terminal row. Recovery after staging can validate and finalize it. Recovery of an unstaged attempt records a failed terminal, preserving partial observations, then may admit one new bounded retry. After a second failure the campaign finishes inconclusively. SIGINT records cancellation. A ten-second per-attempt deadline is checked between cheap built-in evaluations; it is not hostile-code preemption.

Development and confirmation have distinct frozen seeds, with no policy state transfer between trials. Reproduction reserves cover fresh reruns of both phases, linked to original trial IDs. The known-answer objective is public, and deterministic candidate repeats are not independent stochastic samples. Failed work can break consumed-cost parity even when allocations were equal; such a campaign must not claim an equal-cost candidate advantage.

## Export and compatibility

Export versioned JSON records and accessible HTML derived solely from retained observations. Validate all cross-references, objective values, counts, policy replay and reproduction matches. Stage a complete bundle in a sibling directory, fsync its files, validate the manifest, then rename into a previously absent destination. Incomplete staging never appears as a complete bundle. Explicitly refuse overwriting an existing export. Fresh reproduction reads the manifest and executes reviewed built-ins, never a bundled shell command or cached verdict. Format v1 rejects unknown incompatible versions.

Rollback means keeping the old executable and evidence; never migrate accepted evidence in place. New protocols create new campaigns. No publication happens through the runtime.

## Evidence and unresolved decisions

Representative tests must kill real coordinator subprocesses after admission, execution and staging; detect evaluator drift, malformed records, missing observations, duplicate terminals and exhausted reserves; reproduce a packaged run in a new directory. Human/domain review, fresh externally obtained release execution, Git identity, exact GitHub publication permission, Tanduna authentication and native-plan approval remain separate gates. No independent human observation is claimed.


## Concrete integration packet

Root-owned files: `continuum/__init__.py`, `continuum/__main__.py`, `continuum/store.py`, `tests/test_store.py`, `tools/build_release.py`, first-run/release documentation and current evidence. Numerical owner: `continuum/study.py`, `continuum/numerical.py`, the example and numerical tests. Evidence owner: `continuum/evidence.py`, `continuum/report.py`, evidence tests. Roadmap owner: `plan/`, roadmap/task projections and plan validator/renderer. Leaf agents do not delegate.

The registry snapshot v1 retains the exact study and evaluator identity, environment, sources, ordered trial specifications and phase/arm allocations, controls, all attempts with ordered observations and terminal/staged records, and a contiguous transactional event stream. Original trial IDs name phase/policy/seed; reproduction IDs prefix the original ID with `reproduction-`. Retry attempt IDs are fresh UUIDs and name their predecessor. Reports independently reconstruct the schedule and policy trace, not just trust the registry's declared totals.

Verification targets are strict input rejection; known answer controls; full equal-budget original and reproduction execution; failed, cancelled and timed-out costs; real SIGKILL after admission, execution and staging; lock contention; duplicate terminal refusal; missing observation/changed evaluator/rewritten study rejection; tampered bundle inventory and forged metrics; fresh-directory package execution. Actual discovered test commands and results will be recorded only after the files exist and assertions execute.

Atomic export uses Linux `renameat2(RENAME_NOREPLACE)` through the standard library to refuse even a racing existing destination. The initial Linux-only support boundary includes this syscall. JSON input is bounded to 128 MiB per file and 256 MiB per bundle; supported studies additionally cap aggregate clean search evaluations at 65536 before admission. No file/command from an input bundle is executed.

SQLite's [atomic-commit documentation](https://sqlite.org/atomiccommit.html) and Python's [fcntl documentation](https://docs.python.org/3.12/library/fcntl.html) were freshly read. Durability relies on working filesystem locks and flush semantics; process-death tests do not prove hardware power-loss behavior.


## Critic findings resolved before release candidate

A fresh numerical critic found that pre-freeze source hashing could describe disk edits that were not loaded. The evaluator and coordinator now bind their source identity at import and reject later disk divergence, including before initial campaign acceptance. A regression changes source before first identity capture. Numerical tests also independently reconstruct the seeded random affine mapping and normalize oversized-JSON-integer rejection. The frozen scientific protocol and policy parameters are unchanged.

A separate fresh runtime critic found two reproduction gaps. The reproduction API now requires exact source-evidence binding and disjoint attempt identities, rejecting a relabeled copy. The CLI checks output feasibility and forbids outputs inside the input bundle before admitting fresh work. A source-bound completed reproduction can recover a missing record after process death; its record explicitly says no new execution occurred during finalization. A real SIGKILL test covers the gap after final trial completion and before record publication. Unrelated cached campaigns remain ineligible. The critic verified the bounded fixes with no further actionable finding.

The reviewed trusted-local-operator boundary remains unchanged: coordinated malicious rewriting of code, records and identities is not prevented or authenticated by hashes. Human/qualified review is still pending.

## Packaged verification

On September 8, the source preflight exposed a missing generated CSV in the archive. The packaging allowlist now includes CSV; the failed first archive is retained locally. A fresh extraction of the corrected package passes all 53 discovered tests, 25 plan negative probes and the documented campaign/reproduction workflow. A separately versioned eight-evaluation study is killed after admission and resumes with one retained failed attempt, 192 recorded evaluations and 200 charged units; its verdict remains inconclusive. This is agent runtime evidence on the same host, not independent external or human validation. [Packaged summary](../../evidence/runtime/packaged-summary.json) retains the bounded observations.
