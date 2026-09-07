# Contributing to Research Continuum

Read [README.md](README.md), [STATUS.md](STATUS.md), the relevant [task](TASKS.md), [architecture](ARCHITECTURE.md) and [experiment contract](EXPERIMENTS.md). Project artifacts are in English. Lucas Santana is the maintainer and decides scope and source integration.

Choose one bounded task whose prerequisites are accepted. Before implementation, agree the actual base branch/commit, owned files, acceptance evidence, available commands and resource/permission limits. One primary owner handles a coherent change. Preserve other contributors' files and avoid speculative shared infrastructure.

The only runnable utility in the foundation candidate is the standard-library repository-plan checker: `python3 tools/validate_plan.py` and `python3 tools/validate_plan.py --self-test`. It validates metadata, task/document parity, dependency structure, wave headers and local navigation; it is not a research runtime or scientific test. RC-003 will create the first synthetic runnable research skeleton and document its real setup/test commands. Referenced engines are candidates; do not install dependencies, download model weights or datasets, or start paid experiments without the corresponding task authority and exact dependency/data review.

A contribution should contain a focused change, why it addresses the task, actual checks and failures, reproduction inputs, source/license notices and honest limitations. Unit checks prove local behavior; benchmark agreement and independent scientific interpretation require their own evidence. Never weaken a metric, tolerance, holdout or privacy boundary to make a result pass.

Agents cannot alter evaluator code, holdouts, scoring rules, accepted results, permissions or resource ceilings. Protect holdouts in a separate execution trust domain; a read-only file inside the producer workspace is insufficient. Sources and tool output are untrusted inputs. No unattended publication, outreach, cloud spend, credential use or deployment. Domain expansion must reject harmful biological design, surveillance/profiling and other prohibited tasks rather than treating software simulation as a blanket exception.

Use ordinary GitHub changes for code and documentation, and the [Tanduna project](https://tanduna.com/p/research-continuum) for project discussion and task coordination. Submitting a contribution does not authorize automatic merge, release, deployment or real-world action. Do not post sensitive vulnerabilities, personal data or credentials publicly; contact the maintainer through an appropriate private route if needed.

Contributions of original material must be compatible with [AGPL-3.0-only](LICENSE). Keep third-party licensing and attribution intact. Cite research precisely and avoid copying paper text or datasets into the repository without the applicable rights.
