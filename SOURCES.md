# Sources, candidate tools and data policy

Official entry points inspected while preparing this plan on 2026-09-07. These links support the bounded descriptions below; they do not prove an implemented integration, available benchmark data, endorsement or scientific validity for every planned scenario.

| Source | Supported planning use |
| --- | --- |
| [Karpathy autoresearch](https://github.com/karpathy/autoresearch) | Primary inspiration and baseline: a compact single-GPU training experiment loop with bounded run time and a held validation metric. Recheck exact source and license before any future code reuse. |
| [MLCommons benchmarks](https://mlcommons.org/benchmarks/) | Reference for controlled AI evaluation methodology; no affiliation or official benchmark claim. |

## Before adopting a dependency or dataset

Record the exact official release and license, maintenance/advisory state, runtime and transitive dependencies, safe loading behavior, telemetry/network use, storage/compute cost, alternatives and rollback. A source being listed here does not authorize installation or data download. Exact versions are deliberately deferred until the implementation environment and compatibility evidence exist.

For each dataset/model, document provenance, permitted use, attribution, redistribution rights, access requirements, geography/population/time coverage, uncertainty and missing variables. Link source records to all derived artifacts. Reject incompatible terms and use an honestly labeled synthetic fixture when appropriate. Keep private information, credentials, controlled-access data and third-party assets out of this public repository.

## Evidence limits

Karpathy's autoresearch is an inspiration and comparison baseline, not a dependency or claim of affiliation. Its public design centers on a compact training loop and fixed evaluation budget. This project proposes broader adapters, protected evaluation, replication and cost accounting; superiority must be demonstrated. Use simple local process orchestration before considering a workflow framework. No upstream code is copied in this planning release.

Official tool documentation establishes the tool's stated purpose; our model cards and independent benchmarks must establish applicability to our experiment. Sources are not blanket proof for results we have not measured. The project's original documents use AGPL-3.0-only; referenced material retains its own terms.
