from pathlib import Path
import argparse,collections,hashlib,json,math,struct

WAD_SHA256='a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b'
EXIT_SPECIALS={11,51,52,124}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load_map(wad_path):
    p=Path(wad_path); data=p.read_bytes()
    if hashlib.sha256(data).hexdigest()!=WAD_SHA256:
        raise ValueError('WAD_SHA256_MISMATCH')
    ident,num,dir_ofs=struct.unpack_from('<4sII',data,0)
    if ident not in (b'IWAD',b'PWAD'): raise ValueError('BAD_WAD_MAGIC')
    entries=[]
    for i in range(num):
        off,size,name=struct.unpack_from('<II8s',data,dir_ofs+i*16)
        entries.append((name.rstrip(b'\0').decode('ascii'),off,size))
    mi=next(i for i,e in enumerate(entries) if e[0]=='MAP01')
    lumps={name:(off,size) for name,off,size in entries[mi+1:mi+11]}
    def rec(name,fmt):
        off,size=lumps[name]; st=struct.Struct(fmt)
        if size%st.size: raise ValueError('BAD_LUMP_SIZE:'+name)
        return [st.unpack_from(data,off+i) for i in range(0,size,st.size)]
    verts=rec('VERTEXES','<hh')
    lines=rec('LINEDEFS','<HHHHHHH')
    sides=rec('SIDEDEFS','<hh8s8s8sH')
    segs=rec('SEGS','<HHHHHH')
    ssecs=rec('SSECTORS','<HH')
    nodes=rec('NODES','<hhhhhhhhhhhhHH')
    subsector_sector=[]
    for count,first in ssecs:
        secs=[]
        for j in range(first,first+count):
            _sv,_ev,_ang,ld,side,_ofs=segs[j]
            line=lines[ld]
            side_idx=line[5] if side==0 else line[6]
            if side_idx!=0xffff: secs.append(sides[side_idx][-1])
        if not secs or len(set(secs))!=1: raise ValueError('BAD_SUBSECTOR_SECTOR')
        subsector_sector.append(secs[0])
    exits=[]
    for i,line in enumerate(lines):
        if line[3] in EXIT_SPECIALS:
            a=verts[line[0]]; b=verts[line[1]]
            rs=sides[line[5]][-1] if line[5]!=0xffff else None
            ls=sides[line[6]][-1] if line[6]!=0xffff else None
            exits.append({'linedef':i,'special':line[3],'a':a,'b':b,'right_sector':rs,'left_sector':ls})
    if len(exits)!=1: raise ValueError('EXIT_LINE_COUNT_NOT_ONE')
    exit_line=exits[0]; exit_sectors={s for s in (exit_line['right_sector'],exit_line['left_sector']) if s is not None}
    graph=collections.defaultdict(set)
    for line in lines:
        r,l=line[5],line[6]
        if r==0xffff or l==0xffff: continue
        a=sides[r][-1]; b=sides[l][-1]
        if a!=b: graph[a].add(b);graph[b].add(a)
    rev=collections.defaultdict(set)
    for a,ns in graph.items():
        for b in ns: rev[b].add(a)
    q=collections.deque(); hops={}
    for e in exit_sectors:hops[e]=0;q.append(e)
    while q:
        u=q.popleft()
        for v in rev[u]:
            if v not in hops:hops[v]=hops[u]+1;q.append(v)
    def point_sector(x,y):
        idx=len(nodes)-1
        while True:
            n=nodes[idx]; nx,ny,dx,dy=n[:4]; ch0,ch1=n[-2:]
            if dx==0: side=int((dy>0) if x<=nx else (dy<0))
            elif dy==0: side=int((dx<0) if y<=ny else (dx>0))
            else:
                cross=(x-nx)*dy-(y-ny)*dx
                side=1 if cross<0 else 0
            child=ch1 if side else ch0
            if child&0x8000:
                ss=child&0x7fff
                if ss>=len(subsector_sector): raise ValueError('BAD_SUBSECTOR_REF')
                return subsector_sector[ss]
            idx=child
    return exit_line,hops,point_sector

