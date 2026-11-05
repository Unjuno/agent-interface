#!/usr/bin/env python3
"""Verify the selected #8094 source table against a complete local Git repository.

No fetch, checkout, input or runtime execution. A table without local source
objects is not sufficient. This is source identity, not semantic compatibility.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

PATHS = frozenset('''research/doom/doom_batch_key_measurement_backend_v1.py
research/doom/doom_owner_thread_release_batch_backend_v1.py
research/doom/map01_overlap_controller_v39.py
research/doom/session_map01_v12.py
research/doom/session_map01_v15.py
research/doom/v39_measurement_backend_selection_v1.py
research/live_control/input_owner_v12.py
research/live_control/input_transition_owner_v4.py
research/live_control/key_edge_measurement_v1.py
research/live_control/observable_signal_guard_v2.py
research/doom/map01_motor_responder_v10.txt'''.splitlines())
COUNTS = dict(total=11, clean_add=3, main_unchanged_candidate_only=8, conflicts=0)
SHA = re.compile('[0-9a-f]{40}')

class SourceUnavailable(Exception):
    pass

def need(condition, message):
    if not condition:
        raise ValueError(message)

def unique(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, 'duplicate JSON member')
        result[key] = value
    return result

def bad_constant(_value):
    raise ValueError('non-finite JSON number')

def git(repo, *args):
    env = dict(os.environ, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null',
               GIT_NO_REPLACE_OBJECTS='1', GIT_NO_LAZY_FETCH='1')
    p = subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', '-c',
                        'protocol.allow=never', '-C', str(repo), *args],
                       env=env, capture_output=True, timeout=5)
    if p.returncode:
        raise SourceUnavailable('required local Git objects unavailable')
    return p.stdout

def tree(repo, ref):
    need(git(repo, 'cat-file', '-t', ref).strip()==b'commit', 'reference is not a commit')
    found = {}
    raw = git(repo, 'ls-tree', '-r', '--full-tree', '-z', ref, '--', *sorted(PATHS))
    for record in raw.split(b'\0'):
        if not record:
            continue
        header, path = record.split(b'\t', 1)
        mode, kind, sha = header.decode('ascii').split()
        name = path.decode('utf-8')
        need(name in PATHS and name not in found, 'unexpected/duplicate tree path')
        need(kind=='blob' and mode in ('100644','100755'), 'not an ordinary source file')
        found[name] = sha
    return found

def verify(raw, repo):
    data = json.loads(raw, object_pairs_hook=unique, parse_constant=bad_constant)
    need(type(data) is dict, 'root must be an object')
    need(data.get('schema')=='agent-interface/issue59-8094-currentmain-delta-audit-v1', 'wrong schema')
    need(data.get('decision')=='PASS_CURRENT_MAIN_DELTA_NONCONFLICT_SCOPED', 'wrong decision')
    need(type(data.get('candidate_pr')) is int and data['candidate_pr']==8094, 'wrong PR')
    counts = data.get('counts')
    need(type(counts) is dict and set(counts)==set(COUNTS), 'wrong count keys')
    need(all(type(counts[k]) is int and counts[k]==v for k,v in COUNTS.items()), 'wrong counts/type')
    refs = [data.get(k) for k in ('merge_base','intake_main','candidate_head')]
    need(all(type(r) is str and SHA.fullmatch(r) for r in refs), 'invalid commit SHA')
    rows = data.get('paths')
    need(type(rows) is list and len(rows)==len(PATHS), 'wrong row count')
    names = []
    for row in rows:
        need(type(row) is dict, 'row must be an object')
        need(set(row)=={'path','base_sha','main_sha','candidate_sha','classification'}, 'wrong row fields')
        name = row['path']
        need(type(name) is str and name in PATHS and name not in names, 'wrong/duplicate path')
        names.append(name)
        for key in ('base_sha','main_sha','candidate_sha'):
            value = row[key]
            need(value is None or type(value) is str and SHA.fullmatch(value), 'invalid blob SHA')
        need(row['candidate_sha'] is not None, 'missing candidate blob')
    need(set(names)==PATHS, 'incomplete path coverage')
    actual = [tree(repo, ref) for ref in refs]
    common = git(repo, 'merge-base', refs[1], refs[2]).decode('ascii').strip()
    need(common==refs[0], 'declared merge base differs from Git')
    derived = dict(total=len(rows),clean_add=0,main_unchanged_candidate_only=0,conflicts=0)
    for row in rows:
        b, m, c = [t.get(row['path']) for t in actual]
        need((b,m,c)==(row['base_sha'],row['main_sha'],row['candidate_sha']), 'source/table mismatch')
        if b is None and m is None and c is not None:
            expected = 'CANDIDATE_ADD_CLEAN'; derived['clean_add'] += 1
        elif b is not None and b==m and c is not None and c!=m:
            expected = 'MAIN_UNCHANGED_CANDIDATE_ONLY'; derived['main_unchanged_candidate_only'] += 1
        else:
            raise ValueError('selected path is not a candidate-only addition/edit')
        need(row['classification']==expected, 'wrong source classification')
    need(derived==COUNTS, 'derived counts differ')
    return dict(status='PASS_SOURCE_TABLE_VERIFIED', counts=derived,
                grants_input_authority=False, runtime_compatibility_verified=False)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--result', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = verify(args.result.read_bytes(), args.repo)
    except (SourceUnavailable, OSError, subprocess.TimeoutExpired) as error:
        print(json.dumps(dict(status='HOLD_SOURCE_OBJECTS_OR_IO_UNAVAILABLE', error=str(error))))
        return 2
    except (ValueError, TypeError, KeyError) as error:
        print(json.dumps(dict(status='REJECT_SOURCE_TABLE', error=str(error))))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
