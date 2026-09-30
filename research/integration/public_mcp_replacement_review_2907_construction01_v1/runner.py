import asyncio, base64, hashlib, json, os, re, signal, subprocess, time
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

OUT=Path('/evidence/construction01'); DISPLAY=':143'; ENV=dict(os.environ,DISPLAY=DISPLAY)
COMMIT='research-public-mcp-source-51c04; compare relevant file Git blobs separately'; IMAGE=os.environ['EXPERIMENT_IMAGE_ID']
APPS=[('inkscape',['inkscape'],'inkscape'),('calc',['libreoffice','--calc'],'libreoffice-calc'),('chromium',['chromium','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--user-data-dir=/tmp/chromium-original-c02','about:blank'],'chromium')]

def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True); raw=json.dumps(obj,sort_keys=True,indent=2,ensure_ascii=False).encode()+b'\n'; path.write_bytes(raw); return hashlib.sha256(raw).hexdigest()
def procs():
    rows={}
    for p in Path('/proc').iterdir():
        if p.name.isdigit():
            try:
                b=p.joinpath('stat').read_text(); a=b[b.rfind(')')+2:].split(); rows[int(p.name)]={'ppid':int(a[1]),'state':a[0]}
            except (OSError,ValueError,IndexError): pass
    return rows
def descendants(root):
    ps=procs(); found={root}; changed=True
    while changed:
        changed=False
        for pid,row in ps.items():
            if row['ppid'] in found and pid not in found: found.add(pid); changed=True
    return found
def wins():
    p=subprocess.run(['xdotool','search','--onlyvisible','--name','.*'],env=ENV,text=True,capture_output=True)
    return {int(x) for x in p.stdout.splitlines() if x.strip().isdigit()}
def info(w):
    p=subprocess.run(['xprop','-id',str(w),'_NET_WM_PID','WM_CLASS','WM_NAME'],env=ENV,text=True,capture_output=True)
    g=subprocess.run(['xdotool','getwindowgeometry',str(w)],env=ENV,text=True,capture_output=True)
    m=re.search(r'_NET_WM_PID\(CARDINAL\) = (\d+)',p.stdout); sz=re.search(r'Geometry: (\d+)x(\d+)',g.stdout)
    return {'window_id':w,'properties':p.stdout,'owner_pid':int(m.group(1)) if m else None,'size':[int(sz.group(1)),int(sz.group(2))] if sz else None}
def launch(name,argv,hint):
    before=wins(); p=subprocess.Popen(argv,env=ENV,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True); owned=descendants(p.pid); candidates=[]
    deadline=time.monotonic()+45
    while time.monotonic()<deadline:
        owned=descendants(p.pid)
        for w in sorted(wins()-before):
            row=info(w); candidates.append(row)
            if row['owner_pid'] in owned and row['size'] and min(row['size'])>=100 and hint in row['properties'].lower():
                return p,{'name':name,'launcher_pid':p.pid,'owned_pids':sorted(owned),**row}
        time.sleep(.2)
    raise RuntimeError(f'{name}_OWNED_VISIBLE_WINDOW_NOT_FOUND:{candidates[-8:]}')
def getpayload(r):
    texts=[x.text for x in r.content if getattr(x,'type',None)=='text']
    if len(texts)!=1: raise RuntimeError('MCP_TEXT_CARDINALITY')
    return json.loads(texts[0])
def record(path,r):
    payload=r.model_dump(mode='json'); save(path,payload)
    for x in r.content:
        if getattr(x,'type',None)=='image': path.with_suffix('.png').write_bytes(base64.b64decode(x.data,validate=True))
    return getpayload(r)
