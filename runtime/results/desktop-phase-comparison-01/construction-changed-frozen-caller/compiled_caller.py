"""Comparison-caller composition of existing graph and actual public feedback.

No new graph runtime, authority, model or persisted-effect oracle.
"""
import json,time
from pathlib import Path
from runtime.cli_v1.review import present_result
from delivered_capture import DeliveredCapture
from runtime.guarded_x11_v1.bridge import NativeHandleBridge

class ComparisonBridge(NativeHandleBridge):
 """Shorten the existing action lease; never extend adapter authorization."""
 def keyboard(self,alias,offset,*,tail,expires_at_ns=None):
  deadline=time.monotonic_ns()+2_000_000_000
  if expires_at_ns is not None:deadline=min(deadline,expires_at_ns)
  return super().keyboard(alias,offset,tail=tail,expires_at_ns=deadline)


def present_native(bridge,selected,*,compact=False):
 state=DeliveredCapture()
 try:
  raw=json.loads((bridge.out/('public-observation-'+selected['observation_id']+'.json')).read_text())
  if raw.get('observation_id')!=selected['observation_id'] or raw.get('observation')!=selected['native']:raise ValueError('selected/raw capture identity mismatch')
  shown=present_result(raw,bridge.out,compact=compact,report_refs=compact)
  return raw,shown,state.accept(raw,shown)
 except Exception as error:
  return None,{'image':None,'image_status':'needs_review','authority':'none','image_error':repr(error)},None

def run(bridge,owner,ground,regions,out,*,repair=False,compact=False):
 from methods import run as graph_run
 out=Path(out);out.mkdir(exist_ok=False)
 started=time.monotonic_ns();alias='sheet_repaired' if repair else 'sheet_context'
 box=ground['box'];point=[box[0]+(box[2]-box[0])//2,box[1]+(box[3]-box[1])//2]
 minted=bridge.mint_reference(alias,bridge.sequence,point,region_size=(box[2]-box[0],box[3]-box[1]))
 refs={'sheet_context':{'offset':minted['offset'],'box':box,'pixels':ground['pixels']}}
 result=graph_run(bridge,refs,regions,target_alias=alias,reading_directory=out)
 receipt=result['receipt'];prefix=[t['action'] for t in receipt['transitions'] if t.get('release_verified') is True]
 source=None;shown=None;native=None
 # A completed Save needs the same actual read-only public target inspection.
 # The retained execution is the original adapter row, not a synthetic dispatch.
 if prefix and prefix[-1]=='save':
  transition=receipt['transitions'][-1]
  execution=json.loads((bridge.out/(transition['effect_ref']+'.json')).read_text())
  owner.dispatch_attempted=True
  post=owner.inspect_after_dispatch(execution,'app',screen_region=[0,0,1280,800],capture_directory=str(out/'images'),wait_ms=100)
  (out/'post-inspection.json').write_text(json.dumps(post,indent=2)+'\n')
  if post.get('error') is None and post.get('observation_report',{}).get('status')=='returned':
   source=post['observation_report'];shown=present_result(source,out,compact=compact,report_refs=compact);native=DeliveredCapture().accept(source,shown)
 else:
  selected=bridge.history.get(bridge.sequence)
  if selected:source,shown,native=present_native(bridge,selected[0],compact=compact)
 if shown is None:shown={'image':None,'image_status':'needs_review','authority':'none'}
 observations=receipt.get('observations',[])
 refused_changed=(not receipt['transitions'] and bool(observations) and observations[-1].get('predicates',{}).get('present') is False)
 row={'compiled_result':result,'outcome':receipt['outcome'],'reason':receipt['reason'],'confirmed_completed_inputs':prefix,
      'changed_dependency_refused':refused_changed,'task_success':None,'replay_allowed':False,'started_ns':started,'ended_ns':time.monotonic_ns(),'final_capture':native}
 (out/'receipt.json').write_text(json.dumps(row,indent=2)+'\n')
 shown['method_receipt']=row
 return row,source,shown,native
