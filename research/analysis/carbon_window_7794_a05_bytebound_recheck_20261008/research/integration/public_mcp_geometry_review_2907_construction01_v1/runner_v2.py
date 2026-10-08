"""Fresh construction02 setup-corrected runner; construction01 bytes stay fixed."""
import asyncio,subprocess,time
from pathlib import Path
import runner as predecessor

predecessor.OUT=Path('/evidence/construction02')

async def sequence_v2(wid):
    OUT=predecessor.OUT;ENV=predecessor.ENV;tr={'calls':[],'decision':'HOLD_INCOMPLETE','main_window_id':wid}
    params=predecessor.StdioServerParameters(command='python3',args=['-m','runtime.cli_v1.mcp_server','--targets',str(OUT/'targets.json'),'--output-directory',str(OUT/'server-receipts'),'--display',predecessor.DISPLAY,'--session-mode','persistent-x11'],env=ENV,cwd='/opt/importroot')
    async with predecessor.stdio_client(params) as (rd,wr):
      async with predecessor.ClientSession(rd,wr) as c:
        await c.initialize();tr['tools']=sorted(x.name for x in (await c.list_tools()).tools)
        tip=subprocess.run(['xdotool','search','--onlyvisible','--name','Tip of the Day'],env=ENV,text=True,capture_output=True);tipids=[int(x) for x in tip.stdout.splitlines() if x.strip().isdigit()]
        tr['tip_windows_before_close']=tipids;tr['tip_close_commands']=[]
        for tipid in tipids:
          q=subprocess.run(['xdotool','windowclose',str(tipid)],env=ENV,text=True,capture_output=True);tr['tip_close_commands'].append({'window_id':tipid,'returncode':q.returncode,'stderr':q.stderr})
        time.sleep(.4)
        a=subprocess.run(['xdotool','windowactivate','--sync',str(wid)],env=ENV,text=True,capture_output=True);tr['activate_initial']={'returncode':a.returncode,'stderr':a.stderr}
        g0=predecessor.identify(wid)['geometry'];tr['geometry_before']=g0
        q=await c.call_tool('interface_observe',{'target':'calc','frame':'window_client','region':[0,0,160,120]});p=predecessor.record(OUT/'mcp/01-observe-before.json',q);tr['observe_before']=p;tr['initial_session']=p.get('session');tr['calls'].append({'operation':'observe','call_id':p.get('call_id')})
        # Openbox action and independent X11 geometry checks gate all later calls.
        unmax=subprocess.run(['wmctrl','-ir',str(wid),'-b','remove,maximized_vert,maximized_horz'],env=ENV,text=True,capture_output=True);tr['unmaximize']={'returncode':unmax.returncode,'stdout':unmax.stdout,'stderr':unmax.stderr}
        subprocess.run(['xdotool','windowmove','--sync',str(wid),'80','80'],env=ENV,text=True,capture_output=True)
        size=subprocess.run(['xdotool','windowsize','--sync',str(wid),'1280','760'],env=ENV,text=True,capture_output=True);tr['resize']={'returncode':size.returncode,'stdout':size.stdout,'stderr':size.stderr}
        time.sleep(.5);tr['geometry_after']=predecessor.identify(wid)['geometry']
        changed=(tr['geometry_after'].get('WIDTH')!=g0.get('WIDTH') and tr['geometry_after'].get('HEIGHT')!=g0.get('HEIGHT'))
        tr['geometry_changed']=changed
        if not changed:
          rr=await c.call_tool('interface_close',{});tr['close']=predecessor.record(OUT/'mcp/02-close-setup-stop.json',rr);tr['decision']='HOLD_GEOMETRY_NOT_CHANGED_STOP_BEFORE_DISPATCH';return tr
        q=await c.call_tool('interface_observe',{'target':'calc','frame':'window_client','region':[0,0,160,120]});p=predecessor.record(OUT/'mcp/02-observe-after.json',q);tr['observe_after']=p;tr['calls'].append({'operation':'observe','call_id':p.get('call_id')})
        a=subprocess.run(['xdotool','windowactivate','--sync',str(wid)],env=ENV,text=True,capture_output=True);tr['activate_resized_root']={'returncode':a.returncode,'stderr':a.stderr}
        q=await c.call_tool('interface_inspect_target',{'target':'calc','screen_region':[0,0,1500,900]});ip=predecessor.record(OUT/'mcp/03-inspect-resized-root.json',q);tr['inspect']=ip;tr['calls'].append({'operation':'inspect_target','call_id':ip.get('call_id')})
        if ip.get('status')!='needs_review' or not ip.get('review_id') or ip.get('evidence',{}).get('window_id')!=wid:
          rr=await c.call_tool('interface_close',{});tr['close']=predecessor.record(OUT/'mcp/04-close-review-stop.json',rr);tr['decision']='HOLD_INSPECT_DID_NOT_BIND_MAIN_ROOT_STOP_BEFORE_DISPATCH';return tr
        q=await c.call_tool('interface_review_target',{'target':'calc','window_id':wid,'review_id':ip['review_id']});rp=predecessor.record(OUT/'mcp/04-review-root.json',q);tr['review']=rp;tr['calls'].append({'operation':'review_target','call_id':rp.get('call_id')})
        if rp.get('status')!='target_reviewed' or rp.get('binding_revision')!=2:
          rr=await c.call_tool('interface_close',{});tr['close']=predecessor.record(OUT/'mcp/05-close-review-stop.json',rr);tr['decision']='HOLD_REVIEW_DID_NOT_ADVANCE_STOP_BEFORE_DISPATCH';return tr
        q=await c.call_tool('interface_dispatch',{'program':predecessor.program('stale-geometry-binding',2,1,'F6'),'current_observation_seq':2,'current_binding_revision':2});sp=predecessor.record(OUT/'mcp/05-stale-binding.json',q);tr['stale_dispatch']=sp;tr['calls'].append({'operation':'dispatch','call_id':sp.get('call_id')})
        q=await c.call_tool('interface_dispatch',{'program':predecessor.program('fresh-geometry-binding',2,2,'ESC'),'current_observation_seq':2,'current_binding_revision':2});fp=predecessor.record(OUT/'mcp/06-fresh-neutral.json',q);tr['fresh_dispatch']=fp;tr['calls'].append({'operation':'dispatch','call_id':fp.get('call_id')})
        tr['geometry_after_dispatch']=predecessor.identify(wid)['geometry']
        q=await c.call_tool('interface_close',{});tr['close']=predecessor.record(OUT/'mcp/07-close.json',q);tr['calls'].append({'operation':'close','call_id':tr['close'].get('call_id')})
    return tr

predecessor.sequence=sequence_v2
if __name__=='__main__':raise SystemExit(predecessor.main())
