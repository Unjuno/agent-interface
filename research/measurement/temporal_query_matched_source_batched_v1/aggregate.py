import argparse,hashlib,json
from pathlib import Path
CLASSES=('RECENT_DENSE','LONG_BASELINE','EVENT_CENTERED','REVERSAL_BRACKET');TOTAL=220000;BATCHES=20;BS=11000
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--dir',required=True);ap.add_argument('--output',required=True);a=ap.parse_args(); out=Path(a.output);assert not out.exists()
 counts={k:{'n':0,'fixed':0,'query':0} for k in CLASSES};mm=0;leaks={k:0 for k in ('unknown_source','future','cross_scope','budget','authority')};ranges=[];digests=[]
 for b in range(BATCHES):
  p=Path(a.dir)/f'batch_{b:02d}.json';r=json.loads(p.read_text());assert r['batch']==b and r['start']==b*BS and r['end']==(b+1)*BS and r['histories']==BS and not r['construction'];ranges.append((r['start'],r['end']));digests.append(r['digest']);mm+=r['candidate_oracle_mismatches']
  for k in leaks:leaks[k]+=r['leaks'][k]
  for k in CLASSES:
   for x in ('n','fixed','query'):counts[k][x]+=r['counts'][k][x]
 assert ranges==[(b*BS,(b+1)*BS) for b in range(BATCHES)]
 n=sum(v['n'] for v in counts.values());assert n==TOTAL
 f=sum(v['fixed'] for v in counts.values());q=sum(v['query'] for v in counts.values());classes={};worse=[]
 for k,v in counts.items():
  fr=v['fixed']/v['n'];qr=v['query']/v['n'];classes[k]={'n':v['n'],'fixed_rate':fr,'query_rate':qr,'advantage_pp':100*(qr-fr)}
  if qr<fr:worse.append(k)
 adv=100*((q-f)/n);decision='FAIL_MATCHED_SOURCE_TEMPORAL_QUERY_BATCHED'
 if mm==0 and not any(leaks.values()) and not worse:decision='PASS_MATCHED_SOURCE_TEMPORAL_QUERY_BATCHED_SCOPED' if adv>=15 else 'HOLD_NO_SELECTION_DISCRIMINATOR'
 r={'decision':decision,'histories':n,'formal_batches':BATCHES,'batch_size':BS,'formal_invocations':1,'batch_processes':BATCHES,'reruns':0,'candidate_oracle_mismatches':mm,'leaks':leaks,'counts':counts,'classes':classes,'fixed_coverage_rate':f/n,'query_coverage_rate':q/n,'overall_advantage_pp':adv,'query_worse_classes':worse,'batch_digests':digests,'grants_input_authority':False}
 r['aggregate_digest']=hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':')).encode()).hexdigest();out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__':main()
