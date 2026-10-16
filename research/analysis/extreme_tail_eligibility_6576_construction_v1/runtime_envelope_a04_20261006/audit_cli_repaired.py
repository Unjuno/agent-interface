from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
N=1024; SHIFT=512; WINDOW=64; ALARM_K=6; HORIZON=16; P99=-math.log(0.01); CUTOFF=8.0
CONDS=("stationary","declared_shift","undeclared_shift")
SEEDS=set(range(65764101,65764131))
def sample_alarm(xs):
    flags=[x>P99 for x in xs]
    for end in range(WINDOW-1,len(xs)):
        if sum(flags[end-WINDOW+1:end+1])>=ALARM_K: return end
    return None
def audit(raw_path,result_path):
    errors=[]; rows=[]
    for lineno,line in enumerate(Path(raw_path).read_text(encoding='utf-8').splitlines(),1):
        try:r=json.loads(line)
        except Exception as e: errors.append(f"line{lineno}:json:{type(e).__name__}"); continue
        rows.append(r)
    seen=set()
    for i,r in enumerate(rows):
        tag=f"row{i}"
        if type(r.get('seed')) is not int or r.get('seed') not in SEEDS: errors.append(tag+':seed')
        if r.get('condition') not in CONDS: errors.append(tag+':condition'); continue
        key=(r.get('condition'),r.get('seed'))
        if key in seen: errors.append(tag+':duplicate')
        seen.add(key)
        xs=r.get('samples'); modes=r.get('modes')
        if not isinstance(xs,list) or len(xs)!=N or not all(type(x) in (int,float) and not isinstance(x,bool) and math.isfinite(x) and x>=0 for x in xs): errors.append(tag+':samples'); continue
        if not isinstance(modes,list) or len(modes)!=N or not all(isinstance(m,str) for m in modes): errors.append(tag+':modes'); continue
        expected_modes=['reference']*N
        if r['condition']=='declared_shift': expected_modes[SHIFT:]=['rare_heavy']*(N-SHIFT)
        if modes!=expected_modes: errors.append(tag+':mode_schedule')
        digest=hashlib.sha256(json.dumps(xs,separators=(',',':'),allow_nan=False).encode()).hexdigest()
        if r.get('sample_sha256')!=digest: errors.append(tag+':sample_sha')
        ai=sample_alarm(xs)
        if r.get('sample_alarm_index')!=ai: errors.append(tag+':sample_alarm')
        mi=next((j for j,m in enumerate(modes) if m!='reference'),None)
        if r.get('declared_mode_invalidation_index')!=mi: errors.append(tag+':mode_alarm')
        fi=next((j for j in range(SHIFT,SHIFT+HORIZON) if xs[j]>P99),None)
        if r.get('first_extreme_in_horizon')!=fi: errors.append(tag+':first_extreme')
        ce=sum(x>CUTOFF for x in xs[SHIFT:SHIFT+HORIZON])
        if r.get('cutoff_exceedances_in_horizon')!=ce: errors.append(tag+':cutoff_count')
        if r.get('authority') is not False or r.get('task_success') is not None: errors.append(tag+':authority')
    expected={(c,s) for c in CONDS for s in SEEDS}
    if seen!=expected: errors.append('denominator')
    result=json.loads(Path(result_path).read_text(encoding='utf-8'))
    st=[r for r in rows if r.get('condition')=='stationary']; de=[r for r in rows if r.get('condition')=='declared_shift']; un=[r for r in rows if r.get('condition')=='undeclared_shift']
    false=sum(r.get('sample_alarm_index') is not None for r in st)
    exact=len(de)==30 and all(r.get('declared_mode_invalidation_index')==SHIFT for r in de)
    noinvent=len(st)==30 and len(un)==30 and all(r.get('declared_mode_invalidation_index') is None for r in st+un)
    cex=[r for r in de if r.get('sample_alarm_index') is not None and r['sample_alarm_index']-SHIFT>HORIZON and r.get('first_extreme_in_horizon') is not None]
    expected_dec='PASS_RUNTIME_ENVELOPE_INVALIDATION_A04_SCOPED' if not errors and false<=1 and exact and noinvent and cex else 'FAIL_OR_HOLD_A04_GATE'
    if result.get('decision')!=expected_dec: errors.append('result:decision')
    if result.get('stationary_sample_false_alarms')!=false: errors.append('result:false_alarm')
    if result.get('counterexample_count')!=len(cex): errors.append('result:counterexamples')
    if result.get('authority') is not False or result.get('task_success') is not None: errors.append('result:authority')
    return {"checks":len(rows)*10+5,"errors":errors,"decision":expected_dec,"rows":len(rows),"counterexample_count":len(cex),"stationary_false_alarms":false}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('raw'); ap.add_argument('result'); ap.add_argument('--out'); a=ap.parse_args()
    x=audit(a.raw,a.result); s=json.dumps(x,indent=2,sort_keys=True)+'\n'; print(s,end='')
    if a.out: Path(a.out).write_text(s,encoding='utf-8')
    raise SystemExit(0 if not x['errors'] else 1)
if __name__=='__main__': main()
