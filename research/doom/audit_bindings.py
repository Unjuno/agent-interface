"""Audit corrected directional bindings against post-control game response."""
import hashlib,json
from pathlib import Path
from PIL import Image
from audit import audit

HERE=Path(__file__).resolve().parent

def main():
    results=[]
    for cohort,folders in [('bindings-01',['0']),('bindings-fresh-01',['Left','Right','Up','Down'])]:
        root=HERE/'results'/cohort;m=json.loads((root/'manifest.json').read_text())
        for name,digest in m['sources'].items():
            assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==digest,name
        for key in folders:
            folder=root/key;r=audit(folder)
            rows=[json.loads(x) for x in (folder/'events.jsonl').read_text().splitlines()]
            assert rows==[json.loads(x) for x in (folder/'delivered.jsonl').read_text().splitlines()]
            owners=json.loads((folder/'owner-events.json').read_text())
            assert owners[-1]['reason']=='close' and all(x['verified'] for x in owners)
            state=json.loads((folder/'post-control-angle.json').read_text());a,b=state['initial'],state['final']
            if key=='Left':assert 1<b['ANGLE']<180
            elif key in ('0','Right'):assert 180<b['ANGLE']<359
            elif key=='Up':assert b['POSITION_X']>a['POSITION_X']+1
            else:assert b['POSITION_X']<a['POSITION_X']-1
            observations=[x for x in rows if x['event']=='observation' and x['id']!='post-control-refresh']
            def pixels(row):
                with Image.open(folder/Path(row['image']).name) as im:
                    return im.convert('RGB').crop((321,181,961,580)).tobytes()
            assert pixels(observations[0])!=pixels(observations[-1]),'no visible response before scoring'
            r.update(scope='scripted binding correction; not assistant gameplay or speed benchmark',
                state=state,visible_world_changed_before_scoring=True,qualification=False)
            (folder/'binding-audit.json').write_text(json.dumps(r,indent=2))
            results.append(dict(cohort=cohort,key=key,frames=r['exact_frames'],state=state))
    print(json.dumps(results,indent=2))

if __name__=='__main__':main()
