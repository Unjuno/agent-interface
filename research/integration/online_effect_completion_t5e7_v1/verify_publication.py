"""Restore pinned evidence and rerun offline checks only, never live allocations."""
from pathlib import Path
import hashlib, json, shutil, subprocess, sys, tempfile
from unpack import restore, need, relative
HERE = Path(__file__).resolve().parent

def verify():
    with tempfile.TemporaryDirectory(prefix='effect-completion-review-') as td:
        root = Path(td) / 'source'
        count = restore(HERE / 'SOURCE_MANIFEST.json', root)
        vendor = json.loads((root / 'vendor/SOURCE_MANIFEST.json').read_text())
        for name, info in vendor['source_files'].items():
            source = HERE / 'vendor' / relative(name)
            b = source.read_bytes()
            need(len(b) == info['bytes'] and hashlib.sha256(b).hexdigest() == info['sha256'],
                 'vendor hash')
            need(hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()
                 == info['git_blob'], 'vendor Git blob')
            target = root / 'vendor' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b)
        freeze = json.loads((root / 'FREEZE.json').read_text())
        for name, sha in freeze['files'].items():
            need(hashlib.sha256((root / relative(name)).read_bytes()).hexdigest() == sha,
                 'frozen source mismatch')
        result = {'source_members': count, 'frozen_files': len(freeze['files']),
                  'vendor_files': len(vendor['source_files']), 'live_runs': 0}
        result_manifest = HERE / 'RESULT_MANIFEST.json'
        if result_manifest.exists():
            evidence = Path(td) / 'evidence'
            result['result_members'] = restore(result_manifest, evidence)
            for p in evidence.rglob('*'):
                if p.is_file():
                    target = root / p.relative_to(evidence)
                    need(not target.exists(), 'result overwrites source')
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(p, target)
            for script, output in [('audit.py', 'AUDIT.json'), ('controls.py', 'CONTROLS.json')]:
                proc = subprocess.run([sys.executable, '-B', script, 'formal'], cwd=root,
                                      capture_output=True, timeout=45)
                need(proc.returncode == 0, script + ': ' + proc.stderr.decode(errors='replace'))
                need(proc.stdout == (root / output).read_bytes(), script + ': retained output mismatch')
            proc = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'tests'], cwd=root,
                                  capture_output=True, timeout=20)
            need(proc.returncode == 0, 'unit tests')
            result['audit_and_controls_byte_identical'] = True
        result['status'] = 'VERIFIED'
        return result

if __name__ == '__main__':
    print(json.dumps(verify(), indent=2, sort_keys=True))
