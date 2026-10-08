import hashlib,json,os,signal,socket,subprocess,sys,time,xml.etree.ElementTree as ET
from pathlib import Path
from Xlib import display,X
from runtime.cli_v1.mcp_session import MCPSessionOwner
from runtime.cli_v1.observe import observe_in_session
from runtime.cli_v1.review import present_result, review_bytes
from runtime.cli_v1.public_summary import summarize_retained_dispatch
from runtime.guarded_x11_v1.bridge import read_window_title
from delivered_capture import DeliveredCapture
from methods import run_method
root=Path(__file__).resolve().parent
case_name=sys.argv[1];schedule=json.loads((root/'schedule.json').read_text());matches=[x for x in schedule if x['case']==case_name]
if len(matches)!=1:raise ValueError('unallocated case')
row=matches[0];detail=row['detail'];case=root/case_name;case.mkdir(exist_ok=False)
def save(name,row):
    path=case/name;tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(row,indent=2)+'\n');tmp.rename(path)
children=[];connection=None;owner=None;host_exit=None
save('allocation.json',{'source':'522b21e148170f9de12f27f3f0ffca44cbd2d938','pair':row['pair'],'detail':detail,'owner_pid':os.getpid(),'started_ns':time.monotonic_ns(),'retry_budget':0,'repair_budget':0,'command_budget':8,'source_is_current_checkout':True})
for n in range(27901,27950):
    if Path(f'/tmp/.X11-unix/X{n}').exists() or Path(f'/tmp/.X{n}-lock').exists():continue
    sock=socket.socket(socket.AF_UNIX)
    try:sock.connect('\0'+f'/tmp/.X11-unix/X{n}')
    except OSError:break
    finally:sock.close()
