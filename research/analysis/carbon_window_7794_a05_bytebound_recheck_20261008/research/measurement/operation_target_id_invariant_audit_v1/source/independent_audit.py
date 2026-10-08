import json,sys
from collections import defaultdict

def sig_full(r):return json.dumps(r['candidate_input'],sort_keys=True,separators=(',',':'))
def sig_inv(r):
 p=r['candidate_input']; x={'intent_id':p['intent_id'],'state_epoch':p['state_epoch'],'binding_id':p['binding_id'],'allowed_operations':p['allowed_operations'],'payload_ref_present':p['payload_ref_present'],'candidates':[{'role':c['role'],'ops':c['ops']} for c in p['candidates']]}
 return json.dumps(x,sort_keys=True,separators=(',',':'))
def norm(r):
 idx={c['id']:i for i,c in enumerate(r['candidate_input']['candidates'])}; out=[]
 for d in r['acceptable']:
  x={'op':d['op']}
  if 'reason' in d:x['reason']=d['reason']
  if 'payload_ref' in d:x['payload_ref_present']=True
  if 'target' in d:
   if d['target'] not in idx:raise ValueError('missing target')
   x['target_slot']=idx[d['target']]
  out.append(json.dumps(x,sort_keys=True,separators=(',',':')))
 return tuple(sorted(out))
def main(corpus,result):
 rows=json.load(open(corpus)); res=json.load(open(result)); full=defaultdict(set); inv=defaultdict(set); ids=defaultdict(list);errors=[]
 for r in rows:
  y=norm(r);full[sig_full(r)].add(y);s=sig_inv(r);inv[s].add(y);ids[s].append(r['row_id'])
 fc=sum(len(v)>1 for v in full.values()); ic=sum(len(v)>1 for v in inv.values())
 if fc!=res['full_conflicting_groups']:errors.append('full_count')
 if ic!=res['id_invariant_conflicting_groups']:errors.append('invariant_count')
 if res['parent_corpus_digest_sha256']!=res['parent_digest_expected']:errors.append('parent_digest')
 if res['rows']!=96 or res['primary_invocations']!=1 or res['reruns']!=0:errors.append('shape')
 if ic<1 or res['decision']!='HOLD_ID_INVARIANT_REPRESENTATION_ALIAS':errors.append('decision')
 if res['model_calls'] or res['gui_actions'] or res['task_input_actions']:errors.append('actions')
 print(json.dumps({'pass':not errors,'errors':errors,'full_conflicting_groups':fc,'id_invariant_conflicting_groups':ic,'conflicting_row_groups':sorted([sorted(ids[k]) for k,v in inv.items() if len(v)>1])},sort_keys=True));sys.exit(bool(errors))
if __name__=='__main__':main(*sys.argv[1:])
