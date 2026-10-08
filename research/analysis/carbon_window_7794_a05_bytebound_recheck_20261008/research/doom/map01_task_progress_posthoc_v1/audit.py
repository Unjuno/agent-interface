import argparse, collections, hashlib, json, math, pathlib, statistics, struct, sys

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def parse_exit(wad_path):
    b=pathlib.Path(wad_path).read_bytes()
    ident,n,ofs=struct.unpack_from('<4sII',b,0)
    if ident not in (b'IWAD',b'PWAD'): raise ValueError('bad WAD identity')
    entries=[]
    for i in range(n):
        pos,size,name=struct.unpack_from('<II8s',b,ofs+i*16)
        entries.append((name.rstrip(b'\0').decode('ascii','ignore'),pos,size))
    map_i=next(i for i,e in enumerate(entries) if e[0]=='MAP01')
    lumps={name:(pos,size) for name,pos,size in entries[map_i+1:map_i+12]}
    vp,vs=lumps['VERTEXES']; verts=[struct.unpack_from('<hh',b,vp+i) for i in range(0,vs,4)]
    lp,ls=lumps['LINEDEFS']; lines=[struct.unpack_from('<HHHHHHH',b,lp+i) for i in range(0,ls,14)]
    sp,ss=lumps['SIDEDEFS']; sides=[]
    for i in range(0,ss,30):
        xoff,yoff,up,lo,mid,sector=struct.unpack_from('<hh8s8s8sH',b,sp+i)
        dec=lambda x:x.rstrip(b'\0').decode('ascii','ignore')
        sides.append({'upper':dec(up),'lower':dec(lo),'middle':dec(mid),'sector':sector})
    exits=[]
    for i,line in enumerate(lines):
        v1,v2,flags,special,tag,right,left=line
        if special==11:
            exits.append({'index':i,'a':list(verts[v1]),'b':list(verts[v2]),'flags':flags,'special':special,'tag':tag,
                'right':sides[right] if right!=0xffff else None,'left':sides[left] if left!=0xffff else None})
    if len(exits)!=1: raise ValueError(f'unique special11 expected, got {len(exits)}')
    return exits[0]

def point_segment_distance(x,y,a,b):
    ax,ay=a; bx,by=b; dx=bx-ax; dy=by-ay
    denom=dx*dx+dy*dy
    t=0.0 if denom==0 else ((x-ax)*dx+(y-ay)*dy)/denom
    t=max(0.0,min(1.0,t)); qx=ax+t*dx; qy=ay+t*dy
    return math.hypot(x-qx,y-qy)

def collect(root, results_rel, exit_line):
    rows=[]
    rr=root/results_rel
    for case in sorted(rr.glob('case-*')):
        sp=case/'score.json'; tp=case/'trajectory.json'
        if not (sp.exists() and tp.exists()): raise ValueError(f'incomplete case {case}')
        s=json.loads(sp.read_text()); traj=json.loads(tp.read_text())
        if not traj: raise ValueError(f'empty trajectory {case}')
        cells={(math.floor(float(p['x'])/64),math.floor(float(p['y'])/64)) for p in traj}
        d=[point_segment_distance(float(p['x']),float(p['y']),exit_line['a'],exit_line['b']) for p in traj]
        mi=min(range(len(d)), key=d.__getitem__)
        rows.append({'case':case.name,'seed':int(s['seed']),'arm':s['arm'],'coverage64':len(cells),
            'min_exit_distance':d[mi],'min_exit_step':mi,'final_exit_distance':d[-1],
            'release_ok':bool(s['release_ok']),'dead':bool(s['player_dead']),'map_exit':bool(s['map_exit'])})
    if len(rows)!=8: raise ValueError(f'expected 8 rows, got {len(rows)}')
    return rows

