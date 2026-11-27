#!/usr/bin/env python3
"""Independent raw-only audit for focused payload size; no candidate imports."""
import base64,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
RUN='LABEL-CONTROL-AMBIGUITY-1998-T0-A02-20261009'; BASE='4758a95cd4a0aaa78e9cdc9d774f298d4ccf0e36'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load():
 f=json.loads((ROOT/'FREEZE.json').read_text())
 if f['allocation']!=RUN or f['base_commit']!=BASE: raise ValueError('freeze identity/base mismatch')
 for n,h in f['source_sha256'].items():
  if sha(ROOT/n)!=h: raise ValueError('frozen source mismatch:'+n)
 d=json.loads((ROOT/'design.json').read_text()); pix=(ROOT/'source/frame.bin').read_bytes()
 if sha(ROOT/'source/frame.bin')!=f['source_sha256']['source/frame.bin']: raise ValueError('frame hash mismatch')
 return d,pix
def enc(obj): return json.dumps(obj,sort_keys=True,separators=(',',':')).encode('utf-8')
def full_oracle(frame,pix):
 return {'schema':'focused-observation-payload-v1','kind':'FULL_FRAME','frame_id':frame['frame_id'],'epoch':frame['epoch'],'width':frame['width'],'height':frame['height'],'encoding':frame['encoding'],'pixels_b64':base64.b64encode(pix).decode('ascii')}
def refusal(req,frame):
 if req['reason']!='uncertain': return 'REASON_NOT_UNCERTAIN'
 if req['frame_id']!=frame['frame_id']: return 'STALE_FRAME_IDENTITY'
 if req['epoch']!=frame['epoch']: return 'STALE_EPOCH'
 if req['focus_state']!='active': return 'FOCUS_NOT_ACTIVE'
 if len(req['candidate_region_ids'])!=1 or req['candidate_region_ids'][0]!=req['region_id']: return 'AMBIGUOUS_REGION'
 x0,y0,x1,y1=req['bounds']
 if any(type(v)is not int for v in req['bounds']) or not(0<=x0<x1<=frame['width'] and 0<=y0<y1<=frame['height']): return 'REGION_OUT_OF_BOUNDS'
 return None
def expected_rows(d,pix):
 f=d['frame']; full=full_oracle(f,pix); full_size=len(enc(full)); out=[]
 for s in d['scenarios']:
  r=s['request']; why=refusal(r,f); focused=None
  if why is None:
   x0,y0,x1,y1=r['bounds']; crop=b''.join(pix[y*f['width']+x0:y*f['width']+x1] for y in range(y0,y1))
   focused={'schema':'focused-observation-payload-v1','kind':'FOCUSED_REGION','frame_id':f['frame_id'],'epoch':f['epoch'],'width':x1-x0,'height':y1-y0,'encoding':f['encoding'],'region_id':r['region_id'],'bounds':r['bounds'],'reason':r['reason'],'pixels_b64':base64.b64encode(crop).decode('ascii')}
  fsize=len(enc(focused)) if focused is not None else None
  if why: decision='ABSTAIN_'+why; selected=full; skind='FULL_FRAME'
  elif fsize<full_size: decision='FOCUSED_REGION_SELECTED'; selected=focused; skind='FOCUSED_REGION'
  else: decision='FULL_FRAME_NO_SIZE_GAIN'; selected=full; skind='FULL_FRAME'
  out.append({'case_id':s['case_id'],'request':r,'full_frame_payload':full,'full_frame_bytes':full_size,'focused_payload':focused,'focused_bytes':fsize,'selected_kind':skind,'selected_payload':selected,'selected_bytes':len(enc(selected)),'bytes_saved_vs_full':full_size-len(enc(selected)),'decision':decision})
 return out
