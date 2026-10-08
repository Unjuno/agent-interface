"""Offline replay of retained action, source, score, physical-release and image evidence."""
from __future__ import annotations
import argparse,hashlib,json,statistics
from pathlib import Path

LANE=Path('research/doom/autoresearch_direction_v1')
def load(p):return json.loads(p.read_text())
def rows(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()] if p.exists() else []
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(condition,reason):
    if not condition:raise ValueError(reason)
def privileged(obj):
    if isinstance(obj,dict):return bool(set(obj)&{'kill_count','death_count','independent-progress-event-v2'}) or any(privileged(x) for x in obj.values())
    if isinstance(obj,list):return any(privileged(x) for x in obj)
    return False

def audit_case(workspace,spec,allocation,pixels=True):
    case=workspace/'evidence'/allocation/spec['id'];rt=case/'runtime'
    ev=rows(rt/'events.jsonl');sp=rows(rt/'scorer-samples.jsonl');se=rows(rt/'scorer-events.jsonl')
    need((rt/'events.jsonl').read_bytes()==(rt/'delivered.jsonl').read_bytes(),'delivery')
    a=[r for r in ev if r.get('event')=='accepted'];t=[r for r in ev if r.get('event')=='terminal']
    need(len(a)==len(t)==1 and a[0]['id']==t[0]['id']==spec['id'],'program uniqueness')
    a=a[0];t=t[0];need(t['status']=='expired','expected expiry')
    cmd=[r['command'] for r in ev if r.get('event')=='command' and r['command'].get('op')=='submit']
    need(len(cmd)==1,'submit count');cmd=cmd[0]
    expected={'attack':['space'],'back_left':['s','a','space'],'back_right':['s','d','space']}[spec['policy']]
    need(cmd['steps']==[{'op':'hold','keys':expected,'duration_ms':5000}],'declared program')
    need(hashlib.sha256(json.dumps(cmd['steps'],sort_keys=True,separators=(',',':')).encode()).hexdigest()==a['program_sha256'],'program digest')
    clock=next(r for r in ev if r.get('event')=='clock')
    need(cmd['valid_until_ns']==a['valid_until_ns']==clock['runtime_ns']+spec['cutoff_ms']*1_000_000,'fixed authority')
    downs=[r for r in ev if r.get('event')=='input_admission']
    need([r['key'] for r in downs]==expected,'physical admission keys')
    need(all(r['intent_token']==a['intent_token'] and r['valid_until_ns']==a['valid_until_ns'] and r['admitted_ns']<=r['input_ack_ns']<=a['valid_until_ns'] for r in downs),'admission lineage')
    cause=t['interruption'];need(cause['intent_token']==a['intent_token'],'cause lineage');cause=cause['record']
    for r in [cause,t['release']]:need(r['verified'] is True and r['keys_down']==[] and r.get('buttons_down',[])==[],'empty release')
    need(cause['reason']=='expired' and cause['valid_until_ns']==a['valid_until_ns'],'expiry cause')
    need(a['valid_until_ns']<=cause['verified_ns']<=t['terminal_ns'],'release clock order')
    for name,h in load(rt/'sources.json').items():
        p=workspace/'source_runtime/research'/name
        if not p.exists():p=workspace/'runtime/research'/name
        need(digest(p)==h,'runtime source '+name)
    finals=[s for s in sp if s.get('direct_final_sample') is True]
    need(len(finals)==1 and finals[0]==sp[-1],'final scorer uniqueness')
    score=load(rt/'score.json');last=finals[0]['payload']
    for k in ['map_exit','episode_finished','player_dead','death_count','kill_count']:
        need(type(last[k]) is type(score[k]) and last[k]==score[k],'score '+k)
    need(sp[0]['payload']['kill_count']==0,'initial kill baseline')
    need(all(s['controller_visible'] is False for s in sp),'sample visibility')
    got_finish=False
    for r in ev:
        if r.get('event')=='command' and r['command'].get('op')=='finish':got_finish=True
        if not got_finish:need(not privileged(r),'privileged data before finish')
    stamp={s['payload']['sample_ns'] for s in sp}
    need(all(e['controller_visible'] is False and e['observed_ns'] in stamp for e in se),'event sample binding')
    useful=[e['observed_ns'] for e in se if e.get('useful') is True]
    before=any(x<=a['valid_until_ns'] for x in useful)
    published=load(case/'analysis.json')
    need(published['score']['kill_count']==score['kill_count'] and published['useful_observed_before_deadline']==before,'result replay')
    late=(cause['verified_ns']-a['valid_until_ns'])/1e6
    need(abs(late-published['deadline_to_empty_ms'])<1e-9,'timing replay')
    # This retained historical direct-final receipt flaw is counted, not silently repaired.
    bad_brackets=sum(not(s['sample_started_ns']<=s['payload']['sample_ns']<=s['sample_finished_ns']) for s in sp)
    typed={r['sequence']:r for r in ev if r.get('event')=='typed_observation'}
    observations=[r for r in ev if r.get('event')=='observation'];pixel_count=0
    for obs in observations:
        typ=typed[obs['sequence']]
        need(obs['capture_ns']==typ['capture_ns'] and obs['frame_rgb_sha256']==typ['frame_rgb_sha256'],'typed exact association')
        need(obs['exact'] is True and typ['grants_input_authority'] is False,'observation contract')
        if pixels:
            from PIL import Image
            with Image.open(rt/Path(obs['image']).name) as im:
                need(hashlib.sha256(im.convert('RGB').tobytes()).hexdigest()==obs['frame_rgb_sha256'],'pixel digest')
            pixel_count+=1
    trace=rows(rt/'evaluator-trace.jsonl');refresh=[];pre_tics=set()
    if trace:
        prov=load(rt/'evaluator-provenance.json')
        for n,h in prov['source_sha256'].items():need(digest(workspace/LANE/n)==h,'evaluator source')
        for x in trace:
            need(x['mode']==spec['mode'] and x['thread_id']==prov['owner_thread_id'],'traced mode/owner')
            need(x['started_ns']<=x['refresh_started_ns']<=x['refresh_finished_ns']<=x['finished_ns'],'refresh bracket')
            need(x['started_ns']<=x['sample']['sample_ns']<=x['finished_ns'],'sample acquisition bracket')
            need(x['refresh_called']==(spec['mode']=='refresh1'),'refresh mode')
            if x['sample']['sample_ns']<=a['valid_until_ns']:pre_tics.add(x['episode_tic_after'])
            if x['refresh_called']:refresh.append((x['refresh_finished_ns']-x['refresh_started_ns'])/1e6)
    hp=[r['signals']['health']['value'] for r in typed.values() if r['signals']['health'].get('status')=='observed']
    ammo=[r['signals']['ammo']['value'] for r in typed.values() if r['signals']['ammo'].get('status')=='observed']
    return {'id':spec['id'],'stage':allocation,'state':spec['state'],'policy':spec['policy'],'mode':spec.get('mode'),
      'kill_count':score['kill_count'],'death_count':score['death_count'],'map_exit':score['map_exit'],
      'health_start':hp[0],'health_end':hp[-1],'ammo_start':ammo[0],'ammo_end':ammo[-1],
      'deadline_to_empty_ms':late,'useful_before_deadline':before,
      'first_useful_after_first_admission_ms':(min(useful)-downs[0]['admitted_ns'])/1e6 if useful else None,
      'missed_periods':load(rt/'scorer-summary.json')['scheduler']['missed_sample_periods'],
      'historical_invalid_sample_brackets':bad_brackets,'image_checks':pixel_count,'trace_records':len(trace),
      'predeadline_unique_engine_tics':len(pre_tics) if trace else None,'refresh_duration_ms':refresh,
      'pass':True}

