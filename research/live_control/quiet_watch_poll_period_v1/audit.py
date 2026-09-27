#!/usr/bin/env python3
import argparse, base64, hashlib, json, statistics
from pathlib import Path
TARGET_BGR=bytes((50,50,220)); THRESHOLD=512

def sha256_file(p):
    h=hashlib.sha256();
    with open(p,'rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''): h.update(chunk)
    return h.hexdigest()

def med(xs): return statistics.median(xs) if xs else None

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('measured'); ap.add_argument('prereg'); ap.add_argument('source'); ap.add_argument('--out',required=True); a=ap.parse_args()
    m=json.load(open(a.measured)); p=json.load(open(a.prereg)); checks=[]
    def ck(name, ok, detail=None): checks.append({'name':name,'pass':bool(ok),'detail':detail}); return bool(ok)
    ck('schema',m.get('schema')=='quiet_watch_poll_period_v1')
    ck('not_preflight',m.get('preflight') is False)
    ck('source_sha256',sha256_file(a.source)==p['source_sha256'],sha256_file(a.source))
    ck('measured_count',len(m['records'])==p['measured_cases'],len(m['records']))
    actual=[r['case'] for r in m['records']]
    ck('schedule_exact',actual==p['schedule'])
    ids=[c['case_id'] for c in actual]; ck('case_ids_unique',len(ids)==len(set(ids)))
    pixel_ok=True; count_ok=True; detect_ok=True; event_ok=True; release_ok=True; final_ok=True
    for r in m['records']:
        payloads={k:base64.b64decode(v) for k,v in r['pixel_payloads'].items()}
        for dig,raw in payloads.items():
            pixel_ok &= hashlib.sha256(raw).hexdigest()==dig
        observed_detect=False
        for x in r['acquisitions']:
            raw=payloads[x['digest']]
            c=sum(raw[i:i+3]==TARGET_BGR for i in range(0,len(raw),4))
            count_ok &= c==x['match_count']
            observed_detect |= c>=THRESHOLD
        f=r['final']; raw=payloads[f['digest']]; c=sum(raw[i:i+3]==TARGET_BGR for i in range(0,len(raw),4)); count_ok &= c==f['match_count']
        detect_ok &= observed_detect==r['derived']['detected']==('detected_ns' in r['watcher'])
        event_ok &= sum(e['kind']=='app_key_press' for e in r['events'])==1 and sum(e['kind']=='app_key_release' for e in r['events'])==1
        release_ok &= bool(r['owner'].get('verified_empty')) and not bool(r['right_down_final'])
        final_ok &= f['match_count']<THRESHOLD
    ck('pixel_payload_sha256',pixel_ok); ck('pixel_match_counts',count_ok); ck('detection_rederived',detect_ok)
    ck('one_press_one_release',event_ok); ck('verified_empty_all',release_ok); ck('final_roi_clear_all',final_ok)
    # independently recompute key summary
    arms={}
    for per in (10,2):
        rs=[r for r in m['records'] if r['case']['period_ms']==per]
        tar=[r for r in rs if r['case']['kind']=='target']; nui=[r for r in rs if r['case']['kind']=='nuisance']
        arms[str(per)]={
          'target_detected':sum(bool(r['derived']['detected']) for r in tar), 'target_total':len(tar),
          'nuisance_false_cancel':sum(bool(r['derived']['detected']) for r in nui), 'nuisance_total':len(nui),
          'nuisance_acquisition_wall_ms_median':med([r['derived']['acquisition_wall_ms'] for r in nui]),
          'nuisance_acquisition_count_median':med([r['derived']['acquisition_count'] for r in nui]),
          'target_release_ms_median':med([r['derived']['cue_to_app_release_ms'] for r in tar if r['derived']['cue_to_app_release_ms'] is not None]),
        }
    ck('summary_target_counts',all(arms[k]['target_detected']==m['summary']['arms'][k]['target_detected'] for k in arms),arms)
    ck('summary_nuisance_counts',all(arms[k]['nuisance_false_cancel']==m['summary']['arms'][k]['nuisance_false_cancel'] for k in arms))
    ck('summary_cost_medians',all(abs(arms[k]['nuisance_acquisition_wall_ms_median']-m['summary']['arms'][k]['nuisance_acquisition_wall_ms_median'])<1e-12 for k in arms))
    cost_ratio=arms['2']['nuisance_acquisition_wall_ms_median']/arms['10']['nuisance_acquisition_wall_ms_median']
    integrity=event_ok and release_ok and final_ok and arms['10']['nuisance_false_cancel']==0 and arms['2']['nuisance_false_cancel']==0
    if not integrity: decision='FAIL_SAFETY_OR_INTEGRITY'
    elif arms['2']['target_detected']>arms['10']['target_detected'] and cost_ratio<=5: decision='PROMOTE_2MS_SCOPED'
    elif arms['2']['target_detected']>arms['10']['target_detected']: decision='HOLD_DETECTION_GAIN_COST_GATE_FAIL'
    else: decision='HOLD_NO_DETECTION_GAIN'
    ck('decision_rederived',decision==m['summary']['decision'],decision)
    # mechanism diagnostic: every baseline miss lies wholly between an acquisition end and next acquisition start
    misses=[]
    for r in m['records']:
        if r['case']['period_ms']==10 and r['case']['kind']=='target' and not r['derived']['detected']:
            on=r['cue']['on_draw_complete_ns']; off=r['cue']['off_draw_complete_ns']; acq=r['acquisitions']
            prev=[x for x in acq if x['end_ns']<=on]; nxt=[x for x in acq if x['start_ns']>=off]
            contained=bool(prev and nxt and prev[-1]['end_ns']<=on and off<=nxt[0]['start_ns'])
            misses.append({'case_id':r['case']['case_id'],'contained_between_samples':contained,'cue_duration_ms':r['derived']['cue_duration_ms'],'gap_ms':((nxt[0]['start_ns']-prev[-1]['end_ns'])/1e6 if prev and nxt else None)})
    ck('all_10ms_misses_between_samples',len(misses)>0 and all(x['contained_between_samples'] for x in misses),misses)
    out={'formal_pass':all(x['pass'] for x in checks),'checks':checks,'rederived':{'arms':arms,'cost_ratio':cost_ratio,'decision':decision,'baseline_misses':misses},'hashes':{'measured_sha256':sha256_file(a.measured),'prereg_sha256':sha256_file(a.prereg),'source_sha256':sha256_file(a.source)}}
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True),encoding='utf-8')
    print(json.dumps({'formal_pass':out['formal_pass'],'decision':decision,'cost_ratio':cost_ratio,'checks':len(checks)},sort_keys=True))
if __name__=='__main__': main()
