"""Audit guided pointer pilot evidence, with expected failure categories retained."""
import hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
from session_v9 import Decoder
HERE=Path(__file__).resolve().parent
def main():
    report=[]
    for n in (1,2,3):
        root=HERE/f'results/guided-pointer-{n:02d}'
        for name,h in json.loads((root/'sources.json').read_text()).items():assert hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest()==h,name
        events=[json.loads(l) for l in (root/'events.jsonl').read_text().splitlines()];decoder=Decoder('live-control');frames=0
        for r in events:
            if r['event']!='observation':continue
            frames+=1;assert r['sequence']==frames
            f=decoder.accept((root/f'{frames:03d}.ait').read_bytes())
            with Image.open(root/Path(r['image']).name) as im:assert im.size==(f.width,f.height) and im.mode==f.mode and im.tobytes()==f.pixels
        results=json.loads((root/'results.json').read_text());visual=next(r for r in results if r.get('case')=='visual_result')
        assert visual['evaluation']['success'] and visual['within_one_pixel'] and abs(visual['observed_dx']-24)<=1
        rect=ET.parse(root/'shape.svg').getroot().find('{http://www.w3.org/2000/svg}rect')
        assert all(rect.get(k)==v for k,v in visual['evaluation']['actual'].items())
        terminals=[r for r in events if r['event']=='terminal'];assert all(r['release']['verified'] for r in terminals)
        assert all(r['status']=='completed' for r in terminals if r['id'] in ('visual','save','after_stall_recovery'))
        assert all(r['no_late_motion'] for r in results if r.get('case') in ('reply_timeout','original_expiry','consumed_reply_stall'))
        if n==3:assert next(r for r in terminals if r['id']=='consumed_stall')['status']=='failed'
        assert json.loads((root/'cleanup.json').read_text())['all_owned_processes_exited']
        accepted=next(r for r in events if r['event']=='accepted' and r['id']=='visual');terminal=next(r for r in terminals if r['id']=='visual')
        report.append({'cohort':n,'exact_frames':frames,'visual':visual,'guided_program_ms':(terminal['terminal_ns']-accepted['accepted_ns'])/1e6,'terminals':[{'id':r['id'],'status':r['status']} for r in terminals]})
    (HERE/'results/guided-pointer-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
