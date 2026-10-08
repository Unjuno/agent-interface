import hashlib,json,shutil,xml.etree.ElementTree as ET
from pathlib import Path
from openpyxl import load_workbook
p=Path('runtime/results/native-mixed-app-01')
p.mkdir(exist_ok=False)
for index in (1,2):
    shutil.copytree(Path('results-local')/f'native-mixed-app-{index:02}',p/f'run-{index}')
(p/'source').mkdir()
for name in ('native_exchange_v1.py','native_handle_bridge_v1.py','run_native_calc_self_use_v1.py',
             'test_native_exchange_v1.py','test_native_handle_bridge_v1.py'):
    shutil.copyfile(Path('research/live_control')/name,p/'source'/name)
shutil.copyfile('results-local/native-mixed-tests.txt',p/'tests.txt')
summary={'base':'2f29897227445b1e56ea72a2ccbb030701fa1417','runs':[],
         'formal_issue_2499_complete':False,'helper_model_calls':0,'model_usage':None}
links=0
for index in (1,2):
    run=p/f'run-{index}'
    images={q.name:q for q in (run/'bridge/images').glob('*.png')}
    def audit(v):
        global links
        if isinstance(v,dict):
            n=v.get('native')
            if isinstance(n,dict) and 'artifact' in n:
                a=n['artifact']
                assert hashlib.sha256(images[Path(a['path']).name].read_bytes()).hexdigest()==a['sha256']
                assert a['source_raw_sha256']==n['sha256'] and v['capture_ns']==n['capture_started_ns']
                links+=1
            for child in v.values(): audit(child)
        elif isinstance(v,list):
            for child in v: audit(child)
    for q in run.rglob('*.json'): audit(json.loads(q.read_text()))
    actions=json.loads((run/'actions.json').read_text())
    assert len(actions)==(3 if index==1 else 4)
    previous=json.loads((run/'source-1.json').read_text())
    initial_surface=previous['pointer_binding']['surface']
    ledger=[]
    for stage,row in enumerate(actions,1):
        assert row['result']['status']=='completed'
        releases=row['result']['execution']['releases']
        assert releases and all(r['verified'] is True and r['keys_down']==[] and r['buttons_down']==[] for r in releases)
        review=row['window_review']
        assert review['status']=='reviewed' and review['authority_granted'] is False and review['input_dispatched'] is False
        assert review['previous_binding_revision']==stage-1 and review['binding_revision']==stage
        assert review['previous_scope']!=review['scope']
        probes=[row['old_target_probe'],*row['retired_target_probes']]
        assert len(probes)==stage
        assert all(pr['emissions']==0 and pr['result']['status']=='refused' for pr in probes)
        current=review['observation']
        if stage==3:
            if index==1:
                assert current['pointer_binding']['geometry'][2:]==[1,1]
                assert current['pointer_binding']['surface']!=initial_surface
            else:
                assert current['pointer_binding']['geometry'][2:]==[1280,781]
                assert current['pointer_binding']['surface']==initial_surface
                assert current['pointer_binding']['focus']!=initial_surface
        req=(run/f'request-{stage}.json').read_bytes()
        assert json.loads(req)['source_sequence']==previous['sequence']
        reply=json.loads((run/f'reply-{stage}.json').read_text())
        assert reply['decision_sha256']==hashlib.sha256(req).hexdigest()
        ledger.append({'stage':stage,'from':previous['pointer_binding'],'to':current['pointer_binding'],
            'from_revision':stage-1,'to_revision':stage,'stale_probes':len(probes),
            'local_exchange_ms':(json.loads((run/f'client-{stage}.json').read_text())['exchange']['returned_ns']-
                                 json.loads((run/f'client-{stage}.json').read_text())['exchange']['started_ns'])/1e6})
        previous=current
    stage=len(actions)+1
    reply=json.loads((run/f'reply-{stage}.json').read_text())
    assert reply['decision_sha256']==hashlib.sha256((run/f'request-{stage}.json').read_bytes()).hexdigest()
    assert reply['status']=='finished' and reply['evaluation']['success'] is True
    workbook=load_workbook(run/'sheet.xlsx',read_only=True)
    values=[workbook.active['A1'].value,workbook.active['A2'].value]
    workbook.close()
    assert values==([859,568] if index==1 else [324,455])
    rect=ET.parse(run/'shape.svg').getroot().find('{http://www.w3.org/2000/svg}rect').attrib
    assert all(float(rect[k])==v for k,v in dict(x=58 if index==1 else 62,y=50,width=40,height=30).items()) and 'transform' not in rect
    assert all(r['returncode'] is not None for r in json.loads((run/'cleanup.json').read_text()))
    assert len(list((run/'bridge').glob('program-*.json')))==len(actions)
    summary['runs'].append({'run':index,'actions':len(actions),'stale_refusals':sum(range(1,len(actions)+1)),
        'calc_values':values,'inkscape_x':rect['x'],'correct_return_surface':index==2,'ledger':ledger})
summary['image_hash_links']=links
(p/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
shutil.copyfile(__file__,p/'archive-audit.py')
print(json.dumps(summary,indent=2))
