"""Matched scripted fixture: early finalization vs admission-preserving review."""
import hashlib,json,socket,subprocess,sys
from pathlib import Path
from PIL import Image
from session_v9 import Decoder
HERE=Path(__file__).resolve().parent
OUT=HERE/'results/checkpoint-confirmation-02';OUT.mkdir(exist_ok=False)
summaries=[]
for mode in ('review_then_confirm',):
    out=OUT/mode;out.mkdir();root=out/'runtime';responses=[]
    proc=subprocess.Popen([sys.executable,'-u',str(HERE/'confirmation_socket_entry_v4.py'),
        'serve','--','--app','chromium','--seed','991029','--out',str(root),'--presentation','compact'],
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    address=json.loads(proc.stdout.readline())['socket']
    def request(spec):
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as c:
            c.settimeout(35);c.connect(address);c.sendall((json.dumps(spec)+'\n').encode())
            with c.makefile('rb') as stream:reply=json.loads(stream.readline())
        responses.append(dict(request=spec,reply=reply));return reply
    def cli(source,name,steps,boundary):
        stepfile=out/f'{name}-steps.json';stepfile.write_text(json.dumps(steps)+'\n')
        result=subprocess.run([sys.executable,str(HERE/'prepared_exchange_v6.py'),address,
            str(source),str(root),name,str(stepfile),'--lease-ms','30000','--boundary',boundary,
            '--producer','scripted','--out',str(out/name)],capture_output=True,text=True,timeout=12)
        (out/f'{name}-stderr.txt').write_text(result.stderr)
        assert result.returncode==0,result.stderr
        return json.loads(result.stdout)
    try:
        initial=request(dict(after=0,events=['clock'],timeout=10,command=dict(op='clock'),request_id='initial'))
        assert initial['status']=='boundary'
        source=out/'initial.json';source.write_text(json.dumps(initial,indent=2)+'\n')
        goal=next(r['goal'] for r in initial['records'] if r['event']=='ready')
        nav=cli(source,'navigate',[dict(op='chord',modifier='Control_L',key='l'),
            dict(op='text',text=goal['url']),dict(op='key',key='Return'),
            dict(op='settle',quiet_ms=150,timeout_ms=1500)],'terminal')
        assert nav['status']=='boundary'
        attempt=cli(out/'navigate/reply.json','submit',[dict(op='chord',modifier='Control_L',key='a'),
            dict(op='text',text=goal['token']),dict(op='key',key='Return'),
            dict(op='settle',quiet_ms=150,timeout_ms=1500)],
            'outcome' if mode=='premature_final' else 'terminal')
        archived=[json.loads(s) for s in (root/'submission-attempts.jsonl').read_text().splitlines()]
        assert len(archived)==1 and archived[0]['accepted'] is False
        assert archived[0]['fields']=={'value':[goal['token']]}
        (out/'checkpoint.json').write_text(json.dumps(dict(attempts=archived,
            task_success=attempt.get('outcome',{}).get('task_success'),
            scope='harness observation of fixture log; not sent to scripted controller as authority'),indent=2)+'\n')
        def checkpoint(after,name):
            reply=request(dict(after=after,events=['effect_checkpoint'],timeout=5,
                command=dict(op='effect_checkpoint',contract=dict(kind='saved_form_value',expected=goal['token'])),
                request_id=name,read_request_id=name))
            assert reply['status']=='boundary' and reply['records'][-1]['transport_request_id']==name
            assert reply['records'][-1]['task_success'] is None
            return reply
        before=checkpoint(attempt['cursor'],'before-confirm')
        assert before['records'][-1]['evidence']['status']=='UNKNOWN'
        # Advance cursor while keeping the actual prior image reference for preparation.
        checkpoint_source=out/'checkpoint-source.json'
        checkpoint_source.write_text(json.dumps(dict(before,records=attempt['records']+before['records']),indent=2)+'\n')
        confirm=cli(checkpoint_source,'confirm',[dict(op='key',key='Tab'),dict(op='key',key='space'),
            dict(op='key',key='Tab'),dict(op='key',key='Return')],'terminal')
        if mode=='premature_final':
            assert attempt['outcome']['task_success'] is False
            assert confirm['status']=='request_rejected'
            assert confirm['records'][-1]['reason']=='final program already reserved'
        else:
            assert 'outcome' not in attempt
            assert confirm['status']=='boundary' and 'outcome' not in confirm
        after=checkpoint(confirm['cursor'],'after-confirm')
        assert after['records'][-1]['evidence']['status']=='VERIFIED'
        assert not any(json.loads(s)['event']=='independent_evaluation' for s in (root/'events.jsonl').read_text().splitlines())
        request(dict(after=after['cursor'],events=['command'],timeout=5,command=dict(op='finish'),request_id='finish'))
        proc.wait(timeout=10);assert proc.returncode==0 and not Path(address).exists()
        archived=[json.loads(s) for s in (root/'submission-attempts.jsonl').read_text().splitlines()]
        expected=[False] if mode=='premature_final' else [False,True]
        assert [r['accepted'] for r in archived]==expected
        events=[json.loads(s) for s in (root/'events.jsonl').read_text().splitlines()]
        accepted=[r for r in events if r['event']=='accepted']
        terminals=[r for r in events if r['event']=='terminal']
        assert len(accepted)==len(terminals)==(2 if mode=='premature_final' else 3)
        assert all(r['status']=='completed' and r['release']['verified'] for r in terminals)
        assert all(r['producer']=='scripted' for r in events if r['event']=='decision_evidence')
        scores=[r for r in events if r['event']=='independent_evaluation']
        assert len(scores)==1 and scores[0]['success']==(mode=='review_then_confirm')
        assert scores[0].get('admitted_request') is None  # legacy explicit finish, not action-attributed scoring
        delivered=[json.loads(s) for s in (root/'delivered.jsonl').read_text().splitlines()]
        assert initial['records']+nav['records']+attempt['records']+before['records']+confirm['records']+after['records']==delivered[:after['cursor']]
        for name,h in json.loads((root/'sources.json').read_text()).items():
            assert hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest()==h
        decoder=Decoder('live-control');frames=0
        for event in events:
            if event['event']!='observation':continue
            frames+=1;frame=decoder.accept((root/f'{frames:03d}.ait').read_bytes())
            with Image.open(root/Path(event['image']).name) as im:
                assert im.size==(frame.width,frame.height) and im.tobytes()==frame.pixels
        summaries.append(dict(before_checkpoint=before['records'][-1]['evidence']['status'],after_checkpoint=after['records'][-1]['evidence']['status'],mode=mode,task_success=scores[0]['success'],exact_frames=frames,
            admitted_programs=len(accepted),http_acceptance=expected,log_survived_cleanup=True,
            confirmation_status=confirm['status']))
    finally:
        if proc.poll() is None:
            request(dict(after=0,events=['command'],timeout=0,command=dict(op='finish'),request_id='cleanup'))
            proc.wait(timeout=15)
        (out/'responses.json').write_text(json.dumps(responses,indent=2)+'\n')
        (out/'stderr.txt').write_text(proc.stderr.read())
(OUT/'results.json').write_text(json.dumps(dict(cases=summaries,
    scope='One scripted admission-preserving checkpoint run; known fixture, not model recovery or full Issue 34 contract'),indent=2)+'\n')
files=[Path(__file__),HERE/'confirmation_socket_entry_v4.py',HERE/'confirmation_browser_entry_v3.py',
    HERE/'prepared_exchange_v6.py',HERE/'effect_checkpoint.py',HERE/'command_once_v3.py',HERE/'request_boundary_v3.py',HERE/'event_cursor_v6.py',HERE/'event_socket_v14.py']
(OUT/'sources.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2)+'\n')
print(json.dumps(summaries,indent=2))
