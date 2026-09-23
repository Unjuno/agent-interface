from itertools import product
import argparse,hashlib,json
from pathlib import Path
KINDS=('LOCAL_COMPLETE','OPAQUE_SEMANTIC')

def candidate(path_current,kind,local_true,fp_same,approval_valid,old_epoch):
    if path_current:return ('KEEP_ACTION_SAFE',None)
    if kind=='LOCAL_COMPLETE':
        return ('RECOMMIT_LOCAL',old_epoch+1) if local_true else ('REJECT',None)
    if kind=='OPAQUE_SEMANTIC':
        return ('RECOMMIT_REUSED_APPROVAL',old_epoch+1) if fp_same and approval_valid else ('YIELD_FOR_APPROVAL',None)
    raise ValueError(kind)

def oracle(path_current,kind,local_true,fp_same,approval_valid,old_epoch):
    if path_current:
        return ('KEEP_ACTION_SAFE',None)
    if kind=='LOCAL_COMPLETE':
        if local_true:return ('RECOMMIT_LOCAL',old_epoch+1)
        return ('REJECT',None)
    if fp_same:
        if approval_valid:return ('RECOMMIT_REUSED_APPROVAL',old_epoch+1)
        return ('YIELD_FOR_APPROVAL',None)
    return ('YIELD_FOR_APPROVAL',None)

def run(construction=False):
    epochs=(1,) if construction else (1,2)
    st={'rows':0,'mismatch':0,'current_path_keep':0,'stale_path_keep':0,'local_recommit':0,'local_reject':0,'opaque_recommit':0,'opaque_yield':0,'bad_recommit_epoch':0,'sticky_unsafe':0,'current_truth_auto_unsafe':0,'always_yield_false_yield':0,'reuse_old_epoch_violations':0}
    for pc,k,lt,fs,av,e in product((False,True),KINDS,(False,True),(False,True),(False,True),epochs):
        got=candidate(pc,k,lt,fs,av,e);exp=oracle(pc,k,lt,fs,av,e);st['rows']+=1;st['mismatch']+=int(got!=exp)
        disp,ne=got
        if pc:st['current_path_keep']+=int(disp=='KEEP_ACTION_SAFE')
        else:st['stale_path_keep']+=int(disp=='KEEP_ACTION_SAFE')
        if not pc and k=='LOCAL_COMPLETE':
            st['local_recommit']+=int(disp=='RECOMMIT_LOCAL');st['local_reject']+=int(disp=='REJECT')
        if not pc and k=='OPAQUE_SEMANTIC':
            st['opaque_recommit']+=int(disp=='RECOMMIT_REUSED_APPROVAL');st['opaque_yield']+=int(disp=='YIELD_FOR_APPROVAL')
        if disp.startswith('RECOMMIT'):
            st['bad_recommit_epoch']+=int(ne is None or ne<=e)
            st['reuse_old_epoch_violations']+=1
        if not pc:st['sticky_unsafe']+=1
        if not pc and k=='OPAQUE_SEMANTIC' and (not fs) and lt:st['current_truth_auto_unsafe']+=1
        if not pc and disp in ('RECOMMIT_LOCAL','RECOMMIT_REUSED_APPROVAL'):st['always_yield_false_yield']+=1
    directed={
      'keep_current':candidate(True,'OPAQUE_SEMANTIC',False,False,False,1)==('KEEP_ACTION_SAFE',None),
      'local_true_recommit':candidate(False,'LOCAL_COMPLETE',True,False,False,1)==('RECOMMIT_LOCAL',2),
      'local_false_reject':candidate(False,'LOCAL_COMPLETE',False,True,True,1)==('REJECT',None),
      'opaque_exact_recommit':candidate(False,'OPAQUE_SEMANTIC',False,True,True,1)==('RECOMMIT_REUSED_APPROVAL',2),
      'opaque_changed_yield':candidate(False,'OPAQUE_SEMANTIC',True,False,True,1)==('YIELD_FOR_APPROVAL',None),
      'opaque_expired_yield':candidate(False,'OPAQUE_SEMANTIC',True,True,False,1)==('YIELD_FOR_APPROVAL',None),
    }
    corrupt={'sticky_detected':st['sticky_unsafe']>0,'semantic_laundering_detected':st['current_truth_auto_unsafe']>0,'always_yield_overconservative':st['always_yield_false_yield']>0,'old_epoch_reuse_detected':st['reuse_old_epoch_violations']>0}
    good=(st['mismatch']==0 and st['current_path_keep']>0 and st['stale_path_keep']==0 and st['local_recommit']>0 and st['local_reject']>0 and st['opaque_recommit']>0 and st['opaque_yield']>0 and st['bad_recommit_epoch']==0 and all(directed.values()) and all(corrupt.values()))
    return st,directed,corrupt,good

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--construction',action='store_true');ap.add_argument('--output',required=True);a=ap.parse_args();o=Path(a.output);assert not o.exists();st,dc,cor,good=run(a.construction)
    r={'construction':a.construction,'stats':st,'directed':dc,'corruptions':cor,'formal_invocations':0 if a.construction else 1,'reruns':0,'replacements':0,'tuning':0,'decision':('CONSTRUCTION_PASS' if a.construction and good else ('PASS_BELIEF_REPAIR_DECISION_LATTICE_SCOPED' if good else 'FAIL_INTEGRITY'))}
    raw=json.dumps(r,sort_keys=True,separators=(',',':')).encode();r['digest']=hashlib.sha256(raw).hexdigest();o.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__':main()
