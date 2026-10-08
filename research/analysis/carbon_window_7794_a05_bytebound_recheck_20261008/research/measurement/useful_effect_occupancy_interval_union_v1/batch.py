from __future__ import annotations
import argparse,importlib.util,itertools,json,random,sys,time,tracemalloc
from pathlib import Path
ROOT=Path(__file__).parent
BASE_SEED=132820260918100

def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
p=load('parent_batch',ROOT/'parent_candidate.py');c=load('cand_batch',ROOT/'interval_candidate.py')

def oracle(wait,acts):
    vals=[0,0,0,0]
    for t in range(wait.lo,wait.hi):
        g=pp=ag=ap=False
        for a in acts:
            gg=a.down_hi<=t<a.up_lo;poss=a.down_lo<=t<a.up_hi;auth=any(z.lo<=t<z.hi for z in a.authority)
            g|=gg;pp|=poss;ag|=(gg and auth);ap|=(poss and auth)
        vals[0]+=g;vals[1]+=pp;vals[2]+=ag;vals[3]+=ap
    return tuple(vals)
def mk_act(r,j,limit,maxauth=4):
    pts=sorted(r.randrange(0,limit+1) for _ in range(4));auth=[]
    for _ in range(r.randrange(0,maxauth+1)):
        x,y=sorted((r.randrange(0,limit+1),r.randrange(0,limit+1)));auth.append(p.Interval(x,y))
    return p.Actuation(f'a{j}',*pts,tuple(auth))

def run_bounded(idx,count):
    r=random.Random(BASE_SEED+idx);mo=mp=0;start=time.perf_counter()
    for i in range(count):
        lo=r.randrange(0,12);hi=r.randrange(lo,36);wait=p.Interval(lo,hi);acts=[mk_act(r,j,42,4) for j in range(r.randrange(0,6))]
        old=p.occupancy_only(wait,acts);new=c.occupancy_interval_union(wait,acts)
        mo+=old!=new
        if i<5000:mp+=new!=oracle(wait,acts)
    return {'kind':'bounded','index':idx,'cases':count,'old_mismatches':mo,'pointwise_checked':min(count,5000),'pointwise_mismatches':mp,'wall_s':time.perf_counter()-start,'seed':BASE_SEED+idx}
def run_stress(idx,count):
    r=random.Random(BASE_SEED+100+idx);inv=0;start=time.perf_counter();tracemalloc.start()
    for i in range(count):
        base=r.randrange(10**14,10**15);duration=r.randrange(50_000_000,500_000_001);wait=p.Interval(base,base+duration);acts=[]
        for j in range(r.randrange(0,9)):
            dl=base+r.randrange(-20_000_000,duration+20_000_001);dh=dl+r.randrange(0,5_000_001);ul=dh+r.randrange(0,200_000_001);uh=ul+r.randrange(0,5_000_001)
            dl=max(0,dl);auth=[]
            for _ in range(r.randrange(0,9)):
                al=max(0,base+r.randrange(-20_000_000,duration+20_000_001));ah=al+r.randrange(0,100_000_001);auth.append(p.Interval(al,ah))
            acts.append(p.Actuation(f's{j}',dl,dh,ul,uh,tuple(auth)))
        g,poss,ag,ap=c.occupancy_interval_union(wait,acts)
        if not (0<=g<=poss<=duration and 0<=ag<=g and 0<=ap<=poss):inv+=1
    _,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
    return {'kind':'stress','index':idx,'cases':count,'invariant_errors':inv,'wall_s':time.perf_counter()-start,'peak_tracemalloc_bytes':peak,'seed':BASE_SEED+100+idx}
def run_exhaustive():
    mo=mp=cases=0;start=time.perf_counter()
    for whi in range(0,7):
        wait=p.Interval(0,whi)
        for dl,dh,ul,uh in itertools.combinations_with_replacement(range(0,7),4):
            for auth in [()]+[(p.Interval(al,ah),) for al in range(0,7) for ah in range(al,7)]:
                acts=[p.Actuation('a',dl,dh,ul,uh,auth)];old=p.occupancy_only(wait,acts);new=c.occupancy_interval_union(wait,acts);ref=oracle(wait,acts);cases+=1;mo+=old!=new;mp+=new!=ref
    variants=[]
    for pts in itertools.combinations_with_replacement(range(0,3),4):
        for mode in range(3):
            auth=() if mode==0 else ((p.Interval(0,1),) if mode==1 else (p.Interval(1,2),));variants.append((pts,auth))
    for whi in range(0,4):
        wait=p.Interval(0,whi)
        for pa,aa in variants:
            a=p.Actuation('a',*pa,aa)
            for pb,ab in variants:
                acts=[a,p.Actuation('b',*pb,ab)];old=p.occupancy_only(wait,acts);new=c.occupancy_interval_union(wait,acts);ref=oracle(wait,acts);cases+=1;mo+=old!=new;mp+=new!=ref
    return {'kind':'exhaustive','index':0,'cases':cases,'old_mismatches':mo,'pointwise_mismatches':mp,'wall_s':time.perf_counter()-start}

ap=argparse.ArgumentParser();ap.add_argument('kind',choices=['bounded','stress','exhaustive']);ap.add_argument('--index',type=int,default=0);ap.add_argument('--count',type=int);ap.add_argument('--out',required=True);a=ap.parse_args()
out=run_exhaustive() if a.kind=='exhaustive' else (run_bounded(a.index,a.count or 100000) if a.kind=='bounded' else run_stress(a.index,a.count or 20000))
pout=Path(a.out)
if pout.exists():raise SystemExit('output exists')
pout.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
