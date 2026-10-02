"""One bounded batch; only the fresh authenticated Xvfb is given to probe."""
from pathlib import Path
import hashlib, json, os, secrets, selectors, socket, struct, subprocess, sys, time
HERE=Path(__file__).resolve().parent

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x): p.write_text(json.dumps(x,sort_keys=True,indent=2)+'\n')
def main():
    dest=Path(sys.argv[1]); rep=int(sys.argv[2]); samples=int(sys.argv[3])
    if not 0<=rep<5 or samples not in (3,32): raise ValueError('allocation bounds')
    if samples==32:
        freeze=json.loads((HERE/'FREEZE.json').read_text())
        for name,h in freeze['files'].items():
            if digest(HERE/name)!=h: raise ValueError('frozen source changed: '+name)
    dest.mkdir(parents=True,exist_ok=False)
    env={k:v for k,v in os.environ.items() if k not in ('DISPLAY','XAUTHORITY')}
    auth=dest/'private.auth'; cookie=secrets.token_bytes(16)
    # FamilyWild credential is restricted by its private filesystem path and server.
    fields=[b'',b'',b'MIT-MAGIC-COOKIE-1',cookie]
    auth.write_bytes(struct.pack('!H',65535)+b''.join(struct.pack('!H',len(v))+v for v in fields));auth.chmod(0o600)
    r,w=os.pipe(); cmd=['Xvfb','-displayfd',str(w),'-screen','0','320x200x24','-nolisten','tcp','-noreset','-auth',str(auth)]
    log=(dest/'server.stderr').open('wb'); start=time.monotonic_ns()
    server=subprocess.Popen(cmd,pass_fds=(w,),stdout=subprocess.DEVNULL,stderr=log,env=env);os.close(w)
    blocks=[]; display=None
    try:
        with selectors.DefaultSelector() as sel:
            sel.register(r,selectors.EVENT_READ)
            if not sel.select(3):raise TimeoutError('Xvfb displayfd')
            display=':'+os.read(r,32).decode().strip()
        env.update(DISPLAY=display,XAUTHORITY=str(auth))
        for s in range(4):
            for k in range(3):
                arm=(k+rep+s)%3; ident=f'{s}-{arm}'
                argv=[str(HERE/'probe'),display,str(arm),str(s),str(samples),'2']
                t0=time.monotonic_ns()
                proc=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env)
                try: out,err=proc.communicate(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill();out,err=proc.communicate();err+=b'\nPROBE_TIMEOUT\n'
                (dest/(ident+'.jsonl')).write_bytes(out);(dest/(ident+'.stderr')).write_bytes(err)
                receipt=dict(rep=rep,scenario=s,arm=arm,pid=proc.pid,argv=argv,returncode=proc.returncode,before_ns=t0,after_ns=time.monotonic_ns(),stdout_sha256=hashlib.sha256(out).hexdigest(),stderr_sha256=hashlib.sha256(err).hexdigest())
                save(dest/(ident+'.process.json'),receipt);blocks.append(receipt)
                if proc.returncode or err:raise RuntimeError('probe failed '+ident)
        save(dest/'COMPLETE.json',dict(rep=rep,samples=samples,blocks=blocks))
    except BaseException as exc:
        save(dest/'STOP.json',dict(type=type(exc).__name__,detail=str(exc),complete_blocks=len(blocks)));raise
    finally:
        os.close(r);server.terminate()
        try: rc=server.wait(timeout=3)
        except subprocess.TimeoutExpired: server.kill();rc=server.wait(timeout=3)
        log.close();auth.unlink(missing_ok=True)
        sock='/tmp/.X11-unix/X'+display[1:] if display else None
        save(dest/'SERVER.json',dict(pid=server.pid,argv=cmd,returncode=rc,before_ns=start,after_ns=time.monotonic_ns(),socket_removed=sock is not None and not Path(sock).exists(),auth_removed=not auth.exists(),display=display))
if __name__=='__main__': main()
