"""Offline, independent array-based audit of retained frames and resolver receipts."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from collections import Counter
import numpy as np
from PIL import Image


def audit(folder: Path) -> dict:
    manifest = json.loads((folder/'manifest.json').read_text())
    for name, expected in manifest.items():
        assert hashlib.sha256((folder/name).read_bytes()).hexdigest() == expected, name
    rows = [json.loads(x) for x in (folder/'raw.jsonl').read_text().splitlines()]
    assert len(rows) == 120 and [r['ordinal'] for r in rows] == list(range(120))
    assert Counter(r['case'] for r in rows) == dict.fromkeys(
        ('stable','move6','hover','pixel1','duplicate','replacement'), 20)
    cache = {}
    receipts = 0
    for row in rows:
        assert all(row['checks'].values()), row['ordinal']
        key = (row['source']['file'], row['current']['file'])
        if key not in cache:
            source = np.array(Image.open(folder/key[0]).convert('RGB'))
            current = np.array(Image.open(folder/key[1]).convert('RGB'))
            patch = source[80:104,96:128]
            # Does not import, subclass, or invoke TargetHandleStore.
            cache[key] = [(x,y) for y in range(48,113) for x in range(64,129)
                          if np.array_equal(current[y:y+24,x:x+32], patch)]
        matches = cache[key]
        for name in ('top','child'):
            before = row['before'][name]['pointer_binding']
            after = row['after'][name]['pointer_binding']
            r = row['arms'][name]
            assert row['capture0_ns'][0] <= row['capture0_ns'][1]
            assert row['capture1_ns'][0] <= row['capture1_ns'][1] <= r['start_ns'] <= r['end_ns']
            assert r['cpu_ns'] >= 0
            mismatch = any(before[k] != after[k] for k in ('focus','surface'))
            expected = ('SCOPE_MISMATCH' if mismatch else 'MISSING' if not matches
                        else 'AMBIGUOUS' if len(matches)>1 else
                        'VALID' if matches[0] == (96,80) else 'REVALIDATED')
            result = r['result']
            assert result['status'] == expected, (row['ordinal'],name,expected,result)
            assert result['eligible'] == (expected in ('VALID','REVALIDATED'))
            assert 'ordinary admission remains required' in result['authority']
            if result['eligible']:
                assert result['point'] == [matches[0][0]+16,matches[0][1]+12]
                assert r['wrong_identity_eligible'] == (r['oracle_point_window'] != row['original_xid'])
            receipts += 1
    return dict(status='PASS', manifest_files=len(manifest), trials=len(rows),
                independently_audited_receipts=receipts,
                unique_frame_pairs=len(cache),
                oracle_scope='recorded X11 lifecycle/point mapping, not semantic vision',
                production_input_or_safety_validation=False)


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('folder',type=Path)
    print(json.dumps(audit(p.parse_args().folder),indent=2))
