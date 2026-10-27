#!/usr/bin/env python3
"""Finite focused-observation byte-accounting candidate; never calls a GUI or input API."""
import base64, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
RUN='LABEL-CONTROL-AMBIGUITY-1998-T0-A02-20261009'
BASE='4758a95cd4a0aaa78e9cdc9d774f298d4ccf0e36'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load():
 f=json.loads((ROOT/'FREEZE.json').read_text())
 if f['allocation']!=RUN or f['base_commit']!=BASE: raise SystemExit('STOP_FREEZE_ID_OR_BASE')
 for n,h in f['source_sha256'].items():
  if sha(ROOT/n)!=h: raise SystemExit('STOP_SOURCE_HASH:'+n)
 return json.loads((ROOT/'design.json').read_text()),(ROOT/'source/frame.bin').read_bytes()
def canonical(obj): return json.dumps(obj,sort_keys=True,separators=(',',':')).encode('utf-8')
def full_payload(frame,source):
 m=frame['width']; n=frame['height']
 return {'schema':'focused-observation-payload-v1','kind':'FULL_FRAME','frame_id':frame['frame_id'],'epoch':frame['epoch'],'width':m,'height':n,'encoding':frame['encoding'],'pixels_b64':base64.b64encode(source).decode('ascii')}
def crop(source,width,bounds):
 x0,y0,x1,y1=bounds
 return b''.join(source[y*width+x0:y*width+x1] for y in range(y0,y1))
def refusal(req,frame):
 if req['reason']!='uncertain': return 'REASON_NOT_UNCERTAIN'
 if req['frame_id']!=frame['frame_id']: return 'STALE_FRAME_IDENTITY'
 if req['epoch']!=frame['epoch']: return 'STALE_EPOCH'
 if req['focus_state']!='active': return 'FOCUS_NOT_ACTIVE'
 if len(req['candidate_region_ids'])!=1 or req['candidate_region_ids'][0]!=req['region_id']: return 'AMBIGUOUS_REGION'
 x0,y0,x1,y1=req['bounds']
 if not (type(x0)is int and type(y0)is int and type(x1)is int and type(y1)is int and 0<=x0<x1<=frame['width'] and 0<=y0<y1<=frame['height']): return 'REGION_OUT_OF_BOUNDS'
 return None
def focused_payload(frame,req,source):
 x0,y0,x1,y1=req['bounds']; data=crop(source,frame['width'],req['bounds'])
 return {'schema':'focused-observation-payload-v1','kind':'FOCUSED_REGION','frame_id':frame['frame_id'],'epoch':frame['epoch'],'width':x1-x0,'height':y1-y0,'encoding':frame['encoding'],'region_id':req['region_id'],'bounds':req['bounds'],'reason':req['reason'],'pixels_b64':base64.b64encode(data).decode('ascii')}
def run(d,source):
 f=d['frame']; full=full_payload(f,source); full_size=len(canonical(full)); rows=[]
 for s in d['scenarios']:
  req=s['request']; why=refusal(req,f); focus=focused_payload(f,req,source) if why is None else None
  focus_size=len(canonical(focus)) if focus is not None else None
  if why is not None: decision='ABSTAIN_'+why; selected=full; selected_kind='FULL_FRAME'
  elif focus_size<full_size: decision='FOCUSED_REGION_SELECTED'; selected=focus; selected_kind='FOCUSED_REGION'
  else: decision='FULL_FRAME_NO_SIZE_GAIN'; selected=full; selected_kind='FULL_FRAME'
  rows.append({'case_id':s['case_id'],'request':req,'full_frame_payload':full,'full_frame_bytes':full_size,'focused_payload':focus,'focused_bytes':focus_size,'selected_kind':selected_kind,'selected_payload':selected,'selected_bytes':len(canonical(selected)),'bytes_saved_vs_full':full_size-len(canonical(selected)),'decision':decision})
 return {'schema':'1998-a02-payload-raw-v1','allocation':RUN,'base_commit':BASE,'case_count':len(rows),'rows':rows}
def main():
 d,source=load(); print(json.dumps(run(d,source),sort_keys=True,separators=(',',':')))
if __name__=='__main__': main()
