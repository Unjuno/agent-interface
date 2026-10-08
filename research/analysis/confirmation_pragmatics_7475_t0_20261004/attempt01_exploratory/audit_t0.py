from __future__ import annotations
import copy, hashlib, json
from pathlib import Path
p=Path(__file__).resolve().parent
stim=json.loads((p/'stimuli.json').read_text(encoding='utf-8-sig'))
raw=json.loads((p/'candidate_raw.json').read_text(encoding='utf-8-sig'))
key=json.loads((p/'decision_key.json').read_text(encoding='utf-8-sig'))
errors=[]
source={c['id']:c for c in stim['cases']}
rows={}
for row in raw['cards']:
    rows.setdefault(row['case_id'],{})[row['variant']]=row
for cid,c in source.items():
    pair=rows.get(cid,{})
    if set(pair)!={'neutral','framed'}: errors.append(f'{cid}: missing/extra variants'); continue
    a,b=pair['neutral'],pair['framed']
    if a['displayed_facts']!=b['displayed_facts'] or a['displayed_facts']!=c['facts']:
        errors.append(f'{cid}: factual/layout/control fields differ')
    if a['framing_sentence']!=c['neutral'] or b['framing_sentence']!=c['framed'] or a['framing_sentence']==b['framing_sentence']:
        errors.append(f'{cid}: wording field not isolated')
    for r in (a,b):
        expected={'already_performed':False,'confirm_effect':c['facts']['on_confirm'],
          'decline_effect':'no action is dispatched','target':c['facts']['target'],
          'reversibility':c['facts']['reversibility']}
        if r['key']!=expected: errors.append(f'{cid}/{r["variant"]}: key contradicts facts')
        if r['displayed_facts']['status'].split(';')[0].lower() not in ('not sent','not replaced','not submitted'):
            errors.append(f'{cid}/{r["variant"]}: unexpected status')

def check(mutant):
    local=[]
    by={}
    for r in mutant['cards']: by.setdefault(r['case_id'],{})[r['variant']]=r
    for cid,c in source.items():
        pp=by.get(cid,{})
        if set(pp)!={'neutral','framed'}: local.append('pair cardinality'); continue
        x,y=pp['neutral'],pp['framed']
        if x['displayed_facts']!=y['displayed_facts'] or x['displayed_facts']!=c['facts']: local.append('fact/control mismatch')
        if x['framing_sentence']!=c['neutral'] or y['framing_sentence']!=c['framed']: local.append('wording mismatch')
        exp={'already_performed':False,'confirm_effect':c['facts']['on_confirm'],'decline_effect':'no action is dispatched','target':c['facts']['target'],'reversibility':c['facts']['reversibility']}
        if x['key']!=exp or y['key']!=exp: local.append('key mismatch')
    return local
controls={}
m=copy.deepcopy(raw); m['cards'][1]['displayed_facts']['target']='wrong destination'; controls['target_corruption_rejected']=bool(check(m))
m=copy.deepcopy(raw); m['cards'][0]['displayed_facts']['status']='Already sent.'; controls['status_corruption_rejected']=bool(check(m))
m=copy.deepcopy(raw); m['cards'][2]['displayed_facts']['buttons'].reverse(); controls['control_order_corruption_rejected']=bool(check(m))
result={'disposition':'PASS_METHOD_SCOPED' if not errors and all(controls.values()) else 'STOP_AUDIT',
 'baseline_pairs':len(source),'baseline_cards':len(raw['cards']),'baseline_errors':errors,
 'negative_controls':controls,'negative_controls_rejected':sum(controls.values()),
 'claim_boundary':'Stimulus-factor equivalence and key consistency only; no evidence about human interpretation or effect.',
 'human_data_collected':False,'dispatch_performed':False}
(p/'audit_result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
raise SystemExit(0 if result['disposition']=='PASS_METHOD_SCOPED' else 1)
