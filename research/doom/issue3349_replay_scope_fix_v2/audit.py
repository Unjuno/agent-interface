import json,sys
from pathlib import Path

def main(raw_path,out_path):
    raw=json.loads(Path(raw_path).read_text())
    errors=[]; checks={}
    by={r['name']:r for r in raw['cases']}
    checks['count_9']=raw.get('case_count')==9 and len(raw.get('cases',[]))==9
    for n in ('matching_accept','unrelated_then_match','malformed_then_match'):
        r=by[n]; checks['corrected_'+n]=r['corrected']['status']=='RETURN' and r['corrected']['id']=='fallback'
    for n in ('stale_accept_then_match','stale_reject_then_match'):
        r=by[n]
        checks['old_defect_'+n]=r['old']['status']=='ERROR' and len(r['old']['remaining'])==1 and r['old']['remaining'][0].get('id')=='fallback'
        checks['corrected_'+n]=r['corrected']['status']=='RETURN' and r['corrected']['id']=='fallback' and r['corrected']['remaining']==[]
    r=by['matching_reject']; checks['matching_reject_fail_closed']=r['corrected']['status']=='ERROR' and r['corrected']['error_type']=='SessionError'
    checks['terminal_exact']=by['terminal_exact']['corrected']=={'status':'RETURN','id':'fallback'}
    checks['terminal_duplicate']=by['terminal_duplicate']['corrected']['status']=='ERROR' and by['terminal_duplicate']['corrected']['error_type']=='SessionError'
    checks['terminal_wrong_id']=by['terminal_wrong_id']['corrected']['status']=='ERROR' and by['terminal_wrong_id']['corrected']['error_type']=='TimeoutError'
    if not all(checks.values()): errors=[k for k,v in checks.items() if not v]
    decision='PASS_REPLAY_IDENTITY_CORRECTION_SCOPED' if not errors else 'FAIL_REPLAY_IDENTITY_CORRECTION'
    out={'schema':'issue3349-replay-identity-v2-audit','decision':decision,'checks':checks,'errors':errors,'old_stale_failures':sum(1 for n in ('stale_accept_then_match','stale_reject_then_match') if by[n]['old']['status']=='ERROR'),'corrected_stale_failures':sum(1 for n in ('stale_accept_then_match','stale_reject_then_match') if by[n]['corrected']['status']!='RETURN')}
    Path(out_path).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True))
    return 0 if not errors else 1
if __name__=='__main__': raise SystemExit(main(sys.argv[1],sys.argv[2]))
