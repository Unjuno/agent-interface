from itertools import combinations, product
import argparse,json,hashlib
from pathlib import Path
S=('B0','B1','B2')
JS=tuple([(x,) for x in S]+list(combinations(S,2)))
# current state per support relative to commit value/version
ST=('SAME_FALSE','SAME_TRUE','CHANGED_FALSE','CHANGED_TRUE')

def val(state): return state.endswith('TRUE')
def same(state): return state.startswith('SAME_')
def families():
    for mask in range(1,1<<len(JS)):
        yield tuple(JS[i] for i in range(len(JS)) if mask>>i & 1)

def sat(j,vals): return all(vals[x] for x in j)
def commit_sets(fam,cmask):
    vals={b:bool(cmask>>i &1) for i,b in enumerate(S)}
    return tuple(j for j in fam if sat(j,vals))
def cand(recorded,current):
    return any(all(same(current[x]) and val(current[x]) for x in j) for j in recorded)
def oracle(recorded,current):
    # independently quantified: exists recorded commit justification for which every member preserved semantic version and remains true
    for j in recorded:
        ok=True
        for x in j:
            st=current[x]
            if not st.startswith('SAME_') or not st.endswith('TRUE'): ok=False; break
        if ok:return True
    return False
def current_truth(fam,current): return any(all(val(current[x]) for x in j) for j in fam)
def all_committed_supports_current(recorded,current):
    u=set(x for j in recorded for x in j)
    return bool(recorded) and all(same(current[x]) and val(current[x]) for x in u)
def run(limit_families=None):
    stats={'families':0,'rows':0,'mismatch':0,'candidate_safe':0,'stale_all_committed_safe':0,'newly_true_uncommitted_safe':0,'surviving_committed_alt_safe':0,'sticky_unsafe':0,'current_truth_only_unsafe':0,'all_support_false_reject':0,'safe_without_witness':0}
    for fi,fam in enumerate(families()):
        if limit_families is not None and fi>=limit_families:break
        stats['families']+=1
        for cmask in range(8):
            rec=commit_sets(fam,cmask)
            if not rec:continue
            for sts in product(ST,repeat=3):
                cur=dict(zip(S,sts)); truth=current_truth(fam,cur); c=cand(rec,cur); o=oracle(rec,cur);stats['rows']+=1;stats['mismatch']+=int(c!=o);stats['candidate_safe']+=int(c)
                alive=[j for j in rec if all(same(cur[x]) and val(cur[x]) for x in j)]
                if c and not alive:stats['safe_without_witness']+=1
                if not alive:stats['stale_all_committed_safe']+=int(c);stats['sticky_unsafe']+=1
                # unsafe current-truth-only exactly when current truth is true but no recorded justification remains current
                if truth and not alive:stats['current_truth_only_unsafe']+=1
                # newly true justification that wasn't satisfied/recorded at commit, with no recorded path alive
                newly=[j for j in fam if j not in rec and all(val(cur[x]) for x in j)]
                if newly and not alive:stats['newly_true_uncommitted_safe']+=int(c)
                # alternative committed path survives while at least one other committed path is stale
                if alive and any(j not in alive for j in rec):
                    stats['surviving_committed_alt_safe']+=int(c)
                    stats['all_support_false_reject']+=int(not all_committed_supports_current(rec,cur))
    return stats

def directed():
    # fam has two alternatives B0 and B1; both true at commit. Later B0 changes false, B1 remains same true => safe via B1.
    fam=(('B0',),('B1',));rec=commit_sets(fam,0b011);cur={'B0':'CHANGED_FALSE','B1':'SAME_TRUE','B2':'SAME_FALSE'}
    a=cand(rec,cur) and not all_committed_supports_current(rec,cur)
    # B0 false at commit, B1 true at commit; later B1 stale false, B0 changed true. Claim currently true but no committed path current => unsafe.
    rec2=commit_sets(fam,0b010);cur2={'B0':'CHANGED_TRUE','B1':'CHANGED_FALSE','B2':'SAME_FALSE'}
    b=(not cand(rec2,cur2)) and current_truth(fam,cur2)
    # all commit paths stale => sticky comparator unsafe
    c=(not cand(rec2,cur2)) and bool(rec2)
    return {'surviving_alt_admits':a,'newly_true_uncommitted_blocks':b,'sticky_commit_blocks':c}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--construction',action='store_true');ap.add_argument('--output',required=True);a=ap.parse_args();p=Path(a.output);assert not p.exists();st=run(10 if a.construction else None);dc=directed();cor={'recorded_version_mutation_blocks':dc['newly_true_uncommitted_blocks'],'stale_one_alt_preserves_other':dc['surviving_alt_admits'],'stale_all_blocks':dc['sticky_commit_blocks'],'current_truth_not_authority':st['current_truth_only_unsafe']>0};good=(st['mismatch']==0 and st['stale_all_committed_safe']==0 and st['newly_true_uncommitted_safe']==0 and st['surviving_committed_alt_safe']>0 and st['sticky_unsafe']>0 and st['current_truth_only_unsafe']>0 and st['all_support_false_reject']>0 and st['safe_without_witness']==0 and all(dc.values()) and all(cor.values()))
 r={'construction':a.construction,'stats':st,'directed':dc,'corruptions':cor,'formal_invocations':0 if a.construction else 1,'reruns':0,'replacements':0,'tuning':0,'decision':('CONSTRUCTION_PASS' if a.construction and good else ('PASS_JUSTIFICATION_BOUND_ACTION_SAFE_SCOPED' if good else 'FAIL_INTEGRITY'))};raw=json.dumps(r,sort_keys=True,separators=(',',':')).encode();r['digest']=hashlib.sha256(raw).hexdigest();p.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__':main()
