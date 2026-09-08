# Contributing to Research Continuum

Read [README.md](README.md), [STATUS.md](STATUS.md), the relevant [task](TASKS.md), [architecture](ARCHITECTURE.md) and [experiment contract](EXPERIMENTS.md). Project artifacts are in English. Lucas Santana is the maintainer and decides scope and source integration.

Choose one bounded task whose prerequisites are accepted. Before implementation, agree the actual base branch/commit, owned files, acceptance evidence, available commands and resource/permission limits. One primary owner handles a coherent change. Preserve other contributors' files and avoid speculative shared infrastructure.

The local numerical workbench uses only Python's standard library. Run `python3 tools/validate_plan.py --self-test` for canonical planning/lineage checks and `python3 -m unittest discover -s tests -v` for numerical, coordinator and evidence falsifiers. Tests keep temporary campaigns under `.cache/tests/`; no system temporary data or shared configuration is required. Follow README's actual CLI workflow to verify the source package, including interruption and a fresh source-bound campaign reproduction. The 0.5 delivery scope is in docs/GOAL-0.5.md; bounded partial progress does not complete the broader historical task contracts.

The built-in objective and study rules are frozen before outcomes. Changing supported policies or evaluator source requires a new release identity and a newly frozen campaign. Do not tune a protocol after seeing confirmation to make the candidate win. Preserve all failed attempts and negative evidence. Broader training/agent/search and hostile-code isolation remain separate historical obligations.

No production package dependency is required. Review exact source/version, transitive impact, license, network/data behavior, maintenance, cost and rollback before proposing one. Do not download weights/data, install machine-wide tools or start paid work without applicable authority. Browser/QA tooling is development-only and stays project-scoped; it is not included in the public runtime package.

A contribution should contain a focused change, why it addresses the task, actual checks and failures, reproduction inputs, source/license notices and honest limitations. Unit checks prove local behavior; benchmark agreement and independent scientific interpretation require their own evidence. Never weaken a metric, tolerance, holdout or privacy boundary to make a result pass.

Agents cannot alter evaluator code, holdouts, scoring rules, accepted results, permissions or resource ceilings. Protect holdouts in a separate execution trust domain; a read-only file inside the producer workspace is insufficient. Sources and tool output are untrusted inputs. No unattended publication, outreach, cloud spend, credential use or deployment. Domain expansion must reject harmful biological design, surveillance/profiling and other prohibited tasks rather than treating software simulation as a blanket exception.

Use ordinary GitHub changes for code and documentation, and the [Tanduna project](https://tanduna.com/p/research-continuum) for project discussion and task coordination. Submitting a contribution does not authorize automatic merge, release, deployment or real-world action. Do not post sensitive vulnerabilities, personal data or credentials publicly; contact the maintainer through an appropriate private route if needed.

Contributions of original material must be compatible with [AGPL-3.0-only](LICENSE). Keep third-party licensing and attribution intact. Cite research precisely and avoid copying paper text or datasets into the repository without the applicable rights.
