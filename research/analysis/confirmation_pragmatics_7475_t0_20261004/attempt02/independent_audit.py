from pathlib import Path
import copy,hashlib,json
p=Path(__file__).resolve().parent
read=lambda n:json.loads((p/n).read_text(encoding='utf-8-sig'))
facts=read('facts.json'); key=read('answer_key.json'); lock=read('PREWORDING_LOCK.json'); stim=read('stimuli.json'); raw=read('candidate_raw.json')
sha=lambda n:hashlib.sha256((p/n).read_bytes()).hexdigest()
errors=[]
if sha('facts.json')!=lock['facts_sha256']: errors.append('frozen facts hash mismatch')
if sha('answer_key.json')!=lock['answer_key_sha256']: errors.append('frozen answer key hash mismatch')
variants={v['case_id']:v for v in stim['variants']}
rows={}
for r in raw['cards']: rows.setdefault(r['case_id'],{})[r['variant']]=r
for c in facts['cases']:
 pair=rows.get(c['id'],{}); v=variants.get(c['id'])
 if v is None or set(pair)!={'neutral','framed'}: errors.append(f'{c["id"]}: incomplete pair'); continue
 a,b=pair['neutral'],pair['framed']
 if a['displayed_facts']!=c or b['displayed_facts']!=c or a['displayed_facts']!=b['displayed_facts']: errors.append(f'{c["id"]}: changed fact/layout/control')
 if a['framing_sentence']!=v['neutral'] or b['framing_sentence']!=v['framed'] or a['framing_sentence']==b['framing_sentence']: errors.append(f'{c["id"]}: wording mismatch')
 expected={'already_performed':False,'decline_effect':'no action is dispatched','confirm_effect':c['on_confirm'],'target':c['target'],'reversibility':c['reversibility']}
 if a['answer_key']!=expected or b['answer_key']!=expected: errors.append(f'{c["id"]}: key mismatch')

def audit(mut):
 es=[]; rr={}
 for r in mut['cards']:rr.setdefault(r['case_id'],{})[r['variant']]=r
 for c in facts['cases']:
  q=rr.get(c['id'],{})
  if set(q)!={'neutral','framed'}:es.append('pair cardinality');continue
  a,b=q['neutral'],q['framed']; v=variants[c['id']]
  if a['displayed_facts']!=c or b['displayed_facts']!=c:es.append('fact/control mismatch')
  if a['framing_sentence']!=v['neutral'] or b['framing_sentence']!=v['framed']:es.append('wording mismatch')
  exp={'already_performed':False,'decline_effect':'no action is dispatched','confirm_effect':c['on_confirm'],'target':c['target'],'reversibility':c['reversibility']}
  if a['answer_key']!=exp or b['answer_key']!=exp:es.append('key mismatch')
 return es
controls={}
m=copy.deepcopy(raw);m['cards'][0]['displayed_facts']['target']='other@example.invalid';controls['target_change_rejected']=bool(audit(m))
m=copy.deepcopy(raw);m['cards'][2]['displayed_facts']['status']='Already submitted';controls['status_change_rejected']=bool(audit(m))
m=copy.deepcopy(raw);m['cards'][4]['displayed_facts']['buttons'].reverse();controls['button_order_change_rejected']=bool(audit(m))
res={'disposition':'PASS_METHOD_SCOPED' if not errors and all(controls.values()) else 'STOP_AUDIT','pairs':len(facts['cases']),'cards':len(raw['cards']),'baseline_errors':errors,'negative_controls':controls,'negative_controls_rejected':sum(controls.values()),'prewording_lock_verified':not any('hash mismatch' in e for e in errors),'human_data_collected':False,'dispatch_performed':False,'claim_boundary':'Only fact/presentation equivalence and fixed-key consistency; no evidence about human interpretation, approval, authority, or action effects.'}
(p/'audit_result.json').write_text(json.dumps(res,indent=2)+'\n',encoding='utf-8')
print(json.dumps(res,indent=2))
raise SystemExit(0 if res['disposition']=='PASS_METHOD_SCOPED' else 1)
