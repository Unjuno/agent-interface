"""Distinct construction03 run with transient-only Escape and pre-dispatch gates."""
import asyncio,subprocess,time
from pathlib import Path
import runner as predecessor
predecessor.OUT=Path('/evidence/construction03')

async def sequence_v3(wid):
 O=predecessor.OUT;E=predecessor.ENV;t={'calls':[],'decision':'HOLD_INCOMPLETE','main_window_id':wid,'geometry_before':{},'geometry_after':{},'stale_dispatch':{},'fresh_dispatch':{},'inspect':{},'review':{}}
 params=predecessor.StdioServerParameters(command='python3',args=['-m','runtime.cli_v1.mcp_server','--targets',str(O/'targets.json'),'--output-directory',str(O/'server-receipts'),'--display',predecessor.DISPLAY,'--session-mode','persistent-x11'],env=E,cwd='/opt/importroot')
 async with predecessor.stdio_client(params) as (rd,wr):
  async with predecessor.ClientSession(rd,wr) as c:
   await c.initialize();t['tools']=sorted(x.name for x in (await c.list_tools()).tools)
   q=subprocess.run(['xdotool','search','--onlyvisible','--name','Tip of the Day'],env=E,text=True,capture_output=True);tips=[int(x) for x in q.stdout.splitlines() if x.strip().isdigit()];t['tip_windows_before_escape']=tips;t['dismissal']=[]
   for tid in tips:
    act=subprocess.run(['xdotool','windowactivate','--sync',str(tid)],env=E,text=True,capture_output=True)
    key=subprocess.run(['xdotool','key','--clearmodifiers','Escape'],env=E,text=True,capture_output=True)
    t['dismissal'].append({'window_id':tid,'activate_rc':act.returncode,'escape_rc':key.returncode,'escape_stderr':key.stderr})
   time.sleep(.4);t['tip_windows_after_escape']=sorted(w for w in predecessor.windows() if 'Tip of the Day' in predecessor.identify(w)['properties'])
   # Keep process/XID identity explicit and stop if WM_DELETE/Tip handling destroyed the root.
   try:g0=predecessor.identify(wid)['geometry']
   except Exception as e:
    t['root_after_tip_escape_error']=repr(e);q=await c.call_tool('interface_close',{});t['close']=predecessor.record(O/'mcp/01-close-root-lost.json',q);return t
   a=subprocess.run(['xdotool','windowactivate','--sync',str(wid)],env=E,text=True,capture_output=True);t['activate_root']={'returncode':a.returncode,'stderr':a.stderr}
   q=await c.call_tool('interface_observe',{'target':'calc','frame':'window_client','region':[0,0,160,120]});p=predecessor.record(O/'mcp/01-observe-before.json',q);t['observe_before']=p;t['initial_session']=p.get('session');t['calls'].append({'operation':'observe','call_id':p.get('call_id')})
   if p.get('status')!='returned':
    q=await c.call_tool('interface_close',{});t['close']=predecessor.record(O/'mcp/02-close-observe-stop.json',q);t['decision']='STOP_INITIAL_OBSERVATION_FAILED_BEFORE_GEOMETRY';return t
   t['geometry_before']=g0
   u=subprocess.run(['wmctrl','-ir',str(wid),'-b','remove,maximized_vert,maximized_horz'],env=E,text=True,capture_output=True);t['unmaximize']={'returncode':u.returncode,'stdout':u.stdout,'stderr':u.stderr}
   m=subprocess.run(['xdotool','windowmove','--sync',str(wid),'80','80'],env=E,text=True,capture_output=True);t['move_rc']=m.returncode
   z=subprocess.run(['xdotool','windowsize','--sync',str(wid),'1280','760'],env=E,text=True,capture_output=True);t['resize']={'returncode':z.returncode,'stderr':z.stderr}
   time.sleep(.5)
   try:t['geometry_after']=predecessor.identify(wid)['geometry']
   except Exception as e:t['geometry_after_error']=repr(e);t['geometry_after']={}
   t['geometry_changed']=(t['geometry_after'].get('WIDTH')!=g0.get('WIDTH') and t['geometry_after'].get('HEIGHT')!=g0.get('HEIGHT'))
   if not t['geometry_changed']:
    q=await c.call_tool('interface_close',{});t['close']=predecessor.record(O/'mcp/02-close-geometry-stop.json',q);t['decision']='HOLD_GEOMETRY_NOT_CHANGED_STOP_BEFORE_DISPATCH';return t
   q=await c.call_tool('interface_observe',{'target':'calc','frame':'window_client','region':[0,0,160,120]});p=predecessor.record(O/'mcp/02-observe-after.json',q);t['observe_after']=p;t['calls'].append({'operation':'observe','call_id':p.get('call_id')})
   if p.get('status')!='returned':
    q=await c.call_tool('interface_close',{});t['close']=predecessor.record(O/'mcp/03-close-after-observe-stop.json',q);t['decision']='STOP_POST_RESIZE_OBSERVATION_FAILED';return t
   a=subprocess.run(['xdotool','windowactivate','--sync',str(wid)],env=E,text=True,capture_output=True);t['reactivate_root']={'returncode':a.returncode,'stderr':a.stderr}
   q=await c.call_tool('interface_inspect_target',{'target':'calc','screen_region':[0,0,1500,900]});p=predecessor.record(O/'mcp/03-inspect-root.json',q);t['inspect']=p;t['calls'].append({'operation':'inspect_target','call_id':p.get('call_id')})
   if p.get('status')!='needs_review' or not p.get('review_id') or p.get('evidence',{}).get('window_id')!=wid:
    q=await c.call_tool('interface_close',{});t['close']=predecessor.record(O/'mcp/04-close-inspect-stop.json',q);t['decision']='HOLD_INSPECT_DID_NOT_BIND_MAIN_ROOT_STOP_BEFORE_DISPATCH';return t
   q=await c.call_tool('interface_review_target',{'target':'calc','window_id':wid,'review_id':p['review_id']});p=predecessor.record(O/'mcp/04-review-root.json',q);t['review']=p;t['calls'].append({'operation':'review_target','call_id':p.get('call_id')})
   if p.get('status')!='target_reviewed' or p.get('binding_revision')!=2:
    q=await c.call_tool('interface_close',{});t['close']=predecessor.record(O/'mcp/05-close-review-stop.json',q);t['decision']='HOLD_REVIEW_DID_NOT_ADVANCE_STOP_BEFORE_DISPATCH';return t
   q=await c.call_tool('interface_dispatch',{'program':predecessor.program('stale-geometry-binding',2,1,'F6'),'current_observation_seq':2,'current_binding_revision':2});t['stale_dispatch']=predecessor.record(O/'mcp/05-stale-binding.json',q);t['calls'].append({'operation':'dispatch','call_id':t['stale_dispatch'].get('call_id')})
   q=await c.call_tool('interface_dispatch',{'program':predecessor.program('fresh-geometry-binding',2,2,'ESC'),'current_observation_seq':2,'current_binding_revision':2});t['fresh_dispatch']=predecessor.record(O/'mcp/06-fresh-neutral.json',q);t['calls'].append({'operation':'dispatch','call_id':t['fresh_dispatch'].get('call_id')})
   t['geometry_after_dispatch']=predecessor.identify(wid)['geometry']
   q=await c.call_tool('interface_close',{});t['close']=predecessor.record(O/'mcp/07-close.json',q);t['calls'].append({'operation':'close','call_id':t['close'].get('call_id')})
  return t
predecessor.sequence=sequence_v3
if __name__=='__main__':raise SystemExit(predecessor.main())
