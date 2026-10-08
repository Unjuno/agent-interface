import asyncio,base64,hashlib,json,os,re,signal,subprocess,time
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client

OUT=Path('/evidence/construction01');DISPLAY=':144';ENV=dict(os.environ,DISPLAY=DISPLAY)
IMAGE=os.environ['EXPERIMENT_IMAGE_ID']
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);b=json.dumps(x,sort_keys=True,indent=2,ensure_ascii=False).encode()+b'\n';p.write_bytes(b);return hashlib.sha256(b).hexdigest()
def procs():
 r={}
 for p in Path('/proc').iterdir():
  if p.name.isdigit():
   try:
    s=p.joinpath('stat').read_text();a=s[s.rfind(')')+2:].split();r[int(p.name)]={'ppid':int(a[1]),'state':a[0]}
   except (OSError,ValueError,IndexError):pass
 return r
def tree(pid):
 ps=procs();v={pid};change=True
 while change:
  change=False
  for k,x in ps.items():
   if x['ppid'] in v and k not in v:v.add(k);change=True
 return v
def windows():
 p=subprocess.run(['xdotool','search','--onlyvisible','--name','.*'],env=ENV,text=True,capture_output=True)
 return {int(x) for x in p.stdout.splitlines() if x.strip().isdigit()}
def identify(w):
 p=subprocess.run(['xprop','-id',str(w),'_NET_WM_PID','WM_CLASS','WM_NAME'],env=ENV,text=True,capture_output=True)
 g=subprocess.run(['xdotool','getwindowgeometry','--shell',str(w)],env=ENV,text=True,capture_output=True)
 pid=re.search(r'_NET_WM_PID\(CARDINAL\) = (\d+)',p.stdout);vals={}
 for k,v in re.findall(r'^(X|Y|WIDTH|HEIGHT)=(\d+)$',g.stdout,re.M):vals[k]=int(v)
 return {'window_id':w,'owner_pid':int(pid.group(1)) if pid else None,'properties':p.stdout,'geometry':vals}
def launch_calc():
 before=windows();p=subprocess.Popen(['libreoffice','--calc'],env=ENV,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True);deadline=time.monotonic()+45
 while time.monotonic()<deadline:
  owned=tree(p.pid)
  for w in sorted(windows()-before):
   x=identify(w)
   if x['owner_pid'] in owned and x['geometry'].get('WIDTH',0)>=300 and 'libreoffice-calc' in x['properties'].lower():return p,x
  time.sleep(.2)
 raise RuntimeError('CALC_OWNER_WINDOW_NOT_FOUND')
def raw_payload(r):
 texts=[x.text for x in r.content if getattr(x,'type',None)=='text']
 if len(texts)!=1:raise RuntimeError('MCP_TEXT_CARDINALITY')
 p=json.loads(texts[0])
 if p.get('schema')=='agent-interface/review-v1':
  receipt=p.get('receipt',{});raw=receipt.get('source',{}).get('raw_report',{})
  if receipt.get('schema')!='agent-interface/receipt-view-v1' or not isinstance(raw,dict):raise RuntimeError('PUBLIC_RECEIPT_SHAPE')
  p.update(status=raw.get('status'),observation=raw,input_dispatched=raw.get('input_dispatched'),side_effect_authority=raw.get('side_effect_authority'),session=p.get('session') or raw.get('session'))
 return p
def record(path,r):
 payload=r.model_dump(mode='json');save(path,payload)
 for x in r.content:
  if getattr(x,'type',None)=='image':path.with_suffix('.png').write_bytes(base64.b64decode(x.data,validate=True))
 return raw_payload(r)
def program(pid,seq,rev,key):
 return {'schema':'agent-interface/program-v1','program_id':pid,'source':{'observation_seq':seq,'binding_revision':rev},'authority':{'lease_id':'local-geometry-construction-lease','expires_at_ns':time.monotonic_ns()+120_000_000_000},'terminal':{'release_all_required':True},'ops':[{'op':'focus','target':'calc'},{'op':'key_chord','keys':[key]},{'op':'release_all'}]}
