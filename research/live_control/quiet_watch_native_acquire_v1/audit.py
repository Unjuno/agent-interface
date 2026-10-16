#!/usr/bin/env python3
"""Offline replay; no runner import, display, model or input."""
import argparse, base64, hashlib, json, statistics, sys
from pathlib import Path

def audit(raw, prereg):
    obj=json.loads(raw.read_text()); plan=json.loads(prereg.read_text())
    assert obj['mode']=='formal' and not obj['errors']
    assert obj['sources']==plan['sources']
    assert obj['prereg_sha256']==hashlib.sha256(prereg.read_bytes()).hexdigest()
    for name,expected in obj['sources'].items():
        p=prereg.parent/name
        if name=='run_quiet_watch_poll_period_v1.py':
            p=prereg.parent.parent/'quiet_watch_poll_period_v1'/name
        assert hashlib.sha256(p.read_bytes()).hexdigest()==expected
    rs=obj['records']
    case_sequence=[r['case'] for r in rs]
    assert hashlib.sha256(json.dumps(case_sequence,sort_keys=True).encode()).hexdigest()==plan['schedule_sha256']
    assert obj['environment']['binary_sha256']==plan['binary_sha256']
    assert len(rs)==38
    frame_count=0; stats=[]
    for r in rs:
        counts={}
        for sha,encoded in r['pixel_payloads'].items():
            b=base64.b64decode(encoded,validate=True)
            assert len(b)==4096 and hashlib.sha256(b).hexdigest()==sha
            pixels=list(zip(b[0::4],b[1::4],b[2::4]))
            counts[sha]=sum(pixel==(50,50,220) for pixel in pixels)
        ac=r['acquisitions']; metrics=r['acquisition_metrics']
        assert len(ac)==len(metrics)>0
        for a,m in zip(ac+[r['final']],metrics+[r['final_metrics']]):
            assert counts[a['digest']]==a['match_count']
            assert a['start_ns']==m[0]<=a['end_ns']==m[1]<=m[3]
            assert 0<=m[2]<=m[4]
            frame_count+=1
        assert all(a['end_ns']<=b['start_ns'] for a,b in zip(ac,ac[1:]))
        found=[a for a in ac if counts[a['digest']]>=512]
        assert bool(found)==r['derived']['detected']==('detected_ns' in r['watcher'])
        if found: assert found[0]['end_ns']==r['watcher']['detected_ns']
        assert not r['thread_errors'] and r['owner']['verified_empty'] is True
        assert r['right_down_final'] is False
        assert [e['kind'] for e in r['events']]==['app_key_press','app_key_release']
        assert counts[r['final']['digest']]==0
        assert r['owner']['deadline_ns']-r['owner']['app_press_seen_ns']==600000000
        assert r['owner']['release_command_ns']<=r['owner']['release_sync_ns']<=r['owner']['verified_empty_ns']
        assert r['owner']['release_reason']==('watcher_cancel' if found else 'deadline')
        if not found: assert r['owner']['release_command_ns']>=r['owner']['deadline_ns']
        if r['case']['kind']=='nuisance': assert not found
        wall=sum(m[1]-m[0] for m in metrics)/1e6
        cpu=sum(m[2] for m in metrics)/1e6
        full=sum(m[3]-m[0] for m in metrics)/1e6
        fullcpu=sum(m[4] for m in metrics)/1e6
        duration=(r['cue']['off_draw_complete_ns']-r['cue']['on_draw_complete_ns'])/1e6
        assert duration>=5
        assert abs(wall-r['derived']['acquisition_wall_ms'])<1e-8
        assert abs(duration-r['derived']['cue_duration_ms'])<1e-8
        stats.append(dict(case=r['case'],detected=bool(found),count=len(ac),
            acquisition_wall_ms=wall, acquisition_cpu_ms=cpu,
            getter_predicate_wall_ms=full,getter_predicate_cpu_ms=fullcpu,
            cue_ms=duration, max_gap_ms=max((b['start_ns']-a['end_ns'])/1e6 for a,b in zip(ac,ac[1:]))))
    result=dict(raw_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),
        audit_pass=True,frames_reclassified=frame_count,cases=38,arms={},case_stats=stats)
    fields=('acquisition_wall_ms','acquisition_cpu_ms','getter_predicate_wall_ms',
            'getter_predicate_cpu_ms','count','max_gap_ms')
    for arm in ('python','native'):
        ts=[s for s in stats if s['case']['backend']==arm and s['case']['kind']=='target']
        ns=[s for s in stats if s['case']['backend']==arm and s['case']['kind']=='nuisance']
        assert len(ts)==15 and len(ns)==4
        result['arms'][arm]=dict(target_detected=sum(s['detected'] for s in ts),
            target_n=15,nuisance_n=4,nuisance_false=0,
            target_cue_ms_median=statistics.median(s['cue_ms'] for s in ts),
            target_cue_ms_range=[min(s['cue_ms'] for s in ts),max(s['cue_ms'] for s in ts)],
            nuisance={k:dict(median=statistics.median(s[k] for s in ns),
                minimum=min(s[k] for s in ns),maximum=max(s[k] for s in ns)) for k in fields})
    ratios=[]; per_sample=[]
    for s in stats:
        if s['case']['kind']=='nuisance' and s['case']['backend']=='python':
            t=next(t for t in stats if t['case']['pair_id']==s['case']['pair_id'] and t['case']['backend']=='native')
            ratios.append(t['acquisition_wall_ms']/s['acquisition_wall_ms'])
            per_sample.append((t['acquisition_wall_ms']/t['count'])/(s['acquisition_wall_ms']/s['count']))
    sampling_ok=all(270<=s['count']<=330 for s in stats if s['case']['kind']=='nuisance')
    result.update(paired_cost_ratios=ratios,median_paired_cost_ratio=statistics.median(ratios),
        paired_per_sample_ratios=per_sample,median_paired_per_sample_ratio=statistics.median(per_sample),
        sampling_gate=sampling_ok)
    if not sampling_ok:
        decision='HOLD_SAMPLING_RATE_CHANGED'
    elif result['arms']['native']['target_detected']!=15:
        decision='HOLD_DETECTION_GATE'
    elif max(statistics.median(ratios),statistics.median(per_sample))>0.8:
        decision='HOLD_COST_GATE'
    else:
        decision='PASS_COST_SCOPED'
    result['decision']=decision
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('raw',type=Path);ap.add_argument('prereg',type=Path)
    args=ap.parse_args()
    print(json.dumps(audit(args.raw,args.prereg),indent=2,sort_keys=True))
