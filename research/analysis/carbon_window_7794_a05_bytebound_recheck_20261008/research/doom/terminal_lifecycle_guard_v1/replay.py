"""Replay stored trials without a GUI. Pillow is needed only with --pixels."""
from __future__ import annotations
import argparse,hashlib,json,statistics
from pathlib import Path
from audit import analyze,load,rows,sha
HERE=Path(__file__).resolve().parent

def replay(evidence_root:Path,pixels:bool=False):
    evidence_root=Path(evidence_root);checked=0;pngs=0;matched=[]
    for name,record in load(evidence_root/'manifest.json').items():
        p=evidence_root/name
        if p.stat().st_size!=record['bytes'] or sha(p)!=record['sha256']:
            raise ValueError('evidence hash mismatch '+name)
        checked+=1
    runtime=evidence_root/'runtime-source'
    for i in range(12):
        out=evidence_root/f'evidence/matched-{i}'
        r=analyze(out,runtime,HERE)
        if not r['integrity_pass']:raise ValueError(r['failures'])
        if r!=load(out/'result.json'):raise ValueError('retained summary changed')
        spec=r['spec'];ds=rows(out/'runtime/acquisitions.jsonl')
        cancel=[d for d in ds if 'cancel_called_ns' in d]
        isguard=spec['guard'] and spec['timeout_seconds']==40
        if len(cancel)!=int(isguard) or not all(d['cancel_matched'] is True for d in cancel):raise ValueError('cancel cardinality')
        if isguard:
            if r['primary_status']!='cancelled' or r['late_admitted'] or not 0<=r['observed_end_to_empty_ms']<=50:raise ValueError('candidate acceptance gate')
        elif r['primary_status']!='expired' or not r['late_admitted']:raise ValueError('control gate')
        if not spec['guard'] and spec['timeout_seconds']==40 and r['post_end_down_sample_count']==0:raise ValueError('counterexample exposure missing')
        env=load(out/'runtime/environment.json')
        if env['vizdoom']!='1.3.0' or env['mode']!='Mode.ASYNC_SPECTATOR' or env['ticrate']!=35:raise ValueError('engine environment')
        fx=runtime/'research/doom/fixtures/map01-threat-contact-v2'
        for n,h in load(HERE/'matched-plan.json')['fixture'].items():
            if sha(fx/n)!=h:raise ValueError('fixture '+n)
        if pixels:
            from PIL import Image
            es=rows(out/'runtime/events.jsonl')
            typed={v['sequence']:v for v in es if v.get('event')=='typed_observation'}
            for o in (v for v in es if v.get('event')=='observation'):
                path=out/'runtime'/Path(o['image']).name
                with Image.open(path) as im:digest=hashlib.sha256(im.convert('RGB').tobytes()).hexdigest()
                if digest!=o['frame_rgb_sha256'] or typed[o['sequence']]['frame_rgb_sha256']!=digest:raise ValueError('pixel identity')
                if typed[o['sequence']]['capture_ns']!=o['capture_ns']:raise ValueError('typed epoch')
                pngs+=1
        matched.append(r)
    for name in ['preflight','discovery-0','discovery-1']:
        out=evidence_root/'evidence'/name;r=analyze(out,runtime,evidence_root/'discovery-source')
        if not r['integrity_pass'] or r!=load(out/'result.json'):raise ValueError('discovery/preflight replay')
    deltas=[]
    for rep in (1,2,3):
        arms={r['spec']['guard']:r for r in matched if r['spec']['rep']==rep and r['spec']['timeout_seconds']==40}
        deltas.append(arms[False]['observed_end_to_empty_ms']-arms[True]['observed_end_to_empty_ms'])
    summary=load(HERE/'results/summary.json')
    if statistics.median(deltas)!=summary['paired_reduction_ms']['median']:raise ValueError('paired result')
    return dict(pass_replay=True,manifest_entries=checked,matched_cases=12,excluded_cases=3,
        acquisitions=sum(r['acquisition_count'] for r in matched),keymap_samples=sum(r['keymap_count'] for r in matched),
        pixel_observations_checked=pngs,paired_reduction_ms=statistics.median(deltas),
        timeout_score_mismatches_preserved=6)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('evidence_root',type=Path);ap.add_argument('--pixels',action='store_true');a=ap.parse_args()
    print(json.dumps(replay(a.evidence_root,a.pixels),indent=2,sort_keys=True))
