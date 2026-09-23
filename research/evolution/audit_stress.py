"""Audit the declared cohort, original events, exact frames and saved artifacts."""
import hashlib,json,sys,urllib.parse,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
from openpyxl import load_workbook

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'observation_tiles'))
from tile_transport import Decoder,Frame

def audit(folder):
    manifest=json.loads((folder/'manifest.json').read_text())
    assert hashlib.sha256((HERE/'stress_probe.py').read_bytes()).hexdigest()==manifest['harness_sha256']
    for name,digest in manifest['reference_sources'].items():
        assert hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest()==digest,name
    reports=json.loads((folder/'summary.json').read_text());assert len(reports)==len(manifest['cases'])==8
    total=0;results=[]
    for case,report in zip(manifest['cases'],reports):
        assert all(report[k]==v for k,v in case.items()) and 'error' not in report
        run=folder/f"{case['app']}-{case['seed']}"
        assert json.loads((run/'sources.json').read_text())==manifest['reference_sources']
        rows=[json.loads(s) for s in (run/'events.jsonl').read_text().splitlines()]
        ready=next(r for r in rows if r['event']=='ready');goal=ready['goal']
        assert ready['presentation']=='full'
        assert [json.loads(s) for s in (run/'delivered.jsonl').read_text().splitlines()]==rows
        decoder=Decoder('live-control');frames=0
        for r in rows:
            if r['event']=='observation':
                frame=decoder.accept((run/f"{r['sequence']:03d}.ait").read_bytes())
                with Image.open(run/Path(r['image']).name) as im:
                    assert frame==Frame(im.width,im.height,im.mode,im.tobytes())
                frames+=1
        assert frames==report['observations'];total+=frames
        terminal=[r for r in rows if r['event']=='terminal']
        assert len(terminal)==report['accepted_programs']
        assert all(r['release']['verified'] for r in terminal)
        interruption=next(r for r in terminal if r['id']=='interrupt')
        assert interruption['status']==('cancelled' if case['stress']=='cancel' else 'expired')
        assert interruption['steps_completed']==0
        assert all(r['status']=='completed' for r in terminal if r['id']!='interrupt')
        assert not any(r['event']=='step_started' and r.get('id')=='interrupt' and r['step']>0 for r in rows)
        owner=json.loads((run/'owner-events.json').read_text())
        assert owner[-1]['reason']=='close' and all(r['verified'] for r in owner)
        anchor=report['interruption']['anchor_ns']
        assert report['interruption']['release_after_anchor_ms']==(interruption['release']['verified_ns']-anchor)/1e6
        assert any(r['event']=='keys_held' and r['id']=='interrupt' for r in rows)
        if case['stress']=='cancel':assert any(r['event']=='cancel_requested' and r['matched'] for r in rows)
        first_owner=owner[0]
        assert first_owner['verified_ns']<=interruption['release']['verified_ns']
        app=case['app']
        if app=='xterm':actual=(run/'submitted.txt').read_text();correct=actual==goal['token']
        elif app=='chromium':
            actual=urllib.parse.parse_qs((run/'submitted.txt').read_text());correct=actual=={'value':[goal['token']]}
        elif app=='calc':
            wb=load_workbook(run/'sheet.xlsx',read_only=True,data_only=False)
            actual=[wb.active['A1'].value,wb.active['A2'].value];wb.close();correct=actual==[goal['a'],goal['b']]
        else:
            rects=ET.parse(run/'shape.svg').getroot().findall('{http://www.w3.org/2000/svg}rect');assert len(rects)==1
            actual={k:rects[0].get(k) for k in ('x','y','width','height','transform')}
            correct=actual['transform'] is None and float(actual['x'])>50.5 and all(abs(float(actual[k])-v)<.1 for k,v in [('y',50),('width',40),('height',30)])
        assert correct and actual==report['actual'] and report['task_success']
        results.append(dict(**case,exact_frames=frames,independent_task_success=correct,
            interruption_status=interruption['status'],all_release_checks_verified=True,
            owner_release_after_anchor_ms=(first_owner['verified_ns']-anchor)/1e6,
            terminal_release_after_anchor_ms=report['interruption']['release_after_anchor_ms']))
    result=dict(episodes=len(results),successes=len(results),exact_frames=total,results=results,
        qualification=False,scope='four-domain scripted interruption stress; no model/human performance measurement')
    (folder/'audit.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='results'},indent=2))

if __name__=='__main__':audit(Path(sys.argv[1]))
