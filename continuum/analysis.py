"""Descriptive paired seed uncertainty, separate from the frozen verdict.

The resampling distribution is conditional on the chosen seeds. It is not a
population confidence guarantee and does not turn deterministic repeats into n.
"""
from __future__ import annotations

import random
import statistics

STOCHASTIC = frozenset({'uniform_random'})
RESAMPLES = 2000
RESAMPLE_SEED = 1729


def paired_uncertainty(pairs, *, stochastic, eligible=True):
    """Pairs are complete candidate-minus-reference outcomes from original seeds."""
    differences = [candidate - reference for reference, candidate in pairs]
    result = {'method': 'paired-median-bootstrap-percentile-v1',
              'estimand': 'median of paired candidate-minus-reference best objectives',
              'n_pairs': len(differences), 'differences': differences,
              'median_difference': statistics.median(differences) if differences else None,
              'range': [min(differences), max(differences)] if differences else None,
              'interval': None, 'resamples': 0, 'resample_seed': RESAMPLE_SEED,
              'status': 'INELIGIBLE',
              'interpretation': 'Descriptive resampling of these frozen seeds only; no population coverage, significance or general superiority claim. The median paired difference can differ from the difference of medians used for the study verdict.'}
    if not eligible or not differences:
        return result
    if not stochastic:
        result['status'] = 'DETERMINISTIC_NO_SAMPLING_INTERVAL'
        return result
    if len(differences) < 3:
        result['status'] = 'INSUFFICIENT_PAIRS'
        return result
    rng = random.Random(RESAMPLE_SEED)
    medians = sorted(statistics.median(rng.choices(differences, k=len(differences))) for _ in range(RESAMPLES))
    # Fixed nearest-rank empirical percentiles, no interpolation ambiguity.
    result.update(status='DESCRIPTIVE', interval=[medians[49], medians[1949]],
                  resamples=RESAMPLES, percentile_levels=[0.025, 0.975])
    return result


def study_uncertainty(study, summary):
    rows = {(r['policy'], r['seed']): r for r in summary['trials'] if r['phase'] == 'confirmation'}
    pairs = []
    for seed in study.confirmation_seeds:
        base, candidate = (rows[(name, seed)] for name in (study.baseline, study.candidate))
        if base['status'] == candidate['status'] == 'COMPLETED':
            pairs.append((base['best'], candidate['best']))
    return paired_uncertainty(pairs, stochastic=bool({study.baseline, study.candidate} & STOCHASTIC),
                              eligible=summary['verdict'] != 'INCONCLUSIVE')
