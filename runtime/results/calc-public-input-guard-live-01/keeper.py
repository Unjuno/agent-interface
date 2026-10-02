import os,json,time,sys,subprocess,signal,socket,hashlib,shutil
from pathlib import Path
from Xlib import display,X
import openpyxl
from runtime.cli_v1.mcp_guarded import GuardedSessionOwner
from runtime.cli_v1.review import present_result
from runtime.guarded_x11_v1.bridge import read_window_title
from composition import CalcComposition
root=Path(__file__).resolve().parent;name=sys.argv[1]
rows=[x for x in json.loads((root/'schedule.json').read_text()) if x['case']==name]
if len(rows)!=1:raise ValueError('case not frozen')
row=rows[0];case=root/name;case.mkdir(exist_ok=False)
for n in ['commands','replies','home','config','cache','data','run']: (case/n).mkdir(mode=0o700)
def save(path,value):
 p=case/path;p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(value,indent=2)+'\n');tmp.rename(p)
children=[];owner=None;conn=None;reviewed=None;refs=None;close_result=None
for number in range(30101,30150):
 if not Path(f'/tmp/.X11-unix/X{number}').exists() and not Path(f'/tmp/.X{number}-lock').exists():break
else:raise RuntimeError('no free display')
env={k:v for k,v in os.environ.items() if k not in ['WAYLAND_DISPLAY','DBUS_SESSION_BUS_ADDRESS']}
env.update(DISPLAY=f':{number}',GDK_BACKEND='x11',QT_QPA_PLATFORM='xcb',LANG='C.UTF-8',LC_ALL='C.UTF-8',SAL_USE_VCLPLUGIN='gen')
for k,n in [('HOME','home'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache'),('XDG_DATA_HOME','data'),('XDG_RUNTIME_DIR','run')]:env[k]=str(case/n)
def launch(name,args):
 p=subprocess.Popen(args,env=env,stdin=subprocess.DEVNULL,stdout=(case/(name+'.stdout')).open('xb'),stderr=(case/(name+'.stderr')).open('xb'),start_new_session=True);children.append((name,p));return p

def metadata():
 prop=conn.screen().root.get_full_property(conn.intern_atom('_NET_CLIENT_LIST'),X.AnyPropertyType);out=[]
 for wid in ([] if prop is None else prop.value):
  window=conn.create_resource_object('window',int(wid))
  try:title=read_window_title(conn,window)
  except Exception:title=None
  out.append({'window_id':int(wid),'title':title})
 return {'windows':out,'focused_client_window':owner.bridge.focused_client_window() if owner else None}

def shown(raw,call):
 if 'observation_report' in raw:return present_result(raw['observation_report'],call,compact=True,report_refs=True)
 return raw.get('feedback')

save('allocation.json',{'case':row,'started_ns':time.monotonic_ns(),'owner_pid':os.getpid(),'retry_budget':0,'repair_budget':0,'command_budget':18})
workbook=case/'primary-values.xlsx';openpyxl.Workbook().save(workbook)
try:
 xvfb=launch('xvfb',['Xvfb',f':{number}','-screen','0','1280x800x24','-ac','-nolisten','tcp'])
 until=time.monotonic()+10
 while conn is None:
  if xvfb.poll() is not None or time.monotonic()>until:raise RuntimeError('display startup failed')
  try:conn=display.Display(f':{number}')
  except Exception:time.sleep(.05)
 wm=launch('openbox',['openbox','--config-file','/etc/xdg/openbox/rc.xml']);until=time.monotonic()+10
 while conn.screen().root.get_full_property(conn.intern_atom('_NET_SUPPORTING_WM_CHECK'),X.AnyPropertyType) is None:
  if wm.poll() is not None or time.monotonic()>until:raise RuntimeError('WM startup failed')
  time.sleep(.05)
 app=launch('calc',['libreoffice','-env:UserInstallation='+(case/'lo-profile').as_uri(),'--calc','--norestore',str(workbook)])
 until=time.monotonic()+30;target=None
 while target is None:
  for window in metadata()['windows']:
   if workbook.name in (window['title'] or ''):target=window['window_id'];break
  if time.monotonic()>until:raise RuntimeError('Calc startup failed')
  time.sleep(.05)
 owner=GuardedSessionOwner({'app':target},case/'public-owner',f':{number}');owner.get()
 save('owner.json',{'display':f':{number}','main_window':target,'children':{n:p.pid for n,p in children},'metadata':metadata()})
 print(json.dumps({'ready':True,'case':name,'display':f':{number}','main_window':target,'metadata':metadata()}),flush=True)
 until=time.monotonic()+1200
 for index in range(1,19):
  command=case/'commands'/f'{index:03d}.json'
  while not command.exists():
   if time.monotonic()>until:raise TimeoutError('primary lifetime expired')
   time.sleep(.05)
  request=json.loads(command.read_text());op=request['op'];call=case/'calls'/str(index);bridge=owner.bridge;start=time.monotonic_ns();raw=None;feedback=None
  try:
   if op=='primary_review':
    source=bridge.history[request['source_sequence']][0]
    if source['sequence']!=bridge.sequence or source['native']['artifact']['sha256']!=request['image_sha256']:raise ValueError('review source mismatch')
    reviewed=source['sequence'];raw={'status':'primary_review_recorded','source_sequence':reviewed,'purpose':request['purpose'],'input_dispatched':False}
   elif op=='observe':raw=owner.invoke_guarded('guarded_observe',{},call);feedback=shown(raw,call)
   elif op=='review_window':raw=owner.invoke_guarded('guarded_review_window',{'window_id':request['window_id']},call);feedback=shown(raw,call);reviewed=None
   elif op=='mint_many':
    if reviewed!=bridge.sequence:raise ValueError('primary image review required')
    raw=owner.invoke_guarded('guarded_mint_many',{'source_sequence':bridge.sequence,'references':request['references']},call)
    if request.get('sheet_refs') is not None and raw['status']=='minted':refs=request['sheet_refs']
   elif op=='input':
    if reviewed!=bridge.sequence:raise ValueError('primary modal image review required')
    args=dict(request['arguments']);raw=owner.invoke_guarded('guarded_input',args,call);feedback=shown(raw,call);reviewed=None
   elif op=='method':
    if reviewed!=bridge.sequence or refs is None:raise ValueError('reviewed sheet references required')
    native,rgb=bridge.history[bridge.sequence]
    approved={'scope':bridge.scope,'revision':bridge.binding_revision,'binding':native['pointer_binding'],'geometry_reviewed':True,'image_size':[1280,800],'titles':request['main_sheet_titles']}
    composition=CalcComposition(owner,case/'method',refs=refs,approved=approved,reviewed_native=native,reviewed_rgb=rgb,second_value=row['second'])
    raw=composition.run(row['route']);feedback=raw.get('feedback');reviewed=None
   elif op=='close':close_result=owner.close();raw=close_result
   else:raise ValueError('unknown command')
   image=None
   if feedback and feedback.get('image_status')=='image':
    # Return original last-source file path, never a new capture.
    source=bridge.history[bridge.sequence][0];image={'path':source['native']['artifact']['path'],'sha256':source['native']['artifact']['sha256'],'sequence':bridge.sequence}
   save(f'replies/{index:03d}.json',{'op':op,'raw':raw,'feedback':feedback,'image':image,'metadata':metadata(),'elapsed_ns':time.monotonic_ns()-start})
   print(json.dumps({'reply':index,'op':op,'status':raw.get('status') if isinstance(raw,dict) else None,'image':image}),flush=True)
  except Exception as error:
   save(f'replies/{index:03d}.json',{'op':op,'error':repr(error),'replay_allowed':False,'metadata':metadata()});print(json.dumps({'reply':index,'error':repr(error)}),flush=True)
  if op=='close':break
 else:raise RuntimeError('command budget exhausted')
finally:
 if owner is not None:
  if close_result is None:
   try:close_result=owner.close()
   except Exception as error:close_result={'error':repr(error)}
  save('close.json',close_result)
 if conn is not None:conn.close()
 inventory=subprocess.check_output(['ps','-eo','pid=,pgid='],text=True)
 groups={p.pid for n,p in children};owned=[int(line.split()[0]) for line in inventory.splitlines() if len(line.split())==2 and int(line.split()[1]) in groups]
 for n,p in reversed(children):
  try:os.killpg(p.pid,signal.SIGTERM)
  except ProcessLookupError:pass
 for n,p in reversed(children):
  try:p.wait(timeout=3)
  except subprocess.TimeoutExpired:
   try:os.killpg(p.pid,signal.SIGKILL)
   except ProcessLookupError:pass
   p.wait()
 until=time.monotonic()+3
 while any(Path('/proc',str(pid)).exists() for pid in owned) and time.monotonic()<until:time.sleep(.05)
 remaining=[pid for pid in owned if Path('/proc',str(pid)).exists()]
 save('cleanup.json',{'children':[{'name':n,'pid':p.pid,'returncode':p.returncode} for n,p in children],'owned_pids':owned,'remaining':remaining})
 if remaining:save('independent-score.json',{'status':'UNAVAILABLE','reason':'owned process remains; no offline score'})
 else:
  shutil.copyfile(workbook,case/'saved.xlsx');book=openpyxl.load_workbook(case/'saved.xlsx',data_only=True)
  actual={'A1':book.active['A1'].value,'A2':book.active['A2'].value};nonempty={cell.coordinate:cell.value for sheet in book for row_cells in sheet for cell in row_cells if cell.value is not None}
  save('independent-score.json',{'status':'SCORED_AFTER_OWNER_AND_CHILD_TERMINATION','actual':actual,'nonempty_cells':nonempty,'goal_correct':actual=={'A1':731,'A2':864},'saved_sha256':hashlib.sha256((case/'saved.xlsx').read_bytes()).hexdigest()})
 print(json.dumps({'terminal':True,'remaining_owned_pids':remaining}),flush=True)
