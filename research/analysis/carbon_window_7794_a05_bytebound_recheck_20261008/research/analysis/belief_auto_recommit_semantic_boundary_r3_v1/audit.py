import argparse,hashlib,json
from pathlib import Path
F=(0,1,2,3);FUNCS=tuple(range(16))
def bit(fn,x):return bool(fn>>x&1)
def proj(x):return x&1
def recompute():
 s={'local_rows':0,'local_mismatch':0,'local_auto_recommit':0,'local_reject':0,'always_yield_false_yields':0,'opaque_classes':0,'opaque_changed_classes':0,'opaque_ambiguous_changed_classes':0,'opaque_changed_auto_recommits':0,'opaque_yields':0,'opaque_exact_reuse':0,'projected_value_reuse_unsafe_function_rows':0,'projected_value_reuse_unsafe_classes':0}
 for fn in FUNCS:
  for old in F:
   if not bit(fn,old):continue
   for cur in F:
    d='AUTO_RECOMMIT' if bit(fn,cur) else 'REJECT';s['local_rows']+=1;s['local_auto_recommit']+=int(d=='AUTO_RECOMMIT');s['local_reject']+=int(d=='REJECT');s['always_yield_false_yields']+=int(d=='AUTO_RECOMMIT')
 for old in F:
  consistent=[fn for fn in FUNCS if bit(fn,old)]
  for cur in F:
   s['opaque_classes']+=1;vals={bit(fn,cur) for fn in consistent}
   if cur==old:s['opaque_exact_reuse']+=int(vals=={True})
   else:
    s['opaque_changed_classes']+=1;s['opaque_ambiguous_changed_classes']+=int(vals=={False,True});s['opaque_yields']+=1
    if proj(cur)==proj(old):
     u=sum(1 for fn in consistent if not bit(fn,cur))
     if u:s['projected_value_reuse_unsafe_classes']+=1;s['projected_value_reuse_unsafe_function_rows']+=u
 return s
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--result',required=True);ap.add_argument('--freeze',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();o=Path(a.output);assert not o.exists();R=json.loads(Path(a.result).read_text());Z=json.loads(Path(a.freeze).read_text());S=recompute();rs=R['stats']
 checks={'decision':R['decision']=='PASS_BELIEF_AUTO_RECOMMIT_SEMANTIC_BOUNDARY_SCOPED','stats':rs==S,'local_mismatch':rs['local_mismatch']==0,'local_auto':rs['local_auto_recommit']>0,'local_reject':rs['local_reject']>0,'ambiguity':rs['opaque_ambiguous_changed_classes']==rs['opaque_changed_classes'] and rs['opaque_changed_classes']>0,'opaque_auto_zero':rs['opaque_changed_auto_recommits']==0,'opaque_yield':rs['opaque_yields']>0,'exact_reuse':rs['opaque_exact_reuse']>0,'projection_unsafe':rs['projected_value_reuse_unsafe_function_rows']>0,'always_yield_over':rs['always_yield_false_yields']>0,'directed':all(R['directed'].values()),'corruptions':all(R['corruptions'].values()),'formal':R['formal_invocations']==1 and R['reruns']==0 and R['replacements']==0 and R['tuning']==0,'source_plan':h('PLAN.md')==Z['sha256']['PLAN.md'],'source_formal':h('formal.py')==Z['sha256']['formal.py'],'source_audit':h('audit.py')==Z['sha256']['audit.py']}
 out={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'audit_stats':S,'result_sha256':h(a.result),'freeze_sha256':h(a.freeze)};o.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True));raise SystemExit(0 if out['status']=='PASS' else 1)
if __name__=='__main__':main()
