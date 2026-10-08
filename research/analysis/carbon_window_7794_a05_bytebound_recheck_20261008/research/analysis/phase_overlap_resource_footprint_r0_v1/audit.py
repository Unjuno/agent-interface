import argparse, itertools, json, hashlib
from pathlib import Path
R=(0,1,2); INITIAL=((0,1,2),(2,0,1))
OPS=[]
for r in R: OPS.append(('R',r,-1,0))
for r in R: OPS += [('S',r,-1,0),('S',r,-1,1)]
for r in R: OPS.append(('I',r,-1,0))
for x in R:
  for y in R:
    if x!=y: OPS.append(('C',x,y,0))

def footprint(o):
 k,x,y,v=o
 if k=='R': return {x},set()
 if k=='S': return set(),{x}
 if k=='I': return {x},{x}
 if k=='C': return {x},{y}
 raise AssertionError

def clashes(a,b):
 ar,aw=footprint(a); br,bw=footprint(b)
 return bool((aw & (br|bw)) or (ar & bw))

def clashes_fp(a,b):
 ar,aw=a; br,bw=b
 return bool((aw & (br|bw)) or (ar & bw))

def combine(a,b):
 ar,aw=footprint(a); br,bw=footprint(b); return ar|br,aw|bw

def step(st,o):
 s=list(st); k,x,y,v=o
 if k=='R': z=s[x]
 elif k=='S': s[x]=v; z=s[x]
 elif k=='I': s[x]+=1; z=s[x]
 else: s[y]=s[x]+1; z=s[y]
 return tuple(s),z

def run(st,p,seq):
 obs={}; cur=tuple(st)
 for q in seq: cur,z=step(cur,p[q]); obs[q]=z
 return cur,tuple(sorted(obs.items()))

def seqs(order):
 f,s=order
 return (f+'I',f+'T',s+'I',s+'T'),((f+'I',s+'I',f+'T',s+'T'),(f+'I',s+'I',s+'T',f+'T'))

def audit(result):
 c={'program_vectors':0,'rows':0,'complete_overlap_admissions':0,'complete_overlap_schedule_checks':0,'complete_overlap_mismatches':0,'declared_conflict_serializations':0,'surface_only_mismatches':0,'omitted_dependency_admissions':0,'omitted_dependency_mismatches':0,'order_A_B_rows':0,'order_B_A_rows':0}
 for v in itertools.product(OPS,repeat=4):
  p={'AI':v[0],'AT':v[1],'BI':v[2],'BT':v[3]}; c['program_vectors']+=1
  for st in INITIAL:
   for order in (('A','B'),('B','A')):
    c['rows']+=1;c['order_'+order[0]+'_'+order[1]+'_rows']+=1
    f,s=order; serial,ovs=seqs(order); base=run(st,p,serial); bad=any(run(st,p,q)!=base for q in ovs)
    ft=footprint(p[f+'T']); sec=combine(p[s+'I'],p[s+'T']); safe=not clashes_fp(ft,sec)
    if safe:
     c['complete_overlap_admissions']+=1;c['complete_overlap_schedule_checks']+=2
     if bad:c['complete_overlap_mismatches']+=1
    else:
     c['declared_conflict_serializations']+=1
     if bad:c['surface_only_mismatches']+=1
     tr,tw=ft; sr,sw=sec; hidden=(tw&(sr|sw))|(tr&sw)
     if hidden and not clashes_fp((tr-hidden,tw-hidden),sec):
      c['omitted_dependency_admissions']+=1
      if bad:c['omitted_dependency_mismatches']+=1
 errs=[]
 if result['counts']!=c: errs.append('count_mismatch')
 if c['complete_overlap_mismatches']!=0: errs.append('complete_unsound')
 if not c['surface_only_mismatches']: errs.append('surface_discriminator_absent')
 if not c['omitted_dependency_mismatches']: errs.append('omission_discriminator_absent')
 if result.get('unknown_parallel_admissions')!=0: errs.append('unknown_fail_open')
 if result.get('formal_invocations')!=1 or result.get('reruns')!=0: errs.append('invocation_discipline')
 if result.get('decision')!='PASS_PHASE_OVERLAP_RESOURCE_FOOTPRINT_SERIALIZABILITY_SCOPED': errs.append('decision')
 controls={
  'rw_conflict': clashes(('I',0,-1,0),('R',0,-1,0)),
  'disjoint_safe': not clashes(('I',0,-1,0),('R',1,-1,0)),
  'unknown_serial': result.get('unknown_parallel_admissions')==0,
  'surface_discriminator': c['surface_only_mismatches']>0,
  'omission_discriminator': c['omitted_dependency_mismatches']>0,
 }
 if not all(controls.values()): errs.append('control_failure')
 return {'pass':not errs,'errors':errs,'recomputed_counts':c,'controls':controls}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--result',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
 r=json.loads(Path(a.result).read_text()); q=audit(r); q['result_digest']=r['digest']; q['audit_digest']=hashlib.sha256(json.dumps(q,sort_keys=True,separators=(',',':')).encode()).hexdigest();Path(a.output).write_text(json.dumps(q,indent=2,sort_keys=True)+'\n');print(json.dumps(q,indent=2,sort_keys=True))
if __name__=='__main__':main()
