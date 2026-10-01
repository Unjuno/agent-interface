import copy, json
from pathlib import Path

ROOT=Path(__file__).parent
m=json.loads((ROOT/'manifest.json').read_text())
controls=[]

def classify(x):
    terms=["top-down","topdown","geometric scaffold","depth map","side view","occupancy sketch","spatial scaffold"]
    explicit=sum(x['indexed_counts'][k] for k in terms)+x['delta_scan']['scaffold_term_hits']
    if x['indexed_to_main_added_files'] != x['delta_scan']['files_scanned']:
        return 'FAIL_INTEGRITY'
    if x['candidate_matched_pairs']:
        return 'PASS_RETAINED_GEOMETRIC_SCAFFOLD_IDENTIFIABLE_SCOPED' if explicit>0 else 'FAIL_INTEGRITY'
    return 'HOLD_NO_RETAINED_GEOMETRIC_SCAFFOLD_CONTRAST'

x=copy.deepcopy(m);x['delta_scan']['files_scanned']=27;controls.append({'name':'drop_delta_file','rejected':classify(x)=='FAIL_INTEGRITY'})
x=copy.deepcopy(m);x['candidate_matched_pairs']=[{'fake':True}];controls.append({'name':'invent_pair_without_scaffold','rejected':classify(x)=='FAIL_INTEGRITY'})
x=copy.deepcopy(m);x['indexed_counts']['top-down']=1;controls.append({'name':'keyword_without_pair_not_pass','rejected':classify(x)!='PASS_RETAINED_GEOMETRIC_SCAFFOLD_IDENTIFIABLE_SCOPED'})
out={'decision':'PASS_CORRUPTION_CONTROLS' if all(c['rejected'] for c in controls) else 'FAIL_CORRUPTION_CONTROLS','controls':controls}
(ROOT/'CORRUPTION.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,sort_keys=True))
if out['decision'].startswith('FAIL'): raise SystemExit(2)
