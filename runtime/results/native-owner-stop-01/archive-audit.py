import hashlib,json,shutil
from pathlib import Path
p=Path('runtime/results/native-owner-stop-01')
p.mkdir(exist_ok=False)
for index in (1,2):
    shutil.copytree(Path('results-local')/f'native-owner-stop-{index:02}',p/f'run-{index}')
(p/'source').mkdir()
for name in ('native_exchange_v1.py','run_native_calc_self_use_v1.py','probe_native_owner_stop_v1.py','test_native_exchange_v1.py'):
    shutil.copyfile(Path('research/live_control')/name,p/'source'/name)
for name in ('stop_native_owner.py','cleanup_native_probe.py','check_owner_stop_controls.py'):
    shutil.copyfile(Path('results-local')/name,p/'source'/name)
shutil.copyfile('results-local/native-owner-tests.txt',p/'tests.txt')
summary={'base':'ede35c0c891f0255d266aff0529a876b5c73ddc6','cases':[],
         'helper_model_calls':0,'model_usage':None,'formal_issue_2704_complete':False}
links=0
for index in (1,2):
    run=p/f'run-{index}'
    images={q.name:q for q in (run/'bridge/images').glob('*.png')}
    def audit(value):
        global links
        if isinstance(value,dict):
            n=value.get('native')
            if isinstance(n,dict) and 'artifact' in n:
                a=n['artifact']
                assert hashlib.sha256(images[Path(a['path']).name].read_bytes()).hexdigest()==a['sha256']
                assert a['source_raw_sha256']==n['sha256']
                assert value['capture_ns']==n['capture_started_ns']
                links+=1
            for v in value.values(): audit(v)
        elif isinstance(value,list):
            for v in value: audit(v)
    for q in run.rglob('*.json'): audit(json.loads(q.read_text()))
    req=(run/'request-1.json').read_bytes()
    digest=hashlib.sha256(req).hexdigest()
    checkpoint=json.loads((run/'before-reply.json').read_text())
    assert checkpoint['reply_would_be']['decision_sha256']==digest
    assert not (run/'reply-1.json').exists()
    assert len(list((run/'bridge').glob('program-*.json')))==1
    client=json.loads((run/'client-resume-1.json').read_text())
    assert client['decision_sha256']==digest and client['resumed_read_only']
    assert client['status']==('pending' if index==1 else 'unknown_requires_external_reconciliation')
    ext=json.loads((run/'external-audit.json').read_text())
    assert ext['independent_x11']['keys_down']==[] and ext['independent_x11']['pointer_mask']==0
    assert ext['saved_svg_sha256']==hashlib.sha256((run/'independent-shape.svg').read_bytes()).hexdigest()
    assert float(ext['saved_rect']['x'])==(68 if index==1 else 60)
    cleanup=json.loads((run/'external-cleanup.json').read_text())
    assert all(r['after_cleanup'] in ('absent','Z','X','x') for r in cleanup)
    summary['cases'].append({'run':index,'saved_x':ext['saved_rect']['x'],
        'client_after_owner_kill':client['status'],'native_program_files':1,
        'independently_observed_neutral_input':True})
summary['image_hash_links']=links
(p/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
shutil.copyfile(__file__,p/'archive-audit.py')
print(json.dumps(summary,indent=2))
