from pathlib import Path
import argparse, collections, hashlib, json, struct
WAD_SHA='a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b'
EXITS={11,51,52,124}

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(wad):
    d=Path(wad).read_bytes()
    if hashlib.sha256(d).hexdigest()!=WAD_SHA: raise ValueError('WAD_SHA_MISMATCH')
    ident,n,do=struct.unpack_from('<4sII',d,0)
    if ident not in (b'IWAD',b'PWAD'): raise ValueError('BAD_WAD_MAGIC')
    E=[]
    for i in range(n):
        o,s,nm=struct.unpack_from('<II8s',d,do+i*16); E.append((nm.rstrip(b'\0').decode('ascii'),o,s))
    mi=next(i for i,x in enumerate(E) if x[0]=='MAP01')
    L={x[0]:(x[1],x[2]) for x in E[mi+1:mi+11]}
    def R(name,fmt):
        o,s=L[name]; st=struct.Struct(fmt)
        if s%st.size: raise ValueError('BAD_LUMP_SIZE:'+name)
        return [st.unpack_from(d,o+i) for i in range(0,s,st.size)]
    V=R('VERTEXES','<hh'); LD=R('LINEDEFS','<HHHHHHH'); SD=R('SIDEDEFS','<hh8s8s8sH')
    SG=R('SEGS','<HHHHHH'); SS=R('SSECTORS','<HH'); N=R('NODES','<hhhhhhhhhhhhHH'); SEC=R('SECTORS','<hh8s8shhh')
    ssec=[]
    for cnt,first in SS:
        q=[]
        for j in range(first,first+cnt):
            ld=LD[SG[j][3]]; si=ld[5] if SG[j][4]==0 else ld[6]
            if si!=65535:q.append(SD[si][-1])
        if not q or len(set(q))!=1: raise ValueError('BAD_SUBSECTOR_SECTOR')
        ssec.append(q[0])
    exits=[]
    for i,x in enumerate(LD):
        if x[3] in EXITS:
            exits.append((i,x[3],V[x[0]],V[x[1]],SD[x[5]][-1] if x[5]!=65535 else None,SD[x[6]][-1] if x[6]!=65535 else None))
    if len(exits)!=1 or exits[0][1]!=11: raise ValueError('EXIT_LINE_INTEGRITY')
    target={s for s in exits[0][4:] if s is not None}
    graph=collections.defaultdict(set); edge_lines=collections.defaultdict(list)
    for i,x in enumerate(LD):
        if x[5]==65535 or x[6]==65535: continue
        a,b=SD[x[5]][-1],SD[x[6]][-1]
        if a==b: continue
        graph[a].add(b); graph[b].add(a); edge_lines[frozenset((a,b))].append(i)
    q=collections.deque(target); hops={x:0 for x in target}
    while q:
        u=q.popleft()
        for v in graph[u]:
            if v not in hops: hops[v]=hops[u]+1; q.append(v)
    def point_sector(x,y):
        k=len(N)-1
        while True:
            z=N[k]; nx,ny,dx,dy=z[:4]
            if dx==0: side=int((dy>0) if x<=nx else (dy<0))
            elif dy==0: side=int((dx<0) if y<=ny else (dx>0))
            else: side=1 if ((x-nx)*dy-(y-ny)*dx)<0 else 0
            ch=z[-1] if side else z[-2]
            if ch&32768:
                ss=ch&32767
                if ss>=len(ssec): raise ValueError('BAD_SUBSECTOR')
                return ssec[ss]
            k=ch
    def sector_meta(i):
        floor,ceil,ft,ct,light,special,tag=SEC[i]
        return {'sector':i,'floor':floor,'ceiling':ceil,'floor_tex':ft.rstrip(b'\0').decode('ascii'),
                'ceiling_tex':ct.rstrip(b'\0').decode('ascii'),'light':light,'special':special,'tag':tag}
    def line_meta(i):
        x=LD[i]; rs=SD[x[5]][-1] if x[5]!=65535 else None; ls=SD[x[6]][-1] if x[6]!=65535 else None
        return {'linedef':i,'a':list(V[x[0]]),'b':list(V[x[1]]),'flags':x[2],'special':x[3],'tag':x[4],
                'right_sector':rs,'left_sector':ls,
                'right_meta':sector_meta(rs) if rs is not None else None,
                'left_meta':sector_meta(ls) if ls is not None else None}
    return exits[0],hops,graph,edge_lines,point_sector,line_meta

