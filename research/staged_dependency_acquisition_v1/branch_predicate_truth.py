import itertools, json, platform
from pathlib import Path

initial_values=[-3,-2,-1,0,1,2,3]
current_values=list(range(-5,6))
methods=['no_branch_revalidate','exact_value_revalidate','predicate_truth_revalidate']
counts={m:{'stale_execute':0,'false_reject':0,'correct_execute':0,'correct_reject':0} for m in methods}
rows=[]
for x0,x1,selected_guard in itertools.product(initial_values,current_values,[False,True]):
    truth0=x0>=0
    truth1=x1>=0
    selected='A' if truth0 else 'B'
    valid=(truth1==truth0 and selected_guard)
    decisions={
      'no_branch_revalidate': selected_guard,
      'exact_value_revalidate': selected_guard and x1==x0,
      'predicate_truth_revalidate': selected_guard and truth1==truth0,
    }
    for m,execute in decisions.items():
        if execute and not valid:counts[m]['stale_execute']+=1
        elif not execute and valid:counts[m]['false_reject']+=1
        elif execute:counts[m]['correct_execute']+=1
        else:counts[m]['correct_reject']+=1
    rows.append({'x0':x0,'x1':x1,'selected':selected,'selected_guard':selected_guard,
                 'branch_truth0':truth0,'branch_truth1':truth1,'valid':valid,'decisions':decisions})
summary={'schema':'branch-predicate-truth-revalidation-v1','states':len(rows),
         'environment':{'python':platform.python_version(),'platform':platform.platform()},'methods':counts}
assert counts['predicate_truth_revalidate']['stale_execute']==0 and counts['predicate_truth_revalidate']['false_reject']==0
assert counts['no_branch_revalidate']['stale_execute']>0
assert counts['exact_value_revalidate']['false_reject']>0
summary['decision']='RETAIN_SEMANTIC_BRANCH_PREDICATE_REVALIDATION'
Path(__file__).with_name('branch_predicate_truth_summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps(summary,indent=2,sort_keys=True))
