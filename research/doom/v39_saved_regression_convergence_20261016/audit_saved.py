"""Read saved A11/A12 records and Git blobs; never import/run their producers."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess

ORIGINAL = '320d39b6d8f495c78e4863d15a747ce54eed17ed'
BASE = 'f71fce5cbfcf184f18dbe944e7416aae0d1b5763'
SOURCE = 'a6343bb76e4dc0a4afa32a29c8a485a617faeff8'
CARRY = '57337e95ecbecf7e762c8ec8091472b79e8ad49f'
PREFIXES = {a: f'research/doom/v39_recovery_current_main_{a}_20261009' for a in ('a11', 'a12')}
ACTUAL = dict(controller=16, pending_drain=22, final_action_admission=9, running_action_guard=7)


class EvidenceError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise EvidenceError(message)


def git(repo, *args, data=None):
    return subprocess.run(['git', '-C', str(repo), *args], input=data,
                          capture_output=True, check=True).stdout


def tree(repo, ref, paths):
    rows = git(repo, 'ls-tree', '-r', '-z', ref, '--', *paths).split(b'\0')
    return {p.decode(): header.split()[2].decode() for row in rows if row
            for header, p in [row.split(b'\t', 1)]}


def objects(repo, mapping):
    ids = list(dict.fromkeys(mapping.values()))
    raw = git(repo, 'cat-file', '--batch', data=('\n'.join(ids) + '\n').encode())
    blobs, offset = {}, 0
    for expected in ids:
        end = raw.index(b'\n', offset)
        oid, kind, size = raw[offset:end].split()
        require(oid.decode() == expected and kind == b'blob', 'Git object mismatch')
        size = int(size)
        blobs[expected] = raw[end + 1:end + 1 + size]
        offset = end + size + 2
    require(offset == len(raw), 'unexpected Git batch suffix')
    return {path: (oid, blobs[oid]) for path, oid in mapping.items()}


def load_evidence(repo):
    original = tree(repo, ORIGINAL, PREFIXES.values())
    original_data = objects(repo, original)
    files = {}
    for path, (_, data) in original_data.items():
        require((repo / path).read_bytes() == data, f'original bytes changed: {path}')
        for attempt, prefix in PREFIXES.items():
            if path.startswith(prefix + '/'):
                files[f'{attempt}/{path[len(prefix) + 1:]}'] = data
    source_paths = list(json.loads(files['a12/RESULT.json'])['sources'])
    return dict(files=files, original_file_count=len(original),
                original_paths=original,
                sources=objects(repo, tree(repo, SOURCE, source_paths)),
                carry_changed=git(repo, 'diff', '--name-only', SOURCE, CARRY).decode().splitlines(),
                carry=tree(repo, CARRY, source_paths),
                current=tree(repo, BASE, source_paths))


def validate_records(evidence):
    files = evidence['files']
    results, expected_sources, checksum_count = {}, None, 0
    for attempt, decision in [('a11', 'FAIL'), ('a12', 'PASS')]:
        freeze = json.loads(files[f'{attempt}/FREEZE.json'])
        result = json.loads(files[f'{attempt}/RESULT.json'])
        require(freeze['source_commit'] == result['source_commit'] == SOURCE, 'source commit')
        require(freeze['dependency_base_commit'] == result['dependency_base_commit'] == '1f81daa690b567a9a049cc75fae8619b2660c343', 'dependency ref')
        require(freeze['live_execution'] is False, 'live claim')
        require(result['decision'] == decision, 'first failure/corrected verdict')
        require(freeze['suites'] == result['suites'], 'freeze/result suites disagree')
        suites = {s['key']: s for s in freeze['suites']}
        require(len(freeze['suites']) == len(suites) == 4 and set(suites) == set(ACTUAL), 'suite inventory')
        require(set(result['runs']) == set(suites), 'run inventory')
        for key, suite in suites.items():
            expected = {'controller': 15, 'pending_drain': 20}.get(key, ACTUAL[key]) if attempt == 'a11' else ACTUAL[key]
            require(type(suite['tests']) is int and suite['tests'] == expected, 'frozen count')
            require(set(result['runs'][key]) == {'normal', 'optimized'}, 'mode inventory')
            identities = []
            for mode in ('normal', 'optimized'):
                code = result['runs'][key][mode]['exit_code']
                require(type(code) is int and code == 0, 'exit receipt')
                require(files[f'{attempt}/{key}.{mode}.stdout.txt'] == b'', 'unexpected stdout')
                log = '\n'.join(files[f'{attempt}/{key}.{mode}.stderr.txt'].decode().splitlines())
                counts = re.findall(r'^Ran (\d+) tests? in [0-9.]+s$', log, re.M)
                require(counts == [str(ACTUAL[key])] and log.rstrip().endswith('\nOK'), 'raw outcome/count')
                tests = re.findall(r'^(test_\S+) \(([^)]+)\) \.\.\. ok$', log, re.M)
                require(len(tests) == ACTUAL[key] and len(set(tests)) == len(tests), 'raw identity count/duplicate')
                require(all(name == full.rsplit('.', 1)[-1] for name, full in tests), 'raw identity mismatch')
                require(all(full.split('.', 1)[0] == Path(suite['path']).stem for _, full in tests), 'raw suite module')
                identities.append(tests)
            require(identities[0] == identities[1], 'normal/optimized identities differ')
        pins = result['sources']
        require(len(pins) == 34 and set(pins) == set(evidence['sources']), 'source inventory')
        require({s['path'] for s in suites.values()} <= set(pins), 'missing suite source')
        for path, pin in pins.items():
            oid, data = evidence['sources'][path]
            require(pin == dict(blob=oid, sha256=hashlib.sha256(data).hexdigest()), f'source pin: {path}')
        require(expected_sources is None or pins == expected_sources, 'A11/A12 source change')
        expected_sources = pins
        results[attempt] = result['decision']
        # Legacy checksums are custody checks, distinct from semantic controls.
        for line in files[f'{attempt}/SHA256SUMS.txt'].decode().splitlines():
            digest, name = line.split('  ', 1)
            require(hashlib.sha256(files[f'{attempt}/{name}']).hexdigest() == digest, f'legacy checksum: {attempt}/{name}')
            checksum_count += 1
    carry = json.loads(files['a12/MAIN_CARRY_FORWARD.json'])
    require(carry['frozen_source_commit'] == SOURCE and carry['current_main_commit'] == CARRY, 'carry refs')
    require(carry['status'] == 'PASS_BYTE_IDENTICAL_CURRENT_MAIN_CARRY_FORWARD', 'carry verdict')
    require(carry['changed_paths_overlapping_pinned_sources'] == [], 'carry overlap')
    require(not set(evidence['carry_changed']).intersection(expected_sources), 'actual carry overlap')
    require(type(carry['changed_paths_since_frozen_source']) is int and carry['changed_paths_since_frozen_source'] == len(evidence['carry_changed']), 'carry diff count')
    rows = {row['path']: row for row in carry['sources']}
    require(type(carry['source_paths_verified']) is int and carry['source_paths_verified'] == len(rows) == len(carry['sources']) == 34, 'carry source count')
    require(set(rows) == set(expected_sources) == set(evidence['carry']), 'carry inventory')
    for path, pin in expected_sources.items():
        require(rows[path] == dict(path=path, **pin) and evidence['carry'][path] == pin['blob'], 'carry pin')
    return dict(decisions=results, saved_test_executions=2 * 2 * sum(ACTUAL.values()),
                source_count=34, original_file_count=evidence['original_file_count'],
                legacy_checksum_count=checksum_count,
                current_base=BASE, unchanged_current_sources=sum(evidence['current'].get(p) == pin['blob'] for p, pin in expected_sources.items()),
                changed_current_sources=sorted(p for p, pin in expected_sources.items() if evidence['current'].get(p) != pin['blob']),
                scope='Saved CPU regression custody only; no producer, old suite, GUI, model, WSLc or live allocation executed.')


if __name__ == '__main__':
    print(json.dumps(validate_records(load_evidence(Path(__file__).resolve().parents[3])), indent=2))