else:raise RuntimeError('no unused display')
env={k:v for k,v in os.environ.items() if k not in ('WAYLAND_DISPLAY','DBUS_SESSION_BUS_ADDRESS')}
env.update(DISPLAY=f':{n}',GDK_BACKEND='x11',QT_QPA_PLATFORM='xcb',LANG='C.UTF-8',LC_ALL='C.UTF-8')
for key,folder in [('HOME','home'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache'),('XDG_DATA_HOME','data'),('XDG_RUNTIME_DIR','run')]:
    path=case/folder;path.mkdir(mode=0o700);env[key]=str(path)
def launch(name,args):
    p=subprocess.Popen(args,env=env,stdin=subprocess.DEVNULL,stdout=(case/(name+'.stdout')).open('xb'),stderr=(case/(name+'.stderr')).open('xb'),start_new_session=True)
    children.append((name,p));return p
svg=case/'two-rectangles.svg'
svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="400" height="240" viewBox="0 0 400 240"></svg>')
save('original-svg.json',{'sha256':hashlib.sha256(svg.read_bytes()).hexdigest()})
try:
    xvfb=launch('xvfb',['Xvfb',f':{n}','-screen','0','1000x700x24','-ac','-nolisten','tcp','-nolisten','unix'])
    deadline=time.monotonic()+5
    while True:
        if xvfb.poll() is not None:raise RuntimeError('Xvfb exited')
        try:connection=display.Display(f':{n}');break
        except Exception:
            if time.monotonic()>deadline:raise
            time.sleep(.02)
    wm=launch('openbox',['openbox','--config-file','/etc/xdg/openbox/rc.xml'])
    deadline=time.monotonic()+5
    while connection.screen().root.get_full_property(connection.intern_atom('_NET_SUPPORTING_WM_CHECK'),X.AnyPropertyType) is None:
        if wm.poll() is not None or time.monotonic()>deadline:raise RuntimeError('WM not ready')
        time.sleep(.02)
    app=launch('inkscape',['inkscape',str(svg)])
    deadline=time.monotonic()+30;target=None
    while target is None:
        prop=connection.screen().root.get_full_property(connection.intern_atom('_NET_CLIENT_LIST'),X.AnyPropertyType)
        for wid in ([] if prop is None else prop.value):
            win=connection.create_resource_object('window',int(wid))
            try:title=read_window_title(connection,win) or ''
            except Exception:continue
            if svg.name in title:target=int(wid);break
        if time.monotonic()>deadline:raise RuntimeError('Inkscape window not ready')
        time.sleep(.05)
    subprocess.run(['wmctrl','-ir',hex(target),'-b','remove,maximized_vert,maximized_horz'],env=env,check=True)
    subprocess.run(['wmctrl','-ir',hex(target),'-e','0,20,20,900,600'],env=env,check=True)
    subprocess.run(['wmctrl','-ia',hex(target)],env=env,check=True)
    owner=MCPSessionOwner({'app':target},display_name=f':{n}')
    save('owner.json',{'pid':os.getpid(),'display':f':{n}','window':target,'children':{name:p.pid for name,p in children}})
    for folder in ['commands','replies','public']: (case/folder).mkdir()
    capture=DeliveredCapture();sequence=0;index=1;stop_at=time.monotonic()+900
    print('READY public owned Inkscape',flush=True)
    while True:
        if time.monotonic()>stop_at:raise RuntimeError('owner lifetime exhausted')
        if any(p.poll() is not None for _,p in children):raise RuntimeError('owned child exited')
        path=case/'commands'/f'{index:03d}.json'
        if not path.exists():time.sleep(.02);continue
        if index>8:raise RuntimeError('command budget exhausted')
        req=json.loads(path.read_text());op=req['op'];started=time.monotonic_ns();shown=None
        if op=='observe':
            raw=observe_in_session(owner.get(),target='app',frame='screen_physical_px',region=[0,0,1000,700],capture_directory=str(case/'public/images'))
            shown=present_result(raw,case/'public',compact=True,report_refs=True)
            if capture.accept(raw,shown) is not None:sequence+=1
        elif op=='dispatch':
            if req['program']['source']!={'observation_seq':sequence,'binding_revision':owner.binding_revision}:raise ValueError('explicit source mismatch')
            raw=owner.dispatch(req['program'],current_observation_seq=sequence,current_binding_revision=owner.binding_revision,capture_directory=str(case/'public/images'))
            save(f'public/{index:03d}-raw.json',raw)
            report_path=case/f'public/{index:03d}-raw.json'
            full=review_bytes(report_path.read_bytes(),case/'public',compact=True,report_refs=True)
            shown=summarize_retained_dispatch(full,report_path,case/'public') if detail=='summary' else full
            if any(shown.get(k)!=full.get(k) for k in ('image','image_reference','outcome_summary')):raise RuntimeError('critical projection changed')
            if capture.accept(raw,full) is not None:sequence+=1
        elif op=='method':
            raw=run_method(owner,case,req,sequence,row['route'],row['layout']);sequence=raw['sequence']
            shown=present_result(raw['final_observation'],case/'public',compact=True,report_refs=True)
            shown['method_receipt']=raw['common'];shown['raw_method_ref']='method-raw.json'
        elif op=='results':
            prior=req['command_id']
            if type(prior) is not int or not 1<=prior<index:raise ValueError('invalid explicit lookup')
            report_path=case/f'public/{prior:03d}-raw.json'
            raw=json.loads(report_path.read_text())
            shown=review_bytes(report_path.read_bytes(),case/'public',compact=True,report_refs=True,include_image=False)
        elif op=='close':raw=owner.close()
        else:raise ValueError('unsupported command')
        save(f'public/{index:03d}-raw.json',raw)
        save(f'replies/{index:03d}.json',{'request':req,'started_ns':started,'ended_ns':time.monotonic_ns(),'sequence':sequence,'binding_revision':owner.binding_revision,'reply':shown if shown is not None else raw})
        print('REPLY '+str(index)+' '+op,flush=True);index+=1
        if op=='close':break
    owner.close();owner=None;host_exit=0
except Exception as error:
    save('exception.json',{'error':repr(error),'replay_allowed':False});raise
finally:
    if owner is not None:save('fallback-close.json',owner.close())
    if connection is not None:connection.close()
    codes=[]
    for name,p in reversed(children):
        if p.poll() is None:os.killpg(p.pid,signal.SIGTERM)
        try:code=p.wait(timeout=5)
        except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);code=p.wait(timeout=5)
        codes.append({'name':name,'pid':p.pid,'returncode':code})
    save('cleanup.json',{'host_exit':host_exit,'children':codes,'ended_ns':time.monotonic_ns(),'all_owned_processes_terminal':all(p.poll() is not None for _,p in children)})
    tree=ET.parse(svg).getroot();rects=[]
    for el in tree.iter('{http://www.w3.org/2000/svg}rect'):
        rects.append({k:float(el.get(k,'0')) for k in ('x','y','width','height')}|{'transform':el.get('transform')})
    positive=all(v['width']>0 and v['height']>0 and v['x']>=0 and v['y']>=0 and v['x']+v['width']<=400 and v['y']+v['height']<=240 and v['transform'] is None for v in rects)
    overlap=True
    if len(rects)==2:
        a,b=rects;overlap=not(a['x']+a['width']<=b['x'] or b['x']+b['width']<=a['x'] or a['y']+a['height']<=b['y'] or b['y']+b['height']<=a['y'])
    save('evaluation.json',{'rectangles':rects,'success':len(rects)==2 and positive and not overlap,'after_all_owned_processes_terminal':True,'svg_sha256':hashlib.sha256(svg.read_bytes()).hexdigest()})
    print('TERMINAL OWNER',flush=True)
