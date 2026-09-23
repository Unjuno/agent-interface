"""Scoped lossy focus-decision view; full event reply remains authoritative."""
import hashlib,json

def build(reply,target_focus):
 records=reply['records']
 terminals=[e for e in records if e.get('event')=='terminal']
 if len(terminals)!=1:raise ValueError('one terminal required')
 terminal=terminals[0];identifier=terminal['id']
 observations=[e for e in records if e.get('event')=='observation' and e.get('id')==identifier]
 if not observations:raise ValueError('matching observation required')
 observation=max(observations,key=lambda e:e['sequence'])
 return {'format':'focus-decision-view-v1','scope':'lossy historical focus-decision view only; consult full reply for other questions',
 'source_sha256':hashlib.sha256(json.dumps(reply,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
 'action_id':identifier,'cursor':reply['cursor'],'target_focus':target_focus,
 'terminal':{k:terminal[k] for k in ('status','steps_completed','decision_reason','release')},
 'observation':{k:observation[k] for k in ('sequence','pointer_binding','input_focus_before','input_focus_after','input_state_after')},
 'input_authority':'none; new intent and runtime admission required'}
