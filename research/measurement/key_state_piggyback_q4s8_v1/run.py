"""Bounded private-X11 measurement. Construction and frozen runs use new paths."""
from pathlib import Path
import hashlib,json,os,selectors,signal,subprocess,sys,time,traceback
from upstream_infra import save,sha
from server import Server
import bundle
from native import Reader
HERE=Path(__file__).resolve().parent
CONTEXTS=('UP','DOWN','EDGE_BURST','FOCUS_RETURN')

class Actor:
    def __init__(self,role,out,env):
        self.role=role;self.out=out;self.seq=0;self.raw=b'';self.sel=selectors.DefaultSelector();self.closed=False
        self.stderr=open(out/(role+'.stderr'),'wb');self.wire=open(out/(role+'.wire.jsonl'),'x')
        self.argv=[sys.executable,'-B',str(HERE/'actor.py'),role]
        self.start=time.monotonic_ns()
        self.p=subprocess.Popen(self.argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.stderr,env=env,bufsize=0)
        self.sel.register(self.p.stdout,selectors.EVENT_READ)
        self.ready=self.read()
    def read(self):
        deadline=time.monotonic()+3
        while b'\n' not in self.raw:
            remaining=deadline-time.monotonic()
            if remaining<=0 or not self.sel.select(remaining):raise TimeoutError(self.role)
            b=os.read(self.p.stdout.fileno(),65536)
            if not b:raise RuntimeError(self.role+' closed pipe')
            self.raw+=b
            if len(self.raw)>2**20:raise RuntimeError('oversize actor line')
        line,self.raw=self.raw.split(b'\n',1)
        self.wire.write(json.dumps({'direction':'out','ns':time.monotonic_ns(),'text':(line+b'\n').decode()})+'\n');self.wire.flush()
        return json.loads(line)
    def call(self,op,**kw):
        self.seq+=1;req=dict(id=self.seq,op=op,**kw)
        line=json.dumps(req,sort_keys=True)+'\n'
        self.wire.write(json.dumps({'direction':'in','ns':time.monotonic_ns(),'text':line})+'\n');self.wire.flush()
        self.p.stdin.write(line.encode());self.p.stdin.flush();ans=self.read()
        if ans.get('id')!=self.seq or ans.get('op')!=op:raise RuntimeError('actor correlation')
        return ans
    def close(self):
        if self.closed:return
        self.closed=True;error=None
        try:self.call('close');self.p.stdin.close();rc=self.p.wait(timeout=3)
        except Exception as e:
            error=repr(e);self.p.terminate()
            try:rc=self.p.wait(timeout=2)
            except subprocess.TimeoutExpired:self.p.kill();rc=self.p.wait(timeout=2)
        self.stderr.close();self.wire.close();self.sel.close()
        save(self.out/(self.role+'.process.json'),dict(argv=self.argv,pid=self.p.pid,start_ns=self.start,end_ns=time.monotonic_ns(),returncode=rc,error=error,role=self.role))
        if error or rc:raise RuntimeError('actor exit '+str((error,rc)))

def freeze_check():
    f=json.loads((HERE/'FREEZE.json').read_bytes())
    for n,h in f['files'].items():
        if sha((HERE/n).read_bytes())!=h:raise RuntimeError('source drift '+n)
    return sha((HERE/'FREEZE.json').read_bytes())

def run(out,context,formal):
    if context not in CONTEXTS:raise ValueError('context')
    frozen=freeze_check() if formal else None
    out.mkdir(parents=True,exist_ok=False)
    os.sched_setaffinity(0,{0})
    save(out/'START.json',dict(pid=os.getpid(),start_ns=time.monotonic_ns(),context=context,formal=formal,freeze=frozen,affinity=list(os.sched_getaffinity(0))))
    original={k:os.environ.get(k) for k in ('DISPLAY','XAUTHORITY')}
    server=None;writer=None;witness=None;readers=[];completed=0;failure=None
    try:
        server=Server(out)
        os.environ.update({k:server.env[k] for k in ('DISPLAY','XAUTHORITY')})
        lib=bundle.load();writer=Actor('writer',out,server.env);witness=Actor('witness',out,server.env)
        for index in range(3 if formal else 1):
            epoch=context+'-'+str(index);fresh=writer.call('new');v=fresh['result'];target=v['target'];seed=v['state']['keymap'];code=v['state']['keycode']
            if any(bytes.fromhex(seed)):raise RuntimeError('initial keys not neutral')
            readers=[Reader(lib,target,code,seed,True,epoch) for _ in range(4)]
            bootstrap=[r.bootstrap() for r in readers]
            mutation=writer.call('mutate',context=context);before=witness.call('snapshot')
            other_reply=bundle.focus(readers[0])
            other_local=readers[3].observe('LOCAL_ONLY')
            other_sync=readers[3].observe('EVENT_SYNC')
            samples=[]
            for sample in range(17 if formal else 4):
                for i in range(3):
                    arm=(i+sample+index)%3
                    value=bundle.collect(readers[arm],bundle.MODES[arm]);value.update(sample=sample,arm_order=i)
                    samples.append(value)
            after=witness.call('snapshot');release=writer.call('release');neutral=witness.call('snapshot')
            for reader in readers:reader.close()
            readers=[]
            raw=dict(context=context,index=index,epoch=epoch,target=target,code=code,seed=seed,fresh=fresh,bootstrap=bootstrap,
                     mutation=mutation,before=before,other_reply=other_reply,other_local=other_local,other_sync=other_sync,
                     samples=samples,after=after,release=release,neutral=neutral)
            save(out/('block-%02d.json'%index),raw);completed+=1
    except BaseException:
        failure=traceback.format_exc();save(out/'STOP.json',dict(error=failure,completed=completed));raise
    finally:
        cleanup=[]
        for reader in readers:
            try:reader.close()
            except Exception as e:cleanup.append(repr(e))
        for actor in (writer,witness):
            if actor:
                try:actor.close()
                except Exception as e:cleanup.append(repr(e))
        if server:
            try:server.close()
            except Exception as e:cleanup.append(repr(e))
        for k,v in original.items():
            if v is None:os.environ.pop(k,None)
            else:os.environ[k]=v
        save(out/'END.json',dict(pid=os.getpid(),end_ns=time.monotonic_ns(),completed=completed,failure=failure,cleanup_errors=cleanup))
        if cleanup and failure is None:raise RuntimeError('cleanup '+str(cleanup))

if __name__=='__main__':
    def stopped(signum,frame):raise TimeoutError('supervisor termination')
    signal.signal(signal.SIGTERM,stopped)
    run(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3]=='formal')
