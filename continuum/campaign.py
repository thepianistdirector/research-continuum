"""Frozen finite multi-study campaigns over the durable single-study engine."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile
import uuid

from . import store
from .analysis import STOCHASTIC, paired_uncertainty
from .evidence import (canonical_bytes, compare_reproduction, export_bundle, summarize, verify_bundle,
                       _keys, _read_json, _rename_noreplace, _require, _sync_directory)
from .study import Study, builtin_study

MAX_STUDIES = 32
MAX_CLEAN_EVALUATIONS = 1_048_576
MAX_JSON = 2 * 1024 * 1024
TEXT_FIELDS = frozenset({'study_id', 'revision', 'question', 'hypothesis', 'falsifier'})
ABLATION_FACTORS = frozenset({'candidate', 'initial_step', 'start'})


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def read_json(path, limit=MAX_JSON):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as f:
        info = os.fstat(f.fileno())
        _require(stat.S_ISREG(info.st_mode) and info.st_size <= limit, 'Expected bounded regular JSON file')
        data = f.read(limit + 1)
        _require(len(data) == info.st_size, 'JSON file changed during read')
    return _read_json(data)


def write_file(path, data):
    with Path(path).open('xb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())


def validate_plan(plan):
    _keys(plan, 'schema_version campaign_id question studies', 'campaign plan')
    _require(type(plan['schema_version']) is int and plan['schema_version'] == 1, 'Unsupported campaign schema')
    _require(type(plan['campaign_id']) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', plan['campaign_id']), 'Invalid campaign id')
    _require(type(plan['question']) is str and 0 < len(plan['question'].strip()) <= 2000, 'Invalid campaign question')
    _require(type(plan['studies']) is list and 1 <= len(plan['studies']) <= MAX_STUDIES, 'Campaign requires 1–32 studies')
    by_id, total = {}, 0
    for entry in plan['studies']:
        _keys(entry, 'id study ablation_of factor', 'campaign entry')
        key = entry['id']
        _require(type(key) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', key), 'Invalid study entry id')
        _require(key not in by_id, 'Duplicate study entry id')
        study = Study.from_dict(entry['study'])
        _require(study.to_dict() == entry['study'], 'Campaign study must be canonical')
        total += study.total_clean_evaluations
        if entry['ablation_of'] is None:
            _require(entry['factor'] is None, 'Unlinked study cannot declare an ablation factor')
        else:
            _require(type(entry['ablation_of']) is str and entry['ablation_of'] in by_id, 'Ablation reference must precede variant')
            _require(type(entry['factor']) is str and entry['factor'] in ABLATION_FACTORS, 'Unsupported ablation factor')
            reference = by_id[entry['ablation_of']]['study']
            changed = {k for k in reference if k not in TEXT_FIELDS and reference[k] != entry['study'][k]}
            _require(changed == {entry['factor']}, 'Ablation must change exactly its declared computational field')
            _require(study.baseline in ('uniform_random', 'grid_search')
                     and study.candidate in ('coordinate_refinement', 'coordinate_fixed_step'),
                     'Ablation requires a coordinate candidate and an unaffected random or grid baseline')
            if entry['factor'] == 'candidate':
                _require({reference['candidate'], study.candidate} == {'coordinate_refinement', 'coordinate_fixed_step'},
                         'Candidate ablation must isolate coordinate step halving')
        by_id[key] = entry
    _require(total <= MAX_CLEAN_EVALUATIONS, 'Campaign aggregate clean allowance exceeds 1048576 evaluations')
    return plan


def default_plan():
    entries = []
    for objective in ('rosenbrock-2d-v1', 'sphere-2d-v1', 'ellipsoid-2d-v1'):
        prefix = objective.split('-')[0]
        reference = builtin_study(objective).to_dict()
        entries.append({'id': prefix, 'study': reference, 'ablation_of': None, 'factor': None})
        variant = builtin_study(objective, candidate='coordinate_fixed_step').to_dict()
        entries.append({'id': prefix + '-fixed-step', 'study': variant, 'ablation_of': prefix, 'factor': 'candidate'})
        grid = builtin_study(objective, baseline='grid_search').to_dict()
        entries.append({'id': prefix + '-grid', 'study': grid, 'ablation_of': None, 'factor': None})
    return validate_plan({'schema_version': 1, 'campaign_id': 'numerical-workbench',
                          'question': 'How do bounded coordinate search and its step-halving ablation compare with random and grid baselines across three public numerical fixtures?',
                          'studies': entries})


def validate_frozen(frozen):
    _keys(frozen, 'schema_version type execution_id created_at plan plan_digest reproduction_source', 'frozen campaign')
    _require(type(frozen['schema_version']) is int and frozen['schema_version'] == 1
             and frozen['type'] == 'FrozenCampaign', 'Unsupported frozen campaign')
    _require(type(frozen['execution_id']) is str and re.fullmatch('[0-9a-f]{32}', frozen['execution_id']), 'Invalid campaign execution id')
    from .evidence import _timestamp, _digest
    _timestamp(frozen['created_at'])
    validate_plan(frozen['plan'])
    _require(frozen['plan_digest'] == digest(frozen['plan']), 'Campaign plan digest mismatch')
    if frozen['reproduction_source'] is not None:
        _digest(frozen['reproduction_source'], 'campaign reproduction source')
    return frozen


def _binding(frozen, entry):
    return {'id': frozen['execution_id'] + '-' + entry['id'], 'digest': digest(frozen)}


def validate_members(frozen, snapshots):
    validate_frozen(frozen)
    _require(type(snapshots) is dict and set(snapshots) == {e['id'] for e in frozen['plan']['studies']}, 'Campaign study inventory differs')
    ids = set()
    for entry in frozen['plan']['studies']:
        snapshot = snapshots[entry['id']]
        _require(snapshot['study'] == entry['study'], 'Campaign member protocol differs')
        _require(snapshot['campaign_id'] not in ids, 'Campaign reuses a member execution identity')
        ids.add(snapshot['campaign_id'])
        binding = _binding(frozen, entry)
        sources = [s for s in snapshot['source_records'] if s['id'] == 'source-workbench-' + binding['id']]
        _require(len(sources) == 1 and sources[0]['locator'] == 'sha256:' + binding['digest'],
                 'Study was not frozen for this complete campaign inventory')


def create(plan, directory, *, source=None):
    plan = _read_json(canonical_bytes(validate_plan(plan)))
    destination = Path(directory).absolute()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with store._writer_lock(destination):
        _require(not os.path.lexists(destination), 'Campaign directory exists; resume or choose a new path')
        if source is not None:
            validate_members(source['frozen'], source['snapshots'])
            _require(source['frozen']['plan'] == plan, 'Reproduction must retain the full source plan')
        frozen = {'schema_version': 1, 'type': 'FrozenCampaign', 'execution_id': uuid.uuid4().hex,
                  'created_at': store.now(), 'plan': plan, 'plan_digest': digest(plan),
                  'reproduction_source': digest(source) if source is not None else None}
        staging = Path(tempfile.mkdtemp(prefix='.' + destination.name + '.staging-', dir=destination.parent))
        try:
            write_file(staging / 'campaign.json', canonical_bytes(frozen))
            (staging / 'studies').mkdir()
            for entry in plan['studies']:
                original = source['snapshots'][entry['id']] if source is not None else None
                store.create(Study.from_dict(entry['study']), staging / 'studies' / (entry['id'] + '.sqlite'),
                             campaign_source=_binding(frozen, entry),
                             expected_evaluator=original['evaluator_digest'] if original else None,
                             reproduction_source={'campaign_id': original['campaign_id'], 'evidence_digest': digest(original)} if original else None)
            _sync_directory(staging / 'studies')
            _sync_directory(staging)
            _rename_noreplace(staging, destination)
            _sync_directory(destination.parent)
        finally:
            if staging.exists():
                shutil.rmtree(staging)
    return inspect(destination)


def inspect(directory):
    directory = Path(directory)
    _require(directory.is_dir() and not directory.is_symlink(), 'Campaign must be a real directory')
    frozen = validate_frozen(read_json(directory / 'campaign.json'))
    members = directory / 'studies'
    _require(members.is_dir() and not members.is_symlink(), 'Campaign studies must be a real directory')
    expected = {e['id'] + '.sqlite' for e in frozen['plan']['studies']}
    actual = {p.name for p in members.iterdir()}
    allowed = expected | {name + suffix for name in expected for suffix in ('.lock', '-journal', '-wal', '-shm')}
    _require(expected <= actual <= allowed, 'Campaign database inventory differs')
    snapshots = {e['id']: store.inspect(members / (e['id'] + '.sqlite')) for e in frozen['plan']['studies']}
    validate_members(frozen, snapshots)
    return {'frozen': frozen, 'snapshots': snapshots}


def run(directory, *, max_trials=None):
    directory = Path(directory).absolute()
    if max_trials is not None:
        _require(type(max_trials) is int and max_trials > 0, 'pause-after must be a positive integer')
    with store._writer_lock(directory):
        current = inspect(directory)
        environment = store.environment()
        _require(all(snapshot["environment"] == environment for snapshot in current["snapshots"].values()),
                 "Runtime identity changed; resume using the original release and environment")
        remaining = max_trials
        for entry in current['frozen']['plan']['studies']:
            before = summarize(current['snapshots'][entry['id']])
            pending = sum(t['status'] == 'PENDING' for t in before['trials'])
            if not pending:
                continue
            store.run(directory / 'studies' / (entry['id'] + '.sqlite'), max_trials=remaining)
            if remaining is not None:
                remaining -= min(pending, remaining)
                if remaining == 0:
                    break
    return inspect(directory)


def summarize_campaign(data):
    frozen, snapshots = data['frozen'], data['snapshots']
    validate_members(frozen, snapshots)
    summaries = {key: summarize(value) for key, value in snapshots.items()}
    studies, ablations = [], []
    for entry in frozen['plan']['studies']:
        summary = summaries[entry['id']]
        studies.append({'id': entry['id'], 'objective': entry['study']['evaluator'],
                        'baseline': entry['study']['baseline'], 'candidate': entry['study']['candidate'],
                        'ablation_of': entry['ablation_of'], 'factor': entry['factor'], 'summary': summary})
        if entry['ablation_of'] is not None:
            reference = summaries[entry['ablation_of']]
            ref_entry = next(e for e in frozen['plan']['studies'] if e['id'] == entry['ablation_of'])
            pairs, rows = [], []
            for candidate_summary, protocol in ((reference, ref_entry['study']), (summary, entry['study'])):
                rows.append({r['seed']: r for r in candidate_summary['trials']
                             if r['phase'] == 'confirmation' and r['policy'] == protocol['candidate']})
            for seed in entry['study']['confirmation_seeds']:
                left, right = (r[seed] for r in rows)
                if left['status'] == right['status'] == 'COMPLETED':
                    pairs.append((left['best'], right['best']))
            eligible = (all(s['verdict'] != 'INCONCLUSIVE' for s in (reference, summary))
                        and all(rows[0][seed]['charged_evaluations'] == rows[1][seed]['charged_evaluations']
                                for seed in entry['study']['confirmation_seeds']))
            uncertainty = paired_uncertainty(pairs, stochastic=bool({ref_entry['study']['candidate'], entry['study']['candidate']} & STOCHASTIC), eligible=eligible)
            ablations.append({'reference': entry['ablation_of'], 'variant': entry['id'], 'factor': entry['factor'],
                              'eligible': eligible, 'uncertainty': uncertainty,
                              'trial_links': [{'reference': rows[0][s]['trial_id'], 'variant': rows[1][s]['trial_id']}
                                              for s in entry['study']['confirmation_seeds']],
                              'scope': 'Paired candidate outcomes for one frozen factor change; no cross-objective pooling or general causal claim.'})
    return {'schema_version': 1, 'execution_id': frozen['execution_id'], 'plan_digest': frozen['plan_digest'],
            'question': frozen['plan']['question'], 'study_count': len(studies),
            'complete': all(s['campaign_complete'] for s in summaries.values()),
            'charged_evaluations': sum(s['charged_evaluations'] for s in summaries.values()),
            'recorded_evaluations': sum(s['recorded_evaluations'] for s in summaries.values()),
            'reserved_evaluations': sum(s['reserved_evaluations'] for s in summaries.values()),
            'failed_attempts': sum(s['failed_attempts'] for s in summaries.values()),
            'studies': studies, 'ablations': ablations, 'claim_status': 'UNREVIEWED',
            'limitations': ['Objectives have different scales; there is no pooled winner or ranking.',
                            'All frozen studies, failed attempts and null outcomes are retained.',
                            'Seed resampling is descriptive, not a population confidence guarantee.',
                            'Human and qualified domain review remain pending.']}


def export(data, destination):
    summary = summarize_campaign(data)
    _require(summary['complete'], 'Only terminal campaigns can be exported')
    destination = Path(destination).absolute()
    _require(not os.path.lexists(destination), 'Campaign export already exists')
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.' + destination.name + '.staging-', dir=destination.parent))
    try:
        (staging / 'studies').mkdir()
        for key, snapshot in data['snapshots'].items():
            export_bundle(snapshot, staging / 'studies' / key)
        from .workbench import render
        write_file(staging / 'campaign.json', canonical_bytes(data['frozen']))
        write_file(staging / 'summary.json', canonical_bytes(summary))
        write_file(staging / 'index.html', render(data, summary).encode())
        files = {str(p.relative_to(staging)): {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size}
                 for p in sorted(staging.rglob('*')) if p.is_file()}
        write_file(staging / 'manifest.json', canonical_bytes({'schema_version': 1, 'type': 'CampaignBundle',
                   'source_digest': digest(data), 'files': files}))
        _sync_directory(staging / 'studies')
        _sync_directory(staging)
        verify(staging)
        _rename_noreplace(staging, destination)
        _sync_directory(destination.parent)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return destination


def verify(directory):
    directory = Path(directory)
    _require(directory.is_dir() and not directory.is_symlink(), 'Bundle must be a real directory')
    _require({p.name for p in directory.iterdir()} == {'campaign.json', 'summary.json', 'index.html', 'manifest.json', 'studies'}, 'Campaign bundle root inventory differs')
    frozen = validate_frozen(read_json(directory / 'campaign.json'))
    studies_path = directory / 'studies'
    _require(studies_path.is_dir() and not studies_path.is_symlink(), 'Unsafe studies directory')
    _require({p.name for p in studies_path.iterdir()} == {e['id'] for e in frozen['plan']['studies']}, 'Bundle study inventory differs')
    from .evidence import FILE_LIMIT
    total = 0
    for entry in frozen['plan']['studies']:
        member = studies_path / entry['id']
        _require(member.is_dir() and not member.is_symlink(), 'Unsafe member directory')
        for name in ('evidence.json', 'summary.json', 'records.json', 'report.html', 'manifest.json'):
            info = (member / name).lstat()
            _require(stat.S_ISREG(info.st_mode) and info.st_size <= FILE_LIMIT, 'Unsafe or oversized member file')
            total += info.st_size
            _require(total <= 512 * 1024 * 1024, 'Campaign bundle exceeds 512 MiB')
    snapshots = {e['id']: verify_bundle(studies_path / e['id']) for e in frozen['plan']['studies']}
    data = {'frozen': frozen, 'snapshots': snapshots}
    summary = summarize_campaign(data)
    manifest = read_json(directory / 'manifest.json')
    _keys(manifest, 'schema_version type source_digest files', 'campaign manifest')
    _require(type(manifest['schema_version']) is int and manifest['schema_version'] == 1 and manifest['type'] == 'CampaignBundle', 'Unsupported campaign manifest')
    expected = {'campaign.json', 'summary.json', 'index.html'} | {
        f'studies/{e["id"]}/{name}' for e in frozen['plan']['studies']
        for name in ('evidence.json', 'summary.json', 'records.json', 'report.html', 'manifest.json')}
    _require(type(manifest['files']) is dict and set(manifest['files']) == expected, 'Campaign manifest inventory differs')
    # Member bundles have already enforced their own bounded regular-file inventory.
    from .evidence import FILE_LIMIT
    total = 0
    for name in sorted(expected):
        path = directory / name
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, 'rb') as f:
            info = os.fstat(f.fileno())
            _require(stat.S_ISREG(info.st_mode) and info.st_size <= FILE_LIMIT, 'Unsafe or oversized bundle file')
            total += info.st_size
            _require(total <= 512 * 1024 * 1024, 'Campaign bundle exceeds 512 MiB')
            content = f.read(FILE_LIMIT + 1)
            _require(len(content) == info.st_size, 'Bundle changed during verification')
        _require(manifest['files'][name] == {'sha256': hashlib.sha256(content).hexdigest(), 'bytes': len(content)}, 'Campaign checksum mismatch: ' + name)
    _require(manifest['source_digest'] == digest(data), 'Campaign source digest mismatch')
    _require(read_json(directory / 'summary.json', 32 * 1024 * 1024) == summary, 'Derived campaign summary differs')
    from .workbench import render
    _require((directory / 'index.html').read_bytes() == render(data, summary).encode(), 'Derived workbench differs')
    return data


def reproduce(bundle, directory):
    source = verify(bundle)
    directory = Path(directory)
    if os.path.lexists(directory):
        fresh = inspect(directory)
        _require(fresh['frozen']['reproduction_source'] == digest(source), 'Existing campaign was not created for reproducing this exact bundle')
        _require(fresh['frozen']['plan'] == source['frozen']['plan'], 'Reproduction plan differs')
    else:
        create(source['frozen']['plan'], directory, source=source)
    fresh = run(directory)
    _require(fresh['frozen']['execution_id'] != source['frozen']['execution_id'], 'Reproduction must be a fresh campaign')
    records = {key: compare_reproduction(source['snapshots'][key], fresh['snapshots'][key]) for key in source['snapshots']}
    status = 'MISMATCH' if any(r['status'] == 'MISMATCH' for r in records.values()) else (
        'MATCH' if all(r['status'] == 'MATCH' for r in records.values()) else 'INCONCLUSIVE')
    return {'schema_version': 1, 'type': 'CampaignReproduction', 'status': status,
            'source_digest': digest(source), 'fresh_digest': digest(fresh),
            'source_execution_id': source['frozen']['execution_id'], 'fresh_execution_id': fresh['frozen']['execution_id'],
            'records': records, 'review_status': 'UNREVIEWED',
            'numerical_sequences_match': all(c['status'] == 'MATCH' for r in records.values() for c in r['comparisons']),
            'scope': 'Fresh source-bound execution; runtime deviations remain explicit and may make the overall result inconclusive.'}
