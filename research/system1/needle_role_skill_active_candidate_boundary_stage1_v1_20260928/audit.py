"""Independent raw-only audit of the Stage-1 reader/writer schedule."""
import base64,hashlib,json,sys
from pathlib import Path

SRC=Path('/src')
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def h(b):return hashlib.sha256(b).hexdigest()
def unique(pairs):
 d={}
 for k,v in pairs:
  if k in d:raise ValueError('duplicate_key')
  d[k]=v
 return d
def package_ok(raw,generation):
 try:
  p=json.loads(raw,object_pairs_hook=unique);q=dict(p);d=q.pop('payload_sha256')
  return p['schema']=='unjuno.role-skill.numeric-json.v1' and p['generation']==generation and p['graph']['scope']=='synthetic-fixture-v1' and d==h(canon(q))
 except Exception:return False
def main():
 rawpath=Path(sys.argv[1] if len(sys.argv)>1 else '/raw/raw.json')
 outpath=Path(sys.argv[2] if len(sys.argv)>2 else '/audit/audit.json')
 raw=json.loads(rawpath.read_text(encoding='utf-8'),object_pairs_hook=unique)
 old=(SRC/'skill.json').read_bytes(); prev=json.loads((SRC/'predecessor_raw.json').read_text(encoding='utf-8'),object_pairs_hook=unique)
 candidate=base64.b64decode(prev['events'][0]['candidate_b64'],validate=True)
 g0=json.loads(old,object_pairs_hook=unique)['generation'];g1=g0+1
 errors=[];expected=[('PUBLISH_AT_VALIDATION_START',True),('PUBLISH_AFTER_VALIDATION',False)]
 if raw.get('schema')!='issue4986-stage1-raw-v1' or raw.get('allocation')!='needle-role-skill-active-candidate-boundary-stage1-v1-20260928-01':errors.append('raw_identity')
 if h(old)!=raw.get('source_sha256') or h(old)!=prev.get('source_sha256'):errors.append('source_identity')
 if h(candidate)!=raw.get('candidate_sha256') or h(candidate)!=prev['events'][0].get('candidate_sha256'):errors.append('candidate_identity')
 if not package_ok(old,g0) or not package_ok(candidate,g1):errors.append('package_gate')
 if raw.get('source_generation')!=g0 or raw.get('candidate_generation')!=g1:errors.append('generation_gate')
 arms=raw.get('arms',[])
 if [(a.get('arm'),a.get('unsafe_diagnostic')) for a in arms]!=expected:errors.append('arm_order')
 derived={}
 for armname,unsafe in expected:
  arm=next((a for a in arms if a.get('arm')==armname),{})
  rows=arm.get('rows',[]);waves=arm.get('waves',[])
  if len(rows)!=64 or len(waves)!=8:errors.append(armname+':cardinality')
  if arm.get('prevalidation_candidate_published') is not unsafe:errors.append(armname+':treatment')
  if arm.get('validation_delay_ms_per_wave')!=10 or arm.get('validation_elapsed_ns',0)<40_000_000:errors.append(armname+':delay')
  if arm.get('receipt_sha256')!=h(candidate) or arm.get('final_generation')!=g1:errors.append(armname+':finalization')
  if [(w.get('wave'),w.get('queries'),w.get('barrier_parties')) for w in waves]!=[(i,8,9) for i in range(8)]:errors.append(armname+':wave_schedule')
  bywave={i:[] for i in range(8)}
  for r in rows:
   w=r.get('wave');qid=r.get('query_id')
   if w not in bywave:errors.append(armname+':unknown_wave');continue
   bywave[w].append(r)
   if r.get('mode')!='shadow-only' or r.get('dispatch_count')!=0:errors.append(armname+':not_shadow')
   if not r.get('schema_digest_valid'):errors.append(armname+':incomplete_or_invalid_package')
   if r.get('package_sha256') not in (h(old),h(candidate)):errors.append(armname+':unknown_package_digest')
   want_gen=g0 if r.get('package_sha256')==h(old) else g1
   if r.get('generation')!=want_gen:errors.append(armname+':generation_digest_disagree')
   pre=w<4
   if r.get('candidate_validated_at_read') is not (not pre):errors.append(armname+':validation_state')
   if pre:
    if r.get('receipt_at_read') is not None:errors.append(armname+':early_receipt')
    if unsafe and r.get('package_sha256')!=h(candidate):errors.append(armname+':diagnostic_not_exposed')
    if not unsafe and r.get('package_sha256')!=h(old):errors.append(armname+':candidate_visible_before_validation')
   else:
    if r.get('candidate_validated_at_read') is not True or r.get('receipt_at_read')!='audit:'+h(candidate):errors.append(armname+':receipt_not_ready')
    if w>4 and r.get('package_sha256')!=h(candidate):errors.append(armname+':post_publish_old_generation')
  for w,group in bywave.items():
   if len(group)!=8 or sorted(r.get('query_id') for r in group)!=list(range(w*8,w*8+8)):errors.append(armname+f':query_accounting_{w}')
  derived[armname]={'queries':len(rows),'prevalidation_candidate_reads':sum(r.get('wave',9)<4 and r.get('package_sha256')==h(candidate) and not r.get('candidate_validated_at_read') for r in rows),'postvalidation_reads':sum(r.get('wave',-1)>=4 for r in rows),'dispatches':sum(r.get('dispatch_count',0) for r in rows)}
 if len(arms)!=2 or sum(len(a.get('rows',[])) for a in arms)!=128:errors.append('total_queries')
 if derived.get('PUBLISH_AT_VALIDATION_START',{}).get('prevalidation_candidate_reads')!=32:errors.append('diagnostic_discriminator')
 if derived.get('PUBLISH_AFTER_VALIDATION',{}).get('prevalidation_candidate_reads')!=0:errors.append('candidate_gate_failure')
 verdict='PASS_ATOMIC_SKILL_PUBLICATION_SCOPED' if not errors else 'FAIL_OR_STOP_STAGE1_AUDIT'
 report={'schema':'issue4986-stage1-audit-v1','verdict':verdict,'rows_reconstructed':sum(len(a.get('rows',[])) for a in arms),'derived':derived,'errors':errors,'source_sha256':h(old),'candidate_sha256':h(candidate),'raw_sha256':h(rawpath.read_bytes())}
 outpath.write_bytes(canon(report)+b'\n');print(json.dumps(report,sort_keys=True));sys.exit(0 if not errors else 2)
if __name__=='__main__':main()
