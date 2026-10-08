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
    assert hashlib.sha256((HERE/'readiness_probe.py').read_bytes()).hexdigest()==manifest['harness_sha256']
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
        assert all(r['status']=='completed' and r['release']['verified'] for r in terminal)
        owner=json.loads((run/'owner-events.json').read_text())
        assert owner[-1]['reason']=='close' and all(r['verified'] for r in owner)
        if case['stress']:
            first=next(i for i,r in enumerate(rows) if r['event']=='accepted')
            assert any(r['event']=='rejected' and 'expired' in r['reason'] for r in rows[:first])
            assert not any(r['event']=='input_admission' for r in rows[:first])
            assert not any(r['event']=='accepted' and r['id']=='expired' for r in rows)
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
            expired_request_rejected_without_input=True if case['stress'] else None,all_release_checks_verified=True))
    result=dict(episodes=len(results),successes=len(results),exact_frames=total,results=results,
        qualification=False,scope='four-domain scripted readiness; no model/human performance measurement')
    (folder/'audit.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='results'},indent=2))

if __name__=='__main__':audit(Path(sys.argv[1]))
