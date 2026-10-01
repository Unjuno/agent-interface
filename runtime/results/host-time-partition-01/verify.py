from pathlib import Path
import hashlib,importlib.util,json,math,tarfile,tempfile
def require(ok,msg):
    if not ok:raise ValueError(msg)
root=Path(__file__).resolve().parent
with tarfile.open(root/'raw.tar.gz') as t:
    members=t.getmembers();require(all(m.isfile() for m in members),'files only')
    require(len({m.name for m in members})==len(members),'unique names')
    data={m.name:t.extractfile(m).read() for m in members}
manifest=json.loads((root/'manifest.json').read_text())
require(set(data)==set(manifest['files']),'exact files')
for n,h in manifest['files'].items():require(hashlib.sha256(data[n]).hexdigest()==h,n)
base='results-local/host-time-partition-01/'
sources=json.loads(data[base+'sources.json'])
with tempfile.TemporaryDirectory() as d:
    tmp=Path(d);module_path=tmp/'timing.py'
    module_path.write_bytes(data['runtime/integration_checks/host_timing.py'])
    spec=importlib.util.spec_from_file_location('retained_timing',module_path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    for case,prefix in sources.items():
        directory=tmp/case;directory.mkdir()
        for n,b in data.items():
            if n.startswith(prefix+'/'):
                suffix=n[len(prefix)+1:]
                require(Path(suffix).name==suffix,'flat host file')
                (directory/suffix).write_bytes(b)
        report=mod.summarize(directory)
        require(report==json.loads(data[base+case+'.json']),'reproduced summary')
        part=report['time_partition'];require(part is not None,'complete partition')
        require(math.isclose(sum(part[k] for k in ('request_outstanding_ms','presentation_callbacks_ms','other_host_intervals_ms')),part['total_ms'],abs_tol=1e-6),'partition sum')
native=json.loads(data['results-local/host-time-partition-native-01/result.json'])
require(native['status']=='PASS' and all(s['returncode']==0 for s in native['suites']),'native checks')
require('Ran 14 tests' in data[base+'tests.log'].decode(),'timing checks')
print(f'PASS: {len(data)} files; four retained host partitions reproduced; no new task samples')
