"""Read-only supplemental audit of the unchanged PR319 raw evidence."""
import argparse, hashlib, json, os, subprocess, tarfile, tempfile
from pathlib import Path
EXPECTED = '479011156d40e930fe13d2dc2104ab047f43935370788cd3d4e960fd729c67f7'

def review(archive):
    actual = hashlib.sha256(archive.read_bytes()).hexdigest()
    if actual != EXPECTED: raise ValueError('historical archive identity mismatch')
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        with tarfile.open(archive) as t: t.extractall(root, filter='data')
        manifest = json.loads((root/'MANIFEST.json').read_text())
        for item in manifest['files']:
            path = root/item['path']
            if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
                raise ValueError('historical manifest mismatch: ' + item['path'])
        rows = []
        for path in sorted((root/'evidence').glob('*/result.json')):
            r = json.loads(path.read_text())
            if r['schedule'] != 'unrelated_changed': continue
            repo = path.parent/'repo'
            def read(oid):
                return subprocess.check_output(['git', '-c', 'safe.directory='+str(repo),
                    '-C', str(repo), 'show', oid+':unrelated.txt'], timeout=10).decode()
            before, after = read(r['pre_delivery_target']), read(r['final_target'])
            rows.append({'id': r['id'], 'policy': r['policy'],
                         'old_oracle_correct': r['ground_truth_correct'],
                         'before': before, 'after': after, 'preserved': before == after,
                         'pre_ref': r['pre_delivery_target'], 'final_ref': r['final_target']})
        if len(rows) != 10: raise ValueError('unexpected historical subset')
        return {'archive_sha256': actual, 'verified_manifest_count': len(manifest['files']),
                'case_count': len(rows), 'lost_update_count': sum(not r['preserved'] for r in rows),
                'method': 'new state-preservation criterion; old frozen goal/PASS unchanged; no rerun',
                'rows': rows}

if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('archive',type=Path); p.add_argument('out',type=Path)
    a=p.parse_args(); a.out.write_text(json.dumps(review(a.archive),indent=2,sort_keys=True)+'\n')
