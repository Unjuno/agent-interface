import asyncio, base64, hashlib, json, os, re, signal, subprocess, time
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

OUT=Path('/evidence/construction01'); DISPLAY=':142'; ENV=dict(os.environ,DISPLAY=DISPLAY)
COMMIT=os.environ['SOURCE_COMMIT']; IMAGE=os.environ['EXPERIMENT_IMAGE_ID']

def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True); raw=json.dumps(obj,sort_keys=True,indent=2,ensure_ascii=False).encode()+b'\n'; path.write_bytes(raw); return hashlib.sha256(raw).hexdigest()
def processes():
    rows={}
    for p in Path('/proc').iterdir():
        if p.name.isdigit():
            try:
                a=p.joinpath('stat').read_text(); tail=a[a.rfind(')')+2:].split(); rows[int(p.name)]={'ppid':int(tail[1]),'state':tail[0]}
            except (OSError,ValueError,IndexError): pass
    return rows
def descendants(root):
    ps=processes(); got={root}; changed=True
    while changed:
        changed=False
        for pid,r in ps.items():
            if r['ppid'] in got and pid not in got: got.add(pid); changed=True
    return got
def windows():
    p=subprocess.run(['xdotool','search','--onlyvisible','--name','.*'],env=ENV,text=True,capture_output=True)
    return {int(x) for x in p.stdout.splitlines() if x.isdigit()}
def props(w):
    p=subprocess.run(['xprop','-id',str(w),'_NET_WM_PID','WM_CLASS','WM_NAME'],env=ENV,text=True,capture_output=True)
    g=subprocess.run(['xdotool','getwindowgeometry',str(w)],env=ENV,text=True,capture_output=True)
    m=re.search(r'_NET_WM_PID\(CARDINAL\) = (\d+)',p.stdout); sz=re.search(r'Geometry: (\d+)x(\d+)',g.stdout)
    return {'window_id':w,'properties':p.stdout,'owner_pid':int(m.group(1)) if m else None,'size':[int(sz.group(1)),int(sz.group(2))] if sz else None}