def validate(raw,d,pix):
 e=[]; expected=expected_rows(d,pix); rows=raw.get('rows') if isinstance(raw,dict) else None
 if not isinstance(raw,dict) or raw.get('schema')!='1998-a02-payload-raw-v1' or raw.get('allocation')!=RUN or raw.get('base_commit')!=BASE: e.append('identity')
 if not isinstance(rows,list) or raw.get('case_count')!=len(rows or []) or len(rows or [])!=len(expected): e.append('coverage'); rows=rows if isinstance(rows,list) else []
 for i,want in enumerate(expected):
  if i>=len(rows): break
  if rows[i]!=want: e.append('case_mismatch:'+want['case_id'])
 return e,expected
def main():
 d,pix=load(); raw=json.loads((ROOT/'results/candidate_raw.json').read_text()); errors,exp=validate(raw,d,pix)
 rows=raw.get('rows',[]); valid=[r for r in exp if r['focused_payload'] is not None]; invalid=[r for r in exp if r['focused_payload'] is None]
 positive=[r for r in valid if r['focused_bytes']<r['full_frame_bytes']]; fallback=[r for r in valid if r['selected_kind']=='FULL_FRAME']
 mutations=[]
 def try_mutation(name,fn):
  x=json.loads(json.dumps(raw)); fn(x); mutations.append({'name':name,'rejected':bool(validate(x,d,pix)[0])})
 try_mutation('focus_pixel_corruption',lambda x:x['rows'][0]['focused_payload'].__setitem__('pixels_b64','AAAA'))
 try_mutation('stale_epoch_focus_admitted',lambda x:x['rows'][9].__setitem__('selected_kind','FOCUSED_REGION'))
 try_mutation('region_identity_swapped',lambda x:x['rows'][0]['focused_payload'].__setitem__('region_id','other'))
 try_mutation('out_of_bounds_focus_admitted',lambda x:x['rows'][13].__setitem__('decision','FOCUSED_REGION_SELECTED'))
 try_mutation('no_gain_focus_selected',lambda x:x['rows'][7].__setitem__('selected_kind','FOCUSED_REGION'))
 try_mutation('byte_count_tampered',lambda x:x['rows'][0].__setitem__('selected_bytes',1))
 rejected=sum(m['rejected'] for m in mutations); size_gain=len(positive)>0
 method='PASS_METHOD_SCOPED' if not errors and rejected==len(mutations) and len(valid)==9 and len(invalid)==5 and all(r['decision'].startswith('ABSTAIN_') for r in invalid) and all(r['selected_kind']=='FOCUSED_REGION' for r in positive) and all(r['selected_kind']=='FULL_FRAME' for r in fallback) else 'FAIL_METHOD'
 status='PASS_FOCUSED_PAYLOAD_REDUCTION_SCOPED' if method=='PASS_METHOD_SCOPED' and size_gain else 'HOLD_NO_SIZE_GAIN' if method=='PASS_METHOD_SCOPED' else 'FAIL_METHOD'
 out={'schema':'1998-a02-payload-audit-v1','allocation':RUN,'status':status,'method_status':method,'decision':'SUPPORT_FOR_FOCUSED_PAYLOAD_REDUCTION_SCOPED' if status=='PASS_FOCUSED_PAYLOAD_REDUCTION_SCOPED' else status,'errors':errors,'case_count':len(exp),'valid_requests':len(valid),'invalid_requests':len(invalid),'focused_payload_smaller_cases':[r['case_id'] for r in positive],'full_frame_fallback_no_gain_cases':[r['case_id'] for r in fallback],'full_frame_total_bytes':sum(r['full_frame_bytes'] for r in exp),'selected_total_bytes':sum(r['selected_bytes'] for r in exp),'selected_total_bytes_saved':sum(r['bytes_saved_vs_full'] for r in exp),'max_single_case_bytes_saved':max(r['bytes_saved_vs_full'] for r in exp),'mutation_controls':{'rejected':rejected,'total':len(mutations),'results':mutations},'invocations':{'candidate':1,'auditor':1,'retries':0},'scope':'Synthetic serialized-byte accounting only; no token, latency, GUI, model, or task effect claim.'}
 print(json.dumps(out,sort_keys=True,indent=2)); return 0 if method=='PASS_METHOD_SCOPED' else 1
if __name__=='__main__': raise SystemExit(main())
