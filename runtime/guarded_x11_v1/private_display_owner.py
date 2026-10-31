"""Experimental owner of one newly launched, disposable Xvfb process.

This primitive does not integrate cancellation or confer ownership of clients.
The caller must treat every application on this display as disposable.
"""
from dataclasses import dataclass
import os
from pathlib import Path
import secrets
import select
import signal
import subprocess
import threading
import time

@dataclass(frozen=True)
class PrivateDisplay:
    display: str
    authority: Path

class PrivateDisplayOwner:
    def __init__(self, directory):
        self.directory=Path(directory)
        self._process=None
        self._pidfd=None
        self._session=None
        self._retired=False
        self._lock=threading.Lock()
        self._cleanup_lock=threading.RLock()
        self._closed=False
        self._starting=False
        self._kill_requested=False

    def _auth_add(self, display, cookie, timeout):
        subprocess.run(['xauth','-f',str(self.directory/'authority'),'-'],
                       input=f'add {display} . {cookie}\n',text=True,
                       stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                       check=True,timeout=timeout)

    def start(self, *, timeout_s):
        if not callable(getattr(os,'pidfd_open',None)) or not callable(getattr(signal,'pidfd_send_signal',None)):
            raise RuntimeError('pidfd support required')
        if not isinstance(timeout_s,(int,float)) or isinstance(timeout_s,bool) or timeout_s<=0:
            raise ValueError('positive timeout required')
        with self._lock:
            if self._closed or self._starting or self._process is not None or self._retired:
                raise RuntimeError('display owner is single use')
            self._starting=True
        deadline=time.monotonic()+timeout_s
        read_fd=write_fd=None
        try:
            self.directory.mkdir(mode=0o700,parents=False,exist_ok=False)
            authority=self.directory/'authority'
            fd=os.open(authority,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.close(fd)
            cookie=secrets.token_hex(16)
            self._auth_add(':0',cookie,max(0.001,deadline-time.monotonic()))
            read_fd,write_fd=os.pipe()
            with self._lock:
                if self._closed:raise RuntimeError('display owner closed during startup')
                self._process=subprocess.Popen(['Xvfb','-displayfd',str(write_fd),'-screen','0','640x480x24',
                    '-nolisten','tcp','-auth',str(authority)],pass_fds=(write_fd,),
                    stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                self._pidfd=os.pidfd_open(self._process.pid)
            os.close(write_fd);write_fd=None
            remaining=deadline-time.monotonic()
            if remaining<=0 or not select.select([read_fd],[],[],remaining)[0]:
                raise TimeoutError('display startup deadline')
            number=os.read(read_fd,32).strip()
            if not number.isdigit() or self._process.poll() is not None:
                raise RuntimeError('display startup failed')
            display=':'+number.decode('ascii')
            self._auth_add(display,cookie,max(0.001,deadline-time.monotonic()))
            with self._lock:
                if self._closed:raise RuntimeError('display owner closed during startup')
                if time.monotonic() >= deadline:raise TimeoutError('display startup deadline')
                self._session=PrivateDisplay(display,authority)
                self._starting=False
                return self._session
        except BaseException as startup_error:
            if self._process is not None:
                if self._pidfd is not None:
                    try:signal.pidfd_send_signal(self._pidfd,signal.SIGKILL)
                    except ProcessLookupError:pass
                    self._kill_requested=True
                elif self._process.poll() is None:
                    # The unreaped direct child cannot have had its PID reused.
                    self._process.kill()
                    self._kill_requested=True
                else:
                    self._kill_requested=True
                try:self._process.wait(timeout=0.25)
                except subprocess.TimeoutExpired:
                    raise RuntimeError('display startup failed; cleanup unconfirmed') from startup_error
                self._retired=True
            raise
        finally:
            with self._lock:
                self._starting=False
                if self._closed and self._retired and self._pidfd is not None:
                    os.close(self._pidfd);self._pidfd=None
            if read_fd is not None:os.close(read_fd)
            if write_fd is not None:os.close(write_fd)

    def retire(self, *, timeout_s):
        with self._cleanup_lock:
            with self._lock:
                if self._starting:
                    self._closed=True
                    if self._pidfd is not None:
                        try:signal.pidfd_send_signal(self._pidfd,signal.SIGKILL)
                        except ProcessLookupError:pass
                    return {'status':'pending'}
            return self._retire_locked(timeout_s=timeout_s)

    def _retire_locked(self, *, timeout_s):
        if self._retired:return {'status':'retired'}
        if self._process is None:raise RuntimeError('no owned display')
        if self._pidfd is None:
            if not self._kill_requested:raise RuntimeError('no owned display')
            # After a pidfd-open failure, only wait for the direct child already
            # signalled during startup cleanup; never issue a PID-based retry.
        else:
            try:signal.pidfd_send_signal(self._pidfd,signal.SIGKILL)
            except ProcessLookupError:pass
            self._kill_requested=True
        try:self._process.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:return {'status':'unknown'}
        self._retired=True
        return {'status':'retired'}

    def close(self):
        with self._cleanup_lock:
            return self._close_locked()

    def _close_locked(self):
        with self._lock:
            self._closed=True
            if self._starting:
                if self._pidfd is not None:
                    try:signal.pidfd_send_signal(self._pidfd,signal.SIGKILL)
                    except ProcessLookupError:pass
                return {'status':'pending'}
        if self._process is not None and not self._retired:
            result=self.retire(timeout_s=3)
            if result['status']!='retired':raise RuntimeError('display retirement unconfirmed')
        if self._pidfd is not None:os.close(self._pidfd);self._pidfd=None
        return {'status':'retired' if self._retired else 'closed_no_process'}
