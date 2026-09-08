#!/usr/bin/env python3
"""Verify an explicitly checksum-bound candidate in a new extracted workspace.

This executes the supplied source release. Use only an archive whose provenance
and expected digest you have already reviewed. No network or installs are used.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import signal
import subprocess
import sys
import tarfile
import time


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--sha256', required=True, help='Reviewed expected archive SHA-256')
    parser.add_argument('--work-dir', type=Path, required=True, help='New private extraction/work directory')
    parser.add_argument('--out', type=Path, required=True, help='New sanitized verification record')
    args = parser.parse_args()
    archive, work, record = args.archive.resolve(), args.work_dir.resolve(), args.out.resolve()
    if sha(archive.read_bytes()) != args.sha256:
        parser.error('Archive SHA-256 does not match the reviewed input')
    if work.exists() or record.exists():
        parser.error('Work directory and record must be new paths')
    work.mkdir(parents=True)
    checks = []
    started = datetime.now(timezone.utc).isoformat()
    try:
        with tarfile.open(archive, 'r:gz') as tar:
            members = tar.getmembers()
            if not members or len(members) > 5000 or sum(m.size for m in members) > 512 * 1024 * 1024:
                raise ValueError('Archive inventory exceeds verification bounds')
            roots, names = set(), set()
            for member in members:
                path = PurePosixPath(member.name)
                if (not member.isfile() or path.is_absolute() or '..' in path.parts or len(path.parts) < 2
                        or member.name in names or member.size > 128 * 1024 * 1024):
                    raise ValueError('Unsafe or duplicate archive member')
                roots.add(path.parts[0]); names.add(member.name)
            if len(roots) != 1:
                raise ValueError('Archive must have one package root')
            for member in members:
                destination = work / member.name
                destination.parent.mkdir(parents=True, exist_ok=True)
                with destination.open('xb') as output:
                    output.write(tar.extractfile(member).read())
        source = work / next(iter(roots))
        manifest = json.loads((source / 'PACKAGE-MANIFEST.json').read_text())
        expected = {item['path']: item for item in manifest['files']}
        actual = {str(p.relative_to(source)) for p in source.rglob('*') if p.is_file()}
        if actual != set(expected) | {'PACKAGE-MANIFEST.json'}:
            raise ValueError('Package manifest inventory differs')
        for name, item in expected.items():
            content = (source / name).read_bytes()
            if len(content) != item['bytes'] or sha(content) != item['sha256']:
                raise ValueError('Package manifest mismatch: ' + name)
        scratch = source / '.cache' / 'tests'
        scratch.mkdir(parents=True)
        env = {'PATH': os.defpath, 'LANG': 'C.UTF-8', 'TMPDIR': str(scratch), 'PYTHONDONTWRITEBYTECODE': '1'}
        logs = work / 'command-logs'; logs.mkdir()

        def run(*arguments, expected_code=0, timeout=300):
            command = [sys.executable, *map(str, arguments)]
            start = time.monotonic()
            result = subprocess.run(command, cwd=source, env=env, capture_output=True, text=True, timeout=timeout)
            number = len(checks) + 1
            (logs / f'{number:02d}.stdout').write_text(result.stdout)
            (logs / f'{number:02d}.stderr').write_text(result.stderr)
            checks.append({'command': ['python3', *[str(a).replace(str(work), '$WORK') for a in arguments]],
                           'exit_code': result.returncode, 'expected_exit_code': expected_code,
                           'elapsed_seconds': time.monotonic() - start,
                           'stdout_sha256': sha(result.stdout.encode()), 'stdout_bytes': len(result.stdout.encode()),
                           'stderr': result.stderr.replace(str(work), '$WORK')})
            print(('PASS' if result.returncode == expected_code else 'FAIL'), ' '.join(checks[-1]['command']), flush=True)
            if result.returncode != expected_code:
                raise ValueError(f'Command {number} returned {result.returncode}, expected {expected_code}')
            return result.stdout

        version = run('-m', 'continuum', '--version').strip()
        if version != 'Research Continuum ' + manifest['version']:
            raise ValueError('Runtime/package version mismatch')
        run('tools/validate_plan.py', '--self-test')
        run('tools/render_plan.py', '--check')
        test_output = run('-m', 'unittest', 'discover', '-s', 'tests', '-v')
        run('-m', 'continuum', 'campaign', '--out', work / 'draft.json')
        draft = json.loads((work / 'draft.json').read_text())
        if draft != json.loads((source / 'examples/workbench-campaign.json').read_text()):
            raise ValueError('Documented example differs from default campaign draft')
        initial = json.loads(run('-m', 'continuum', 'campaign-init', '--plan', work / 'draft.json', '--dir', work / 'campaign'))
        partial = json.loads(run('-m', 'continuum', 'campaign-run', '--dir', work / 'campaign', '--pause-after', '2'))
        run('-m', 'continuum', 'campaign-inspect', '--dir', work / 'campaign')
        done = json.loads(run('-m', 'continuum', 'campaign-resume', '--dir', work / 'campaign'))
        if (initial['study_count'] != 9 or initial['reserved_evaluations'] != 55296
                or partial['charged_evaluations'] != 256 or partial['complete']
                or not done['complete'] or done['charged_evaluations'] != 27648
                or done['recorded_evaluations'] != 27648 or done['failed_attempts'] != 0):
            raise ValueError('Default campaign count or completion invariant failed')
        old_attempts = partial['studies'][0]['summary']['trials'][0]['attempt_ids']
        if old_attempts != done['studies'][0]['summary']['trials'][0]['attempt_ids']:
            raise ValueError('Pause/resume replaced admitted attempts')
        run('-m', 'continuum', 'campaign-export', '--dir', work / 'campaign', '--out', work / 'bundle')
        run('-m', 'continuum', 'campaign-verify', '--bundle', work / 'bundle')
        reproduction = json.loads(run('-m', 'continuum', 'campaign-reproduce', '--bundle', work / 'bundle',
                                       '--dir', work / 'fresh', '--record', work / 'reproduction.json'))
        if reproduction['status'] != 'MATCH' or not reproduction['numerical_sequences_match']:
            raise ValueError('Fresh default campaign reproduction did not match')
        run('-m', 'continuum', 'campaign-reproduce', '--bundle', work / 'bundle', '--dir', work / 'fresh',
            '--record', work / 'reproduction.json', expected_code=2)
        if json.loads((work / 'reproduction.json').read_text()) != reproduction:
            raise ValueError('Overwrite refusal changed accepted reproduction record')
        # Real process death inside a member ledger, followed by campaign-level recovery.
        recovery = json.loads(json.dumps(draft)); recovery['studies'] = recovery['studies'][:2]
        for entry in recovery['studies']:
            entry['study'].update(evaluations_per_policy=8, development_seeds=[11], confirmation_seeds=[101])
        (work / 'recovery-draft.json').write_text(json.dumps(recovery))
        run('-m', 'continuum', 'campaign-init', '--plan', work / 'recovery-draft.json', '--dir', work / 'recovery')
        run('-c', 'import sys; from continuum.store import run; run(sys.argv[1], _crash_at="after-admission")',
            work / 'recovery' / 'studies' / 'rosenbrock.sqlite', expected_code=-signal.SIGKILL)
        recovered = json.loads(run('-m', 'continuum', 'campaign-resume', '--dir', work / 'recovery'))
        if (not recovered['complete'] or recovered['failed_attempts'] != 1 or recovered['charged_evaluations'] != 136
                or recovered['recorded_evaluations'] != 128 or recovered['ablations'][0]['eligible']):
            raise ValueError('Process-death accounting or ablation eligibility failed')
        run('-m', 'continuum', 'campaign-export', '--dir', work / 'recovery', '--out', work / 'recovery-bundle')
        run('-m', 'continuum', 'campaign-verify', '--bundle', work / 'recovery-bundle')
        # Source files must not change while running tests or the documented workflow.
        for name, item in expected.items():
            if sha((source / name).read_bytes()) != item['sha256']:
                raise ValueError('Packaged source mutated during verification: ' + name)
        result = {'schema_version': 1, 'status': 'PASS', 'evidence_level': 'PACKAGED_RUNTIME',
                  'started_at': started, 'finished_at': datetime.now(timezone.utc).isoformat(),
                  'archive_sha256': args.sha256, 'version': manifest['version'], 'package_files': len(expected),
                  'default': {k: done[k] for k in ('study_count', 'complete', 'charged_evaluations', 'recorded_evaluations', 'reserved_evaluations', 'failed_attempts')},
                  'reproduction': {'status': reproduction['status'], 'numerical_sequences_match': reproduction['numerical_sequences_match'],
                                   'source_execution_id': reproduction['source_execution_id'], 'fresh_execution_id': reproduction['fresh_execution_id']},
                  'recovery': {k: recovered[k] for k in ('complete', 'charged_evaluations', 'recorded_evaluations', 'failed_attempts')},
                  'checks': checks, 'source_unchanged': True,
                  'limitations': ['Agent execution in a fresh extraction on the same host; not external or human evidence.',
                                  'Real SIGKILL recovery does not establish hardware power-loss durability.',
                                  'No publication or independent scientific validity is established.']}
    except (OSError, ValueError, KeyError, tarfile.TarError, subprocess.SubprocessError) as exc:
        result = {'schema_version': 1, 'status': 'FAIL', 'started_at': started, 'archive_sha256': args.sha256,
                  'error': str(exc).replace(str(work), '$WORK'), 'checks': checks}
    record.parent.mkdir(parents=True, exist_ok=True)
    with record.open('x') as output:
        json.dump(result, output, indent=2); output.write('\n')
    print(result['status'], str(record))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