def segdist(px,py,a,b):
    x1,y1=a;x2,y2=b;dx=x2-x1;dy=y2-y1
    if dx==0 and dy==0:return math.hypot(px-x1,py-y1)
    t=max(0.0,min(1.0,((px-x1)*dx+(py-y1)*dy)/(dx*dx+dy*dy)))
    return math.hypot(px-(x1+t*dx),py-(y1+t*dy))

def score_case(case_dir,wad_path):
    case_dir=Path(case_dir)
    score=json.loads((case_dir/'score.json').read_text())
    traj=json.loads((case_dir/'trajectory.json').read_text())
    exit_line,hops,point_sector=load_map(wad_path)
    hop_seq=[]; eu=[]; sectors=[]
    for row in traj:
        sec=point_sector(float(row['x']),float(row['y']))
        if sec not in hops: raise ValueError('UNREACHABLE_STRUCTURAL_SECTOR')
        sectors.append(sec);hop_seq.append(hops[sec]);eu.append(segdist(float(row['x']),float(row['y']),exit_line['a'],exit_line['b']))
    if not traj: raise ValueError('EMPTY_TRAJECTORY')
    return {
        'arm':score['arm'],'seed':score['seed'],'decisions':len(traj),
        'player_dead':score['player_dead'],'release_ok':score['release_ok'],'final_health':score['final_health'],
        'coverage64':len({(math.floor(float(r['x'])/64),math.floor(float(r['y'])/64)) for r in traj}),
        'start_hops':hop_seq[0],'min_hops':min(hop_seq),'final_hops':hop_seq[-1],
        'start_euclidean':eu[0],'min_euclidean':min(eu),'final_euclidean':eu[-1],
        'unique_sectors':len(set(sectors)),
        'exit_linedef':exit_line['linedef'],'exit_special':exit_line['special'],
        'exit_segment':[list(exit_line['a']),list(exit_line['b'])],
    }

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--plan',required=True);ap.add_argument('--wad',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
    plan=json.loads(Path(a.plan).read_text())
    rows=[]
    for c in plan['cases']:
        d=Path(a.root)/f"case-{c['case']:02d}"
        row=score_case(d,a.wad)
        if row['arm']!=c['arm'] or row['seed']!=c['seed']: raise ValueError('CASE_IDENTITY_MISMATCH')
        rows.append(row)
    pairs=[];better=0;cov_nonworse=0
    for seed in plan['seeds']:
        b=next(r for r in rows if r['seed']==seed and r['arm']=='repeat_small')
        c=next(r for r in rows if r['seed']==seed and r['arm']=='escalate')
        delta=c['min_hops']-b['min_hops']; cov=c['coverage64']-b['coverage64']
        pairs.append({'seed':seed,'baseline_min_hops':b['min_hops'],'candidate_min_hops':c['min_hops'],'min_hop_delta':delta,
                      'baseline_final_hops':b['final_hops'],'candidate_final_hops':c['final_hops'],'final_hop_delta':c['final_hops']-b['final_hops'],
                      'baseline_min_euclidean':b['min_euclidean'],'candidate_min_euclidean':c['min_euclidean'],
                      'coverage_delta':cov})
        better += delta<0; cov_nonworse += cov>=0
    ds=sorted(p['min_hop_delta'] for p in pairs); med=(ds[1]+ds[2])/2
    safety=all((not r['player_dead']) and r['release_ok'] for r in rows if r['arm']=='escalate') and all(r['final_health']>=80 for r in rows if r['arm']=='escalate')
    if not safety: decision='FAIL_EXIT_TOPOLOGY_SAFETY'
    elif better>=3 and med<=-1: decision='PASS_EXIT_TOPOLOGY_PROGRESS'
    elif cov_nonworse>=3 and better<=1 and med>=0: decision='REJECT_COVERAGE_AS_TASK_PROGRESS_PROXY'
    else: decision='HOLD_EXIT_PROGRESS_MIXED'
    out={'schema':'agent-interface/map01-exit-topology-progress-v1','wad_sha256':sha(a.wad),'rows':rows,'pairs':pairs,
         'candidate_better_min_hops_pairs':better,'coverage_nonworse_pairs':cov_nonworse,'paired_median_min_hop_delta':med,'decision':decision}
    Path(a.out).write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'decision':decision,'better_pairs':better,'median_delta':med,'coverage_nonworse_pairs':cov_nonworse}))
if __name__=='__main__':main()