def classify_line(m):
    if m['special']!=0: return 'special_'+str(m['special'])
    return 'ordinary_two_sided'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); ap.add_argument('--plan',required=True); ap.add_argument('--wad',required=True); ap.add_argument('--out',required=True)
    a=ap.parse_args(); plan=json.loads(Path(a.plan).read_text()); ex,hops,graph,edge_lines,sector,line_meta=load(a.wad)
    rows=[]; first_sector_counts=collections.Counter()
    for c in plan['cases']:
        p=Path(a.root)/f"case-{c['case']:02d}"/'trajectory.json'
        if sha(p)!=c['trajectory_sha256']: raise ValueError('TRAJECTORY_SHA_MISMATCH')
        t=json.loads(p.read_text()); seq=[]
        for r in t:
            s=sector(float(r['x']),float(r['y'])); seq.append({'i':r['i'],'sector':s,'hop':hops.get(s)})
        hs=[z['hop'] for z in seq if z['hop'] is not None]
        if not hs: raise ValueError('NO_REACHABLE_HOPS')
        mh=min(hs); plateau=[z for z in seq if z['hop']==mh]
        first=plateau[0]; last=plateau[-1]; visited=sorted({z['sector'] for z in plateau}); edges=[]
        for s in visited:
            if hops.get(s)!=mh: continue
            for n in sorted(graph[s]):
                if hops.get(n)!=mh-1: continue
                for li in edge_lines[frozenset((s,n))]:
                    lm=line_meta(li); edges.append({'from_sector':s,'to_sector':n,'from_hop':mh,'to_hop':mh-1,'class':classify_line(lm),'line':lm})
        first_sector_counts[first['sector']]+=1
        rows.append({'case':c['case'],'seed':c['seed'],'arm':c['arm'],'min_hop':mh,'first_min':first,'last_min':last,'plateau_sectors':visited,'candidate_next_edges':edges})
    common_sector=first_sector_counts.most_common(1)[0] if first_sector_counts else (None,0)
    run_classes=[sorted({e['class'] for e in r['candidate_next_edges']}) for r in rows]
    run_class_count=collections.Counter(cl for cls in run_classes for cl in cls)
    best_class,best_n=run_class_count.most_common(1)[0] if run_class_count else (None,0)
    if best_n>=6: decision='PLATEAU_COMMON_INTERACTION_SCOPED'
    else: decision='PLATEAU_GEOMETRY_BRANCHING'
    out={'schema':'agent-interface/map01-hop15-plateau-v1','wad_sha256':sha(a.wad),
         'exit':{'linedef':ex[0],'special':ex[1],'a':list(ex[2]),'b':list(ex[3]),'sectors':[ex[4],ex[5]]},
         'rows':rows,'first_min_sector_counts':dict(sorted(first_sector_counts.items())),
         'run_boundary_classes':run_classes,'run_boundary_class_counts':dict(sorted(run_class_count.items())),
         'dominant_first_sector':{'sector':common_sector[0],'runs':common_sector[1]},
         'dominant_boundary_class':{'class':best_class,'runs':best_n},'decision':decision}
    Path(a.out).write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'decision':decision,'dominant_first_sector':out['dominant_first_sector'],'dominant_boundary_class':out['dominant_boundary_class'],'first_counts':out['first_min_sector_counts']}))
if __name__=='__main__': main()
