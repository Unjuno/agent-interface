import json,sys
from pathlib import Path
ARMS=('forward','use','left','right','noop')
DWELLS=(4,16)
REQUIRED=('case_id','arm','dwell_tics','emitted_vector','declared_button','ready','pre','post','screen_hash_before','screen_hash_after','process_identity','cleanup_ok')

def audit(rows):
    expected={(a,d) for a in ARMS for d in DWELLS}
    seen={(r.get('arm'),r.get('dwell_tics')) for r in rows}
    issues=[]
    if len(rows)!=10: issues.append('ROW_COUNT')
    if seen!=expected: issues.append('CASE_SET')
    for r in rows:
        missing=[k for k in REQUIRED if k not in r]
        if missing: issues.append('MISSING_FIELDS')
        if not isinstance(r.get('emitted_vector'), list): issues.append('VECTOR_TYPE')
        if r.get('declared_button') != r.get('arm'): issues.append('BUTTON_MAPPING')
        if r.get('ready') is not True: issues.append('NOT_READY')
        if not r.get('process_identity'): issues.append('PROCESS_IDENTITY')
        if r.get('cleanup_ok') is not True: issues.append('CLEANUP')
    return {'schema':'action-contract-evidence-audit-v1','passed':not issues,'issues':sorted(set(issues)),'rows':len(rows)}

def main():
    if len(sys.argv)!=3: return 2
    rows=[json.loads(x) for x in Path(sys.argv[1]).read_text().splitlines() if x.strip()]
    result=audit(rows)
    Path(sys.argv[2]).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True))
    return 0 if result['passed'] else 1

if __name__=='__main__': raise SystemExit(main())