def launch():
    before=windows(); p=subprocess.Popen(['libreoffice','--calc'],env=ENV,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
    deadline=time.monotonic()+45
    while time.monotonic()<deadline:
        for w in windows()-before:
            r=props(w)
            if r['owner_pid'] in descendants(p.pid) and r['size'] and min(r['size'])>=100 and 'libreoffice-calc' in r['properties'].lower(): return p,r
        time.sleep(.2)
    raise RuntimeError('CALC_MAIN_SURFACE_NOT_FOUND')
def payload(res):
    texts=[c.text for c in res.content if getattr(c,'type',None)=='text']
    if not texts: raise RuntimeError('MCP_TEXT_MISSING')
    return json.loads(texts[0])
def record(path,res):
    data=res.model_dump(mode='json'); save(path,data)
    for c in res.content:
        if getattr(c,'type',None)=='image':
            b=base64.b64decode(c.data,validate=True); path.with_suffix('.png').write_bytes(b)
    return payload(res)
def program(pid,seq,rev,key):
    return {'schema':'agent-interface/program-v1','program_id':pid,'source':{'observation_seq':seq,'binding_revision':rev},'authority':{'lease_id':'local-construction-lease','expires_at_ns':time.monotonic_ns()+120_000_000_000},'terminal':{'release_all_required':True},'ops':[{'op':'focus','target':'calc'},{'op':'key_chord','keys':[key]},{'op':'release_all'}]}
async def sequence(target):
    params=StdioServerParameters(command='python3',args=['-m','runtime.cli_v1.mcp_server','--targets',str(OUT/'targets.json'),'--output-directory',str(OUT/'server-receipts'),'--display',DISPLAY,'--session-mode','persistent-x11'],env=ENV,cwd='/opt/importroot')
    trace={'allocation':'public-mcp-binding-review-2907-docker-20260927-construction01','calls':[],'decision':'HOLD_INCOMPLETE'}
    async with stdio_client(params) as (rd,wr):
      async with ClientSession(rd,wr) as c:
        init=await c.initialize(); trace['protocol_version']=init.protocolVersion
        trace['tool_names']=sorted(t.name for t in (await c.list_tools()).tools)
        r=await c.call_tool('interface_observe',{'target':'calc','frame':'window_client','region':[0,0,128,96]}); p=record(OUT/'mcp/01-initial-observe.json',r); trace['initial']=p
        oldrev=p.get('session',{}).get('binding_revision'); sessionid=p.get('session',{}).get('session_id')
        x=subprocess.run(['xdotool','windowactivate','--sync',str(target)] + ['key','ctrl+o'],env=ENV,text=True,capture_output=True)
        trace['open_dialog_command']={'returncode':x.returncode,'stdout':x.stdout,'stderr':x.stderr}
        time.sleep(1.0)
        inspect=await c.call_tool('interface_inspect_target',{'target':'calc','screen_region':[0,0,1500,900]}); ip=record(OUT/'mcp/02-inspect-focused.json',inspect); trace['inspect']=ip
        if ip.get('status')!='needs_review' or not ip.get('review_id'):
            raise RuntimeError('INSPECT_NO_REVIEW: '+json.dumps(ip))
        wid=ip['evidence']['window_id']; trace['focus_matches_distinct_dialog']=wid!=target
        review=await c.call_tool('interface_review_target',{'target':'calc','window_id':wid,'review_id':ip['review_id']}); rp=record(OUT/'mcp/03-review-target.json',review); trace['review']=rp
        if rp.get('status')!='target_reviewed': raise RuntimeError('REVIEW_FAILED: '+json.dumps(rp))
        newrev=rp['binding_revision']; trace['old_binding_revision']=oldrev; trace['new_binding_revision']=newrev
        stale=await c.call_tool('interface_dispatch',{'program':program('stale-old-binding',2,oldrev,'F6'),'current_observation_seq':2,'current_binding_revision':newrev}); sp=record(OUT/'mcp/04-stale-binding-dispatch.json',stale); trace['stale_dispatch']=sp
        fresh=await c.call_tool('interface_dispatch',{'program':program('fresh-reviewed-binding',2,newrev,'ESC'),'current_observation_seq':2,'current_binding_revision':newrev}); fp=record(OUT/'mcp/05-fresh-neutral-dispatch.json',fresh); trace['fresh_dispatch']=fp
        close=await c.call_tool('interface_close',{}); cp=record(OUT/'mcp/06-close.json',close); trace['close']=cp
        trace['session_identity_consistent']=sessionid==cp.get('session_id')
        trace['retained_reads']=[]
        for i,item in enumerate(trace['calls'],1):
            rr=await c.call_tool('interface_results',{'call_id':item['call_id'],'include_image':False}); q=record(OUT/f'mcp/retained-{i:02}.json',rr); trace['retained_reads'].append(q)
        trace['server_processes_before_exit']=[p.name for p in Path('/proc').iterdir() if p.name.isdigit() and 'runtime.cli_v1.mcp_server' in Path('/proc',p.name,'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')]
    return trace
def main():
    OUT.mkdir(parents=True,exist_ok=False); (OUT/'mcp').mkdir(); (OUT/'server-receipts').mkdir()
    save(OUT/'environment.json',{'source_commit':COMMIT,'image_id':IMAGE,'base_image_id':'sha256:eaf46582f96fd46a1ad6a240928b4c2a828de3d058a4b1490bbadf708d5a52d3','platform':'linux/amd64','display':DISPLAY})
    xv=subprocess.Popen(['Xvfb',DISPLAY,'-screen','0','1600x1000x24'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); apps=[xv]
    try:
      deadline=time.monotonic()+8
      while time.monotonic()<deadline and not Path('/tmp/.X11-unix/X142').exists(): time.sleep(.05)
      if not Path('/tmp/.X11-unix/X142').exists(): raise RuntimeError('XVFB_SOCKET_MISSING')
      wm=subprocess.Popen(['openbox','--replace'],env=ENV,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); apps.append(wm); time.sleep(.5)
      calc,identity=launch(); apps.append(calc); save(OUT/'calc-identity.json',identity); save(OUT/'targets.json',{'calc':identity['window_id']})
      trace=asyncio.run(sequence(identity['window_id']))
      report={'decision':'HOLD_REVIEW_NOT_AUDITED','construction_trace':trace,'owned_pids':[],'remaining_running_owned_pids':[],'authority_granted':False,'network_calls':0,'model_calls':0}
    except Exception as e:
      report={'decision':'STOP_CONSTRUCTION_EXCEPTION_NO_RETRY','error':repr(e),'authority_granted':False,'network_calls':0,'model_calls':0}
    finally:
      for proc in reversed(apps):
        for pid in sorted(descendants(proc.pid),reverse=True):
          try: os.kill(pid,signal.SIGTERM)
          except (ProcessLookupError,PermissionError): pass
      time.sleep(.4)
    save(OUT/'result.json',report)
    print(json.dumps(report,sort_keys=True))
    if report['decision'].startswith('STOP'): return 2
    tr=report['construction_trace']; action=tr.get('fresh_dispatch',{}).get('receipt',{}).get('source',{}).get('raw_report',{}).get('result',{})
    stale=tr.get('stale_dispatch',{}).get('receipt',{}).get('source',{}).get('raw_report',{}).get('result',{})
    modal=tr.get('focus_matches_distinct_dialog') is True
    good=(modal and stale.get('error') in ('STALE_BINDING','SESSION_BINDING_REVISION_MISMATCH') and stale.get('backend_emissions',0)==0 and action.get('status')=='completed')
    report['decision']='PASS_CONSTRUCTION_BINDING_REVIEW_SCOPED' if good else 'HOLD_MODAL_OR_GUARD_GATE_UNMET'
    save(OUT/'result.json',report); print('FINAL_DECISION='+report['decision'])
    return 0 if good else 3
if __name__=='__main__': raise SystemExit(main())

