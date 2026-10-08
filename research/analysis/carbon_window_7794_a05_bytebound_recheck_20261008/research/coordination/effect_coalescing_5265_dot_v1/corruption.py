"""Audit copied outputs only; never reruns model or changes first output."""
import copy,hashlib,json,tempfile
from pathlib import Path
from audit import audit

root=Path(__file__).resolve().parent
original=root/'construction/matrix-c1'
rows=[json.loads(l) for l in (original/'RAW.jsonl').read_text().splitlines()]
result=json.loads((original/'RESULT.json').read_text())
controls=[]

def run(name,change):
    rr,summary=copy.deepcopy(rows),copy.deepcopy(result)
    change(rr,summary)
    with tempfile.TemporaryDirectory(prefix='corruption-',dir=root/'construction') as tmp:
        d=Path(tmp);raw=''.join(json.dumps(r,sort_keys=True)+'\n' for r in rr);(d/'RAW.jsonl').write_text(raw)
        # Recompute transport digest: scorer, not a checksum-only detector, must reject.
        summary['raw_sha256']=hashlib.sha256(raw.encode()).hexdigest();(d/'RESULT.json').write_text(json.dumps(summary))
        checked=audit(d);controls.append(dict(control=name,rejected=bool(checked['errors']),errors=checked['errors']))

def selected(rr): return next(r for r in rr if r['arm']=='SEMANTIC' and r['case_id']=='same_state_two_independent--0')
run('duplicate_effect',lambda rr,s:selected(rr)['outcome']['decisions'][1].update(effect=1,status='EXECUTED'))
run('false_suppression',lambda rr,s:selected(rr)['outcome']['decisions'][0].update(effect=0,status='COALESCED'))
run('bad_merge_target',lambda rr,s:selected(rr)['outcome']['decisions'][1].update(coalesced_to=99))
run('authority_creation',lambda rr,s:selected(rr)['outcome'].update(authority_created=1))
run('missing_row',lambda rr,s:rr.pop())
run('false_promotion',lambda rr,s:s.update(overall_disposition='PASS_PRODUCT'))
output=dict(audit='PASS' if all(c['rejected'] for c in controls) else 'FAIL',controls=controls,allocation='read_only_copied_result_checks',formal_invocations=0)
print(json.dumps(output,indent=2,sort_keys=True))
raise SystemExit(output['audit']!='PASS')
