# Decision 001: a frozen, bounded numerical comparison

Date: 2026-09-07. Status: implementation decision under Lucas Santana's owner launch instruction; results have not been inspected when choosing this protocol.

## Scope and lineage

The 0.1 fixture promotes a narrow part of RC-015 into a separate numerical release path. It does not complete the original training, agent-search, adversarial isolation, numerical generality, or qualified scientific-review requirements. The objective and policies are independently written standard-library Python; no autoresearch source is copied. Original material uses the repository's AGPL-3.0-only license.

The external user can freeze and execute a new versioned study, inspect complete outcomes, recover interruptions, and reproduce the bundle. The supported initial environment is Python 3.12 on Linux. CPU use is one local worker and no network, model, third-party runtime package, or paid compute is required. Logical interfaces between reviewed built-ins are not hostile-code isolation.

## Question, hypothesis and falsifier

Question: on the declared two-dimensional Rosenbrock domain, does fixed coordinate refinement obtain a lower median best objective than seeded uniform random search with the same finite evaluation allowance?

Hypothesis: coordinate refinement's local scalar feedback will yield a lower median best objective in the three reserved confirmation runs. The falsifier is confirmation median greater than or equal to the random-search median. Every null, adverse, invalid and interrupted result remains part of the outcome set. Missing or invalid runs and unequal charged budgets prevent a complete comparative conclusion.

This fixture is public and analytically transparent. Confirmation is fresh seeded execution of fixed policies, not secret held-out data. Candidate runs are deterministic and identical across seeds: three candidate repetitions are implementation checks, not three independent stochastic observations. No p-value, confidence interval, statistical significance, causal mechanism, optimizer novelty, general superiority, or comparison to autoresearch is claimed.

## Protocol frozen before outcomes

| Item | Frozen example value |
| --- | --- |
| Objective | `100 * (y - x*x)**2 + (1-x)**2`, minimize, dimensionless |
| Domain | closed rectangle `[-2,2] × [-1,3]` |
| Known answer | both nonnegative terms vanish at `(1,1)`, value exactly `0` |
| Nonzero control | `(0,0)`, value exactly `1` |
| Baseline | `uniform_random`, independent coordinates from Python's seeded `random.Random.random()` mapped to the bounds |
| Candidate | `coordinate_refinement`, start `(-1.2,1.0)`, step `0.5` |
| Candidate sweep | propose `+x,-x,+y,-y` in that order from the current incumbent; clip to bounds; accept strict improvement immediately; halve step after a complete sweep with no improvement |
| Evaluation allowance | 128 observations per policy run, including the initial candidate point; boundary duplicates still cost an observation |
| Development seeds | `11,22,33` |
| Confirmation seeds | `101,202,303`, disjoint from development |
| Feedback | each policy receives only its own scalar objective or explicit failed observation; fresh policy per run; no development state transferred to confirmation |
| Quality threshold | best objective `<=0.01`; diagnostic proximity to known zero, not a statistical threshold |
| Comparison | descriptive median of best valid objective per completed confirmation run; report all individual runs and development outcomes too |
| Reproduction | fresh execution of both policies for every development and confirmation seed, linked to source trials; point and objective sequence agreement at absolute and relative tolerance `1e-12` |
| Attempt limit | two attempts per logical trial, 10 seconds per attempt |

Equal evaluation counts do not establish equal CPU or wall-clock costs; those remain separately measured. The Rosenbrock valley can make local coordinate movement ineffective, and this is a useful possible negative result. No parameter is retuned in this study after observing results. Different supported parameters require a newly frozen revision and digest.

## Reservations and failures

The coordinator reserves baseline, candidate, confirmation and reproduction capacity before execution. A logical trial is one complete policy run. Admission charges its full 128-evaluation allowance; observations actually executed are recorded separately. A crash cannot erase that charge. A retry has a fresh attempt identity and another finite debit, up to two attempts per logical trial. The full attempt capacity is reserved up front; exploration cannot spend another arm or phase's allocation.

