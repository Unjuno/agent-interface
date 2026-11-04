"""Research WSLc container driver; no host custody or input-release guarantees."""
import base64
from functools import partial
import json
import math
import os
from pathlib import Path
import re
import subprocess
import time

from recovery import reconcile_owned
from wslc_cleanup import cleanup_owned


def _run(args, timeout):
    return subprocess.run(args, capture_output=True, timeout=timeout, check=False)


def _budget(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
        raise ValueError('positive finite timeout required')
    return time.monotonic() + value


class ContainerDriver:
    """One attempt only. Persist raw journal privately; do not use as parent-death custody."""
    def __init__(self, allocation, run_id, image, command, *, mounts=None, environment=None, runner=_run):
        self.root = Path(allocation)
        if not re.fullmatch('[0-9a-f]{32}', run_id) or not re.fullmatch('sha256:[0-9a-f]{64}', image):
            raise ValueError('invalid identity or image')
        if not isinstance(command, list) or not command or any(not isinstance(x,str) or not x or '\0' in x for x in command):
            raise ValueError('command must be nonempty strings')
        args = ['wslc','run','--detach','--name','ai-calc-'+run_id[:16],
                '--label','agent-interface.run-id='+run_id,'--cidfile',str(self.root/'container.cid'),
                '--network','none','--cpus','1','--memory','1g','--pull','never']
        for target, pair in (mounts or {}).items():
            if target not in ('/src','/in','/out','/exchange') or not isinstance(pair,tuple) or len(pair)!=2:
                raise ValueError('invalid mount')
            path, readonly = pair
            path = Path(path).resolve(strict=True)
            if not path.is_dir() or type(readonly) is not bool or (target in ('/src','/in') and not readonly):
                raise ValueError('invalid mount')
            if any(c in str(path) for c in ',\n\r'):
                raise ValueError('unsafe mount path')
            args += ['--mount','type=bind,source='+str(path)+',target='+target+(',readonly' if readonly else '')]
        for key,value in (environment or {}).items():
            if not isinstance(key,str) or not re.fullmatch('[A-Z_][A-Z0-9_]*',key) or not isinstance(value,str) or '\0' in value:
                raise ValueError('invalid environment')
            args += ['--env',key+'='+value]
        args += ['--entrypoint',command[0],image,*command[1:]]
        self.run_id=run_id;self.args=args;self.runner=runner;self.cid=None;self.started=False;self.start_confirmed=False;self.counter=0
        self.cidfile=self.root/'container.cid';self.journal=self.root/'commands.jsonl'
        if self.cidfile.exists() or self.journal.exists():raise FileExistsError('preexisting attempt file')
        with (self.root/'identity.json').open('x',encoding='utf-8') as f:
            json.dump({'run_id':run_id,'image':image,'argv':args},f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        with self.journal.open('x',encoding='utf-8') as f:
            f.flush();os.fsync(f.fileno())

    def _log(self, data):
        with self.journal.open('a',encoding='utf-8') as f:
            f.write(json.dumps(data,sort_keys=True)+'\n');f.flush();os.fsync(f.fileno())

    def _call(self, args, deadline, *, allow_stderr=False):
        remaining=deadline-time.monotonic()
        if remaining<=0:return None
        self.counter+=1; seq=self.counter
        self._log({'event':'intent','seq':seq,'argv':args,'time_ns':time.monotonic_ns()})
        remaining=deadline-time.monotonic()
        if remaining<=0:
            self._log({'event':'not_invoked','seq':seq,'reason':'deadline'});return None
        try:p=self.runner(args,timeout=remaining)
        except (OSError,subprocess.TimeoutExpired) as exc:
            event={'event':'error','seq':seq,'type':type(exc).__name__,'time_ns':time.monotonic_ns()}
            if isinstance(exc,subprocess.TimeoutExpired):
                for field in ('stdout','stderr'):
                    value=getattr(exc,field,None)
                    if isinstance(value,bytes):event[field+'_b64']=base64.b64encode(value).decode('ascii')
            self._log(event);return None
        self._log({'event':'returned','seq':seq,'exit':p.returncode,'stdout_b64':base64.b64encode(p.stdout).decode('ascii'),
                   'stderr_b64':base64.b64encode(p.stderr).decode('ascii'),'time_ns':time.monotonic_ns()})
        if p.returncode or (p.stderr and not allow_stderr) or time.monotonic()>=deadline:return None
        return p.stdout

    def _read_cid(self):
        try: value=self.cidfile.read_text(encoding='ascii').strip()
        except (OSError,UnicodeError):return None
        return value if re.fullmatch('[0-9a-f]{64}',value) else None

    def _inspect(self, deadline):
        raw=self._call(['wslc','container','inspect',self.cid,'--format','json'],deadline)
        try:
            rows=json.loads(raw)
            if not isinstance(rows,list) or len(rows)!=1 or not isinstance(rows[0],dict):return {'status':'UNKNOWN'}
            item=rows[0];state=item['State']
            if item.get('Id')!=self.cid or item['Config']['Labels'].get('agent-interface.run-id')!=self.run_id:return {'status':'UNKNOWN'}
            if state.get('Running') is True and state.get('Status')=='running':return {'status':'running','cid':self.cid}
            if state.get('Running') is False and state.get('Status')=='exited' and type(state.get('ExitCode')) is int:
                return {'status':'exited','cid':self.cid,'exit_code':state['ExitCode']}
        except (ValueError,TypeError,KeyError,AttributeError):pass
        return {'status':'UNKNOWN'}

    def start(self, *, timeout_s):
        deadline=_budget(timeout_s)
        if self.started:raise RuntimeError('attempt already started')
        self.started=True
        launched=self._call(self.args,deadline,allow_stderr=True)
        if launched is None:return {'status':'UNKNOWN'}
        while time.monotonic()<deadline:
            self.cid=self._read_cid()
            if self.cid:
                if launched.strip()!=self.cid.encode('ascii'):return {'status':'UNKNOWN'}
                result=self._inspect(deadline)
                self.start_confirmed=result.get('status') in ('running','exited')
                return result
            time.sleep(min(.05,max(0,deadline-time.monotonic())))
        return {'status':'UNKNOWN'}

    def wait(self, *, timeout_s):
        deadline=_budget(timeout_s)
        if not self.started or not self.cid or not self.start_confirmed:return {'status':'UNKNOWN'}
        while time.monotonic()<deadline:
            state=self._inspect(deadline)
            if state['status']!='running':return state
            time.sleep(min(.1,max(0,deadline-time.monotonic())))
        return {'status':'UNKNOWN','reason':'deadline'}

    def reconcile(self, *, timeout_s):
        if not self.started:return {'task_status':'UNKNOWN','reason':'not_started'}
        self.cid=self.cid or self._read_cid()
        if not self.cid:return {'task_status':'UNKNOWN','reason':'cid_unavailable'}
        return reconcile_owned(self.cid,self.run_id,self.root,timeout_s=timeout_s,
                               cleanup=partial(cleanup_owned,runner=self.runner))
