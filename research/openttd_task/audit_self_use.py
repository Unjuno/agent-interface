"""Offline verification of the first shared-pointer OpenTTD self-use episode."""
import argparse,hashlib,json,sys
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'observation_tiles'))
from tile_transport import Decoder
sys.path.insert(0,str(HERE.parent/'openttd_oracle'))
from score import score

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def audit(root):
    manifest=json.loads((root/'manifest.json').read_text())
    for name,h in manifest['sources'].items():assert sha(HERE.parent/name)==h,name
    assert sha(HERE/'results/cohort-03/baseline.sav')==manifest['save_sha256']
    cleanup=json.loads((root/'cleanup.json').read_text());assert all(cleanup.values())
    events=[json.loads(l) for l in (root/'events.jsonl').read_text().splitlines()]
    frames=[r for r in events if r['event']=='observation'];decoder=Decoder('live-control')
    for seq,r in enumerate(frames,1):
        assert r['sequence']==seq
        frame=decoder.accept((root/f'{seq:03d}.ait').read_bytes())
        with Image.open(root/Path(r['image']).name) as im:
            assert im.size==(frame.width,frame.height) and im.mode==frame.mode and im.tobytes()==frame.pixels
        assert r['pointer_binding'] and r['pointer_context_before']==r['pointer_context_after']
    terminals=[r for r in events if r['event']=='terminal']
    assert len(terminals)==3 and all(r['status']=='completed' and r['release']['verified'] for r in terminals)
    accepted={r['id']:r for r in events if r['event']=='accepted'}
    durations={r['id']:(r['terminal_ns']-accepted[r['id']]['accepted_ns'])/1e6 for r in terminals}
    evaluation=json.loads((root/'evaluation.json').read_text())
    independent=score(evaluation['observation'],{'target':[678,679,680],'forbidden':[742,743,744],'owner':0})
    assert independent['success'] and independent['checks']==evaluation['checks']
    game=[json.loads(l.split('AIT ',1)[1]) for l in (root/'game-stderr.txt').read_text().splitlines() if 'AIT {' in l]
    assert evaluation['observation']==game[-1]
    assert not score(game[0],{'target':[678,679,680],'forbidden':[742,743,744],'owner':0})['success']
    settle=[r for r in events if r['event']=='settle_result']
    supplementary=['live_control/quiet_window.py','observation_tiles/tile_transport.py','observation_tiles/image_artifact.py','observation_gating/gui_suite.py','observation_gating/exact_gate.py','real_apps_v1/real_app_suite_v1.py']
    return {'scope':'one assistant visual self-use episode, not a performance comparison','frames_exact':len(frames),'programs':len(terminals),'program_accept_to_terminal_ms':durations,'initial_capture_to_last_terminal_ms':(terminals[-1]['terminal_ns']-frames[0]['capture_ns'])/1e6,'independent_score':independent,'settle':settle,'cleanup':cleanup,'supplementary_dependency_hashes_at_audit':{n:sha(HERE.parent/n) for n in supplementary},'artifacts_sha256':{p.name:sha(p) for p in sorted(root.iterdir()) if p.is_file() and p.name!='audit.json'}}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);a=ap.parse_args();r=audit(a.root)
    (a.root/'audit.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ('artifacts_sha256','supplementary_dependency_hashes_at_audit')},indent=2))