With six development and six confirmation trials, plus twelve reproduction trials covering both phases, the example permits 24 × 2 × 128 = 6144 charged evaluation units. A clean first-attempt run uses 3072 actual search evaluations. Evaluator controls have their own explicit call records and are additional to search counts. Recovery can cause unequal consumed costs; reporting must expose lost parity and qualify comparison as inconclusive rather than advertising equal-budget superiority.

Invalid input, boolean numeric values, non-finite values, unknown fields, domain escape, missing observations, altered evaluator identity, exceeded trial capacity and exhausted budget fail closed. The evaluator rejects malformed points before objective calculation. Failed feedback is not a zero objective. An incomplete run never masquerades as a completed run.

## State and interfaces

`Study.from_dict` accepts only the documented strict JSON shape, normalizes numbers, validates bounds, and creates an immutable value. `Study.to_dict` returns a detached JSON object; its canonical representation determines SHA-256 study identity. The coordinator freezes a SHA-256 over `numerical.py` and `study.py`, using fixed filename separators and excluding installation paths, and passes that expected identity to each evaluator, including after restart. Runtime objective replacement is also detected. Digests detect integrity changes; they are neither signatures nor scientific validation.

`Point(x,y)` is the proposal type. `make_policy(name, study, seed)` returns a reviewed built-in exposing `propose()` and `observe(point, objective_or_none)`. Policies receive no ledger, evaluator, file, network, or budget capabilities through this interface. They are stateful only within a run and reject unsolicited/mismatched feedback and repeated proposals without feedback. Ordered observations can reconstruct the same policy state after restart. Built-ins are trusted code in the same Python process.

`Evaluator(study, expected_identity=...)` validates the frozen identity and point before computing. `controls(study)` returns individually named expected/observed verdicts with explicit `objectiveCalls`. The coordinator owns all admission, debit, attempt identity, durable records, timeouts and terminal states. The report/exporter owns complete-result comparison and reproduction linking; policies cannot promote claims.

## Bounded customization and compatibility

Schema version 1 permits a new study identifier/revision and short question/hypothesis/falsifier text; a rectangle within `[-10,10]²` containing both `(0,0)` and `(1,1)`; an in-domain start; initial step between `1e-6` and the widest domain side; 8–4096 evaluations per policy; one to sixteen distinct seeds in each phase with equal phase repetition counts; and quality threshold between `0` and `1`. A second aggregate bound requires `4 × evaluations_per_policy × (development seed count + confirmation seed count) <= 65536`, covering both arms and original plus reproduction phases before retries. The two-attempt cap therefore limits reserved debit to 131072 units. Oversized studies fail before admission. This envelope keeps the trusted local adapter and evidence export bounded; the bundle validator separately caps a JSON input at 128 MiB. Adapter, policy names, feedback/comparison/reproduction rules, retry count and timeout remain fixed. No contributed code or arbitrary objective expression is accepted.

Changing schema semantics or adapter source creates a new adapter/release identity. Existing campaigns fail on an evaluator mismatch and require their original code to resume; silently migrating accepted evidence is prohibited. Retaining the original release permits rollback and reproduction. Alternative objectives, elaborate search policies, protected holdouts, distributed workers and statistical inference remain separately reviewed later work.

## Verification and remaining evidence

Numerical tests must independently derive known zero/nonzero controls; reject malformed and non-finite points, source/callable mutation, unknown study fields and invalid reservations; demonstrate deterministic seeded replay and strict proposal-feedback sequencing; and show both policies consume the same requested observation count without tuning their outcomes. Coordinator tests own budget exhaustion, failure accounting and crash recovery. Fresh packaged/public reproduction and qualified human review remain separate gates even if these local tests pass.

Implementation evidence: `python3 -m unittest discover -s tests -p test_numerical.py -v` executed 14 tests successfully on Python 3.12.14/Linux on 2026-09-07. These cover independent polynomial agreement, exact known controls, invalid candidates without hidden objective calls, source/callable/code mutation rejection, immutable and bounded study validation, deterministic policy replay, strict feedback sequencing, immediate coordinate updates, halving only after a failed sweep, clipped duplicates and failed observations consuming slots. The example parameters and rules were not changed after running these checks. This is automated component evidence, not external reproduction, human review, or publication evidence.
