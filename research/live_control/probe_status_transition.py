"""Live private X11 input, delayed ordinary evaluation, read-only continuation."""
import hashlib,json,socket,subprocess,sys,time
from pathlib import Path
from PIL import Image
from session_v9 import Decoder
from outcome_wait import wait_request,interpret
from outcome_fallback_v2 import wait_with_status
HERE=Path(__file__).resolve().parent
out=HERE/'results/status-transition-01';out.mkdir(exist_ok=False);summaries=[]
for case,token in (('success','t991026'),('failure','wrong-token')):
    directory=out/case;directory.mkdir();root=directory/'runtime';gate=directory/'release.gate';responses=[]
    process=subprocess.Popen([sys.executable,'-u',str(HERE/'gated_socket_entry_v2.py'),str(gate),'serve','--','--app','xterm','--seed','991026','--out',str(root),'--presentation','compact'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    address=json.loads(process.stdout.readline())['socket']
    def request(spec):
        started=time.perf_counter_ns()
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as connection:
            connection.settimeout(8);connection.connect(address)
            connection.sendall((json.dumps(spec)+'\n').encode())
            with connection.makefile('rb') as stream:reply=json.loads(stream.readline())
        responses.append(dict(request=spec,reply=reply,started_ns=started,returned_ns=time.perf_counter_ns()))
        return reply
    try:
        initial=request(dict(after=0,events=['observation'],timeout=5));limit=time.monotonic()+20
        while initial['status']=='timeout' and process.poll() is None and time.monotonic()<limit:
            initial=request(dict(after=initial['cursor'],events=['observation'],timeout=5))
        assert initial['status']=='boundary';obs=initial['records'][-1]
        clock=request(dict(after=initial['cursor'],events=['clock'],timeout=5,command=dict(op='clock'),request_id='clock'))
        command=dict(op='submit',id='submit',finish_after=True,expected_sequence=obs['sequence'],
            valid_until_ns=clock['records'][-1]['runtime_ns']+10_000_000_000,
            decision_evidence=dict(delivery_id=obs['delivery_id'],observation_sequence=obs['sequence'],producer='scripted'),
            steps=[dict(op='text',text=token),dict(op='key',key='Return')])
        terminal=request(dict(after=clock['cursor'],events=['terminal'],timeout=5,command=command,request_id='submit',read_request_id='submit'))
        assert terminal['status']=='boundary' and terminal['records'][-1]['status']=='completed'
        limit=time.monotonic()+2
        while not gate.with_suffix('.waiting').exists() and process.poll() is None and time.monotonic()<limit:time.sleep(.005)
        assert gate.with_suffix('.waiting').exists() and process.poll() is None
        fallback=wait_with_status(request,'submit','submit',terminal['cursor'],timeout=.1,status_timeout=1)
        pending=fallback['result']
        assert pending['state']=='pending' and pending['task_success'] is None
        assert pending['reason']=='pending' and len(fallback['transcript'])==2
        old_query=fallback['transcript'][1]['request']
        old_snapshot=fallback['transcript'][1]['reply']['records'][-1]
        assert old_snapshot['state']=='pending'
        gate.write_text('release evaluation')
        final_batch=request(wait_request('submit',pending['cursor'],timeout=5));final=interpret(final_batch,'submit')
        assert final['state']=='evaluated' and final['task_success'] is (case=='success')
        replay=request(old_query)
        assert replay['command_receipt']['replayed'] and replay['records'][-1]==old_snapshot
        # A new helper invocation after the final event has been consumed must
        # use a fresh status ID and recover the now-available retained result.
        fresh=wait_with_status(request,'submit','submit',final_batch['cursor'],timeout=.1,status_timeout=1)
        assert len(fresh['transcript'])==2
        assert fresh['transcript'][1]['request']['request_id']!=old_query['request_id']
        assert fresh['result']['state']=='evaluated' and fresh['result']['task_success'] is (case=='success')
        assert fresh['result']['evidence']['state']=='available'
        request(dict(after=fresh['result']['cursor'],events=['command'],timeout=5,command=dict(op='finish'),request_id='finish'))
        process.wait(timeout=10);assert process.returncode==0
        assert not Path(address).exists()
        assert (root/'submitted.txt').read_text()==token
        events=[json.loads(line) for line in (root/'events.jsonl').read_text().splitlines()]
        commands=[r for r in events if r['event']=='command']
        assert sum(r['command'].get('id')=='submit' for r in commands)==1
        assert sum(r['command'].get('op')=='finalization_status' for r in commands)==2
        assert not any(r['event']=='rejected' for r in events)
        accepted,=[r for r in events if r['event']=='accepted'];ended,=[r for r in events if r['event']=='terminal']
        assert ended['release']['verified'] and ended['admitted_request']==final['evidence']['admitted_request']==accepted['admitted_request']
        delivered=[json.loads(line) for line in (root/'delivered.jsonl').read_text().splitlines()]
        collected=[r for response in responses for r in response['reply']['records']]
        assert all(response['reply']['records']==delivered[response['request']['after']:response['reply']['cursor']] for response in responses)
        for name,h in json.loads((root/'sources.json').read_text()).items():assert hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest()==h
        decoder=Decoder('live-control');count=0
        for event in events:
            if event['event']!='observation':continue
            count+=1;frame=decoder.accept((root/f'{count:03d}.ait').read_bytes())
            with Image.open(root/Path(event['image']).name) as im:assert im.size==(frame.width,frame.height) and im.tobytes()==frame.pixels
        timing=json.loads(gate.with_suffix('.timing').read_text())
        summaries.append(dict(case=case,first_state=pending['state'],final_success=final['task_success'],
            exact_frames=count,submit_commands=1,status_commands=2,old_query_replays_pending=True,fresh_query_available=True,
            terminal_to_evaluation_ms=(final['evidence']['known_ns']-ended['terminal_ns'])/1e6,
            evaluation_gate_ms=(timing['released_ns']-timing['started_ns'])/1e6,
            fallback_calls=[len(fallback['transcript']),len(fresh['transcript'])]))
    finally:
        gate.touch(exist_ok=True)
        if process.poll() is None:
            request(dict(after=0,events=['command'],timeout=0,command=dict(op='finish'),request_id='cleanup'))
            process.wait(timeout=15)
        (directory/'responses.json').write_text(json.dumps(responses,indent=2)+'\n')
        (directory/'stderr.txt').write_text(process.stderr.read())
sources=[Path(__file__),HERE/'gated_evaluation_entry_v2.py',HERE/'gated_socket_entry_v2.py',HERE/'outcome_wait.py',HERE/'outcome_fallback_v2.py',HERE/'event_socket_v11.py',HERE/'event_cursor_v5.py',HERE/'request_boundary_v2.py']
(out/'sources.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},indent=2)+'\n')
(out/'results.json').write_text(json.dumps(summaries,indent=2)+'\n');print(json.dumps(summaries,indent=2))
