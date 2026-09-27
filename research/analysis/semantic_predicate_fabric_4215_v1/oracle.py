from __future__ import annotations
PREDICATES=("TARGET_CORRECT","FORM_COMPLETE","MODAL_BLOCKING","RECOVERY_NEEDED","INTENT_SUBMIT","ENVELOPE_VALID")
MAP={
 "TARGET_CORRECT":("target_pos","target_neg"),"FORM_COMPLETE":("form_pos","form_neg"),
 "MODAL_BLOCKING":("modal_pos","modal_neg"),"RECOVERY_NEEDED":("recovery_pos","recovery_neg"),
 "INTENT_SUBMIT":("intent_pos","intent_neg"),"ENVELOPE_VALID":("envelope_pos","envelope_neg")}
def truth(f,p):
 a,b=MAP[p]; pair=(f[a],f[b])
 if pair==(1,0):return "TRUE"
 if pair==(0,1):return "FALSE"
 return "UNKNOWN"
def labels(f):return {p:truth(f,p) for p in PREDICATES}
def disposition(p):
 if any(p[k]=="UNKNOWN" for k in PREDICATES):return "YIELD_UNKNOWN"
 if p["ENVELOPE_VALID"]=="FALSE":return "YIELD_OUT_OF_ENVELOPE"
 if p["MODAL_BLOCKING"]=="TRUE":return "YIELD_MODAL"
 if p["TARGET_CORRECT"]=="FALSE":return "YIELD_TARGET"
 if p["FORM_COMPLETE"]=="FALSE":return "CONTINUE_FILL"
 if p["RECOVERY_NEEDED"]=="TRUE":return "RECOVER"
 if p["INTENT_SUBMIT"]!="TRUE":return "YIELD_INTENT"
 return "SUBMIT_READY"
