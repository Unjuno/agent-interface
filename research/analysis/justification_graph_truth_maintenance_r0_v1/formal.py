import argparse,random,json,hashlib
from pathlib import Path
BASE=[f'B{i}' for i in range(4)]
DER=[f'C{i}' for i in range(4)]
SEED=185020260919001
FORMAL_GRAPHS=5000
CONSTRUCTION_GRAPHS=80

def gen_graph(rng):
    g={}
    for i,c in enumerate(DER):
        parents=BASE+DER[:i]
        all_sets=[]
        # candidate singleton and pair antecedent sets
        for a in parents: all_sets.append((a,))
        for x in range(len(parents)):
            for y in range(x+1,len(parents)): all_sets.append((parents[x],parents[y]))
        rng.shuffle(all_sets)
        n=1+rng.randrange(min(3,len(all_sets)))
        # canonical unique justification sets
        chosen=[]
        for s in all_sets:
            fs=tuple(sorted(s))
            if fs not in chosen: chosen.append(fs)
            if len(chosen)==n: break
        g[c]=tuple(chosen)
    return g

def edges_rev(g):
    r={n:set() for n in BASE+DER}
    for c,js in g.items():
        for j in js:
            for p in j:r[p].add(c)
    return r

def full(g,mask):
    v={b:bool(mask>>i &1) for i,b in enumerate(BASE)}
    for c in DER:
        v[c]=any(all(v[p] for p in j) for j in g[c])
    return v

def cone(g,base):
    r=edges_rev(g);seen=set();stack=list(r[base])
    while stack:
        x=stack.pop()
        if x in seen:continue
        seen.add(x);stack.extend(r[x])
    return seen

def incremental(g,old,base,new_base):
    v=dict(old);v[base]=new_base;aff=cone(g,base)
    for c in DER:
        if c in aff:v[c]=any(all(v[p] for p in j) for j in g[c])
    return v,aff

def blind_invalidate(g,old,base,new_base):
    v=dict(old);v[base]=new_base
    if new_base:return v
    for c in cone(g,base):v[c]=False
    return v

def direct_child_only(g,old,base,new_base):
    v=dict(old);v[base]=new_base;r=edges_rev(g)
    for c in DER:
        if c in r[base]:v[c]=any(all(v[p] for p in j) for j in g[c])
    return v

def one_graph(g,stats):
    rev=edges_rev(g)
    for mask in range(16):
        old=full(g,mask)
        for bi,b in enumerate(BASE):
            new_val=not old[b]
            nm=mask ^ (1<<bi);truth=full(g,nm);inc,aff=incremental(g,old,b,new_val)
            stats['cases']+=1
            stats['incremental_full_mismatch']+=int(inc!=truth)
            outside=set(DER)-aff
            stats['outside_cone_changes']+=sum(old[n]!=truth[n] for n in outside)
            direct=direct_child_only(g,old,b,new_val)
            if direct!=truth:
                stats['direct_child_only_bad_cases']+=1
                # multi-hop if some wrong node isn't a direct child
                wrong={n for n in DER if direct[n]!=truth[n]}
                if any(n not in rev[b] for n in wrong):stats['multihop_witnesses']+=1
            if old[b] and not new_val:
                blind=blind_invalidate(g,old,b,new_val)
                over=sum((not blind[n]) and truth[n] for n in DER)
                if over:
                    stats['blind_overinvalid_cases']+=1;stats['blind_overinvalid_nodes']+=over
                    stats['alternative_survival_witnesses']+=1

def run(n):
    rng=random.Random(SEED);stats={'graphs':n,'cases':0,'incremental_full_mismatch':0,'outside_cone_changes':0,'blind_overinvalid_cases':0,'blind_overinvalid_nodes':0,'direct_child_only_bad_cases':0,'alternative_survival_witnesses':0,'multihop_witnesses':0}
    graph_digest=hashlib.sha256()
    for _ in range(n):
        g=gen_graph(rng);graph_digest.update(json.dumps(g,sort_keys=True,separators=(',',':')).encode());one_graph(g,stats)
    stats['graph_digest']=graph_digest.hexdigest();return stats

def directed():
    # Separate witnesses: OR-alternative survival and pure multi-hop propagation.
    g_alt={'C0':(('B0',),('B1',)),'C1':(('C0',),),'C2':(('B2',),),'C3':(('B3',),)}
    old_a=full(g_alt,0b0011); truth_a=full(g_alt,0b0010); inc_a,aff_a=incremental(g_alt,old_a,'B0',False); blind_a=blind_invalidate(g_alt,old_a,'B0',False)
    g_chain={'C0':(('B0',),),'C1':(('C0',),),'C2':(('C1',),),'C3':(('B2',),)}
    old_c=full(g_chain,0b0001); truth_c=full(g_chain,0b0000); inc_c,aff_c=incremental(g_chain,old_c,'B0',False); direct_c=direct_child_only(g_chain,old_c,'B0',False)
    return {'incremental_exact':inc_a==truth_a and inc_c==truth_c,'alt_support_survives':truth_a['C0'] and not blind_a['C0'],'multihop_direct_child_fails':direct_c!=truth_c,'outside_unchanged':all(old_a[n]==truth_a[n] for n in set(DER)-aff_a) and all(old_c[n]==truth_c[n] for n in set(DER)-aff_c)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--construction',action='store_true');ap.add_argument('--output',required=True);a=ap.parse_args();o=Path(a.output);assert not o.exists();n=CONSTRUCTION_GRAPHS if a.construction else FORMAL_GRAPHS;st=run(n);dc=directed();corrupt={'missing_reverse_edge_detectable':st['multihop_witnesses']>0,'alt_support_required':st['blind_overinvalid_cases']>0,'topology_matters':st['direct_child_only_bad_cases']>0,'outside_fabrication_rejected':st['outside_cone_changes']==0};good=(st['incremental_full_mismatch']==0 and st['outside_cone_changes']==0 and st['blind_overinvalid_cases']>0 and st['direct_child_only_bad_cases']>0 and st['alternative_survival_witnesses']>0 and st['multihop_witnesses']>0 and all(dc.values()) and all(corrupt.values()))
    r={'construction':a.construction,'seed':SEED,'stats':st,'directed':dc,'corruptions':corrupt,'formal_invocations':0 if a.construction else 1,'reruns':0,'replacements':0,'tuning':0,'decision':('CONSTRUCTION_PASS' if a.construction and good else ('PASS_JUSTIFICATION_GRAPH_INCREMENTAL_TRUTH_MAINTENANCE_SCOPED' if good else 'FAIL_INTEGRITY'))};raw=json.dumps(r,sort_keys=True,separators=(',',':')).encode();r['digest']=hashlib.sha256(raw).hexdigest();o.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__':main()
