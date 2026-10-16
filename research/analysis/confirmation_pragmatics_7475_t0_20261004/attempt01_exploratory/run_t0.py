from __future__ import annotations
import json
from pathlib import Path
p=Path(__file__).resolve().parent
stim=json.loads((p/'stimuli.json').read_text(encoding='utf-8-sig'))
key=json.loads((p/'decision_key.json').read_text(encoding='utf-8-sig'))
rows=[]
for c in stim['cases']:
    f=c['facts']
    for variant in ('neutral','framed'):
        rows.append({
            'case_id':c['id'], 'variant':variant, 'framing_sentence':c[variant],
            'displayed_facts':f,
            'key':{
                'already_performed':key['questions']['already_performed'],
                'confirm_effect':f['on_confirm'], 'decline_effect':key['questions']['decline_effect'],
                'target':f['target'], 'reversibility':f['reversibility']
            }
        })
raw={'study_id':stim['study_id'],'candidate':'synthetic-card-render-model-v1','cards':rows,
     'human_data_collected':False,'dispatch_performed':False}
(p/'candidate_raw.json').write_text(json.dumps(raw,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(f"CANDIDATE_EXIT=0 cards={len(rows)} pairs={len(stim['cases'])} human_data=0 dispatch=0")
