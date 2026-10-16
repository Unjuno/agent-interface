from pathlib import Path
import json
p=Path(__file__).resolve().parent
facts=json.loads((p/'facts.json').read_text(encoding='utf-8-sig'))
key=json.loads((p/'answer_key.json').read_text(encoding='utf-8-sig'))
stim=json.loads((p/'stimuli.json').read_text(encoding='utf-8-sig'))
rows=[]
by={v['case_id']:v for v in stim['variants']}
for case in facts['cases']:
 v=by[case['id']]
 for variant in ('neutral','framed'):
  rows.append({'case_id':case['id'],'variant':variant,'framing_sentence':v[variant],
   'displayed_facts':case,
   'answer_key':{'already_performed':key['questions']['already_performed'],
    'decline_effect':key['questions']['decline_effect'],
    'confirm_effect':case['on_confirm'],'target':case['target'],'reversibility':case['reversibility']}})
raw={'cards':rows,'human_data_collected':False,'dispatch_performed':False}
(p/'candidate_raw.json').write_text(json.dumps(raw,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(f'CANDIDATE_EXIT=0 cards={len(rows)} pairs={len(facts["cases"])} human_data=0 dispatch=0')
