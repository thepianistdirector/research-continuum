# Canonical programme maintenance

`tasks.json` is the sole current task-state ledger. `STATUS.md` is the project narrative and evidence summary; it does not define a second independent task table. Change the canonical rows first, then run:

```sh
python3 tools/render_plan.py
python3 tools/validate_plan.py --self-test
python3 tools/render_plan.py --check
```

The renderer writes `ROADMAP.md`, `TASKS.md`, `plan/exports/tanduna-plan.json` and `plan/exports/tasks.csv`. Generated files must not be edited separately. The export is review/import material, not an invented native API request or proof of publication.

The plan contains 228 outcome rows across 28 waves: three retained foundation outcomes, 50 narrow 0.1 outcomes, and 175 conditional later or exploratory outcomes. Wave sizes follow feature and evidence coverage; they are not an equal-row quota. The five-wave numerical path is separate from the original training/agent research graph.

The owner additionally selected the local numerical workbench through 0.5 on
September 8. `activeDelivery` records that scope; `implementationSlice` describes
bounded progress and remaining acceptance on relevant later rows. These rows stay
IN PROGRESS while their broader historical acceptance or prerequisites remain
unfulfilled. The current local export includes this new development scope; it does
not alter the already frozen native 0.1 submission revision or claim publication.

## Progress and evidence interface

Update only the relevant task's `status` and `evidenceRefs` when actual evidence supports advancement. The vocabulary is `PLANNED`, `IN PROGRESS`, `IMPLEMENTED`, `AUTOMATED PASS`, `RUNTIME VERIFIED`, `USER VALIDATED`, `RELEASE VERIFIED`, `BLOCKED`, `FAILED` and `NOT TESTED`. A higher label is not an automatic replacement for missing human or release evidence. Evidence references identify actual project-relative artifacts or public evidence locations. `DONE` is reserved for the three retained historical foundation rows.

New task rows must include identity, title, outcome, area, wave, release horizon, prerequisites with outcome rationale, falsifiable acceptance, source/decision references, risk/evidence needs, status and evidence references. New work starts PLANNED. Every row belongs to one wave, maps reciprocally to a historical source requirement, and feeds an intended programme exit. Proposals that are options are labelled separately from accepted source requirements; their existence does not promise adoption.

Immediate execution packets bind actual files, runtime commands, failure probes and exit evidence as implementation begins. Long-term rows are outcome contracts to refine at wave entry, not an assertion that all future implementation details or resources are known.

## Immutable history and prerequisite coverage

`lineage/` retains exact source bytes from the accepted architecture foundation and its predecessor. Its manifest and the validator pin those identities. Do not rewrite these files, original acceptance text, statuses, owned paths, task order, wave gates or prerequisites. Current source mappings preserve structured prerequisites and separately describe textual-only prerequisite evidence. Both original roadmaps remain available in full.

`sourceMappings[].successorIds` names expanded current outcomes. `narrowSuccessorIds` identifies partial 0.1 scope; `expandedSuccessorIds` identifies later expansion or retained foundation rows. Neither list claims that the original contract is complete. `prerequisiteOutcomeCoverage` maps every original prerequisite to its current successor set; the exact original graph remains normative for any future historical-contract acceptance. The validator checks this traceability separately from the owner-authorized new 0.1 dependency graph.

The validator rejects exact normalized duplicate titles, outcomes and acceptance text, missing source coverage, dangling edges, cycles, orphan outcomes, wave/order disagreement, missing critical 0.1 dependencies, altered historical contracts, unauthorized scope expansion, missing evidence references and stale generated files. Human review remains necessary for semantic near-duplicates and whether an acceptance condition is substantively adequate. The negative self-test also mutates a disposable historical copy and a generated document; it creates and removes scratch data only under this project's `plan/` directory.

## Publication interface

Before native publication, re-read the exact public project, roadmap, all tasks and relevant proposal contracts. Use supported task and plan draft/review/approval controls. Do not assume the current export's observation is still fresh or that a Discussion proposal has been accepted.

When native IDs are actually returned, set each `tasks[].platformId` and the same entry in `publication.platformMapping`. Retain original source IDs separately; no source native task ID existed in the recorded snapshot. Reconcile partial creation by returned stable IDs before retrying. The supported platform observation allows up to 32 waves and 80 characters per wave title; this 28-wave plan fits that envelope.

Update `publication.releaseAccess` only with the real version, public URL, honest evidence state and tested access instructions. Keep `publication.status` distinct from local task implementation. Public completion requires read-back of native waves, counts, ordering, dependencies, scope/status and 0.1 instructions, plus independently observed execution of the publicly obtained artifact. Local JSON/CSV exports and unaccepted proposals leave those gates open.

## Reconciled native draft, September 8

All 228 current task rows and 28 wave rows carry real returned `platformId` values. `publication.platformMapping` mirrors the task rows; `publication.observedOriginalPlatformMapping` records the 27 original native records separately from historical source observations. The authenticated inventory has 252 records, while anonymous readers still see zero published tasks. Never conflate these counts.

Saved/submitted plan revision 1, proposal `prp_df7f3bd9e870117e57f01e5c8937764c`, option `yes`, is frozen against the export at commit `a59af53d9b356c5f69b20d29dc65dce55bf261b8` (SHA-256 `3654e6ed4285394870dfcb807a3b13920dd6724d856df06da62b9ef12c9cdaf1`). Its reviewer failed with an input error. Current Git mapping and external-evidence updates do not change that frozen payload. Preserve the proposal and returned IDs, diagnose the actual platform failure through supported controls, and wait for real review/option approval before claiming publication. Do not blindly import the latest export as a replacement draft.
