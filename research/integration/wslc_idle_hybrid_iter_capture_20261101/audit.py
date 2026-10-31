"""Check packaged bytes and re-audit retained Xvfb observations."""
import hashlib,json,pathlib,subprocess,sys,tempfile,zipfile
root=pathlib.Path(__file__).resolve().parent
expected=json.loads((root/'archive-manifest.json').read_text())
with zipfile.ZipFile(root/'raw.zip') as archive:
    names=archive.namelist()
    if len(names)!=len(set(names)) or set(names)!=set(expected):raise RuntimeError('archive entry set mismatch')
    for name in names:
        path=pathlib.PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts:raise RuntimeError('unsafe archive path')
        if hashlib.sha256(archive.read(name)).hexdigest()!=expected[name]:raise RuntimeError('digest mismatch: '+name)
    with tempfile.TemporaryDirectory(prefix='history-evidence-audit-') as directory:
        archive.extractall(directory)
        auditor=pathlib.Path(directory)/'idle-large-live-r98'/'audit_results.py'
        proc=subprocess.run([sys.executable,'-B',str(auditor)],capture_output=True,text=True)
        if proc.returncode:raise RuntimeError('capture audit failed: '+proc.stdout+proc.stderr)
        result=json.loads(proc.stdout)
        if result['status']!='pass' or len(result['rows'])!=4:raise RuntimeError('unexpected audit result')
        for mode in ('normal','optimized'):
            test=pathlib.Path(directory)/'idle-hybrid-iter-cost-r95'/('tests-'+mode)
            if json.loads((test/'result.json').read_text())['returncode']!=0:raise RuntimeError('regression failed '+mode)
            stderr=(test/'stderr').read_text()
            if 'Ran 90 tests' not in stderr or '\nOK' not in stderr:raise RuntimeError('missing regression summary '+mode)
print(json.dumps({'status':'pass','entries':len(expected),'xvfb_arms':4,'observation_records':84,'test_modes':2}))
