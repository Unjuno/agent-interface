import argparse,collections,hashlib,json,math,pathlib,statistics,struct

def sha(p):
 h=hashlib.sha256();
 with open(p,'rb') as f:
  for c in iter(lambda:f.read(1<<20),b''):h.update(c)
 return h.hexdigest()

def exit_line(wad):
 b=pathlib.Path(wad).read_bytes();ident,n,ofs=struct.unpack_from('<4sII',b,0);ents=[]
 for i in range(n):
  p,s,name=struct.unpack_from('<II8s',b,ofs+i*16);ents.append((name.rstrip(b'\0').decode(),p,s))
 idx=next(i for i,e in enumerate(ents) if e[0]=='MAP01');d={n:(p,s) for n,p,s in ents[idx+1:idx+11]}
 vp,vs=d['VERTEXES'];verts=[struct.unpack_from('<hh',b,vp+i) for i in range(0,vs,4)]
 lp,ls=d['LINEDEFS'];lines=[struct.unpack_from('<HHHHHHH',b,lp+i) for i in range(0,ls,14)]
 sp,ss=d['SIDEDEFS'];sides=[]
 for i in range(0,ss,30):
  xoff,yoff,up,lo,mid,sector=struct.unpack_from('<hh8s8s8sH',b,sp+i)
  dec=lambda x:x.rstrip(b'\0').decode('ascii','ignore')
  sides.append({'upper':dec(up),'lower':dec(lo),'middle':dec(mid),'sector':sector})
 found=[]
 for i,l in enumerate(lines):
  if l[3]==11:
   found.append({'index':i,'a':verts[l[0]],'b':verts[l[1]],'flags':l[2],'special':l[3],'tag':l[4],
     'right':sides[l[5]] if l[5]!=0xffff else None,'left':sides[l[6]] if l[6]!=0xffff else None})
 if len(found)!=1:raise ValueError(f'exactly one MAP01 special11 expected, got {len(found)}')
 return found[0]

def segdist(x,y,a,b):
 ax,ay=a;bx,by=b;dx=bx-ax;dy=by-ay;t=((x-ax)*dx+(y-ay)*dy)/(dx*dx+dy*dy);t=max(0,min(1,t));qx=ax+t*dx;qy=ay+t*dy;return math.hypot(x-qx,y-qy)

def case_rows(root,exitline):
 rows=[]
 for cp in sorted(root.glob('case-*')):
  if not (cp/'score.json').exists():continue
  sc=json.loads((cp/'score.json').read_text());tr=json.loads((cp/'trajectory.json').read_text())
  cells={(math.floor(r['x']/64),math.floor(r['y']/64)) for r in tr}
  ds=[segdist(r['x'],r['y'],exitline['a'],exitline['b']) for r in tr]
  mi=min(range(len(ds)),key=ds.__getitem__)
  rows.append({'case':cp.name,'seed':sc['seed'],'arm':sc['arm'],'coverage64':len(cells),'min_exit_distance':ds[mi],
    'min_exit_step':mi,'final_exit_distance':ds[-1],'final_x':tr[-1]['x'],'final_y':tr[-1]['y'],'release_ok':sc['release_ok'],'dead':sc['player_dead'],'map_exit':sc['map_exit']})
 return rows

def aggregate(rows):
 g=collections.defaultdict(dict)
 for r in rows:g[r['seed']][r['arm']]=r
 pairs=[]
 for seed,v in sorted(g.items()):
  b=v['repeat_small'];c=v['escalate']
  pairs.append({'seed':seed,'baseline_coverage':b['coverage64'],'candidate_coverage':c['coverage64'],'coverage_delta':c['coverage64']-b['coverage64'],
    'baseline_min_exit':b['min_exit_distance'],'candidate_min_exit':c['min_exit_distance'],'candidate_min_closer':b['min_exit_distance']-c['min_exit_distance'],
    'baseline_final_exit':b['final_exit_distance'],'candidate_final_exit':c['final_exit_distance'],'candidate_final_closer':b['final_exit_distance']-c['final_exit_distance'],
    'baseline_min_step':b['min_exit_step'],'candidate_min_step':c['min_exit_step']})
 return {'pairs':pairs,'paired_median_coverage_delta':statistics.median(p['coverage_delta'] for p in pairs),
   'paired_median_min_exit_closer':statistics.median(p['candidate_min_closer'] for p in pairs),
   'paired_median_final_exit_closer':statistics.median(p['candidate_final_closer'] for p in pairs),
   'candidate_min_exit_closer_pairs':sum(p['candidate_min_closer']>1e-6 for p in pairs),
   'candidate_final_exit_closer_pairs':sum(p['candidate_final_closer']>0 for p in pairs),
   'common_prefix_min_step_all':all(p['baseline_min_step']==p['candidate_min_step']==5 for p in pairs)}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--normal',type=pathlib.Path,required=True);ap.add_argument('--nomonsters',type=pathlib.Path,required=True);ap.add_argument('--wad',type=pathlib.Path,required=True);ap.add_argument('--normal-archive',type=pathlib.Path,required=True);ap.add_argument('--nomonsters-archive',type=pathlib.Path,required=True);args=ap.parse_args()
 ex=exit_line(args.wad)
 nr=case_rows(args.normal/'results',ex); mr=case_rows(args.nomonsters/'package-v2'/'results',ex)
 out={'schema':'agent-interface/map01-task-progress-posthoc-v1','inputs':{'wad_sha256':sha(args.wad),'normal_archive_sha256':sha(args.normal_archive),'nomonsters_archive_sha256':sha(args.nomonsters_archive)},
      'exit_linedef':ex,'normal':{'rows':nr,**aggregate(nr)},'nomonsters':{'rows':mr,**aggregate(mr)}}
 out['diagnostic']={'coverage_improved_but_min_exit_not':out['normal']['paired_median_coverage_delta']>0 and out['normal']['paired_median_min_exit_closer']<=0 and out['nomonsters']['paired_median_coverage_delta']>0 and out['nomonsters']['paired_median_min_exit_closer']<=0,
                    'candidate_final_farther_in_all_pairs':out['normal']['candidate_final_exit_closer_pairs']==0 and out['nomonsters']['candidate_final_exit_closer_pairs']==0}
 print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
