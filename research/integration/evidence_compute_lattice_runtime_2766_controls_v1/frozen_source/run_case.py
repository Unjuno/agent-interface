import argparse, hashlib, json, os, time
from pathlib import Path
from lattice import decide_cached
from runtime_path import write_source, read_source, capture, compute_once, measure_compute, calibrate_profile, active_decision, ns

CASES=[
 'cached_reuse_current','cached_reuse_at_deadline','cached_expired','cached_mismatch','cached_mismatch_attractive','cached_mismatch_expired',
 'active_run_low_p','active_wait_high_p','active_tie_shared','active_tie_zero','active_stale_attractive','active_tardy_attractive',
 'active_capture_invalidation','active_compute_invalidation','active_partial_cancel','active_deadline_cross','rebuild_measure_then_active','rebuild_no_implicit_run'
]

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--case',required=True,choices=CASES); ap.add_argument('--out',required=True); a=ap.parse_args()
    out=Path(a.out); out.mkdir(parents=True,exist_ok=False); src=out/'source.json'; png=out/'capture.png'; write_source(src,1,17)
    cap=capture(src,png); baseline_version=cap['source_version_before']; decisions=[]; notes=[]; published=False; partial=False
    # Default measured calibration from actual PNG path.
    profile='run'
    if 'wait' in a.case: profile='wait'
    if 'tie' in a.case: profile='tie'
    cal=calibrate_profile(profile,png,src)
    write_source(src,1,17)
    t=ns(); deadline=t+50_000_000
    if a.case=='cached_reuse_at_deadline': deadline=t

    if a.case.startswith('cached_') or a.case.startswith('rebuild_'):
        cached=[1]; current=[1]
        if 'mismatch' in a.case or a.case.startswith('rebuild_'): current=[2]; write_source(src,2,17)
        if 'expired' in a.case and 'mismatch' not in a.case: deadline=t-1
        if a.case=='cached_mismatch_expired': deadline=t-1
        d=decide_cached(cached,current,t,deadline)
        decisions.append({'name':a.case,'object':'CACHED_COMPLETE','stage':'initial','source_versions':cached,'current_versions':current,'t_ns':t,'deadline_ns':deadline,'disposition':d})
        if a.case=='rebuild_measure_then_active':
            # Explicitly measure rebuild cost before creating a fresh ACTIVE_JOB identity.
            write_source(src,2,17); rcap=capture(src,out/'rebuild.png'); m=measure_compute(out/'rebuild.png',0,3)
            notes.append({'rebuild_measurement':m,'rebuild_capture':rcap})
            now=ns(); dl=now+max(20_000_000,m['median_ns']*20)
            cal2=calibrate_profile('run',out/'rebuild.png',src); write_source(src,2,17)
            ad=active_decision('fresh_after_rebuild',[2],[2],now,m['median_ns'],dl,cal2,'new_job_after_measurement'); decisions.append(ad)
            if ad['disposition']=='RUN':
                comp=compute_once(out/'rebuild.png'); notes.append({'compute':comp}); published=True
        result={'case':a.case,'capture':cap,'calibration':cal,'decisions':decisions,'notes':notes,'partial_result':False,'published_reusable':published,'final_source':read_source(src)}
    else:
        source=[1]; current=[1]
        remaining=max(1,cal['compute_measure']['median_ns'])
        if a.case=='active_stale_attractive': current=[2]; write_source(src,2,17)
        if a.case=='active_tardy_attractive': deadline=t+max(1,remaining//2)
        if a.case=='active_tie_zero': cal={**cal,'p_num':1,'p_den':2,'g_ns':0,'w_ns':0}; remaining=0; deadline=t+50_000_000
        if a.case=='active_tie_shared': deadline=t+50_000_000
        if a.case in ('active_capture_invalidation','active_compute_invalidation','active_partial_cancel','active_deadline_cross'):
            deadline=t+30_000_000
        d0=active_decision(a.case,source,current,t,remaining,deadline,cal,'precompute'); decisions.append(d0)
        if d0['disposition']=='RUN':
            if a.case=='active_capture_invalidation':
                cap2=capture(src,out/'capture2.png',mutate_during=True); notes.append({'capture2':cap2})
                now=ns(); mid=active_decision(a.case,source,[read_source(src)['version']],now,remaining,deadline,cal,'postcapture'); decisions.append(mid)
            elif a.case in ('active_compute_invalidation','active_partial_cancel'):
                def cb(pns,val):
                    nonlocal partial
                    partial=True; write_source(src,2,17); notes.append({'partial_at_ns':pns,'partial_value':val})
                comp=compute_once(png,sleep_ns=1_000_000,partial_callback=cb); notes.append({'compute':comp})
                now=ns(); mid=active_decision(a.case,source,[read_source(src)['version']],now,0,deadline,cal,'midcompute_revalidation'); decisions.append(mid)
            elif a.case=='active_deadline_cross':
                # Injected compute delay is visible in the raw ledger; final hard gate must catch tardiness.
                comp=compute_once(png,sleep_ns=35_000_000); notes.append({'compute':comp})
                now=ns(); mid=active_decision(a.case,source,[read_source(src)['version']],now,0,deadline,cal,'postcompute_revalidation'); decisions.append(mid)
            else:
                comp=compute_once(png); notes.append({'compute':comp}); published=True
        # Publication is forbidden if any later revalidation canceled.
        if any(x['disposition'] in ('CANCEL_STALE','CANCEL_TARDY') for x in decisions[1:]): published=False
        result={'case':a.case,'capture':cap,'calibration':cal,'decisions':decisions,'notes':notes,'partial_result':partial,'published_reusable':published,'final_source':read_source(src)}
    (out/'result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    (out/'receipt.json').write_text(json.dumps({'case':a.case,'result_sha256':sha(out/'result.json'),'exit':0},sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'case':a.case,'decisions':[x['disposition'] for x in decisions],'published':published,'partial':partial}))
if __name__=='__main__': main()