def audit(workspace,pixels=True):
    results=[]
    for name in ['plan_stage1.json','plan_stage2.json','plan_stage3.json']:
        plan=load(workspace/LANE/name)
        for n,h in plan['source_sha256'].items():need(digest(workspace/LANE/n)==h,'experiment source '+n)
        for spec in plan['cases']:
            fp=(workspace/'runtime/research/doom/fixtures/map01-threat-contact-v2/fixture.json' if spec['state']=='original' else workspace/'evidence/setup'/spec['state']/'save.json')
            need(digest(fp)==spec['fixture_sha256'],'fixture manifest')
            fm=load(fp)
            need(digest(fp.parent/fm['save_file'])==fm['save_sha256'],'fixture save')
            need(digest(fp.parent/fm['source_frame'])==fm['source_frame_sha256'],'fixture source frame')
            results.append(audit_case(workspace,spec,plan['allocation'],pixels))
    return {'schema':'independent-autoresearch-replay-v1','case_count':len(results),'cases':results,
      'pass':True,'image_checks':sum(r['image_checks'] for r in results),
      'historic_final_bracket_issues':sum(r['historical_invalid_sample_brackets'] for r in results),
      'trace_records_validated':sum(r['trace_records'] for r in results)}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('workspace',type=Path);ap.add_argument('--out',type=Path);ap.add_argument('--no-pixels',action='store_true');a=ap.parse_args()
    result=audit(a.workspace,not a.no_pixels)
    if a.out:a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='cases'},indent=2))
