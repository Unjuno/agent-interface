"""Finite native-input construction/formal batches. Never uses inherited display."""
import argparse,base64,hashlib,itertools,json,os,secrets,select,struct,subprocess,sys,tempfile,time,traceback,zlib
from pathlib import Path
from Xlib import X,display
from load_backend import load
from policy import decide
HERE=Path(__file__).resolve().parent
POLICIES=('CLICK_THEN_TYPE','POST_FOCUS','HIT_AND_FOCUS')
SCENARIOS=('CLEAR','COVER_BEFORE','COVER_AFTER','UNRELATED')

def dump(p,obj):
    with p.open('x') as f: json.dump(obj,f,sort_keys=True); f.write('\n'); f.flush(); os.fsync(f.fileno())
def digest(b): return hashlib.sha256(b).hexdigest()
def get_line(p,timeout=3):
    if not select.select([p.stdout],[],[],timeout)[0]: raise TimeoutError('pipe response')
    line=p.stdout.readline()
    if not line: raise RuntimeError('unexpected EOF')
    if not hasattr(p,'wire_out'): p.wire_out=[]
    p.wire_out.append(line)
    return json.loads(line)
def schedule():
    rows=[]
    for rep in range(2):
        for scen in SCENARIOS:
            for pol in POLICIES[rep:]+POLICIES[:rep]: rows.append({'rep':rep,'scenario':scen,'policy':pol})
    rows+=[{'rep':0,'scenario':s,'policy':'NO_TASK_INPUT'} for s in ('CLEAR','COVER_BEFORE')]
    return [dict(r,index=i) for i,r in enumerate(rows)]
def observe(d,ids):
    root=d.screen().root; chain=[]; win=root
    for _ in range(16):
        q=win.query_pointer(); chain.append({'window':win.id,'child':getattr(q.child,'id',q.child),'x':q.root_x,'y':q.root_y,'mask':q.mask})
        if not getattr(q.child,'id',0): break
        win=q.child
    else: raise RuntimeError('pointer depth')
    focus=d.get_input_focus().focus
    return {'captured_ns':time.monotonic_ns(),'chain':chain,'leaf':win.id,
            'keymap':list(d.query_keymap()),'button_mask':root.query_pointer().mask & (X.Button1Mask|X.Button2Mask|X.Button3Mask|X.Button4Mask|X.Button5Mask),
            'server_focus':getattr(focus,'id',focus)}
def capture(d,rootdir,tag,marker):
    info=d.display.info; image=d.screen().root.get_image(0,0,640,360,X.ZPixmap,0xffffffff)
    raw=bytes(image.data); (rootdir/(tag+'.ximage.zlib')).write_bytes(zlib.compress(raw))
    fmt=next(f for f in info.pixmap_formats if f.depth==image.depth)
    vis=next(v for s in info.roots for dp in s.allowed_depths for v in dp.visuals if v.visual_id==image.visual)
    return {'file':tag+'.ximage.zlib','sha256':digest(raw),'size':len(raw),'width':640,'height':360,
        'depth':image.depth,'bits_per_pixel':fmt.bits_per_pixel,'byte_order':info.image_byte_order,
        'masks':[vis.red_mask,vis.green_mask,vis.blue_mask],'marker_xy':marker,'capture_ns':time.monotonic_ns()}