def server_pids():
    out=[]
    for p in Path('/proc').iterdir():
        if p.name.isdigit():
            try:
                cmd=p.joinpath('cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
                if 'runtime.cli_v1.mcp_server' in cmd: out.append(int(p.name))
            except OSError: pass
    return out
async def run(targets,original):
    params=StdioServerParameters(command='python3',args=['-m','runtime.cli_v1.mcp_server','--targets',str(OUT/'targets.json'),'--output-directory',str(OUT/'server-receipts'),'--display',DISPLAY,'--session-mode','persistent-x11'],env=ENV,cwd='/opt/importroot')
    t={'calls':[],'decision':'HOLD_INCOMPLETE','server_pids':[]}
    async with stdio_client(params) as (rd,wr):
      async with ClientSession(rd,wr) as c:
        init=await c.initialize(); t['protocol_version']=init.protocolVersion
        t['tool_names']=sorted(x.name for x in (await c.list_tools()).tools); t['server_pids']=server_pids()
        for i,name in enumerate(('inkscape','calc','chromium'),1):
            r=await c.call_tool('interface_observe',{'target':name,'frame':'window_client','region':[0,0,128,96]})
            p=record(OUT/'mcp'/f'{i:02}-observe-{name}.json',r)
            if r.isError or p.get('status')!='returned' or p.get('input_dispatched') is not False or p.get('side_effect_authority') is not False: raise RuntimeError(f'BASELINE_OBSERVE_FAILED:{name}:{p}')
            t['calls'].append({'operation':'observe','target':name,'call_id':p.get('call_id'),'session':p.get('session'),'observation':p.get('observation')})
        sess=t['calls'][0]['session']; t['initial_session']=sess; t['initial_target']=original
        close=subprocess.run(['xdotool','windowclose',str(original['window_id'])],env=ENV,text=True,capture_output=True)
        t['close_original_window']={'returncode':close.returncode,'stdout':close.stdout,'stderr':close.stderr}
        deadline=time.monotonic()+12
        while time.monotonic()<deadline and original['window_id'] in wins(): time.sleep(.1)
        t['old_window_gone']=original['window_id'] not in wins()
        deadline=time.monotonic()+8
        while time.monotonic()<deadline and original['launcher_pid'] in procs(): time.sleep(.1)
        t['old_launcher_pid_alive']=original['launcher_pid'] in procs()
        proc,replacement=launch('chromium-replacement',['chromium','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--user-data-dir=/tmp/chromium-replacement-c02','about:blank'],'chromium')
        t['replacement']=replacement; t['replacement_launcher_pid']=proc.pid
        t['identity_distinct']=(replacement['window_id']!=original['window_id'] and replacement['launcher_pid']!=original['launcher_pid'] and replacement['owner_pid']!=original['owner_pid'])
        a=subprocess.run(['xdotool','windowactivate','--sync',str(replacement['window_id'])],env=ENV,text=True,capture_output=True)
        t['focus_replacement']={'returncode':a.returncode,'stdout':a.stdout,'stderr':a.stderr}
        r=await c.call_tool('interface_inspect_target',{'target':'chromium','screen_region':[0,0,1400,900]})
        p=record(OUT/'mcp/04-inspect-replacement.json',r); t['inspect_replacement']=p; t['calls'].append({'operation':'inspect_target','target':'chromium','call_id':p.get('call_id'),'response':p})
        t['session_after_inspect']=p.get('session')
        t['no_dispatch_after_failed_or_incomplete_review']=True
        close=await c.call_tool('interface_close',{}); cp=record(OUT/'mcp/05-close.json',close); t['close']=cp
    t['server_pids_after_transport']=server_pids()
    return t
def main():
    OUT.mkdir(parents=True,exist_ok=False); (OUT/'mcp').mkdir(); (OUT/'server-receipts').mkdir()
    save(OUT/'environment.json',{'source_commit_label':COMMIT,'image_id':IMAGE,'base_image_id':'sha256:eaf46582f96fd46a1ad6a240928b4c2a828de3d058a4b1490bbadf708d5a52d3','platform':'linux/amd64','display':DISPLAY,'network':'none'})
    xv=subprocess.Popen(['Xvfb',DISPLAY,'-screen','0','1600x1000x24'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); apps=[xv]
    try:
      deadline=time.monotonic()+10
      while time.monotonic()<deadline and not Path('/tmp/.X11-unix/X143').exists(): time.sleep(.05)
      if not Path('/tmp/.X11-unix/X143').exists(): raise RuntimeError('XVFB_SOCKET_MISSING')
      wm=subprocess.Popen(['openbox','--replace'],env=ENV,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); apps.append(wm); time.sleep(.5)
      identities=[]; targets={}
      for name,argv,hint in APPS:
        proc,ident=launch(name,argv,hint); apps.append(proc); identities.append(ident); targets[name]=ident['window_id']
      original=next(x for x in identities if x['name']=='chromium')
      save(OUT/'initial-identities.json',identities); save(OUT/'targets.json',targets)
      t=asyncio.run(run(targets,original)); save(OUT/'trace.json',t)
      inspect=t['inspect_replacement']; ses=t['session_after_inspect'] or {}; oldses=t['initial_session']
      failclosed=(inspect.get('status')=='needs_review' and not inspect.get('review_id') and 'outside configured transient family' in inspect.get('error',''))
      stable=(ses.get('targets',{}).get('chromium')==original['window_id'] and ses.get('binding_revision')==oldses.get('binding_revision')==1)
      closed=t['close'].get('status')=='closed' and t['close'].get('release_attempted') is False
      passed=(t['identity_distinct'] and t['old_window_gone'] and not t['old_launcher_pid_alive'] and failclosed and stable and closed and not t['server_pids_after_transport'])
      result={'decision':'PASS_ROOT_REPLACEMENT_FAIL_CLOSED_SCOPED' if passed else 'HOLD_OR_STOP_GATE_UNMET','trace':t,'authority_granted':False,'input_dispatch_count':0,'model_calls':0,'network_calls':0}
    except Exception as e: result={'decision':'STOP_CONSTRUCTION_EXCEPTION_NO_RETRY','error':repr(e),'authority_granted':False,'input_dispatch_count':0,'model_calls':0,'network_calls':0}
    finally:
      for p in reversed(apps):
        for pid in sorted(descendants(p.pid),reverse=True):
          try: os.kill(pid,signal.SIGTERM)
          except (ProcessLookupError,PermissionError): pass
      time.sleep(.4)
    save(OUT/'result.json',result); print('DECISION='+result['decision']); print(json.dumps({'error':result.get('error'),'identity_distinct':result.get('trace',{}).get('identity_distinct'),'inspect_status':result.get('trace',{}).get('inspect_replacement',{}).get('status'),'inspect_error':result.get('trace',{}).get('inspect_replacement',{}).get('error'),'binding_revision':result.get('trace',{}).get('session_after_inspect',{}).get('binding_revision'),'target_after':result.get('trace',{}).get('session_after_inspect',{}).get('targets'),'close_status':result.get('trace',{}).get('close',{}).get('status')},sort_keys=True))
    return 0 if result['decision'].startswith('PASS') else 3
if __name__=='__main__': raise SystemExit(main())

