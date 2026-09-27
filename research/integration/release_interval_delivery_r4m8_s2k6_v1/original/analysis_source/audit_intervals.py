"""Independent finite oracle. Reads saved rows; imports no estimator/runner."""
from __future__ import annotations
import json, sys
from pathlib import Path

def audit(rows):
    errors=[]; checks=0; coverage=[]; empty=0; original_empty=0
    bad_lo=0; bad_hi=0; hidden_witnesses=0
    def need(ok, label):
        nonlocal checks
        checks+=1
        if not ok: errors.append(label)
    if not isinstance(rows,list):
        return {'decision':'FAIL_INTERVAL_CHECK','errors':['rows_not_list'],'checks':1}
    for i,row in enumerate(rows):
        try:
            a,b,c,d=row['bounds_ns']; coverage.append((a,b,c,d))
            need(all(type(v) is int for v in (a,b,c,d)) and 10<=a<=b<=c<=d<=18,'bounds:'+str(i))
            if not all(type(v) is int for v in (a,b,c,d)) or not 10<=a<=b<=c<=d<=18:
                continue
            need(row['id']==i,'id:'+str(i)); need(row['deadline_ns']==d,'deadline:'+str(i))
            ctx={'case_id':f'finite-{i:03}','server_epoch':'analytical-not-a-display'}
            need(row['context']==ctx,'context:'+str(i))
            expected_samples=[]
            for j,(lo,hi,down) in enumerate([(0,1,False),(a,b,True),(c,d,False)]):
                bits=bytearray(32)
                if down: bits[8]=1
                expected_samples.append(dict(ctx,sequence=j,start_ns=lo,end_ns=hi,keycode=64,bitmap_hex=bits.hex()))
            need(row['samples']==expected_samples,'sample_binding:'+str(i))
            # Independent hidden-time enumeration rather than reusing a bound formula.
            possible=set()
            for down_snapshot in range(a,b+1):
                for up_snapshot in range(c,d+1):
                    for release in range(10,19):
                        if down_snapshot<release<=up_snapshot:
                            possible.add(release); hidden_witnesses+=1
            result=row['nonempty_guard']; old=row['original_local_estimator']
            for label,value in [('guard',result),('original',old)]:
                need(value['authority']=='none' and value['task_success'] is False,'authority_'+label+':'+str(i))
            # The historical construction prototype is recorded, not repaired in place.
            need(old['interval_ns']==[a,d] and old['status']=='WITHIN_BOUND','original_binding:'+str(i))
            need(old['last_down_sequence']==1 and old['first_up_sequence']==2,'original_indices:'+str(i))
            if possible:
                tight=[min(possible)-1,max(possible)]
                need(result['interval_ns']==tight and result['status']=='WITHIN_BOUND','tight_interval:'+str(i))
                lo,hi=result['interval_ns']
                need({t for t in range(10,19) if lo<t<=hi}==possible,'exact_coverage:'+str(i))
                need(result['last_down_sequence']==1 and result['first_up_sequence']==2,'guard_indices:'+str(i))
            else:
                empty+=1
                need(result['status']=='UNKNOWN' and result['interval_ns'] is None,'empty_not_unknown:'+str(i))
                if old['status']=='WITHIN_BOUND': original_empty+=1
            need(row['return_lower_comparator']==[b,d],'lower_comparator_binding:'+str(i))
            need(row['request_upper_comparator']==[a,c],'upper_comparator_binding:'+str(i))
            lower,upper=row['return_lower_comparator']
            if any(not lower<t<=upper for t in possible): bad_lo+=1
            lower,upper=row['request_upper_comparator']
            if any(not lower<t<=upper for t in possible): bad_hi+=1
        except (KeyError,TypeError,ValueError,IndexError) as e:
            errors.append('malformed:'+repr(e))
    expected=[(a,b,c,d) for a in range(10,19) for b in range(a,19) for c in range(b,19) for d in range(c,19)]
    need(coverage==expected and len(rows)==len(expected),'denominator_and_order')
    need(empty==9,'empty_inputs'); need(original_empty==9,'empty_control_exposed')
    need(bad_lo>0 and bad_hi>0,'narrowing_controls_exposed')
    return {'decision':'PASS_LOCAL_INTERVAL_CONTRACT' if not errors else 'FAIL_INTERVAL_CHECK',
      'rows':len(rows),'checks':checks,'errors':errors,'feasible_inputs':len(rows)-empty,
      'empty_inputs':empty,'original_local_estimator_empty_promotions':original_empty,
      'narrowed_lower_unsafe_inputs':bad_lo,'narrowed_upper_unsafe_inputs':bad_hi,
      'hidden_witness_triples':hidden_witnesses,'live_gui_trials':0}
if __name__=='__main__':
    result=audit(json.loads(Path(sys.argv[1]).read_text()))
    print(json.dumps(result,indent=2,sort_keys=True)); raise SystemExit(bool(result['errors']))
