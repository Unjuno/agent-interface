"""Offline audit of desktop pointer transfer and scripted precision failures."""
import hashlib,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'observation_tiles'))
from tile_transport import Decoder

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def frames(root):
    events=[json.loads(l) for l in (root/'events.jsonl').read_text().splitlines()]
    decoder=Decoder('live-control');count=0
    for r in events:
        if r['event']!='observation':continue
        count+=1;assert r['sequence']==count
        f=decoder.accept((root/f'{count:03d}.ait').read_bytes())
        with Image.open(root/Path(r['image']).name) as im:assert im.size==(f.width,f.height) and im.mode==f.mode and im.tobytes()==f.pixels
    terminals=[r for r in events if r['event']=='terminal'];assert all(r['status']=='completed' and r['release']['verified'] for r in terminals)
    return events,count

def main():
    pilot=HERE/'results/pointer-desktop-01'
    hashes=json.loads((pilot/'sources.json').read_text())
    for name,h in hashes.items():assert sha(HERE.parent/name)==h,name
    events,count=frames(pilot)
    rejected=[r for r in events if r['event']=='rejected'];assert len(rejected)==1 and rejected[0]['reason']=='unsupported chord'
    assert not any(r.get('id')=='drag-and-save' and r['event']=='accepted' for r in events)
    assert next(r for r in events if r['event']=='independent_evaluation')['success']
    report={'scope':'known desktop task; no speedup or exact-motor-success claim','assistant_exact_frames':count,'prevalidation_rejection_retained':True,'paired_runs':[]}
    for i,source in [(1,'desktop_drag_probe.py'),(2,'desktop_drag_probe_v2.py')]:
        root=HERE/f'results/drag-resolution-{i:02d}'
        plan=json.loads((root/'plan.json').read_text());assert plan['source_sha256']==sha(HERE/source)
        for mode in plan['order']:
            p=root/mode;r=json.loads((p/'result.json').read_text());_,n=frames(p)
            rect=ET.parse(p/'shape.svg').getroot().find('{http://www.w3.org/2000/svg}rect')
            for k,v in r['legacy_evaluation']['actual'].items():assert rect.get(k)==v
            assert r['legacy_evaluation']['success'] and not r['within_one_pixel']
            assert json.loads((p/'cleanup.json').read_text())['all_owned_processes_exited']
            report['paired_runs'].append({'cohort':i,'mode':mode,'requested_dx_pixels':24,'actual_dx_pixels':r['observed_dx_pixels'],'saved_x':rect.get('x'),'exact_frames':n})
    report['audit_source_sha256']=sha(Path(__file__))
    (HERE/'results/desktop-pointer-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
