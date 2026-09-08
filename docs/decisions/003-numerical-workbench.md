# Decision 003: a bounded local numerical workbench

Accepted implementation direction: September 8, 2026, after the owner selected
local research workbench scope through 0.5. Scientific review remains pending.

Schema 1 retains its exact accepted field restrictions and default protocol.
Schema 2 selects named, reviewed objective and policy implementations. Neither
schema imports expressions, modules, commands, plugins or contributed code.
Old source-bound databases and bundles require their original immutable release;
0.5 does not silently reinterpret 0.1 source identities.

Objectives are Rosenbrock `100(y-x*x)^2+(1-x)^2`, sphere `x*x+y*y`, and ellipsoid
`x*x+100*y*y`. All are minimized, dimensionless, nonnegative, two-dimensional,
and public known-answer fixtures. Rosenbrock has its minimum at (1,1); the
quadratics at (0,0). Controls include the minimum and a separately known nonzero
point, plus invalid input and evaluator-identity rejection. They do not prove
coverage of arbitrary scientific domains.

Uniform random search remains the stochastic baseline. Grid search traverses
cell centres in row order on a `ceil(sqrt(allowance))` square grid, stopping at the
exact allowance. A partial final row is not area-uniform. Coordinate refinement
retains its existing strict-improvement/step-halving rules. The fixed-step variant
removes only step halving, providing a controlled mechanistic ablation. Grid and
coordinate policies ignore seeds; repeating them is a determinism check.

A multi-study campaign freezes the full ordered inventory, per-study protocols,
aggregate reserve and declared ablation links before execution. Each study owns
its existing durable SQLite ledger. A campaign has at most 32 studies and at most
1,048,576 clean objective evaluations (twice that reserve with the fixed retry
limit). No adaptive selection or cross-study feedback occurs. Resume executes
only remaining work and never replaces a finished or failed attempt.

Uncertainty uses complete original confirmation pairs. Its estimand is the median
of candidate-minus-reference paired best values, distinct from the study verdict's
difference of medians. For at least three pairs involving a stochastic policy,
2,000 paired bootstrap resamples use fixed seed 1729; empirical nearest-rank
2.5%/97.5% endpoints describe the observed finite seed set. Selected fixed seeds
are not a justified probability sample of arbitrary workloads; population
coverage, significance and superiority are not claimed. Two deterministic
policies receive no sampling interval. Missing, unequal-cost or unreproduced
comparisons remain ineligible, with their observations retained.

Ablations declare one changed mechanism or numerical setting against a preceding
reference study. All other computational protocol fields must agree, including
objective, budgets, seed sets and comparison rules. Contrasts use paired candidate
outcomes and explicitly require equal retained costs and eligible source studies.
No post-hoc pooled winner or cross-objective raw-value ranking is reported.
