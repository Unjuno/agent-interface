from pathlib import Path
import argparse,collections,hashlib,json,math,struct
WAD_SHA='a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b'; EXITS={11,51,52,124}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def parse(wad):
 d=Path(wad).read_bytes()
 if hashlib.sha256(d).hexdigest()!=WAD_SHA:raise AssertionError('wad-sha')
 ident,n,do=struct.unpack_from('<4sII',d,0);E=[]
 for i in range(n):
  o,s,nm=struct.unpack_from('<II8s',d,do+i*16);E.append((nm.rstrip(b'\0').decode(),o,s))
 mi=next(i for i,x in enumerate(E) if x[0]=='MAP01');L={x[0]:(x[1],x[2]) for x in E[mi+1:mi+11]}
 def R(name,fmt):
  o,s=L[name];z=struct.Struct(fmt);assert s%z.size==0;return [z.unpack_from(d,o+i) for i in range(0,s,z.size)]
 V=R('VERTEXES','<hh');LD=R('LINEDEFS','<HHHHHHH');SD=R('SIDEDEFS','<hh8s8s8sH');SG=R('SEGS','<HHHHHH');SS=R('SSECTORS','<HH');N=R('NODES','<hhhhhhhhhhhhHH')
 ssec=[]
 for cnt,first in SS:
  q=[]
  for j in range(first,first+cnt):
   ld=LD[SG[j][3]];si=ld[5] if SG[j][4]==0 else ld[6]
   if si!=65535:q.append(SD[si][-1])
  assert q and len(set(q))==1;ssec.append(q[0])
 ex=[]
 for i,x in enumerate(LD):
  if x[3] in EXITS:
   ex.append((i,x[3],V[x[0]],V[x[1]],SD[x[5]][-1] if x[5]!=65535 else None,SD[x[6]][-1] if x[6]!=65535 else None))
 assert len(ex)==1 and ex[0][1]==11
 targets={q for q in ex[0][4:] if q is not None}
 G=collections.defaultdict(set)
 for x in LD:
  if x[5]!=65535 and x[6]!=65535:
   a,b=SD[x[5]][-1],SD[x[6]][-1]
   if a!=b:G[a].add(b);G[b].add(a)
 Q=collections.deque(targets);H={x:0 for x in targets}
 while Q:
  u=Q.popleft()
  for v in G[u]:
   if v not in H:H[v]=H[u]+1;Q.append(v)
 def sector(x,y):
  k=len(N)-1
  while 1:
   z=N[k];nx,ny,dx,dy=z[:4]
   if dx==0:s=int((dy>0) if x<=nx else (dy<0))
   elif dy==0:s=int((dx<0) if y<=ny else (dx>0))
   else:s=1 if ((x-nx)*dy-(y-ny)*dx)<0 else 0
   ch=z[-1] if s else z[-2]
   if ch&32768:return ssec[ch&32767]
   k=ch
 return ex[0],H,sector
def dist(px,py,a,b):
 x1,y1=a;x2,y2=b;dx=x2-x1;dy=y2-y1;t=max(0,min(1,((px-x1)*dx+(py-y1)*dy)/(dx*dx+dy*dy)));return math.hypot(px-(x1+t*dx),py-(y1+t*dy))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--plan',required=True);ap.add_argument('--wad',required=True);ap.add_argument('--scored',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
 plan=json.loads(Path(a.plan).read_text()); measured=json.loads(Path(a.scored).read_text());ex,H,sector=parse(a.wad);errors=[];rows=[]
 for c in plan['cases']:
  d=Path(a.root)/f"case-{c['case']:02d}";s=json.loads((d/'score.json').read_text());t=json.loads((d/'trajectory.json').read_text())
  hs=[];es=[]
  for r in t:
   sec=sector(float(r['x']),float(r['y']));
   if sec not in H:errors.append(f"case{c['case']}:unreachable");continue
   hs.append(H[sec]);es.append(dist(float(r['x']),float(r['y']),ex[2],ex[3]))
  cov=len({(math.floor(float(r['x'])/64),math.floor(float(r['y'])/64)) for r in t})
  rows.append({'case':c['case'],'arm':s['arm'],'seed':s['seed'],'coverage64':cov,'min_hops':min(hs),'final_hops':hs[-1],'min_euclidean':min(es),'final_health':s['final_health'],'player_dead':s['player_dead'],'release_ok':s['release_ok']})
 if len(measured.get('rows',[]))!=len(rows):errors.append('row-count')
 for r in rows:
  m=next((x for x in measured.get('rows',[]) if x['arm']==r['arm'] and x['seed']==r['seed']),None)
  if not m:errors.append(f"missing:{r['case']}");continue
  for k in ('coverage64','min_hops','final_hops','player_dead','release_ok'):
   if m[k]!=r[k]:errors.append(f"case{r['case']}:{k}")
  if abs(float(m['min_euclidean'])-r['min_euclidean'])>1e-6:errors.append(f"case{r['case']}:euclid")
 pairs=[];better=0;covnw=0
 for seed in plan['seeds']:
  b=next(x for x in rows if x['seed']==seed and x['arm']=='repeat_small');c=next(x for x in rows if x['seed']==seed and x['arm']=='escalate');delta=c['min_hops']-b['min_hops'];cov=c['coverage64']-b['coverage64'];pairs.append((delta,cov));better+=delta<0;covnw+=cov>=0
 ds=sorted(x[0] for x in pairs);med=(ds[1]+ds[2])/2;safety=all((not x['player_dead']) and x['release_ok'] and x['final_health']>=80 for x in rows if x['arm']=='escalate')
 if not safety:dec='FAIL_EXIT_TOPOLOGY_SAFETY'
 elif better>=3 and med<=-1:dec='PASS_EXIT_TOPOLOGY_PROGRESS'
 elif covnw>=3 and better<=1 and med>=0:dec='REJECT_COVERAGE_AS_TASK_PROGRESS_PROXY'
 else:dec='HOLD_EXIT_PROGRESS_MIXED'
 if measured.get('decision')!=dec:errors.append('decision')
 out={'schema':'agent-interface/map01-exit-topology-progress-audit-v1','status':'PASS_AUDIT' if not errors else 'FAIL_AUDIT','scientific_decision':dec,'errors':errors,'exit_linedef':ex[0],'exit_special':ex[1],'exit_segment':[list(ex[2]),list(ex[3])],'candidate_better_min_hops_pairs':better,'paired_median_min_hop_delta':med,'coverage_nonworse_pairs':covnw}
 Path(a.out).write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps(out));raise SystemExit(0 if not errors else 2)
if __name__=='__main__':main()
