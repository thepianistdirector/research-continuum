"""Workbench falsifiers: generality, frozen inventory, recovery and inference limits."""
import copy
import hashlib
import json
from pathlib import Path
import random
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from continuum import campaign, numerical, store
from continuum.analysis import paired_uncertainty
from continuum.evidence import canonical_bytes, summarize
from continuum.numerical import Evaluator, EvaluatorMismatch, Point, controls, make_policy
from continuum.study import DEFAULT_STUDY, Study, StudyError, builtin_study
from continuum.workbench import render

ROOT = Path(__file__).resolve().parents[1]
SCRATCH = ROOT / '.cache' / 'tests'
SCRATCH.mkdir(parents=True, exist_ok=True)


def small_plan():
    plan = campaign.default_plan()
    plan['studies'] = plan['studies'][:3]
    for entry in plan['studies']:
        entry['study']['evaluations_per_policy'] = 8
    return plan


class AdapterTests(unittest.TestCase):
    def test_new_objectives_match_independent_known_answers(self):
        for name, expected in [('sphere-2d-v1', [0, 2, 5]), ('ellipsoid-2d-v1', [0, 101, 104])]:
            study = builtin_study(name)
            evaluator = Evaluator(study)
            for point, value in zip([Point(0, 0), Point(1, 1), Point(-2, -1)], expected):
                self.assertEqual(evaluator.evaluate(point), value)
            self.assertTrue(all(r['passed'] for r in controls(study)))
            self.assertEqual(sum(r['objectiveCalls'] for r in controls(study)), 2)

    def test_schema_one_does_not_adopt_new_policy_or_objective(self):
        for change in [{'baseline': 'grid_search'}, {'candidate': 'coordinate_fixed_step'}, {'evaluator': 'sphere-2d-v1'}]:
            with self.assertRaises(StudyError):
                Study.from_dict(DEFAULT_STUDY | change)
        for change in [{'baseline': 'coordinate_refinement'}, {'evaluator': '__import__("os")'}, {'candidate': []}]:
            with self.assertRaises(StudyError):
                Study.from_dict(builtin_study().to_dict() | change)

    def test_grid_is_finite_cell_centre_sequence_independent_of_feedback(self):
        study = Study.from_dict(builtin_study('sphere-2d-v1', baseline='grid_search').to_dict() | {'evaluations_per_policy': 8})
        grid = make_policy('grid_search', study, 101)
        expected = [(x, y) for y in (-4/3, 0, 4/3) for x in (-4/3, 0, 4/3)][:8]
        for i, (x, y) in enumerate(expected):
            point = grid.propose()
            self.assertAlmostEqual(point.x, x)
            self.assertAlmostEqual(point.y, y)
            grid.observe(point, 100 - i)
        with self.assertRaises(StopIteration):
            grid.propose()

    def test_fixed_step_only_changes_failed_sweep_halving(self):
        study = builtin_study('sphere-2d-v1', candidate='coordinate_fixed_step')
        refined = make_policy('coordinate_refinement', study, 11)
        fixed = make_policy('coordinate_fixed_step', study, 11)
        for i in range(5):
            p, q = refined.propose(), fixed.propose()
            self.assertEqual(p, q)
            refined.observe(p, 1)
            fixed.observe(q, 1)
        p, q = refined.propose(), fixed.propose()
        self.assertAlmostEqual(p.x - study.start[0], study.initial_step / 2)
        self.assertAlmostEqual(q.x - study.start[0], study.initial_step)

    def test_new_objective_runtime_replacement_fails_before_call(self):
        evaluator = Evaluator(builtin_study('sphere-2d-v1'))
        with patch.object(numerical, 'sphere', lambda p: 0):
            with self.assertRaises(EvaluatorMismatch):
                evaluator.evaluate(Point(1, 1))
        self.assertEqual(evaluator.objective_calls, 0)
        with patch.dict(numerical._OBJECTIVES, {'sphere-2d-v1': numerical.objective}):
            with self.assertRaises(EvaluatorMismatch):
                Evaluator(builtin_study('sphere-2d-v1'))


