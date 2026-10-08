import argparse,random,json,hashlib
from pathlib import Path
BASE=[f'B{i}' for i in range(4)];DER=[f'C{i}' for i in range(4)];SEED=185020260919001;N=5000
def graph(r):
 g={}
 for i,c in enumerate(DER):
  p=BASE+DER[:i];opts=[(a,) for a in p]+[(p[x],p[y]) for x in range(len(p)) for y in range(x+1,len(p))];r.shuffle(opts);n=1+r.randrange(min(3,len(opts)));out=[]
  for s in opts:
   q=tuple(sorted(s))
   if q not in out:out.append(q)
   if len(out)==n:break
  g[c]=tuple(out)
 return g
def rev(g):
 z={n:set() for n in BASE+DER}
 for c,js in g.items():
  for j in js:
   for p in j:z[p].add(c)
 return z
def fold(g,m):
 v={b:bool(m>>i&1) for i,b in enumerate(BASE)}
 for c in DER:v[c]=any(all(v[p] for p in j) for j in g[c])
 return v
def affected(g,b):
 r=rev(g);q=list(r[b]);s=set()
 while q:
  x=q.pop()
  if x in s:continue
  s.add(x);q.extend(r[x])
 return s
def inc(g,old,b,val):
 v=dict(old);v[b]=val;a=affected(g,b)
 for c in DER:
  if c in a:v[c]=any(all(v[p] for p in j) for j in g[c])
 return v,a
def counts():
 r=random.Random(SEED);s={'graphs':N,'cases':0,'incremental_full_mismatch':0,'outside_cone_changes':0,'blind_overinvalid_cases':0,'blind_overinvalid_nodes':0,'direct_child_only_bad_cases':0,'alternative_survival_witnesses':0,'multihop_witnesses':0};gd=hashlib.sha256()
 for _ in range(N):
  g=graph(r);gd.update(json.dumps(g,sort_keys=True,separators=(',',':')).encode());rv=rev(g)
  for m in range(16):
   old=fold(g,m)
   for i,b in enumerate(BASE):
    nm=m^(1<<i);truth=fold(g,nm);x,a=inc(g,old,b,not old[b]);s['cases']+=1;s['incremental_full_mismatch']+=int(x!=truth);s['outside_cone_changes']+=sum(old[n]!=truth[n] for n in set(DER)-a)
    direct=dict(old);direct[b]=not old[b]
    for c in DER:
     if c in rv[b]:direct[c]=any(all(direct[p] for p in j) for j in g[c])
    if direct!=truth:
     s['direct_child_only_bad_cases']+=1;wrong={n for n in DER if direct[n]!=truth[n]};s['multihop_witnesses']+=int(any(n not in rv[b] for n in wrong))
    if old[b]:
     blind=dict(old);blind[b]=False
     for c in a:blind[c]=False
     over=sum((not blind[n]) and truth[n] for n in DER)
     if over:s['blind_overinvalid_cases']+=1;s['blind_overinvalid_nodes']+=over;s['alternative_survival_witnesses']+=1
 s['graph_digest']=gd.hexdigest();return s
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--result',required=True);ap.add_argument('--freeze',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();o=Path(a.output);assert not o.exists();R=json.loads(Path(a.result).read_text());F=json.loads(Path(a.freeze).read_text());S=counts();rs=R['stats'];checks={'decision':R['decision']=='PASS_JUSTIFICATION_GRAPH_INCREMENTAL_TRUTH_MAINTENANCE_SCOPED','stats':rs==S,'mismatch':S['incremental_full_mismatch']==0,'outside':S['outside_cone_changes']==0,'blind':S['blind_overinvalid_cases']>0,'direct':S['direct_child_only_bad_cases']>0,'alt':S['alternative_survival_witnesses']>0,'multihop':S['multihop_witnesses']>0,'directed':all(R['directed'].values()),'corruptions':all(R['corruptions'].values()),'formal':R['formal_invocations']==1 and R['reruns']==0 and R['replacements']==0 and R['tuning']==0,'source_plan':h('PLAN.md')==F['sha256']['PLAN.md'],'source_formal':h('formal.py')==F['sha256']['formal.py'],'source_audit':h('audit.py')==F['sha256']['audit.py']};z={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'result_sha256':h(a.result),'freeze_sha256':h(a.freeze)};o.write_text(json.dumps(z,indent=2,sort_keys=True)+'\n');print(json.dumps(z,indent=2,sort_keys=True));raise SystemExit(0 if z['status']=='PASS' else 1)
if __name__=='__main__':main()
