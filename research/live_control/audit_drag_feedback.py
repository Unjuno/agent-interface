"""Audit all drag feedback cohorts, including partial failures."""
import hashlib,json
from pathlib import Path
from PIL import Image
from session_v9 import suite
from tile_transport import Decoder
HERE=Path(__file__).resolve().parent
def main():
    report=[]
    for root in sorted((HERE/'results').glob('drag-feedback-*')):
        sources=json.loads((root/'sources.json').read_text())
        for name,h in sources.items():assert hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest()==h,name
        events=[json.loads(l) for l in (root/'events.jsonl').read_text().splitlines()];decoder=Decoder('live-control');boxes={}
        for r in events:
            if r['event']!='observation':continue
            seq=r['sequence'];f=decoder.accept((root/f'{seq:03d}.ait').read_bytes())
            with Image.open(root/Path(r['image']).name) as im:assert im.size==(f.width,f.height) and im.mode==f.mode and im.tobytes()==f.pixels
            boxes[seq]=suite.red_bbox(f)
        assert json.loads((root/'cleanup.json').read_text())['all_owned_processes_exited']
        terminals=[r for r in events if r['event']=='terminal'];assert all(r['release']['verified'] for r in terminals)
        results=json.loads((root/'results.json').read_text())
        report.append({'cohort':root.name,'exact_frames':len(boxes),'results':results,'terminals':[{'id':r['id'],'status':r['status']} for r in terminals],
            'completed_drag_feedback':[{'point':r['point_index'],'sequence':r['sequence'],'red_bbox':boxes[r['sequence']]} for r in events if r['event']=='drag_feedback' and r['id']=='complete']})
    (HERE/'results/drag-feedback-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'cohorts':len(report),'exact_frames':sum(r['exact_frames'] for r in report),'partial_failures':[r['cohort'] for r in report if any('error' in x for x in r['results'])]}))
if __name__=='__main__':main()
