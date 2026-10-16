from pathlib import Path
import hashlib

ROOT = Path(__file__).parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

expected_sha256 = {
    'a02': {
        'executor_v11.py':'ec98b6e44ae820e6b2955c062f431c33a1d86e4a626ab60b4e72178508988676',
        'executor_v12.py':'c7273b9e5dc7b2ab3513bcafc2898177b453c3c7e47aa8ee0a23c03f987e2f65',
        'executor_v3.py':'ea3fa8c9751a6a41b4814ad6e0d03bec85166765b0a41d2488a51750d17b3a4a',
        'executor_v5.py':'a36d45bf17d4d174683d982fd83fff24c87149df79dc3f7c0f7235c59c742400',
        'lease.py':'e71f9850d3999a31fcb86c00f9ef7a8ba19bae8d3a8bdc11bf7bd620817a535f',
        'lease_cause_v1.py':'800880125308a91aaf7ff49bc6f01ca33782e4161b79e3af4a944f517081d918',
        'lease_cause_v2.py':'6a61cabc540841f76ed518c4e0d49869f6600ed73f14ed030344d64ad3805a47',
        'lease_release_v1.py':'b4b1521b5207ea14654463f769b05337685750e9040bed36a8acf006aa1d34ff',
    },
    'current': {
        'executor_v11.py':'ec98b6e44ae820e6b2955c062f431c33a1d86e4a626ab60b4e72178508988676',
        'executor_v12.py':'11ed8e63fffa45bba52d8be2a926a1b5a09b20cfcbb0be0b02defc4b8a1e038b',
        'executor_v3.py':'ea3fa8c9751a6a41b4814ad6e0d03bec85166765b0a41d2488a51750d17b3a4a',
        'executor_v5.py':'a36d45bf17d4d174683d982fd83fff24c87149df79dc3f7c0f7235c59c742400',
        'lease.py':'e71f9850d3999a31fcb86c00f9ef7a8ba19bae8d3a8bdc11bf7bd620817a535f',
        'lease_cause_v1.py':'800880125308a91aaf7ff49bc6f01ca33782e4161b79e3af4a944f517081d918',
        'lease_cause_v2.py':'6a61cabc540841f76ed518c4e0d49869f6600ed73f14ed030344d64ad3805a47',
        'lease_release_v1.py':'b4b1521b5207ea14654463f769b05337685750e9040bed36a8acf006aa1d34ff',
    },
}
blob_files = {
    'a02':'SOURCE-A02-BLOB-IDS.txt',
    'current':'SOURCE-CURRENT-BLOB-IDS.txt',
    'parent':'SOURCE-PARENT-BLOB-IDS.txt',
}
errors=[]
for source_dir, files in expected_sha256.items():
    for name, digest in files.items():
        if sha(ROOT/'source'/source_dir/name) != digest:
            errors.append(f'{source_dir} source SHA-256 mismatch: {name}')
for source_dir, id_file in blob_files.items():
    for line in (ROOT/id_file).read_text().splitlines():
        name, expected_blob = line.split()
        data=(ROOT/'source'/source_dir/name).read_bytes()
        actual_blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if actual_blob != expected_blob:
            errors.append(f'{source_dir} Git blob mismatch: {name}')
for filename, expected_exit, required in [
    ('RAW-A01','1',('TypeError',)),
    ('RAW-A02','0',( "'closed_after_nested_close': True", "'worker_ident_when_close_returns': None", "'worker_alive_after_close_return': True", "'execute_called': False", 'PASS: reentrant close returned before submit launched its cancelled worker')),
    ('RAW-A03','0',( "'closed_after_nested_close': True", "'worker_ident_when_close_returns': None", "'worker_alive_after_close_return': True", "'execute_called': False", 'PASS: reentrant close returned before submit launched its cancelled worker')),
    ('RAW-PARENT','0',('cannot join thread before it is started',"'worker_alive': False","'execute_called': False")),
]:
    if (ROOT/(filename+'.exit.txt')).read_text().strip() != expected_exit:
        errors.append(filename+' exit mismatch')
    raw=(ROOT/(filename+'.stdout.txt')).read_text()
    for phrase in required:
        if phrase not in raw:
            errors.append(filename+' missing: '+phrase)
source=(ROOT/'source/current/executor_v12.py').read_text()
if not source.index('self.emit({"event": "accepted"') < source.index('worker.start()'):
    errors.append('accepted/start order changed')
if 'job[2].ident is not None' not in source:
    errors.append('unstarted-worker close guard absent')
result={
    'passed':not errors,
    'errors':errors,
    'sha256_source_files_checked':sum(map(len, expected_sha256.values())),
    'git_blob_source_files_checked':sum(len((ROOT/p).read_text().splitlines()) for p in blob_files.values()),
    'A01_preserved_harness_error':True,
    'A02_and_A03_reproduce_expected_boundary':not errors,
    'parent_control_preserves_previous_close_error':not errors,
}
print(result)
raise SystemExit(bool(errors))
