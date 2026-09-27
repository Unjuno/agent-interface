import json, pathlib, sys
root=pathlib.Path(__file__).parent
d=json.loads((root/'ledger.json').read_text())
errs=[]
ids={f['id'] for f in d['families']}
adm=[]
for p in d['candidate_pairs']:
    if p['left'] not in ids or p['right'] not in ids: errs.append(p['id']+':ref')
    allpass=all(v=='PASS' for v in p['gates'].values())
    if allpass: adm.append(p['id'])
    if allpass != bool(p['admissible']): errs.append(p['id']+':label')
    if p['gates']['presentation_differs_only']!='FAIL': errs.append(p['id']+':unexpected_presentation_gate')
if len(d['families'])<3: errs.append('family_count')
if any(f['presentation']!='packed_temporal_sheet' for f in d['families']): errs.append('presentation')
if d['search_scope_findings']['matched_separate_frames_arm']!='NOT_FOUND_IN_SEARCH_SCOPE': errs.append('separate_search')
out={'pass':not errs,'errors':errs,'metrics':{'families':len(d['families']),'candidate_pairs':len(d['candidate_pairs']),'admissible_pairs':len(adm)}}
(root/'INDEPENDENT_AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True)); sys.exit(0 if out['pass'] else 4)
