from __future__ import annotations
import json
from typing import Any
MAX_HINT_BYTES=512
MAX_HISTORY=3

def capture_coast_sample(event: dict[str,Any], previous_sequence: int) -> dict[str,Any]|None:
 if type(event) is not dict or event.get('event')!='typed_observation' or event.get('schema')!='doom-typed-observation-v1': return None
 if event.get('artifact_published') is not False or event.get('grants_input_authority') is not False: return None
 seq,cap=event.get('sequence'),event.get('capture_ns'); bind=event.get('pointer_binding'); signals=event.get('signals')
 if type(seq) is not int or seq<=previous_sequence or type(cap) is not int or cap<=0: return None
 if type(bind) is not dict or set(bind)!={'focus','surface','geometry'} or type(bind.get('geometry')) is not list or len(bind['geometry'])!=4: return None
 if type(event.get('frame_rgb_sha256')) is not str or len(event['frame_rgb_sha256'])!=64 or type(signals) is not dict or set(signals)!={'health','ammo'}: return None
 compact={}
 for name in ('health','ammo'):
  row=signals[name]
  if type(row) is not dict or row.get('signal_id')!=name or row.get('sequence')!=seq or row.get('capture_ns')!=cap or row.get('binding')!=bind or row.get('status')!='observed' or type(row.get('value')) is not int or row['value']<0: return None
  compact[name]={'status':'observed','value':row['value']}
 sample={'sequence':seq,'capture_ns':cap,'id':event.get('id'),'step':event.get('step'),'frame_rgb_sha256':event['frame_rgb_sha256'],'pointer_binding':bind,'signals':compact,'grants_input_authority':False,'task_success_verified':False}
 return sample if len(json.dumps(sample,separators=(',',':')).encode())<=MAX_HINT_BYTES else None

def reconcile_coast_sample(sample:dict, full:dict)->dict|None:
 if type(sample) is not dict or type(full) is not dict or full.get('event')!='observation' or full.get('exact') is not True: return None
 if any(sample.get(k)!=full.get(k) for k in ('id','step','sequence','capture_ns','pointer_binding','frame_rgb_sha256')): return None
 for name in ('health','ammo'):
  row=sample.get('signals',{}).get(name)
  if type(row) is not dict or row.get('status')!='observed' or type(row.get('value')) is not int: return None
 result={'sequence':sample['sequence'],'capture_ns':sample['capture_ns'],'health':sample['signals']['health']['value'],'ammo':sample['signals']['ammo']['value'],'reconciled_full_observation':True,'grants_input_authority':False,'task_success_verified':False}
 return result if len(json.dumps(result,separators=(',',':')).encode())<=MAX_HINT_BYTES else None

class CoastHistory:
 def __init__(self): self.pending=[]; self.reconciled=[]; self.last_sequence=0
 def observe_typed(self,event):
  sample=capture_coast_sample(event,self.last_sequence)
  if sample is None: return False
  self.last_sequence=sample['sequence'];self.pending.append(sample)
  if len(self.pending)>MAX_HISTORY: self.pending.pop(0)
  return True
 def observe_full(self,event):
  pending=[];matched=None
  for sample in self.pending:
   if sample['sequence']==event.get('sequence'): matched=reconcile_coast_sample(sample,event)
   else: pending.append(sample)
  self.pending=pending
  if matched is not None:
   self.reconciled.append(matched);self.reconciled=self.reconciled[-MAX_HISTORY:]
  return matched
 def prompt_context(self,current_full):
  if type(current_full) is not dict or current_full.get('event')!='observation' or current_full.get('exact') is not True: return {'current_sequence':None,'coast_history':[],'grants_input_authority':False}
  items=[dict(x) for x in self.reconciled if x['sequence']<current_full['sequence'] and x['capture_ns']<current_full['capture_ns']]
  return {'current_sequence':current_full['sequence'],'coast_history':items[-MAX_HISTORY:],'grants_input_authority':False}
