"""Offline evidence checks for historical input-state observations."""
import hashlib,json
from pathlib import Path
from PIL import Image
from session_v9 import Decoder
HERE=Path(__file__).resolve().parent
def main():
    root=HERE/'results/input-state-01';boundary=HERE/'results/pointer-focus-02'
    for p in (root,boundary):
        for name,h in json.loads((p/'sources.json').read_text()).items():assert hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest()==h
    checks=json.loads((boundary/'results.json').read_text());assert len(checks)==8 and not any('error' in r for r in checks)
    events=[json.loads(l) for l in (root/'events.jsonl').read_text().splitlines()];decoder=Decoder('live-control');frames=0
    for r in events:
        if r['event']!='observation':continue
        frames+=1;assert r['sequence']==frames
        f=decoder.accept((root/f'{frames:03d}.ait').read_bytes())
        with Image.open(root/Path(r['image']).name) as im:assert im.size==(f.width,f.height) and im.mode==f.mode and im.tobytes()==f.pixels
        a,b=r['input_state_before'],r['input_state_after']
        assert a['sample_finished_ns']<=r['capture_ns']<=b['sample_started_ns']<=b['sample_finished_ns']<=r['delivered_ns']
        assert a['revision']<=b['revision']
        assert r['owner_revision_unchanged']==(a['revision']==b['revision'])
    results=json.loads((root/'results.json').read_text());assert len(results)==4 and not any('error' in r for r in results)
    for r in results:
        assert r['before']['owned_buttons']==[1]
        if r['case'].endswith('_capture'):
            assert r['after']['owned_buttons']==[] and r['after']['revision']>r['before']['revision']
        if r['case']=='cancel_delivery':
            assert r['after']['owned_buttons']==[1] and r['release_sample_while_blocked']['owned_buttons']==[]
            assert r['after']['sample_finished_ns']<r['release_sample_while_blocked']['sample_finished_ns']<r['delivered_ns']
    terminals=[r for r in events if r['event']=='terminal'];assert len(terminals)==4 and all(r['release']['verified'] for r in terminals)
    assert json.loads((root/'cleanup.json').read_text())['all_owned_processes_exited']
    summary={'exact_frames':frames,'input_state_cases':4,'focus_boundary_regressions':8,'capture_bracket_order_verified':True,'delivery_can_outlive_hold_verified':True,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (root/'audit.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
if __name__=='__main__':main()
