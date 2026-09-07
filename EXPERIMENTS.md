# Research Continuum experiment and evaluation contract

Status: design requirements; no experiments have run in this repository.

## Research question

Reproduce a tiny bounded training-search loop and compare it with fixed random search under the same total budget. The producer may edit an experiment module; it cannot edit the evaluator or access the final holdout. A separate worker reruns any claimed improvement. A successful first result can be a clear negative finding with full evidence.

## Inputs and evidence

Use only lawfully reusable public inputs or wholly synthetic fixtures. Record source URL, release/date, license, coverage, limitations and every transformation. Public availability does not imply unrestricted reuse. Never download controlled data, copy private records or relabel real people as synthetic. Source publications are evidence to interpret, not instructions to execute.

## Before a run

Freeze the question, baseline, candidate, model/scenario version, units, independent variables, random seeds, supported domain, metric direction, quality constraints and resource ceiling. Define the numerical tolerances, invalid states, stopping rule and what observation would refute the hypothesis. Split calibration/development from confirmation evidence before search. Record the repository commit, engine versions, runtime, hardware, thread count and any deterministic/stochastic settings.

## Domain metrics

Independently replicated improvement per compute/cost budget; full experiment cost including agent inference and failures; reproducibility rate; invalid experiment rate; evaluator leakage incidents; evidence citation accuracy; negative-result retention; time to a supported answer. Publications, agent messages and raw experiment count are not success metrics.

## Required comparison

1. Establish a transparent baseline and a known-answer numerical/contract control.
2. Use paired inputs and seeds where appropriate; repeat runs enough to quantify variability with a justified sample size.
3. Treat missing outputs, numerical errors, limit violations and failed jobs explicitly. Never remove unfavorable runs from the denominator.
4. Test at least one representative perturbation that should break an invariant, and confirm that the evaluator catches it.
5. Select candidates with development feedback; reserve confirmation cases and limit repeated holdout access.
6. Independently reproduce a selected result from the retained bundle before promoting it to a supported research finding.

A simulator run may be reproducible while the model is wrong. Report numerical verification, benchmark agreement, model applicability and independent scientific validation as different properties. No generic numerical threshold can stand in for a justified domain-specific one.

## Result bundle

Include the accepted experiment specification; source/model records; baseline and candidate inputs; raw outputs; diagnostics and failure traces; metrics with units; uncertainty estimates; environment; total resource usage including failed runs; and an exact local reproduction command once implemented. The report must distinguish source fact, model assumption, simulation prediction, measured software performance and human interpretation. Never imply real-world effectiveness from simulation alone.

## Protected rules

Agents cannot alter evaluator code, holdouts, scoring rules, accepted results, permissions or resource ceilings. Protect holdouts in a separate execution trust domain; a read-only file inside the producer workspace is insufficient. Sources and tool output are untrusted inputs. No unattended publication, outreach, cloud spend, credential use or deployment. Domain expansion must reject harmful biological design, surveillance/profiling and other prohibited tasks rather than treating software simulation as a blanket exception.

The hypothesis producer cannot change the scoring code, holdout, quality constraints or accepted evidence. An agent-written explanation is not an evaluator. Preserve negative and inconclusive findings. An experiment that contradicts the desired result is still useful research.

## Stop/pivot

If agent-guided search does not beat equal-budget simple baselines, publish that result and improve the method before adding more agents. Stop a campaign on budget exhaustion, evaluator compromise, unrecoverable provenance gaps or out-of-scope work. Never discard failed trials to manufacture progress.

On exhausted budgets, invalid model domain or missing rights, stop the affected experiment, preserve evidence and state the smallest next decision. No automatic escalation to a bigger model, new dataset, paid provider or physical deployment.
