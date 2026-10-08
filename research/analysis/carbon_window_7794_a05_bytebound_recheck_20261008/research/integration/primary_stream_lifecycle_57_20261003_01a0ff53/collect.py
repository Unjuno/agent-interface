from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys,time

W=Path(__file__).resolve().parent
REPO=W.parent/'agent-interface'
NODE='/opt/homebrew/bin/node'
FILES=['primary_stdio.mjs','primary_exchange.mjs','primary_caller.mjs','relay_host.mjs','relay_client.mjs']
SCENARIOS=['ready_input','ready_output','terminal_output','normal_eof']

def sha(b):return hashlib.sha256(b).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()

def collect(label,source):
    output=W/label;output.mkdir(exist_ok=False)
    pins={name:sha((source/name).read_bytes()) for name in FILES}
    freeze={'created_utc':utc(),'classification':'ordinary actual-owner/fixture-relay regression construction; not old comparison/auditor allocation','source_directory':str(source),'source_sha256':pins,'helper_sha256':{n:sha((W/n).read_bytes()) for n in ['relay_fixture.mjs','lifecycle_probe.mjs','collect.py']},'node_binary':str(Path(NODE).resolve()),'node_binary_sha256':sha(Path(NODE).resolve().read_bytes()),'node_version':subprocess.check_output([NODE,'--version']).decode().strip(),'scenarios':SCENARIOS,'parent_timeout_seconds':5,'owned_fixture_observation_seconds':3,'maximum_parent_runs':4,'no_new_relay_requests_expected':True,'shared_backend_or_GUI':False}
    (output/'SOURCE_FREEZE.json').write_text(json.dumps(freeze,indent=2)+'\n')
    rows=[]
    for scenario in SCENARIOS:
        directory=output/scenario;directory.mkdir()
        cmd=[NODE,str(W/'lifecycle_probe.mjs'),scenario,str(source),str(directory)]
        record={'scenario':scenario,'argv':cmd,'started_utc':utc()}
        try:
            p=subprocess.run(cmd,capture_output=True,timeout=5)
            record.update(exit_code=p.returncode,ended_utc=utc(),timed_out=False)
            stdout,stderr=p.stdout,p.stderr
        except subprocess.TimeoutExpired as e:
            stdout,stderr=e.stdout or b'',e.stderr or b''
            record.update(exit_code=None,ended_utc=utc(),timed_out=True)
        (directory/'stdout.txt').write_bytes(stdout);(directory/'stderr.txt').write_bytes(stderr)
        record.update(stdout_sha256=sha(stdout),stderr_sha256=sha(stderr))
        deadline=time.monotonic()+3
        while not (directory/'fixture.exit.json').exists() and time.monotonic()<deadline:time.sleep(.02)
        for name in ['fixture.started.json','fixture.exit.json','owner.summary.json','host/exit.json']:
            if (directory/name).exists():record[name]=json.loads((directory/name).read_bytes())
        if 'fixture.started.json' in record:
            pid=record['fixture.started.json']['pid']
            while time.monotonic()<deadline:
                try:os.kill(pid,0)
                except ProcessLookupError:break
                time.sleep(.02)
            try:os.kill(pid,0);record['fixture_pid_absent']=False
            except ProcessLookupError:record['fixture_pid_absent']=True
        (directory/'receipt.json').write_text(json.dumps(record,indent=2)+'\n');rows.append(record)
        if record['timed_out']:break
    assert {name:sha((source/name).read_bytes()) for name in FILES}==pins
    (output/'RAW.json').write_text(json.dumps({'classification':freeze['classification'],'rows':rows},indent=2)+'\n')
    print(json.dumps({'label':label,'actual_parent_exits':[x['exit_code'] for x in rows],'fixture_exits':[x.get('fixture.exit.json') for x in rows],'owner_receipts':[bool(x.get('owner.summary.json')) for x in rows],'fixture_pid_absent':[x.get('fixture_pid_absent') for x in rows]}))

if __name__=='__main__':collect(sys.argv[1],Path(sys.argv[2]))
