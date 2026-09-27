"""Read-only verification: no native/GUI/measurement runner is executed."""
import hashlib,json,subprocess,sys,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def main():
    manifest=json.loads((ROOT/'MANIFEST.json').read_text())
    for name,meta in manifest['files'].items():
        p=ROOT/name
        if p.is_symlink() or not p.is_file():raise RuntimeError('missing/nonregular '+name)
        data=p.read_bytes()
        if len(data)!=meta['bytes'] or hashlib.sha256(data).hexdigest()!=meta['sha256']:raise RuntimeError('identity mismatch '+name)
    results={}
    for script,expected in (('audit.py','AUDIT.json'),('controls.py','CONTROLS.json')):
        p=subprocess.run([sys.executable,'-S','-B',str(ROOT/script),str(ROOT)],cwd=ROOT,capture_output=True,timeout=35)
        if p.returncode or p.stderr or p.stdout!=(ROOT/expected).read_bytes():raise RuntimeError('read-only reconstruction mismatch '+script)
        results[script]=json.loads(p.stdout)
    p=subprocess.run([sys.executable,'-S','-B','-m','unittest','-v','test_fold'],cwd=ROOT,capture_output=True,timeout=15)
    if p.returncode or b'Ran 16 tests' not in p.stderr or not p.stderr.rstrip().endswith(b'OK'):raise RuntimeError('unit tests')
    print(json.dumps(dict(status='PASS_READONLY_RECONSTRUCTION',manifest_members=len(manifest['files']),
        cases=results['audit.py']['correctness']['cases'],decisions=results['audit.py']['correctness']['decisions'],
        checks=results['audit.py']['checks'],controls=results['controls.py']['count'],units=16,
        measurement_reruns=0,native_library_loads=0,gui_runs=0,model_calls=0),sort_keys=True))
if __name__=='__main__':main()