class UncertaintyTests(unittest.TestCase):
    def test_deterministic_and_small_samples_never_get_sampling_intervals(self):
        for kwargs, status in [({'stochastic': False}, 'DETERMINISTIC_NO_SAMPLING_INTERVAL'),
                               ({'stochastic': True, 'eligible': False}, 'INELIGIBLE')]:
            result = paired_uncertainty([(10, 8)] * 12, **kwargs)
            self.assertIsNone(result['interval'])
            self.assertEqual(result['status'], status)
        self.assertEqual(paired_uncertainty([(1, 2), (1, 3)], stochastic=True)['status'], 'INSUFFICIENT_PAIRS')

    def test_interval_and_estimand_match_independent_resampling(self):
        pairs = [(10, 9), (20, 15), (30, 32)]
        actual = paired_uncertainty(pairs, stochastic=True)
        generator = random.Random(1729)
        independent = []
        for _ in range(2000):
            sample = [-1, -5, 2]
            drawn = sorted(sample[int(generator.random() * 3)] for _ in range(3))
            independent.append(drawn[1])
        independent.sort()
        self.assertEqual(actual['interval'], [independent[49], independent[1949]])
        self.assertEqual(actual['median_difference'], -1)
        self.assertEqual(actual['range'], [-5, 2])
        self.assertEqual(actual['resamples'], 2000)


class CampaignTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.plan = small_plan()
        self.directory = self.root / 'campaign'

    def create(self):
        return campaign.create(self.plan, self.directory)

    def complete(self):
        self.create()
        return campaign.run(self.directory)

    def test_plan_rejects_hidden_changes_duplicate_ids_and_overbudget(self):
        mutations = []
        changed = copy.deepcopy(self.plan)
        changed['studies'][1]['study']['quality_threshold'] = .5
        mutations.append(changed)
        changed = copy.deepcopy(self.plan)
        changed['studies'][1]['id'] = changed['studies'][0]['id']
        mutations.append(changed)
        changed = copy.deepcopy(self.plan)
        changed['studies'][0]['id'] = '../outside'
        mutations.append(changed)
        changed = copy.deepcopy(self.plan)
        changed['studies'][1]['ablation_of'] = 'later'
        mutations.append(changed)
        changed = copy.deepcopy(self.plan)
        changed['studies'][1]['study']['candidate'] = 'grid_search'
        mutations.append(changed)
        changed = copy.deepcopy(self.plan)
        changed['studies'][1]['factor'] = 'evaluations_per_policy'
        mutations.append(changed)
        changed = copy.deepcopy(self.plan)
        changed['studies'] = [dict(changed['studies'][0], id=f'large-{i}', study=changed['studies'][0]['study'] | {'evaluations_per_policy': 4096, 'development_seeds': [1, 2], 'confirmation_seeds': [3, 4]}) for i in range(17)]
        mutations.append(changed)
        for value in mutations:
            with self.subTest(value=value['studies'][0]['id']), self.assertRaises(ValueError):
                campaign.validate_plan(value)

    def test_pause_resume_preserves_attempts_and_full_frozen_reserve(self):
        start = self.create()
        initial = campaign.summarize_campaign(start)
        self.assertEqual(initial['reserved_evaluations'], 1152)
        paused = campaign.run(self.directory, max_trials=2)
        before = paused['snapshots']['rosenbrock']['attempts'][:]
        self.assertEqual(len(before), 2)
        self.assertEqual(campaign.summarize_campaign(paused)['charged_evaluations'], 16)
        done = campaign.run(self.directory)
        summary = campaign.summarize_campaign(done)
        self.assertTrue(summary['complete'])
        self.assertEqual(summary['charged_evaluations'], 576)
        self.assertEqual(summary['reserved_evaluations'], 1152)
        self.assertEqual(done['snapshots']['rosenbrock']['attempts'][:2], before)
        self.assertEqual(campaign.run(self.directory), done)
        self.assertEqual(summary['ablations'][0]['uncertainty']['status'], 'DETERMINISTIC_NO_SAMPLING_INTERVAL')

    def test_inventory_cannot_be_shrunk_even_with_updated_plan_hash(self):
        self.create()
        path = self.directory / 'campaign.json'
        frozen = json.loads(path.read_text())
        frozen['plan']['studies'].pop()
        frozen['plan_digest'] = campaign.digest(frozen['plan'])
        path.write_bytes(canonical_bytes(frozen))
        with self.assertRaisesRegex(ValueError, 'inventory differs'):
            campaign.inspect(self.directory)

    def test_frozen_question_mutation_breaks_all_member_bindings(self):
        self.create()
        path = self.directory / 'campaign.json'
        frozen = json.loads(path.read_text())
        frozen['plan']['question'] = 'Post-hoc replacement'
        frozen['plan_digest'] = campaign.digest(frozen['plan'])
        path.write_bytes(canonical_bytes(frozen))
        with self.assertRaisesRegex(ValueError, 'complete campaign inventory'):
            campaign.inspect(self.directory)

    def test_real_process_death_retains_charge_and_ineligible_ablation(self):
        self.create()
        db = self.directory / 'studies' / 'rosenbrock.sqlite'
        code = 'import sys; from continuum.store import run; run(sys.argv[1], _crash_at="after-admission")'
        process = subprocess.run([sys.executable, '-c', code, str(db)], cwd=ROOT, capture_output=True)
        self.assertEqual(process.returncode, -signal.SIGKILL)
        done = campaign.run(self.directory)
        summary = campaign.summarize_campaign(done)
        self.assertEqual(summary['failed_attempts'], 1)
        self.assertEqual(summary['charged_evaluations'], 584)
        self.assertEqual(summary['recorded_evaluations'], 576)
        self.assertFalse(summary['ablations'][0]['eligible'])
        self.assertEqual(summary['ablations'][0]['uncertainty']['status'], 'INELIGIBLE')
        self.assertEqual(summary['studies'][0]['summary']['verdict'], 'INCONCLUSIVE')

    def test_export_verify_fresh_reproduce_and_cached_refusal(self):
        source = self.complete()
        bundle = campaign.export(source, self.root / 'bundle')
        self.assertEqual(campaign.verify(bundle), source)
        proof = campaign.reproduce(bundle, self.root / 'fresh')
        self.assertEqual(proof['status'], 'MATCH')
        self.assertTrue(proof['numerical_sequences_match'])
        self.assertNotEqual(proof['source_execution_id'], proof['fresh_execution_id'])
        self.assertEqual(campaign.reproduce(bundle, self.root / 'fresh'), proof)
        campaign.create(self.plan, self.root / 'unbound')
        with self.assertRaisesRegex(ValueError, 'not created for reproducing'):
            campaign.reproduce(bundle, self.root / 'unbound')
        with self.assertRaises(ValueError):
            campaign.reproduce(bundle, self.directory)

    def test_reproduction_resumes_bound_partial_campaign(self):
        source = self.complete()
        bundle = campaign.export(source, self.root / 'bundle')
        fresh = self.root / 'fresh'
        campaign.create(self.plan, fresh, source=source)
        paused = campaign.run(fresh, max_trials=1)
        attempt = paused['snapshots']['rosenbrock']['attempts'][0]
        self.assertEqual(campaign.reproduce(bundle, fresh)['status'], 'MATCH')
        self.assertEqual(campaign.inspect(fresh)['snapshots']['rosenbrock']['attempts'][0], attempt)

    def test_bundle_rejects_derived_tampering_even_with_new_checksum(self):
        source = self.complete()
        bundle = campaign.export(source, self.root / 'bundle')
        path = bundle / 'summary.json'
        summary = json.loads(path.read_text())
        summary['charged_evaluations'] = 0
        path.write_bytes(canonical_bytes(summary))
        manifest = json.loads((bundle / 'manifest.json').read_text())
        manifest['files']['summary.json'] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size}
        (bundle / 'manifest.json').write_bytes(canonical_bytes(manifest))
        with self.assertRaisesRegex(ValueError, 'Derived campaign summary'):
            campaign.verify(bundle)

    def test_html_untrusted_text_is_data_and_every_study_has_fallback_link(self):
        self.plan['question'] = '</script><script>alert(1)</script>'
        self.plan['studies'][0]['study']['question'] = '<img src=x onerror=alert(1)>'
        data = self.complete()
        page = render(data, campaign.summarize_campaign(data))
        self.assertNotIn('<script>alert(1)', page)
        self.assertNotIn('<img src=x', page)
        self.assertIn('\\u003cimg', page)
        for entry in self.plan['studies']:
            self.assertIn('studies/' + entry['id'] + '/report.html', page)
        self.assertIn('aria-live="polite"', page)
        self.assertIn('script-src \'sha256-', page)

    def test_concurrent_campaign_coordinator_refused(self):
        self.create()
        with store._writer_lock(self.directory):
            with self.assertRaises(store.CampaignBusy):
                campaign.run(self.directory)

    def test_no_op_or_confounded_ablation_is_rejected(self):
        plan = small_plan()
        plan['studies'] = plan['studies'][:2]
        for entry in plan['studies']:
            entry['study']['baseline'] = 'coordinate_fixed_step'
            entry['study']['candidate'] = 'coordinate_refinement'
        plan['studies'][1]['factor'] = 'initial_step'
        plan['studies'][1]['study']['initial_step'] = .25
        with self.assertRaisesRegex(ValueError, 'unaffected'):
            campaign.validate_plan(plan)

    def test_extra_database_sidecar_name_cannot_hide_an_extra_member(self):
        self.create()
        (self.directory / 'studies' / 'unlisted.sqlite-journal').write_text('unlisted')
        with self.assertRaisesRegex(ValueError, 'inventory differs'):
            campaign.inspect(self.directory)

    def test_reproduction_runtime_deviation_is_retained(self):
        source = self.complete()
        bundle = campaign.export(source, self.root / 'bundle')
        original_environment = store.environment()
        with patch.object(store, 'environment', lambda: original_environment | {'machine': 'different-observed-machine'}):
            campaign.create(self.plan, self.root / 'different', source=source)
            campaign.run(self.root / 'different')
        # Reading evidence is allowed; resuming under a different runtime remains forbidden.
        from continuum.evidence import compare_reproduction
        fresh = campaign.inspect(self.root / 'different')
        record = compare_reproduction(source['snapshots']['rosenbrock'], fresh['snapshots']['rosenbrock'])
        self.assertEqual(record['status'], 'INCONCLUSIVE')
        self.assertIn('environment machine differs', record['deviations'])
        self.assertTrue(all(r['status'] == 'MATCH' for r in record['comparisons']))

    def test_pause_after_skips_previously_exhausted_trials(self):
        self.create()
        db = self.directory / 'studies' / 'rosenbrock.sqlite'
        code = 'import sys; from continuum.store import run; run(sys.argv[1], _crash_at="after-admission")'
        for _ in range(2):
            process = subprocess.run([sys.executable, '-c', code, str(db)], cwd=ROOT, capture_output=True)
            self.assertEqual(process.returncode, -signal.SIGKILL)
        store.run(db, max_trials=1)
        before = campaign.summarize_campaign(campaign.inspect(self.directory))
        completed_before = sum(t['status'] == 'COMPLETED' for s in before['studies'] for t in s['summary']['trials'])
        after = campaign.summarize_campaign(campaign.run(self.directory, max_trials=1))
        completed_after = sum(t['status'] == 'COMPLETED' for s in after['studies'] for t in s['summary']['trials'])
        self.assertEqual(completed_after, completed_before + 1)
        self.assertEqual(after['failed_attempts'], 2)

    def test_completed_campaign_cannot_resume_under_a_changed_runtime(self):
        self.complete()
        environment = store.environment()
        with patch.object(store, 'environment', lambda: environment | {'machine': 'different-machine'}):
            with self.assertRaisesRegex(ValueError, 'Runtime identity changed'):
                campaign.run(self.directory)

    def test_cli_full_campaign_workflow_and_record_no_overwrite(self):
        plan = self.root / 'plan.json'
        plan.write_bytes(canonical_bytes(self.plan))
        def cli(*args):
            return subprocess.run([sys.executable, '-m', 'continuum', *map(str, args)], cwd=ROOT, capture_output=True, text=True, timeout=45)
        for args in [('campaign-init', '--plan', plan, '--dir', self.directory),
                     ('campaign-run', '--dir', self.directory, '--pause-after', 1),
                     ('campaign-resume', '--dir', self.directory),
                     ('campaign-export', '--dir', self.directory, '--out', self.root / 'bundle'),
                     ('campaign-verify', '--bundle', self.root / 'bundle'),
                     ('campaign-reproduce', '--bundle', self.root / 'bundle', '--dir', self.root / 'fresh', '--record', self.root / 'proof.json')]:
            result = cli(*args)
            self.assertEqual(result.returncode, 0, result.stderr)
        proof = (self.root / 'proof.json').read_bytes()
        result = cli('campaign-reproduce', '--bundle', self.root / 'bundle', '--dir', self.root / 'fresh', '--record', self.root / 'proof.json')
        self.assertEqual(result.returncode, 2)
        self.assertEqual((self.root / 'proof.json').read_bytes(), proof)
        before = campaign.inspect(self.root / 'fresh')
        result = cli('campaign-reproduce', '--bundle', self.root / 'bundle', '--dir', self.root / 'fresh', '--record', self.root / 'reconciled.json')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('no new execution', json.loads(result.stdout)['publication_context'])
        self.assertEqual(campaign.inspect(self.root / 'fresh'), before)


if __name__ == '__main__':
    unittest.main()
