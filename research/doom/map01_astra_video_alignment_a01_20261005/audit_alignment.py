#!/usr/bin/env python3
"""Independent arithmetic and source-integrity audit of ALIGNMENT_RESULT.json."""
import hashlib, json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'research/doom/results/map01-astra-attempt-v1'
PKG=Path(__file__).resolve().parent

def digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''): h.update(chunk)
    return h.hexdigest()

def main():
    result=json.loads((PKG/'ALIGNMENT_RESULT.json').read_text())
    freeze=json.loads((PKG/'FREEZE.json').read_text())
    for label,path in [('video',SRC/'map01-astra-live-01-2x.mp4'),('events',SRC/'events.jsonl'),('report',SRC/'report.json')]:
        key={'video':'video_sha256','events':'events_sha256','report':'report_sha256'}[label]
        assert digest(path)==result['source'][key], f'{label} source hash mismatch'
    for rel,expected_hash in freeze['inputs'].items():
        assert digest(ROOT/rel)==expected_hash, f'frozen input changed: {rel}'
    events=[json.loads(s) for s in (SRC/'events.jsonl').read_text().splitlines()]
    report=json.loads((SRC/'report.json').read_text())
    observations={e['sequence']:e for e in events if e.get('event')=='observation'}
    anchors=result['anchors']; assert len(anchors)==12
    expected=[63,115,176,220,286,362,418,473,538,591,647,708]
    assert [a['best_frames'][0]['frame'] for a in anchors]==expected
    x=[(a['capture_ns']-anchors[0]['capture_ns'])/1e9 for a in anchors]
    y=[a['best_frames'][0]['frame'] for a in anchors]
    xb=sum(x)/len(x); yb=sum(y)/len(y)
    slope=sum((u-xb)*(v-yb) for u,v in zip(x,y))/sum((u-xb)**2 for u in x)
    intercept=yb-slope*xb
    errors=[v-(slope*u+intercept) for u,v in zip(x,y)]
    fit=result['fit']
    assert abs(slope-fit['frame_per_capture_second'])<1e-10
    assert abs(intercept-fit['intercept'])<1e-8
    assert abs(math.sqrt(sum(e*e for e in errors)/len(errors))-fit['rms_residual_frames'])<1e-8
    dec=report['decisions'][11]
    accepted=next(e for e in events if e.get('event')=='accepted' and e.get('id')=='plan-11-primary-0-2')['accepted_ns']
    timing=result['decision_11_timing']
    assert timing['controller_model_started_ns']==dec['controller_model_started_ns']
    assert timing['controller_model_ended_ns']==dec['controller_model_ended_ns']
    assert timing['accepted_ns']==accepted
    # Independently check the direction of the encoded HUD state transition.
    hud=result['health_roi_comparison']
    before=[r for r in hud if 647<=r['frame']<=702]
    after=[r for r in hud if 703<=r['frame']<=708]
    assert len(before)==56 and len(after)==6
    assert all(r['mae_to_4pct']<r['mae_to_0pct'] for r in before)
    assert all(r['mae_to_0pct']<r['mae_to_4pct'] for r in after)
    assert result['inference_boundary']['limits'].startswith('Video was encoded')
    print('PASS: source hashes, 12 anchor IDs, OLS reconstruction, controller timestamps, and HUD-reference ordering')
    print(f"PASS: LOO max error {fit['loo_max_abs_residual_frames']:.3f} frames; control-time frame {fit['frame_period_ms']:.3f} ms")
if __name__=='__main__': main()
