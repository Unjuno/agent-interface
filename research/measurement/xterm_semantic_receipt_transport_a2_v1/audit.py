#!/opt/pyvenv/bin/python3
import argparse,json,pathlib

def audit(obj):
    errs=[]; rows=obj.get('rows',[])
    if len(rows)!=40: errs.append('row_count')
    ids=[r.get('case_id') for r in rows]
    expected=[f'p{i:03d}-{tr}' for i in range(20) for tr in ('file','dgram')]
    if set(ids)!=set(expected) or len(set(ids))!=40: errs.append('case_identity')
    for r in rows:
        if not (r.get('focus_match') and r.get('press_before_frontier') and r.get('input_byte_hex')=='78' and r.get('receipt_valid') and not r.get('terminal_key_down') and r.get('xterm_rc')==0): errs.append('integrity:'+str(r.get('case_id')))
    s=obj.get('stats',{}); f=s.get('file',{}); d=s.get('dgram',{})
    if f.get('n')!=20 or d.get('n')!=20: errs.append('arm_count')
    if errs: decision='FAIL_RECEIPT_TRANSPORT_INTEGRITY_A2'
    else:
        fast=(d['transport_p95_ms']<1 and d['drain_p95_ms']<6 and d['drain_max_ms']<8)
        discr=obj['matched_file_minus_dgram_median_ms']>=0.75
        decision='PASS_XTERM_SEMANTIC_RECEIPT_TRANSPORT_TAIL_LOCALIZED_A2' if fast and discr else 'HOLD_TRANSPORT_NOT_DOMINANT_A2'
    return {'audit_pass':not errs,'errors':errs,'decision':decision}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    obj=json.loads(pathlib.Path(a.input).read_text()); res=audit(obj); pathlib.Path(a.out).write_text(json.dumps(res,indent=2,sort_keys=True)); print(json.dumps(res,indent=2))
if __name__=='__main__': main()
