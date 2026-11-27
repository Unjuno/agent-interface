"""Experimental outer Job host: concurrent binary drain, no model-readiness claim."""
import hashlib
import math
from pathlib import Path
import threading
import time

from win_job_spawn import AtomicJobProcess


def _deadline(timeout):
    if type(timeout) not in (int,float) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('positive finite timeout required')
    return time.monotonic()+timeout


class _Reader:
    def __init__(self, name, stream, output, failure):
        self.name=name;self.stream=stream;self.output=output;self.failure=failure
        self.done=threading.Event();self.attempted=False;self.started=False;self.start_state='not_attempted';self.eof=False;self.errors=[];self.bytes=0;self.sha256=None
        self.thread=threading.Thread(target=self._run,name='job-host-'+name,daemon=True)
    def start(self):
        self.attempted=True;self.start_state='unknown'
        # Once Thread.start is entered, an exception may arrive after native
        # creation but before ident/alive state is published. Keep ownership.
        self.thread.start()
        self.started=True;self.start_state='started'
    def _run(self):
        digest=hashlib.sha256()
        try:
            while True:
                data=self.stream.read(65536)
                if type(data) is not bytes:raise OSError('indeterminate pipe read')
                if data==b'':
                    self.eof=True;break
                remaining=memoryview(data)
                while remaining:
                    written=self.output.write(remaining)
                    if type(written) is not int or written<=0 or written>len(remaining):raise OSError('log write made no progress')
                    digest.update(remaining[:written]);self.bytes+=written;remaining=remaining[written:]
        except BaseException as exc:
            self.errors.append(type(exc).__name__);self.failure.set()
        finally:
            try:self.output.close()
            except BaseException as exc:self.errors.append(type(exc).__name__);self.failure.set()
            self.sha256=digest.hexdigest();self.done.set()
    def snapshot(self):
        return {'attempted':self.attempted,'started':self.started,'start_state':self.start_state,'done':self.done.is_set(),'eof':self.eof,
                'errors':list(self.errors),'bytes':self.bytes,'sha256':self.sha256}


class JobHost:
    """One host, one control thread. No automatic model, input or process-tree success claim."""
    def __init__(self, argv, allocation, *, cwd=None, environment=None):
        self.root=Path(allocation);self.owner=threading.get_ident();self.failure=threading.Event()
        self.process=AtomicJobProcess(argv,stdio=True,cwd=cwd,environment=environment)
        self.readers={};self.start_attempted=False;self.start_complete=False;self.final=None

    def _check_owner(self):
        if threading.get_ident()!=self.owner:raise RuntimeError('one control thread required')

    def start(self):
        self._check_owner()
        if self.start_attempted:raise RuntimeError('start already attempted')
        self.start_attempted=True;opened=[]
        try:
            for name in ('stdout','stderr'):
                opened.append((self.root/(name+'.bin')).open('xb',buffering=0))
            self.process.start()
            self.process.stdin.close()
            self.readers={'stdout':_Reader('stdout',self.process.stdout,opened[0],self.failure),
                          'stderr':_Reader('stderr',self.process.stderr,opened[1],self.failure)}
            for reader in self.readers.values():reader.start()
            self.process.resume();self.start_complete=True
        except BaseException as exc:
            for output in opened:
                if all(reader.output is not output or reader.start_state in ('not_attempted','not_started') for reader in self.readers.values()):
                    try:output.close()
                    except BaseException as cleanup_exc:exc.add_note('log close error: '+repr(cleanup_exc))
            try:
                receipt=self.close(timeout_s=5)
                if receipt.get('status')!='closed_scoped':exc.add_note('cleanup unconfirmed: '+repr(receipt))
            except BaseException as cleanup_exc:exc.add_note('cleanup error: '+repr(cleanup_exc))
            raise

    def wait(self, *, timeout_s):
        self._check_owner();deadline=_deadline(timeout_s)
        if not self.start_complete:return {'status':'UNKNOWN','reason':'start_unconfirmed'}
        while True:
            if self.failure.is_set():return {'status':'UNKNOWN','reason':'reader_error'}
            remaining=deadline-time.monotonic()
            if remaining<=0:return {'status':'UNKNOWN','reason':'deadline'}
            try:
                code=self.process.wait(min(.1,remaining))
                if self.failure.is_set():return {'status':'UNKNOWN','reason':'reader_error','observed_exit_code':code}
                if time.monotonic()>=deadline:return {'status':'UNKNOWN','reason':'deadline','observed_exit_code':code}
                return {'status':'exited','exit_code':code}
            except TimeoutError:pass
            except Exception as exc:return {'status':'UNKNOWN','reason':'wait_error','error_type':type(exc).__name__}

    def close(self, *, timeout_s):
        self._check_owner();deadline=_deadline(timeout_s)
        if self.final is not None:return self.final
        try:process=self.process.close(timeout_s=max(0,deadline-time.monotonic()))
        except Exception as exc:process={'job_closed':False,'process_exited':False,'kernel_handles_closed':False,'errors':[{'type':type(exc).__name__}]}
        for reader in self.readers.values():
            if reader.thread.ident is not None:reader.thread.join(timeout=max(0,deadline-time.monotonic()))
        readers={name:reader.snapshot() for name,reader in self.readers.items()}
        joined=all(r.start_state in ('not_attempted','not_started') or (r.thread.ident is not None and not r.thread.is_alive()) for r in self.readers.values())
        streams=self.process.close_streams() if joined else {'streams_closed':False,'errors':[{'type':'reader_still_alive'}]}
        deadline_exceeded=time.monotonic()>=deadline
        good=(not deadline_exceeded and process.get('job_closed') is True and process.get('process_exited') is True
              and process.get('kernel_handles_closed') is True and not process.get('errors')
              and joined and len(readers)==2 and all(r['start_state']=='started' and r['started'] and r['done'] and r['eof'] and not r['errors'] for r in readers.values())
              and streams.get('streams_closed') is True and not streams.get('errors'))
        result={'status':'closed_scoped' if good else 'UNKNOWN','process':process,'readers':readers,'streams':streams,'deadline_exceeded':deadline_exceeded}
        if good:self.final=result
        return result
