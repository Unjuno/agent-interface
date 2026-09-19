#!/usr/bin/env python3
"""Audit archived paused projections; never infer gameplay success."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

def read(path):
    return json.loads(path.read_text())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def validate(value):
    assert value['width'] == 250 and value['height'] == 300
    assert value['paused'] is True and value['core_present'] is True
    assert value['task_success'] is None
    assert type(value['copper']) is int and type(value['wave']) is int
    rows = value['tiles']
    assert len(rows) == value['height']
    for row in rows:
        assert len(row) == value['width']
        for tile in row:
            assert len(tile) == 5
            assert all(isinstance(x, str) and x for x in tile[:3])
            assert type(tile[3]) is int
            assert tile[4] is None or (type(tile[4]) is int and 0 <= tile[4] <= 3)
    # The core's linked tiles share its Building, so this is not a building count.
    assert sum(t[4] is not None for row in rows for t in row) > 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cohort', type=Path)
    ap.add_argument('--reference', type=Path, required=True)
    a = ap.parse_args()
    expected = read(a.reference)
    validate(expected)
    manifest = read(a.cohort / 'manifest.json')
    for path, digest in manifest['sources'].items():
        assert sha(HERE.parent / path) == digest, path
    save_hash = sha(a.cohort / 'canonical.msav')
    results = read(a.cohort / 'results.json')
    assert [r['label'] for r in results] in [
        ['create', 'reload-1', 'reload-2'], ['reload-1', 'reload-2']]
    rows = []
    for result in results:
        out = a.cohort / result['label']
        assert result['ready'] is True and result['all_owned_processes_exited'] is True
        assert result['windows'].strip()
        assert sha(out / 'screen.png') == result['screen_sha256']
        if result['label'] != 'create':
            assert result['input_sha256'] == save_hash
        actual = read(out / 'oracle.json')
        validate(actual)
        assert actual == expected, result['label']
        rows.append({'label': result['label'], 'projection_equal': True,
                     'setup_s': result['setup_s'], 'forced_kill': result['forced_kill']})
    summary = {'canonical_sha256': save_hash, 'tiles_compared_per_attempt': 75000,
               'rotation_bearing_tiles': sum(t[4] is not None for row in expected['tiles'] for t in row),
               'rows': rows, 'task_success': None,
               'scope': 'exact paused projection equality only; not whole engine state, reliable reset rate, or gameplay'}
    (a.cohort / 'audit.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary))

if __name__ == '__main__':
    main()
