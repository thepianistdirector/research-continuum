#!/usr/bin/env python3
"""Validate canonical planning, lineage and generated views; not scientific validity."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import re
import sys
import shutil
import tempfile
from pathlib import Path, PurePosixPath
from render_plan import generated_files

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / 'plan/tasks.json'
FOUNDATION_IDS = ['RC-F01', 'RC-F02', 'RC-F03']
SOURCE_IDS = FOUNDATION_IDS + [f'RC-{n:03d}' for n in range(1, 25)]
STATUSES = {'PLANNED', 'IN PROGRESS', 'IMPLEMENTED', 'AUTOMATED PASS', 'RUNTIME VERIFIED', 'USER VALIDATED', 'RELEASE VERIFIED', 'BLOCKED', 'FAILED', 'NOT TESTED', 'DONE'}
RELEASES = {'foundation', '0.1', 'later 0.x', 'long-term', 'exploratory'}
LINEAGE_HASHES = {
 'architecture-foundation-2026-09-07/tasks.json': 'f6f600eb5b6b449a0d1efeb7297cf99d5a0d2b65fb0b82f112ec46df0a4bf512',
 'architecture-foundation-2026-09-07/TASKS.md': '365c7b46e7baa4d54b5d18b5b85e452fa04fe4604f47355c221f9a3acceb29b9',
 'architecture-foundation-2026-09-07/ROADMAP.md': '12e2218c8748ff326ffa0e7fc19a47312f174794b4307229b0c75a77fcd2e2f9',
 'architecture-foundation-2026-09-07/STATUS.md': 'bebac26b2037bdd7e76f16e80c7eaaed1e92fb98ac97720695208292d7885c2d',
 'pre-foundation/tasks.json': '94cf19e780277ede37db6e5045c64708932b537700651e923e3aec33a9ebb299',
 'pre-foundation/TASKS.md': 'fc2cf64d2aa0beeadf7e38fbc1028f81a0b7f967ef84a349de44ee19e05f26f2',
 'pre-foundation/ROADMAP.md': '5f239b487d59420946bd3d6d13f31b1a8af31c122b494cc6f76c4be1edff3f86',
 'pre-foundation/STATUS.md': '2018e3351a0c805ab48c99d4d8ef54cbdf446c45416bd615a38544a6f19646c9',
}
# Reviewed load-bearing 0.1 prerequisites. The exact original DAG is preserved
# separately; these new edges cannot complete an old scientific contract.
CRITICAL_EDGES = {
 'RC-W02-T05': ['RC-W02-T02', 'RC-W02-T04'],
 'RC-W02-T07': ['RC-W02-T05', 'RC-W02-T06'],
 'RC-W03-T06': ['RC-W03-T02', 'RC-W03-T03', 'RC-W03-T04', 'RC-W03-T05'],
 'RC-W05-T04': ['RC-W05-T02', 'RC-W05-T03'], 'RC-W05-T05': ['RC-W05-T04'],
 'RC-W05-T06': ['RC-W05-T05'], 'RC-W05-T07': ['RC-W05-T06'],
 'RC-W05-T08': ['RC-W05-T06', 'RC-W05-T07'], 'RC-W05-T09': ['RC-W05-T08'],
 'RC-W05-T10': ['RC-W05-T09'], 'RC-W05-T11': ['RC-W05-T08', 'RC-W05-T09'],
}

def nonempty(value):
 return isinstance(value, str) and bool(value.strip())

def text_list(value, allow_empty=True):
 return isinstance(value, list) and (allow_empty or bool(value)) and all(nonempty(v) for v in value) and len(value) == len(set(value))

def normalized(value):
 return re.sub(r'[^a-z0-9]+', ' ', value.casefold()).strip()

def local_path(value):
 return nonempty(value) and not value.startswith('/') and '\\' not in value and all(p not in {'.', '..'} for p in PurePosixPath(value).parts)

def validate_plan_dict(plan):
 if not isinstance(plan, dict): return ['plan root must be a JSON object']
 errors = []
 if type(plan.get('schemaVersion')) is not int or plan.get('schemaVersion') != 2: errors.append('schemaVersion must be integer 2')
 if plan.get('project') != 'research-continuum': errors.append('project identity must be research-continuum')
 if plan.get('stateAuthority') != 'tasks.json' or plan.get('statusNarrative') != '../STATUS.md': errors.append('canonical stateAuthority or statusNarrative invalid')
 for field in ('contractVersion', 'objective', 'lineageManifest'):
  if not nonempty(plan.get(field)): errors.append(f'{field} must be non-empty text')
 for field in ('tasks', 'waves', 'sourceMappings', 'sourceRecords', 'planningDecisions'):
  if not isinstance(plan.get(field), list) or not plan[field] or not all(isinstance(v, dict) for v in plan[field]): errors.append(f'{field} must be a non-empty object list')
 if not isinstance(plan.get('publication'), dict): errors.append('publication must be an object')
 if not text_list(plan.get('terminalOutcomes'), False): errors.append('terminalOutcomes must name programme exits')
 if errors: return errors
 tasks = plan['tasks']
 if not 200 <= len(tasks) <= 400: errors.append('task count must be 200–400; shortfall remains a visible gate')
 for index, task in enumerate(tasks):
  for field in ('id', 'title', 'outcome', 'featureArea', 'acceptance', 'riskEvidenceNeeds', 'basis'):
   if not nonempty(task.get(field)): errors.append(f'task[{index}].{field} must be non-empty text')
  for field in ('dependsOn', 'sourceRefs', 'decisionRefs', 'evidenceRefs'):
   if not text_list(task.get(field), field in {'dependsOn', 'evidenceRefs'}): errors.append(f'task[{index}].{field} must be a unique text list')
  if type(task.get('wave')) is not int or task['wave'] < 0: errors.append(f'task[{index}].wave must be a non-negative integer, not boolean')
  if not isinstance(task.get('status'), str) or task['status'] not in STATUSES: errors.append(f'task[{index}].status invalid')
  if not isinstance(task.get('targetRelease'), str) or task['targetRelease'] not in RELEASES: errors.append(f'task[{index}].targetRelease invalid')
  if not isinstance(task.get('dependencyRationale'), dict) or not all(nonempty(k) and nonempty(v) for k,v in task['dependencyRationale'].items()): errors.append(f'task[{index}].dependencyRationale must explain prerequisite outcomes')
  if task.get('platformId') is not None and not nonempty(task['platformId']): errors.append(f'task[{index}].platformId invalid')
 for index,wave in enumerate(plan['waves']):
  for field in ('id', 'title', 'outcome', 'exitEvidence', 'targetRelease'):
   if not nonempty(wave.get(field)): errors.append(f'wave[{index}].{field} must be non-empty text')
  if type(wave.get('number')) is not int: errors.append(f'wave[{index}].number must be integer')
  for field in ('taskIds', 'entryDependencies'):
   if not text_list(wave.get(field), field=='entryDependencies'): errors.append(f'wave[{index}].{field} must be unique IDs')
 if errors: return errors
 ids=[t['id'] for t in tasks]; by_id={t['id']:t for t in tasks}; position={v:i for i,v in enumerate(ids)}
 if len(by_id)!=len(ids): errors.append('duplicate task ID')
 if ids[:3]!=FOUNDATION_IDS: errors.append('retained foundation identities/order changed')
 for field in ('title','outcome','acceptance'):
  seen={}
  for task in tasks:
   key=normalized(task[field])
   if key in seen: errors.append(f'duplicate {field}/outcome: {seen[key]} and {task["id"]}')
   seen[key]=task['id']
 for task in tasks:
  identifier=task['id']
  if re.fullmatch(r'RC-(?:F0[123]|W\d{2}-T\d{2})',identifier) is None: errors.append(f'unsupported task identity {identifier}')
  if set(task['dependencyRationale'])!=set(task['dependsOn']): errors.append(f'{identifier} prerequisite explanations differ from dependencies')
  if identifier not in FOUNDATION_IDS and task['status']=='DONE': errors.append(f'{identifier} cannot acquire historical DONE by planning')
  if task['status'] not in {'PLANNED','NOT TESTED'} and not task['evidenceRefs']: errors.append(f'{identifier} advanced status needs actual evidence references')
  if task['wave'] in range(1,6) and task['targetRelease']!='0.1': errors.append(f'{identifier} release-scope mismatch')
  if task['targetRelease']=='0.1' and task['wave'] not in range(1,6): errors.append(f'{identifier} expands 0.1 beyond five waves')
  for dependency in task['dependsOn']:
   if dependency not in by_id: errors.append(f'{identifier} missing dependency {dependency}')
   elif position[dependency]>=position[identifier]: errors.append(f'{identifier} dependency {dependency} is not earlier in plan order')
   elif task['targetRelease']=='0.1' and by_id[dependency]['targetRelease'] not in {'foundation','0.1'}: errors.append(f'{identifier} later-scope prerequisite on narrow path')
  if any(v not in SOURCE_IDS for v in task['sourceRefs']): errors.append(f'{identifier} unknown historical source reference')
 for identifier,dependencies in CRITICAL_EDGES.items():
  if identifier not in by_id or not set(dependencies)<=set(by_id[identifier]['dependsOn']): errors.append(f'{identifier} missing critical prerequisite outcome coverage')
 visiting,visited=set(),set()
 def visit(identifier):
  if identifier in visiting: errors.append(f'dependency cycle reaches {identifier}'); return
  if identifier in visited: return
  visiting.add(identifier)
  for dependency in by_id[identifier]['dependsOn']:
   if dependency in by_id: visit(dependency)
  visiting.remove(identifier); visited.add(identifier)
 for identifier in by_id: visit(identifier)
 waves=plan['waves']
 if not 20<=len(waves)<=32: errors.append('wave count outside outcome/platform envelope 20–32')
 if [w['number'] for w in waves]!=list(range(len(waves))): errors.append('wave numbers must be contiguous and ordered')
 if [i for w in waves for i in w['taskIds']]!=ids: errors.append('wave assignment/order has orphan, duplicate or misplaced tasks')
 for wave in waves:
  if wave['id']!=f'RC-W{wave["number"]:02d}' or len(wave['title'])>80: errors.append(f'{wave["id"]} identity/title exceeds native contract')
  for identifier in wave['taskIds']:
   if identifier not in by_id: errors.append(f'{wave["id"]} unknown task {identifier}')
   elif by_id[identifier]['wave']!=wave['number']: errors.append(f'{identifier} wave membership mismatch')
   elif by_id[identifier]['targetRelease'] not in {wave['targetRelease'],'exploratory'}: errors.append(f'{identifier} horizon differs from wave')
  if any(i not in by_id for i in wave['entryDependencies']): errors.append(f'{wave["id"]} dangling entry dependency')
 mappings=plan['sourceMappings']
 if [m.get('sourceId') for m in mappings]!=SOURCE_IDS: errors.append('missing, duplicate or reordered source mappings')
 mapping_by_id={m.get('sourceId'):m for m in mappings if isinstance(m.get('sourceId'),str)}
 try:
  original=json.loads((ROOT/'plan/lineage/architecture-foundation-2026-09-07/tasks.json').read_text())
  original_by_id={t['id']:t for t in original['tasks']}
 except (OSError,ValueError,KeyError,TypeError) as exc: return errors+[f'cannot read historical contracts: {exc}']
 referenced=set()
 for mapping in mappings:
  identifier=mapping.get('sourceId')
  if not isinstance(identifier,str) or identifier not in original_by_id: errors.append('unsupported source mapping identity'); continue
  source=original_by_id[identifier]
  expected={'sourceKey':'research-continuum:'+identifier,'sourceRevision':original['contractVersion'],'originalStatus':source['status'],'originalAcceptance':source['acceptance'],'structuredPrerequisites':source['dependsOn'],'textualPrerequisites':[],'frozenPredecessor':None}
  for field,value in expected.items():
   if mapping.get(field)!=value: errors.append(f'{identifier} historical {field} changed or omitted')
  if not isinstance(mapping.get('treatment'),str) or mapping['treatment'] not in {'retained','expanded','split','merged','deferred','superseded'}: errors.append(f'{identifier} invalid treatment')
  for field in ('reason','textualPrerequisiteEvidence','prerequisiteCoverage','sourceContract'):
   if not nonempty(mapping.get(field)): errors.append(f'{identifier} lacks {field}')
  for field in ('successorIds','narrowSuccessorIds','expandedSuccessorIds','historyRefs'):
   if not text_list(mapping.get(field),field in {'narrowSuccessorIds','expandedSuccessorIds'}): errors.append(f'{identifier} invalid or missing {field}')
  if not text_list(mapping.get('successorIds'),False): continue
  referenced.update(mapping['successorIds'])
  for successor in mapping['successorIds']:
   if successor not in by_id: errors.append(f'{identifier} dangling successor {successor}')
   elif identifier not in by_id[successor]['sourceRefs']: errors.append(f'{identifier}/{successor} missing reciprocal source reference')
  expected_narrow=[i for i in mapping['successorIds'] if i in by_id and by_id[i]['targetRelease']=='0.1']
  if mapping.get('narrowSuccessorIds')!=expected_narrow: errors.append(f'{identifier} narrow mapping misrepresents original scope')
  coverage={d:mapping_by_id.get(d,{}).get('successorIds') for d in source['dependsOn']}
  if mapping.get('prerequisiteOutcomeCoverage')!=coverage: errors.append(f'{identifier} missing original prerequisite outcome coverage')
 if referenced!=set(ids): errors.append('orphan tasks or dangling IDs in complete source mapping coverage')
 for identifier in FOUNDATION_IDS:
  if identifier in by_id:
   for field,value in original_by_id[identifier].items():
    if by_id[identifier].get(field)!=value: errors.append(f'{identifier} retained foundation {field} changed')
 decision_ids={s.get('id') for s in plan['sourceRecords'] if isinstance(s.get('id'),str)}
 for task in tasks:
  if any(d not in decision_ids for d in task['decisionRefs']): errors.append(f'{task["id"]} dangling decision reference')
 pub=plan['publication']
 if not isinstance(pub.get('platformMapping'),dict) or pub['platformMapping']!={t['id']:t['platformId'] for t in tasks}: errors.append('native platform mapping differs from row identities')
 if not isinstance(pub.get('status'),str) or pub['status'] not in STATUSES: errors.append('publication status invalid')
 access=pub.get('releaseAccess')
 if not isinstance(access,dict) or not nonempty(access.get('instructions')): errors.append('release access instructions missing')
 elif access.get('status')=='RELEASE VERIFIED' and not all(nonempty(access.get(k)) for k in ('version','url')): errors.append('verified release needs actual version and URL')
 if not any('cycle' in e for e in errors):
  ancestors={}
  def predecessors(identifier):
   if identifier not in ancestors:
    result=set()
    for dependency in by_id[identifier]['dependsOn']:
     if dependency in by_id:
      result.add(dependency); result.update(predecessors(dependency))
    ancestors[identifier]=result
   return ancestors[identifier]
  for wave in waves:
   for identifier in wave['taskIds']:
    if identifier in by_id and not set(wave['entryDependencies'])<=predecessors(identifier): errors.append(f'{identifier} lacks wave-entry prerequisite outcome coverage')
  reachable=set()
  def collect(identifier):
   if identifier in reachable or identifier not in by_id: return
   reachable.add(identifier)
   for dependency in by_id[identifier]['dependsOn']: collect(dependency)
  for identifier in plan['terminalOutcomes']:
   if identifier not in by_id: errors.append('dangling terminal outcome')
   collect(identifier)
  if reachable!=set(ids): errors.append('orphan task outcomes do not feed intended programme exits')
 return errors

def validate_lineage(root=ROOT):
 errors=[]; expected={}
 for relative,digest in LINEAGE_HASHES.items():
  expected['plan/lineage/'+relative]=digest
  try:
   if hashlib.sha256((root/'plan/lineage'/relative).read_bytes()).hexdigest()!=digest: errors.append(f'immutable lineage changed: {relative}')
  except OSError: errors.append(f'immutable lineage missing: {relative}')
 try:
  records=json.loads((root/'plan/lineage/manifest.json').read_text())['records']
  if {r['path']:r['sha256'] for r in records}!=expected or len(records)!=len(expected): errors.append('lineage manifest differs from retained historical identities')
 except (OSError,ValueError,KeyError,TypeError): errors.append('lineage manifest malformed or missing')
 return errors

def validate_documents(plan, root=ROOT):
 errors=[]
 for relative,expected in generated_files(plan).items():
  try:
   if (root/relative).read_text(encoding='utf-8')!=expected: errors.append(f'generated document/export parity failed: {relative}')
  except OSError: errors.append(f'generated document/export missing: {relative}')
 for source in plan['sourceRecords']:
  locator=source.get('locator')
  if not local_path(locator) or not (root/locator).is_file(): errors.append(f'source decision locator missing or unsafe: {locator}')
 for document in root.glob('*.md'):
  for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',document.read_text(encoding='utf-8')):
   if '://' in target or target.startswith(('#','mailto:')): continue
   relative=target.split('#',1)[0]
   if relative and not (document.parent/relative).exists(): errors.append(f'broken local link in {document.name}: {target}')
 return errors

def run_self_tests(plan):
 failures=[]; count=0
 def probe(name,mutate,expected):
  nonlocal count
  candidate=copy.deepcopy(plan); mutate(candidate)
  try: errors=validate_plan_dict(candidate)
  except Exception as exc: failures.append(f'{name} crashed instead of rejecting: {type(exc).__name__}: {exc}'); return
  count+=1
  if not any(expected in e for e in errors): failures.append(f'{name} failed to reject {expected}')
 probe('missing dependency',lambda p:p['tasks'][3]['dependsOn'].append('RC-W99-T99'),'missing dependency')
 probe('cycle',lambda p:p['tasks'][3]['dependsOn'].append(p['tasks'][-1]['id']),'cycle')
 probe('malformed task',lambda p:p['tasks'][3].update(wave=True,dependsOn=[{}]),'must be')
 probe('duplicate outcome',lambda p:p['tasks'][4].update(outcome=p['tasks'][3]['outcome']),'duplicate outcome')
 probe('missing mapping',lambda p:p['sourceMappings'].pop(),'source mappings')
 probe('historical acceptance rewrite',lambda p:p['sourceMappings'][3].update(originalAcceptance='narrowed away'),'historical originalAcceptance')
 probe('historical status rewrite',lambda p:p['sourceMappings'][3].update(originalStatus='DONE'),'historical originalStatus')
 probe('prerequisite coverage loss',lambda p:p['sourceMappings'][4].update(prerequisiteOutcomeCoverage={}),'original prerequisite outcome coverage')
 probe('orphan task',lambda p:p['waves'][1]['taskIds'].pop(),'orphan')
 probe('scope expansion',lambda p:p['tasks'][-1].update(targetRelease='0.1'),'expands 0.1')
 probe('missing evidence',lambda p:p['tasks'][3].update(status='RUNTIME VERIFIED',evidenceRefs=[]),'actual evidence references')
 probe('invented completion',lambda p:p['tasks'][3].update(status='DONE'),'historical DONE')
 probe('wrong identity',lambda p:p.update(project='sibling-project'),'project identity')
 probe('outcome order',lambda p:p['tasks'].reverse(),'not earlier')
 def remove_critical(p):
  t=next(t for t in p['tasks'] if t['id']=='RC-W05-T09'); t['dependsOn'].remove('RC-W05-T08'); del t['dependencyRationale']['RC-W05-T08']
 probe('publication without approval prerequisite',remove_critical,'critical prerequisite outcome coverage')
 probe('false platform ID',lambda p:p['tasks'][3].update(platformId='fabricated'),'platform mapping differs')
 probe('malformed metadata',lambda p:p.update(schemaVersion=True),'schemaVersion')
 probe('malformed source treatment',lambda p:p['sourceMappings'][3].update(treatment=[]),'invalid treatment')
 probe('invalid source identity',lambda p:p['sourceMappings'][3].update(sourceId=[]),'unsupported source mapping identity')
 probe('malformed publication state',lambda p:p['publication'].update(status=[]),'publication status invalid')
 probe('unknown wave entry',lambda p:p['waves'][1]['entryDependencies'].append('RC-W99-T99'),'dangling entry dependency')
 if not validate_plan_dict([]): failures.append('non-object root accepted')
 changed=copy.deepcopy(plan); changed['tasks'][3]['title']+=' [deliberate drift]'
 if generated_files(changed)==generated_files(plan): failures.append('generated drift did not affect outputs')
 with tempfile.TemporaryDirectory(prefix='.validation-probe-',dir=ROOT/'plan') as directory:
  scratch=Path(directory)
  shutil.copytree(ROOT/'plan/lineage',scratch/'plan/lineage')
  target=scratch/'plan/lineage/architecture-foundation-2026-09-07/tasks.json'
  target.write_bytes(target.read_bytes()+b' ')
  if not any('immutable lineage changed' in e for e in validate_lineage(scratch)): failures.append('lineage byte mutation accepted')
  for relative,content in generated_files(plan).items():
   target=scratch/relative; target.parent.mkdir(parents=True,exist_ok=True); target.write_text(content)
  (scratch/'TASKS.md').write_text('A deliberately stale generated document.\n')
  if not any('parity failed: TASKS.md' in e for e in validate_documents(plan,scratch)): failures.append('stale document accepted')
 if not failures: print(f'PASS: {count+4} negative plan/view/lineage probes rejected')
 return failures

def main():
 parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--self-test',action='store_true'); args=parser.parse_args()
 try: plan=json.loads(PLAN_PATH.read_text(encoding='utf-8'))
 except (OSError,ValueError) as exc: print(f'FAIL: cannot load plan: {exc}',file=sys.stderr); return 1
 errors=validate_plan_dict(plan)+validate_lineage()
 if not errors: errors+=validate_documents(plan)
 if not errors and args.self_test: errors+=run_self_tests(plan)
 if errors:
  for error in errors: print('FAIL: '+error,file=sys.stderr)
  return 1
 print(f'PASS: {len(plan["tasks"])} task contracts, {len(plan["waves"])} waves, 27 immutable source mappings, outcome coverage, scope, DAG/order, generated exports and local links')
 return 0

if __name__=='__main__': raise SystemExit(main())