def one(root,config,dname,auth):
    root.mkdir(); session=secrets.token_hex(16); record={'config':config,'session':session,'calls':[],'rpcs':[],'decisions':[]}; start=time.monotonic_ns()
    env={k:os.environ[k] for k in ('PATH','LANG') if k in os.environ}; env.update(DISPLAY=dname,XAUTHORITY=str(auth),HOME=str(root),PYTHONDONTWRITEBYTECODE='1')
    err=(root/'app.stderr').open('w'); p=subprocess.Popen([sys.executable,'-B',str(HERE/'app.py'),str(root),session],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,env=env)
    backend=None; obs=None; seq=0; wire_in=[]
    def rpc(op,**kwargs):
        nonlocal seq
        seq+=1; req=dict(id=seq,op=op,**kwargs); before=time.monotonic_ns()
        wire=json.dumps(req)+'\n'; wire_in.append(wire); p.stdin.write(wire); p.stdin.flush(); response=get_line(p)
        record['rpcs'].append({'request':req,'response':response,'sent_ns':before,'received_ns':time.monotonic_ns()})
        if response.get('id')!=seq or 'error' in response: raise RuntimeError(response)
        return response['snapshot']
    def call(method,*args):
        before=time.monotonic_ns(); ret=getattr(backend,method)(*args)
        record['calls'].append({'method':method,'args':args,'returned':ret,'started_ns':before,'ended_ns':time.monotonic_ns(),'emissions':backend.emissions})
        return ret
    try:
        ready=get_line(p); record['ready']=ready
        ids=ready['ready']['ids']; obs=display.Display(dname)
        surface=obs.create_resource_object('window',ids['root']).query_tree().parent.id
        if surface==obs.screen().root.id: surface=ids['root']
        backend=load()(dname,{'surface':surface,'a':ids['a']})
        call('focus','surface'); initial=rpc('snapshot'); record['initial']=initial
        if initial['a'] or initial['b'] or initial['counter'] or initial['focus']!=ids['b']:
            raise RuntimeError('initial fixture state')
        g=initial['geometry']; record['geometry_before']=call('geometry','a')
        if config['scenario']=='COVER_BEFORE': rpc('cover',mode='target')
        if config['scenario']=='UNRELATED': rpc('cover',mode='unrelated')
        call('pointer_move','surface','screen_physical_px',g['x']+g['width']//2,g['y']+g['height']//2)
        pre=rpc('snapshot'); preobs=observe(obs,ids); record['pre']=pre; record['pre_observer']=preobs
        expected={'session':session,'surface':surface,'target':ids['a'],'geometry':g}
        def decision(phase,snap,obsrow):
            receipt={'session':snap['session'],'surface':surface,'target':ids['a'],'geometry':snap['geometry'],
                     'sequence':len(record['decisions'])+1,'captured_ns':snap['captured_ns'],'focus':snap['focus'],'hit':obsrow['leaf']}
            result=decide(config['policy'],phase,expected,receipt)
            record['decisions'].append({'phase':phase,'expected':expected,'receipt':receipt,'result':result,'decided_ns':time.monotonic_ns()})
            return result['allow']
        click=decision('click',pre,preobs)
        if config['scenario']=='COVER_AFTER': rpc('cover',mode='target')
        record['before_click']=rpc('snapshot'); record['before_click_observer']=observe(obs,ids)
        record['before_capture']=capture(obs,root,'before',pre['marker_xy'])
        if click:
            call('pointer_button','left',True)
            try: rpc('wait',counts={'4':1})
            finally: call('pointer_button','left',False)
            after=rpc('wait',counts={'5':1})
        else: after=rpc('snapshot')
        record['after_click']=after; aftobs=observe(obs,ids); record['after_click_observer']=aftobs
        typed=click and decision('type',after,aftobs)
        if typed:
            call('key_chord',['7']); rpc('wait',counts={'2':1,'3':1})
        record['release']=call('release_all'); final=rpc('snapshot'); record['final']=final
        record['final_observer']=observe(obs,ids); record['after_capture']=capture(obs,root,'after',final['marker_xy'])
        record['geometry_after']=call('geometry','a')
        if record['final_observer']['button_mask'] or any(record['final_observer']['keymap']) or not record['release']['verified']:
            raise RuntimeError('STOP_NON_NEUTRAL_INPUT')
        record['close']=rpc('close'); p.stdin.close(); rest=p.stdout.read(); rc=p.wait(timeout=3)
        record['app_exit']=rc; record['stdout_tail']=rest
        if rc or rest: raise RuntimeError('unexpected application terminal')
        record['execution']='COMPLETE'
    except BaseException as e:
        record['execution']='STOP'; record['error']=repr(e); record['traceback']=traceback.format_exc()
    finally:
        if backend is not None:
            try: record['cleanup_release']=backend.release_all(); backend.close()
            except Exception as e: record['cleanup_error']=repr(e)
        if obs is not None: obs.close()
        if p.poll() is None:
            p.terminate()
            try: p.wait(timeout=2)
            except subprocess.TimeoutExpired: p.kill(); p.wait(timeout=2)
        record['observed_app_exit']=p.returncode; err.close(); record['app_stderr']=(root/'app.stderr').read_text()
        (root/'app.stdin').write_text(''.join(wire_in)); (root/'app.stdout').write_text(''.join(getattr(p,'wire_out',[]))+record.get('stdout_tail',''))
        record['elapsed_ns']=time.monotonic_ns()-start; dump(root/'record.json',record)
    return record

def server_start(root):
    # Private Xauthority: family-wild record; cookie never enters public evidence.
    priv=Path(tempfile.mkdtemp(prefix='ai-hit-',dir='/tmp')); os.chmod(priv,0o700)
    auth=priv/'Xauthority'; cookie=os.urandom(16)
    def fld(b): return struct.pack('>H',len(b))+b
    auth.write_bytes(struct.pack('>H',65535)+fld(b'')+fld(b'')+fld(b'MIT-MAGIC-COOKIE-1')+fld(cookie)); os.chmod(auth,0o600)
    r,w=os.pipe(); stderr=(root/'xvfb.stderr').open('w')
    cmd=['Xvfb','-displayfd',str(w),'-screen','0','640x360x24','-nolisten','tcp','-auth',str(auth),'-noreset']
    p=subprocess.Popen(cmd,pass_fds=(w,),stdout=subprocess.DEVNULL,stderr=stderr); os.close(w)
    if not select.select([r],[],[],3)[0]:
        p.terminate(); p.wait(timeout=2); raise TimeoutError('Xvfb displayfd')
    num=os.read(r,64).decode().strip(); os.close(r)
    if not num.isdigit(): raise RuntimeError('invalid displayfd')
    # Python-Xlib 0.15 requires an exact local-family entry; Xvfb accepts the initial wildcard.
    with auth.open('ab') as f:
        f.write(struct.pack('>H',256)+fld(os.uname().nodename.encode())+fld(num.encode())+fld(b'MIT-MAGIC-COOKIE-1')+fld(cookie))
    os.environ['XAUTHORITY']=str(auth); os.environ['DISPLAY']=':'+num
    return p,auth,priv,stderr,cmd,':'+num

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('mode',choices=['construction','formal']); ap.add_argument('out'); ap.add_argument('--batch',type=int,default=0); ap.add_argument('--single',type=int); args=ap.parse_args()
    if args.mode=='formal':
        if args.batch not in (0,1,2) or args.single is not None: raise RuntimeError('STOP_UNPLANNED_BATCH')
        if Path(args.out).resolve()!=HERE/'results'/f'formal-batch-{args.batch:02d}': raise RuntimeError('STOP_WRONG_OUTPUT')
        if args.batch:
            previous=HERE/'results'/f'formal-batch-{args.batch-1:02d}.execution.json'
            status=json.loads(previous.read_text())
            if type(status['returncode']) is not int or status['returncode']!=0 or status['timed_out'] is not False: raise RuntimeError('STOP_PREVIOUS_BATCH')
            prior=json.loads((HERE/'results'/f'formal-batch-{args.batch-1:02d}'/'END.json').read_text())
            if prior['error'] is not None or prior['server_exit']!=0: raise RuntimeError('STOP_PREVIOUS_INCOMPLETE')
        freeze=json.loads((HERE/'FREEZE.json').read_text())
        for n,h in freeze['sha256'].items():
            if digest((HERE/n).read_bytes())!=h: raise RuntimeError('STOP_SOURCE:'+n)
        rows=schedule()[args.batch*9:min((args.batch+1)*9,26)]
    else:
        rows=schedule()[:12]
        if args.single is not None: rows=[rows[args.single]]
    root=Path(args.out).resolve(); root.mkdir(parents=True,exist_ok=False)
    dump(root/'START.json',{'mode':args.mode,'batch':args.batch,'schedule':rows,'pid':os.getpid(),'monotonic_ns':time.monotonic_ns()})
    p=auth=priv=stderr=None; results=[]; summary={'mode':args.mode,'batch':args.batch,'error':None}
    try:
        p,auth,priv,stderr,cmd,dname=server_start(root); summary['server_pid']=p.pid; summary['server_command']=cmd; summary['display']=dname
        for cfg in rows:
            rec=one(root/f"case-{cfg['index']:02d}",cfg,dname,auth); results.append({'index':cfg['index'],'execution':rec['execution'],'final':rec.get('final')})
            print(json.dumps({'index':cfg['index'],'execution':rec['execution'],'values':{k:rec.get('final',{}).get(k) for k in ('a','b','counter')}}),flush=True)
            if rec['execution']!='COMPLETE': raise RuntimeError('case failed')
    except BaseException as e: summary['error']=repr(e); summary['traceback']=traceback.format_exc()
    finally:
        if p is not None:
            p.terminate()
            try: p.wait(timeout=3)
            except subprocess.TimeoutExpired: p.kill(); p.wait(timeout=2)
            summary['server_exit']=p.returncode; stderr.close()
            summary['socket_removed']=not Path('/tmp/.X11-unix/X'+summary['display'][1:]).exists()
        if auth is not None: auth.unlink(); priv.rmdir(); summary['auth_removed']=not auth.exists()
        summary['completed_cases']=len(results); summary['results']=results; summary['monotonic_ns']=time.monotonic_ns()
        dump(root/'END.json',summary)
    return int(summary['error'] is not None)
if __name__=='__main__': sys.exit(main())
