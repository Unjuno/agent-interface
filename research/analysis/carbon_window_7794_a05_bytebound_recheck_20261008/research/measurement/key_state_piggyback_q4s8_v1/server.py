"""Private Xvfb setup: consume the complete LF-terminated displayfd receipt."""
import os,secrets,select,subprocess,time
from upstream_infra import now,save,sha
class Server:
    def __init__(self,out):
        self.out=out;self.auth=out/'private.Xauthority';self.auth.touch(mode=0o600)
        self.cookie=secrets.token_hex(16);self.commands=[]
        self.base={'PATH':os.environ.get('PATH','/usr/bin:/bin'),'HOME':str(out),'LANG':'C.UTF-8',
                   'XAUTHORITY':str(self.auth),'PYTHONNOUSERSITE':'1','PYTHONDONTWRITEBYTECODE':'1'}
        self.xauth(':0')
        r,w=os.pipe();self.log=open(out/'xvfb.stdout','wb');self.err=open(out/'xvfb.stderr','wb')
        self.argv=['/usr/bin/Xvfb','-displayfd',str(w),'-screen','0','640x480x24','-nolisten','tcp','-auth',str(self.auth)]
        self.started=now();self.p=subprocess.Popen(self.argv,stdout=self.log,stderr=self.err,pass_fds=(w,),env=self.base)
        os.close(w)
        try:
            raw=bytearray();deadline=time.monotonic()+3
            while not raw.endswith(b'\n'):
                remaining=deadline-time.monotonic()
                if remaining<=0:raise TimeoutError('Xvfb complete displayfd line')
                ready,_,_=select.select([r],[],[],remaining)
                if not ready:raise TimeoutError('Xvfb displayfd')
                chunk=os.read(r,64)
                if not chunk:raise RuntimeError('Xvfb partial display number: '+repr(bytes(raw)))
                raw.extend(chunk)
                if len(raw)>32:raise RuntimeError('invalid displayfd frame')
            self.display_bytes=bytes(raw);number=int(self.display_bytes)
        except BaseException:
            self.p.terminate();self.p.wait(timeout=2);raise
        finally:os.close(r)
        self.display=f':{number}';self.socket=f'/tmp/.X11-unix/X{number}'
        self.xauth(self.display);self.env=dict(self.base,DISPLAY=self.display)
    def xauth(self,target):
        p=subprocess.run(['/usr/bin/xauth','-f',str(self.auth),'add',target,'.',self.cookie],capture_output=True,timeout=2)
        self.commands.append(dict(argv=['/usr/bin/xauth','-f',str(self.auth),'add',target,'.','<ephemeral-private-cookie>'],
                                  returncode=p.returncode,stdout=p.stdout.decode(),stderr=p.stderr.decode()))
        if p.returncode:raise RuntimeError('private Xauthority construction failed')
    def close(self):
        self.p.terminate();rc=self.p.wait(timeout=3);self.log.close();self.err.close()
        authhash=sha(self.auth.read_bytes());self.auth.unlink()
        save(self.out/'server.json',dict(argv=self.argv,pid=self.p.pid,start_ns=self.started,end_ns=now(),
              returncode=rc,display=self.display,displayfd_hex=self.display_bytes.hex(),socket=self.socket,
              socket_absent=not os.path.exists(self.socket),auth_removed=not self.auth.exists(),
              expired_auth_sha256=authhash,xauth=self.commands))
