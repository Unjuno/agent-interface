from __future__ import annotations
import time

PREDICATES=("TARGET_CORRECT","FORM_COMPLETE","MODAL_BLOCKING","RECOVERY_NEEDED","INTENT_SUBMIT","ENVELOPE_VALID")
FEATURES={
 "TARGET_CORRECT":("target_pos","target_neg"),
 "FORM_COMPLETE":("form_pos","form_neg"),
 "MODAL_BLOCKING":("modal_pos","modal_neg"),
 "RECOVERY_NEEDED":("recovery_pos","recovery_neg"),
 "INTENT_SUBMIT":("intent_pos","intent_neg"),
 "ENVELOPE_VALID":("envelope_pos","envelope_neg"),
}

def classify_pair(pos:int,neg:int)->str:
    score=int(pos)-int(neg)
    return "TRUE" if score>0 else ("FALSE" if score<0 else "UNKNOWN")

def predicate_forward(features:dict)->dict:
    return {p:classify_pair(features[a],features[b]) for p,(a,b) in FEATURES.items()}

def graph(pred:dict):
    reads=[]
    def read(p): reads.append(p); return pred[p]
    # Every uncertainty yields before executable dispositions.
    if any(pred[p]=="UNKNOWN" for p in PREDICATES): return "YIELD_UNKNOWN",reads
    if read("ENVELOPE_VALID")=="FALSE": return "YIELD_OUT_OF_ENVELOPE",reads
    if read("MODAL_BLOCKING")=="TRUE": return "YIELD_MODAL",reads
    if read("TARGET_CORRECT")=="FALSE": return "YIELD_TARGET",reads
    if read("FORM_COMPLETE")=="FALSE": return "CONTINUE_FILL",reads
    if read("RECOVERY_NEEDED")=="TRUE": return "RECOVER",reads
    # Submit node deliberately reuses target correctness after the earlier target gate.
    if read("TARGET_CORRECT")!="TRUE": return "YIELD_TARGET",reads
    if read("INTENT_SUBMIT")!="TRUE": return "YIELD_INTENT",reads
    return "SUBMIT_READY",reads

def direct_forward(features:dict)->str:
    # Same frozen linear semantic family, but the disposition is returned directly.
    pred=predicate_forward(features)
    return graph(pred)[0]

def timed_forward(kind:str,features:dict):
    t0=time.perf_counter_ns()
    if kind=="direct": out=direct_forward(features)
    elif kind=="predicates": out=predicate_forward(features)
    else: raise ValueError(kind)
    t1=time.perf_counter_ns()
    return out,t1-t0
