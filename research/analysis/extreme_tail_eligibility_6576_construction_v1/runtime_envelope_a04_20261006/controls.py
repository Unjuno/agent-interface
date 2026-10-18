from __future__ import annotations
import copy, json, tempfile
from pathlib import Path
from audit import audit
def write(rows,result,root):
    raw=Path(root)/'RAW.jsonl'; res=Path(root)/'RESULT.json'
    raw.write_text('\n'.join(json.dumps(r,separators=(',',':'),allow_nan=False) for r in rows)+'\n',encoding='utf-8')
    res.write_text(json.dumps(result),encoding='utf-8'); return raw,res
def main():
    rows=[json.loads(x) for x in Path('formal/RAW.jsonl').read_text().splitlines()]; result=json.loads(Path('formal/RESULT.json').read_text())
    muts=[]
    def add(name,fn):
        rr=copy.deepcopy(rows); rs=copy.deepcopy(result); fn(rr,rs); muts.append((name,rr,rs))
    add('drop_row',lambda r,s:r.pop())
    add('duplicate_row',lambda r,s:r.append(copy.deepcopy(r[0])))
    add('bool_seed',lambda r,s:r[0].__setitem__('seed',True))
    add('sample_value',lambda r,s:r[35]['samples'].__setitem__(520,r[35]['samples'][520]+1.0))
    add('sample_alarm',lambda r,s:r[40].__setitem__('sample_alarm_index',999))
    add('mode_label',lambda r,s:r[30]['modes'].__setitem__(511,'rare_heavy'))
    add('mode_alarm',lambda r,s:r[30].__setitem__('declared_mode_invalidation_index',513))
    add('authority',lambda r,s:r[0].__setitem__('authority',True))
    add('result_decision',lambda r,s:s.__setitem__('decision','PASS_RUNTIME_ENVELOPE_INVALIDATION_A04_SCOPED' if s['decision']!='PASS_RUNTIME_ENVELOPE_INVALIDATION_A04_SCOPED' else 'FAIL_OR_HOLD_A04_GATE'))
    add('counterexample_count',lambda r,s:s.__setitem__('counterexample_count',s['counterexample_count']+1))
    rejected=[]
    for name,rr,rs in muts:
        with tempfile.TemporaryDirectory() as td:
            raw,res=write(rr,rs,td); out=audit(raw,res); rejected.append({"name":name,"rejected":bool(out['errors']),"errors":out['errors'][:4]})
    summary={"controls":len(rejected),"rejected":sum(x['rejected'] for x in rejected),"rows":rejected}
    Path('CONTROLS.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,sort_keys=True))
    raise SystemExit(0 if summary['rejected']==summary['controls'] else 1)
if __name__=='__main__': main()