def pair_summary(rows):
    by=collections.defaultdict(dict)
    for r in rows: by[r['seed']][r['arm']]=r
    if len(by)!=4: raise ValueError('expected 4 seeds')
    pairs=[]
    for seed,v in sorted(by.items()):
        if set(v)!={'repeat_small','escalate'}: raise ValueError(f'bad arms {seed}: {set(v)}')
        b=v['repeat_small']; c=v['escalate']
        pairs.append({'seed':seed,'coverage_delta':c['coverage64']-b['coverage64'],
            'min_closer':b['min_exit_distance']-c['min_exit_distance'],
            'final_closer':b['final_exit_distance']-c['final_exit_distance'],
            'baseline_min_step':b['min_exit_step'],'candidate_min_step':c['min_exit_step']})
    return {
        'median_coverage_delta':statistics.median(p['coverage_delta'] for p in pairs),
        'median_min_closer':statistics.median(p['min_closer'] for p in pairs),
        'median_final_closer':statistics.median(p['final_closer'] for p in pairs),
        'min_closer_pairs_gt_1unit':sum(p['min_closer']>1.0 for p in pairs),
        'final_closer_pairs':sum(p['final_closer']>0 for p in pairs),
        'common_prefix_min_step_all':all(p['baseline_min_step']==p['candidate_min_step']==5 for p in pairs),
        'pairs':pairs,
    }

def close(a,b,tol=1e-6): return abs(float(a)-float(b))<=tol

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--normal-root',type=pathlib.Path,required=True)
    ap.add_argument('--nomonsters-root',type=pathlib.Path,required=True)
    ap.add_argument('--normal-archive',type=pathlib.Path,required=True)
    ap.add_argument('--nomonsters-archive',type=pathlib.Path,required=True)
    ap.add_argument('--wad',type=pathlib.Path,required=True)
    ap.add_argument('--result',type=pathlib.Path,required=True)
    args=ap.parse_args()
    expected=json.loads(args.result.read_text()); errors=[]
    hashes={'normal_archive_sha256':sha256(args.normal_archive),'nomonsters_archive_sha256':sha256(args.nomonsters_archive),'wad_sha256':sha256(args.wad)}
    for k,v in hashes.items():
        if expected['inputs'].get(k)!=v: errors.append(f'hash:{k}')
    ex=parse_exit(args.wad)
    if ex!=expected.get('exit_linedef'): errors.append('exit_linedef_mismatch')
    normal=pair_summary(collect(args.normal_root,pathlib.Path('results'),ex))
    nom=pair_summary(collect(args.nomonsters_root,pathlib.Path('package-v2/results'),ex))
    expn=expected['normal']; expm=expected['nomonsters']
    checks=[
        ('normal.coverage',normal['median_coverage_delta'],expn['paired_median_coverage_delta']),
        ('normal.min',normal['median_min_closer'],expn['paired_median_min_exit_closer']),
        ('normal.final',normal['median_final_closer'],expn['paired_median_final_exit_closer']),
        ('nom.coverage',nom['median_coverage_delta'],expm['paired_median_coverage_delta']),
        ('nom.min',nom['median_min_closer'],expm['paired_median_min_exit_closer']),
        ('nom.final',nom['median_final_closer'],expm['paired_median_final_exit_closer']),
    ]
    for name,a,b in checks:
        if not close(a,b): errors.append(name)
    if normal['min_closer_pairs_gt_1unit']!=0: errors.append('normal_material_min_closer')
    if nom['min_closer_pairs_gt_1unit']!=0: errors.append('nom_material_min_closer')
    if normal['final_closer_pairs']!=0 or nom['final_closer_pairs']!=0: errors.append('final_closer_pair')
    if not normal['common_prefix_min_step_all'] or not nom['common_prefix_min_step_all']: errors.append('common_prefix')
    classification = ('COVERAGE_NOT_TASK_PROGRESS_SCOPED' if not errors and normal['median_coverage_delta']>0 and nom['median_coverage_delta']>0 and normal['median_min_closer']<=0 and nom['median_min_closer']<=0 else 'DIAGNOSTIC_NOT_ESTABLISHED')
    out={'schema':'agent-interface/map01-task-progress-audit-v1','status':'PASS_AUDIT' if not errors else 'FAIL_AUDIT','classification':classification,'errors':errors,'hashes':hashes,'exit_linedef':ex,'normal':normal,'nomonsters':nom}
    print(json.dumps(out,indent=2,sort_keys=True))
    raise SystemExit(0 if not errors else 2)
if __name__=='__main__': main()
