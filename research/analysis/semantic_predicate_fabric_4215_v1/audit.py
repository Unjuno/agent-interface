from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
PRED=("TARGET_CORRECT","FORM_COMPLETE","MODAL_BLOCKING","RECOVERY_NEEDED","INTENT_SUBMIT","ENVELOPE_VALID")
MAP={"TARGET_CORRECT":("target_pos","target_neg"),"FORM_COMPLETE":("form_pos","form_neg"),"MODAL_BLOCKING":("modal_pos","modal_neg"),"RECOVERY_NEEDED":("recovery_pos","recovery_neg"),"INTENT_SUBMIT":("intent_pos","intent_neg"),"ENVELOPE_VALID":("envelope_pos","envelope_neg")}
def lab(f,p):
 a,b=MAP[p]
 if (f[a],f[b])==(1,0):return "TRUE"
 if (f[a],f[b])==(0,1):return "FALSE"
 return "UNKNOWN"
def graph(p):
 if any(p[x]=="UNKNOWN" for x in PRED):return "YIELD_UNKNOWN"
 if p["ENVELOPE_VALID"]=="FALSE":return "YIELD_OUT_OF_ENVELOPE"
 if p["MODAL_BLOCKING"]=="TRUE":return "YIELD_MODAL"
 if p["TARGET_CORRECT"]=="FALSE":return "YIELD_TARGET"
 if p["FORM_COMPLETE"]=="FALSE":return "CONTINUE_FILL"
 if p["RECOVERY_NEEDED"]=="TRUE":return "RECOVER"
 if p["INTENT_SUBMIT"]!="TRUE":return "YIELD_INTENT"
 return "SUBMIT_READY"
def audit(root_path,formal_path):
 root=Path(root_path);obj=json.loads(Path(formal_path).read_text());errors=[];checks=0
 freeze=json.loads((root/'FREEZE.json').read_text())
 for n,d in freeze['sha256'].items():
  checks+=1
  if hashlib.sha256((root/n).read_bytes()).hexdigest()!=d:errors.append('source_hash:'+n)
 rows=obj.get('rows',[]);checks+=1
 if len(rows)!=20:errors.append('row_count')
 pred_ok=pred_total=unknown_tp=unknown_fp=unknown_fn=joint=graph_ok=direct_ok=0
 semantic_errors=0;reuse=0
 for i,r in enumerate(rows):
  f=r.get('features',{});truth={p:lab(f,p) for p in PRED};expected=graph(truth);cand=r.get('predicates',{})
  checks+=10
  if r.get('index')!=i:errors.append(f'{i}:index')
  if set(cand)!=set(PRED):errors.append(f'{i}:predicate_keys')
  row_joint=True
  for p in PRED:
   pred_total+=1
   if cand.get(p)==truth[p]:pred_ok+=1
   else: row_joint=False; semantic_errors+=1
   t=truth[p]=="UNKNOWN";c=cand.get(p)=="UNKNOWN"
   unknown_tp+=int(t and c);unknown_fp+=int((not t) and c);unknown_fn+=int(t and (not c))
  joint+=int(row_joint)
  graph_ok+=int(r.get('graph')==expected);direct_ok+=int(r.get('direct')==expected)
  if r.get('graph')!=expected:errors.append(f'{i}:graph')
  if r.get('direct')!=expected:errors.append(f'{i}:direct')
  if r.get('authority_granted') is not False:errors.append(f'{i}:authority')
  reads=r.get('graph_reads',[]); rr=sum(max(0,reads.count(p)-1) for p in PRED);reuse+=rr
  if r.get('reuse_reads')!=rr:errors.append(f'{i}:reuse')
  if any(truth[p]=='UNKNOWN' for p in PRED) and r.get('graph')!='YIELD_UNKNOWN':errors.append(f'{i}:unknown_collapse')
 checks+=10
 acc=pred_ok/pred_total if pred_total else 0
 precision=unknown_tp/(unknown_tp+unknown_fp) if unknown_tp+unknown_fp else 1.0
 recall=unknown_tp/(unknown_tp+unknown_fn) if unknown_tp+unknown_fn else 1.0
 if acc!=1.0:errors.append('predicate_accuracy')
 if precision!=1.0 or recall!=1.0:errors.append('unknown_metrics')
 if joint!=20:errors.append('joint')
 if graph_ok!=20 or direct_ok!=20 or graph_ok<direct_ok:errors.append('disposition_accuracy')
 if semantic_errors!=0:errors.append('semantic_errors')
 if obj.get('direct_calls')!=20 or obj.get('predicate_calls')!=20:errors.append('call_count')
 if reuse<1 or obj.get('reuse_reads')!=reuse:errors.append('no_compositional_reuse')
 if obj.get('formal_invocations')!=1 or any(obj.get(k)!=0 for k in ('reruns','replacements','exclusions','tuning')):errors.append('execution_discipline')
 decision='PASS_SEMANTIC_PREDICATE_FABRIC_SCOPED' if not errors else ('FAIL_UNKNOWN_COLLAPSE' if any('unknown_collapse' in x for x in errors) else ('FAIL_GRAPH_AMPLIFICATION' if graph_ok<direct_ok else 'FAIL_PREDICATE_FIDELITY'))
 return {"decision":decision,"errors":errors,"checks":checks,"case_count":len(rows),"predicate_total":pred_total,"predicate_accuracy":acc,"unknown_precision":precision,"unknown_recall":recall,"joint_correct":joint,"graph_correct":graph_ok,"direct_correct":direct_ok,"semantic_errors":semantic_errors,"reuse_reads":reuse,"formal_sha256":hashlib.sha256(Path(formal_path).read_bytes()).hexdigest()}
if __name__=='__main__':
 if len(sys.argv)!=3:raise SystemExit('usage: audit.py ROOT FORMAL')
 r=audit(sys.argv[1],sys.argv[2]);print(json.dumps(r,sort_keys=True,indent=2));raise SystemExit(bool(r['errors']))
