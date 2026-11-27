"""Build an isolated real-Git fixture and finite malformed-table corpus."""
import copy
import json
import os
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent

def git(repo, *args):
    env = dict(os.environ, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null',
               GIT_AUTHOR_NAME='Fixture', GIT_AUTHOR_EMAIL='fixture@example.invalid',
               GIT_COMMITTER_NAME='Fixture', GIT_COMMITTER_EMAIL='fixture@example.invalid',
               GIT_AUTHOR_DATE='2026-10-06T00:00:00+00:00',
               GIT_COMMITTER_DATE='2026-10-06T00:00:00+00:00',
               GIT_NO_REPLACE_OBJECTS='1')
    return subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', '-C', str(repo), *args],
                          env=env, capture_output=True, text=True, check=True, timeout=5).stdout.strip()

def build(root):
    repo = root / 'repo'
    repo.mkdir(parents=True)
    git(repo, 'init', '-q', '-b', 'base')
    data = json.loads((HERE/'original/RESULT.json').read_bytes())
    for row in data['paths']:
        if row['base_sha'] is not None:
            p = repo / row['path']; p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('base fixture: ' + row['path'] + '\n')
    git(repo, 'add', '.'); git(repo, 'commit', '-qm', 'base fixture')
    base = git(repo, 'rev-parse', 'HEAD')
    git(repo, 'checkout', '-qb', 'main')
    (repo/'UNRELATED.txt').write_text('unchanged selected paths\n')
    git(repo, 'add', '.'); git(repo, 'commit', '-qm', 'unrelated main update')
    main = git(repo, 'rev-parse', 'HEAD')
    git(repo, 'checkout', '-qb', 'candidate', base)
    for row in data['paths']:
        p = repo / row['path']; p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('candidate fixture: ' + row['path'] + '\n')
    git(repo, 'add', '.'); git(repo, 'commit', '-qm', 'candidate fixture')
    candidate = git(repo, 'rev-parse', 'HEAD')
    data.update(merge_base=base, intake_main=main, candidate_head=candidate)
    for row in data['paths']:
        if row['base_sha'] is not None:
            row['base_sha'] = row['main_sha'] = git(repo, 'rev-parse', base+':'+row['path'])
        row['candidate_sha'] = git(repo, 'rev-parse', candidate+':'+row['path'])
    git(repo, 'bundle', 'create', str((root/'fixture.bundle').resolve()), '--all')
    (root/'baseline.json').write_text(json.dumps(data, indent=2)+'\n')
    return repo, data

def corpus(base):
    cases = []
    def add(name, accepted, mutate=None, raw=None):
        d = copy.deepcopy(base)
        if mutate is not None: mutate(d)
        text = raw if raw is not None else json.dumps(d, indent=2)+'\n'
        cases.append({'name':name, 'expected_accept':accepted, 'input':text})
    add('valid', True)
    add('row_order', True, lambda d:d['paths'].reverse())
    add('compact_json', True, raw=json.dumps(base, separators=(',', ':')))
    add('main_sha_changed', False, lambda d:d['paths'][1].update(main_sha='0'*40))
    add('candidate_equals_main', False, lambda d:d['paths'][1].update(candidate_sha=d['paths'][1]['main_sha']))
    add('classification_changed', False, lambda d:d['paths'][1].update(classification='CANDIDATE_ADD_CLEAN'))
    add('addition_gets_base', False, lambda d:d['paths'][0].update(base_sha='0'*40))
    add('drop_row', False, lambda d:d['paths'].pop())
    add('duplicate_replace', False, lambda d:d['paths'].__setitem__(2, copy.deepcopy(d['paths'][1])))
    add('modified_candidate_null', False, lambda d:d['paths'][1].update(candidate_sha=None))
    add('invalid_class', False, lambda d:d['paths'][1].update(classification='UNKNOWN'))
    add('forged_equal_base_main', False, lambda d:d['paths'][1].update(base_sha='f'*40, main_sha='f'*40))
    add('candidate_ref_is_main', False, lambda d:d.update(candidate_head=d['intake_main']))
    add('main_ref_is_candidate', False, lambda d:d.update(intake_main=d['candidate_head']))
    add('source_commit_missing', False, lambda d:d.update(candidate_head='0'*40))
    add('unknown_path', False, lambda d:d['paths'][1].update(path='../unlisted.py'))
    add('bool_count_alias', False, lambda d:d['counts'].update(conflicts=False))
    add('wrong_decision', False, lambda d:d.update(decision='FAIL'))
    add('duplicate_json_key', False, raw=json.dumps(base)[:-1]+',"candidate_pr":8094}')
    add('malformed_sha', False, lambda d:d['paths'][0].update(candidate_sha='not-an-object'))
    if len(cases) != 20: raise RuntimeError('wrong corpus size')
    return cases