async def sequence(wid):
 params=StdioServerParameters(command='python3',args=['-m','runtime.cli_v1.mcp_server','--targets',str(OUT/'targets.json'),'--output-directory',str(OUT/'server-receipts'),'--display',DISPLAY,'--session-mode','persistent-x11'],env=ENV,cwd='/opt/importroot')
 tr={'calls':[],'decision':'HOLD_INCOMPLETE'}
 async with stdio_client(params) as (rd,wr):
  async with ClientSession(rd,wr) as c:
   await c.initialize();tr['tools']=sorted(x.name for x in (await c.list_tools()).tools)
   r=await c.call_tool('interface_observe',{'target':'calc','frame':'window_client','region':[0,0,160,120]});p=record(OUT/'mcp/01-observe-before.json',r)
   tr['initial_observation']=p;tr['initial_session']=p.get('session')
   g0=identify(wid)['geometry'];tr['geometry_before']=g0
   sz=subprocess.run(['xdotool','windowsize','--sync',str(wid),'1320','780'],env=ENV,text=True,capture_output=True);tr['resize_command']={'returncode':sz.returncode,'stdout':sz.stdout,'stderr':sz.stderr}
   time.sleep(.5);g1=identify(wid)['geometry'];tr['geometry_after']=g1
   r=await c.call_tool('interface_inspect_target',{'target':'calc','screen_region':[0,0,1500,900]});ip=record(OUT/'mcp/02-inspect-resized.json',r);tr['inspect']=ip;tr['calls'].append({'operation':'inspect_target','call_id':ip.get('call_id')})
   rev=await c.call_tool('interface_review_target',{'target':'calc','window_id':wid,'review_id':ip.get('review_id','')});rp=record(OUT/'mcp/03-review.json',rev);tr['review']=rp;tr['calls'].append({'operation':'review_target','call_id':rp.get('call_id')})
   r=await c.call_tool('interface_dispatch',{'program':program('stale-geometry-binding',2,1,'F6'),'current_observation_seq':2,'current_binding_revision':2});sp=record(OUT/'mcp/04-stale-binding.json',r);tr['stale_dispatch']=sp;tr['calls'].append({'operation':'dispatch','call_id':sp.get('call_id')})
   r=await c.call_tool('interface_dispatch',{'program':program('fresh-geometry-binding',2,2,'ESC'),'current_observation_seq':2,'current_binding_revision':2});fp=record(OUT/'mcp/05-fresh-neutral.json',r);tr['fresh_dispatch']=fp;tr['calls'].append({'operation':'dispatch','call_id':fp.get('call_id')})
   tr['geometry_after_dispatch']=identify(wid)['geometry']
   r=await c.call_tool('interface_close',{});cp=record(OUT/'mcp/06-close.json',r);tr['close']=cp;tr['calls'].append({'operation':'close','call_id':cp.get('call_id')})
 return tr
def main():
 OUT.mkdir(parents=True,exist_ok=False);(OUT/'mcp').mkdir();(OUT/'server-receipts').mkdir()
 save(OUT/'environment.json',{'image_id':IMAGE,'base_image_id':'sha256:eaf46582f96fd46a1ad6a240928b4c2a828de3d058a4b1490bbadf708d5a52d3','platform':'linux/amd64','display':DISPLAY,'network':'none','source_closure':'51c04; seven relevant source blobs separately pinned'})
 xv=subprocess.Popen(['Xvfb',DISPLAY,'-screen','0','1600x1000x24'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);apps=[xv]
 try:
  deadline=time.monotonic()+10
  while time.monotonic()<deadline and not Path('/tmp/.X11-unix/X144').exists():time.sleep(.05)
  if not Path('/tmp/.X11-unix/X144').exists():raise RuntimeError('XVFB_SOCKET_MISSING')
  wm=subprocess.Popen(['openbox','--replace'],env=ENV,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);apps.append(wm);time.sleep(.5)
  calc,identity=launch_calc();apps.append(calc);save(OUT/'calc-identity.json',identity);save(OUT/'targets.json',{'calc':identity['window_id']})
  tr=asyncio.run(sequence(identity['window_id']));save(OUT/'trace.json',tr)
  stale=tr['stale_dispatch'].get('receipt',{}).get('source',{}).get('raw_report',{}).get('result',{})
  fresh=tr['fresh_dispatch'].get('receipt',{}).get('source',{}).get('raw_report',{}).get('result',{})
  rel=(fresh.get('execution',{}).get('releases') or [{}])[0]
  same=tr['inspect'].get('evidence',{}).get('window_id')==identity['window_id']==tr['review'].get('window_id')
  changed=(tr['geometry_before'].get('WIDTH')!=tr['geometry_after'].get('WIDTH') and tr['geometry_before'].get('HEIGHT')!=tr['geometry_after'].get('HEIGHT'))
  inspected=tr['inspect'].get('evidence',{}).get('geometry',[None,None,None,None])[2:]==[tr['geometry_after'].get('WIDTH'),tr['geometry_after'].get('HEIGHT')]
  release=rel.get('verified') is True and rel.get('keys_down')==[] and rel.get('buttons_down')==[]
  ok=(changed and inspected and same and tr['review'].get('binding_revision')==2 and stale.get('error')=='STALE_BINDING' and stale.get('backend_emissions')==0 and fresh.get('status')=='completed' and release and tr['close'].get('status')=='closed' and tr['close'].get('release_attempted') is True)
  result={'decision':'PASS_GEOMETRY_REVIEW_STALE_BINDING_SCOPED' if ok else 'HOLD_GEOMETRY_REVIEW_GATE_UNMET','trace':tr,'authority_granted':False,'model_calls':0,'network_calls':0}
 except Exception as e:result={'decision':'STOP_CONSTRUCTION_EXCEPTION_NO_RETRY','error':repr(e),'authority_granted':False,'model_calls':0,'network_calls':0}
 finally:
  for p in reversed(apps):
   for pid in sorted(tree(p.pid),reverse=True):
    try:os.kill(pid,signal.SIGTERM)
    except (ProcessLookupError,PermissionError):pass
  time.sleep(.4)
 save(OUT/'result.json',result);print('DECISION='+result['decision']);t=result.get('trace',{});print(json.dumps({'error':result.get('error'),'before':t.get('geometry_before'),'after':t.get('geometry_after'),'evidence':t.get('inspect',{}).get('evidence'),'revision':t.get('review',{}).get('binding_revision'),'stale':t.get('stale_dispatch',{}).get('receipt',{}).get('source',{}).get('raw_report',{}).get('result'),'fresh':t.get('fresh_dispatch',{}).get('receipt',{}).get('source',{}).get('raw_report',{}).get('result',{}).get('status'),'close':t.get('close',{}).get('status')},sort_keys=True))
 return 0 if result['decision'].startswith('PASS') else 3
if __name__=='__main__':raise SystemExit(main())
