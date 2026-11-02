"""Windows-only research prototype: create a suspended process directly in a private job.

Optional experimental stdio; no model, production shutdown, or general custody claim.
"""
import ctypes
from ctypes import wintypes
import math
import os
import subprocess
import sys

if sys.platform == 'win32':
    k = ctypes.WinDLL('kernel32', use_last_error=True)
    class IO_COUNTERS(ctypes.Structure):
        _fields_=[(n,ctypes.c_ulonglong) for n in ('ReadOperationCount','WriteOperationCount','OtherOperationCount','ReadTransferCount','WriteTransferCount','OtherTransferCount')]
    class BASIC_LIMIT(ctypes.Structure):
        _fields_=[('PerProcessUserTimeLimit',ctypes.c_longlong),('PerJobUserTimeLimit',ctypes.c_longlong),('LimitFlags',wintypes.DWORD),('MinimumWorkingSetSize',ctypes.c_size_t),('MaximumWorkingSetSize',ctypes.c_size_t),('ActiveProcessLimit',wintypes.DWORD),('Affinity',ctypes.c_size_t),('PriorityClass',wintypes.DWORD),('SchedulingClass',wintypes.DWORD)]
    class EXTENDED_LIMIT(ctypes.Structure):
        _fields_=[('BasicLimitInformation',BASIC_LIMIT),('IoInfo',IO_COUNTERS),('ProcessMemoryLimit',ctypes.c_size_t),('JobMemoryLimit',ctypes.c_size_t),('PeakProcessMemoryUsed',ctypes.c_size_t),('PeakJobMemoryUsed',ctypes.c_size_t)]
    class STARTUPINFO(ctypes.Structure):
        _fields_=[('cb',wintypes.DWORD),('lpReserved',wintypes.LPWSTR),('lpDesktop',wintypes.LPWSTR),('lpTitle',wintypes.LPWSTR),('dwX',wintypes.DWORD),('dwY',wintypes.DWORD),('dwXSize',wintypes.DWORD),('dwYSize',wintypes.DWORD),('dwXCountChars',wintypes.DWORD),('dwYCountChars',wintypes.DWORD),('dwFillAttribute',wintypes.DWORD),('dwFlags',wintypes.DWORD),('wShowWindow',wintypes.WORD),('cbReserved2',wintypes.WORD),('lpReserved2',ctypes.POINTER(ctypes.c_byte)),('hStdInput',wintypes.HANDLE),('hStdOutput',wintypes.HANDLE),('hStdError',wintypes.HANDLE)]
    class STARTUPINFOEX(ctypes.Structure):
        _fields_=[('StartupInfo',STARTUPINFO),('lpAttributeList',ctypes.c_void_p)]
    class PROCESS_INFORMATION(ctypes.Structure):
        _fields_=[('hProcess',wintypes.HANDLE),('hThread',wintypes.HANDLE),('dwProcessId',wintypes.DWORD),('dwThreadId',wintypes.DWORD)]
    k.CreateJobObjectW.argtypes=[ctypes.c_void_p,wintypes.LPCWSTR];k.CreateJobObjectW.restype=wintypes.HANDLE
    k.SetInformationJobObject.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD];k.SetInformationJobObject.restype=wintypes.BOOL
    k.InitializeProcThreadAttributeList.argtypes=[ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,ctypes.POINTER(ctypes.c_size_t)];k.InitializeProcThreadAttributeList.restype=wintypes.BOOL
    k.UpdateProcThreadAttribute.argtypes=[ctypes.c_void_p,wintypes.DWORD,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_void_p];k.UpdateProcThreadAttribute.restype=wintypes.BOOL
    k.DeleteProcThreadAttributeList.argtypes=[ctypes.c_void_p];k.DeleteProcThreadAttributeList.restype=None
    k.CreateProcessW.argtypes=[wintypes.LPCWSTR,wintypes.LPWSTR,ctypes.c_void_p,ctypes.c_void_p,wintypes.BOOL,wintypes.DWORD,ctypes.c_void_p,wintypes.LPCWSTR,ctypes.c_void_p,ctypes.POINTER(PROCESS_INFORMATION)];k.CreateProcessW.restype=wintypes.BOOL
    k.IsProcessInJob.argtypes=[wintypes.HANDLE,wintypes.HANDLE,ctypes.POINTER(wintypes.BOOL)];k.IsProcessInJob.restype=wintypes.BOOL
    k.ResumeThread.argtypes=[wintypes.HANDLE];k.ResumeThread.restype=wintypes.DWORD
    k.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD];k.WaitForSingleObject.restype=wintypes.DWORD
    k.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)];k.GetExitCodeProcess.restype=wintypes.BOOL
    k.CloseHandle.argtypes=[wintypes.HANDLE];k.CloseHandle.restype=wintypes.BOOL
    k.TerminateProcess.argtypes=[wintypes.HANDLE,wintypes.UINT];k.TerminateProcess.restype=wintypes.BOOL


def _error(where):
    return OSError(ctypes.get_last_error(),where)


class AtomicJobProcess:
    def __init__(self, argv, *, stdio=False, cwd=None, environment=None):
        if sys.platform!='win32':raise OSError('Windows required')
        if type(stdio) is not bool:raise ValueError('stdio must be boolean')
        if not isinstance(argv,list) or not argv or any(not isinstance(x,str) or not x or '\0' in x for x in argv) or not os.path.isabs(argv[0]):
            raise ValueError('absolute executable and nonempty arguments required')
        if cwd is not None:
            cwd=os.fsdecode(cwd)
            if not os.path.isabs(cwd) or not os.path.isdir(cwd) or '\0' in cwd:raise ValueError('existing absolute cwd required')
        env_block=None
        if environment is not None:
            if not isinstance(environment,dict):raise ValueError('environment must be a dict')
            keys=set()
            for key,value in environment.items():
                if not isinstance(key,str) or not key or '=' in key or '\0' in key or not isinstance(value,str) or '\0' in value:
                    raise ValueError('invalid environment entry')
                normalized=key.upper()
                if normalized in keys:raise ValueError('duplicate environment key')
                keys.add(normalized)
            env_block='\0'.join(key+'='+environment[key] for key in sorted(environment,key=str.upper))+'\0\0'
        self.cwd=cwd;self.environment_block=env_block
        self.job=None;self.process=None;self.thread=None;self.pid=None;self.suspended=True
        self.stdio=stdio;self.stdin=None;self.stdout=None;self.stderr=None;self._raw_fds=set();self._unknown_raw_fds=set();self.pipe_close_errors=[];self.stream_close_errors=[]
        self.argv=list(argv);self.start_attempted=False;self.start_complete=False;self.closing=False;self.membership_confirmed=False;self.pi=PROCESS_INFORMATION()

    def start(self):
        if self.start_attempted or self.closing:raise RuntimeError('start unavailable')
        self.start_attempted=True
        argv=self.argv
        attrs=None;initialized=False
        try:
            child_handles=None
            if self.stdio:
                import msvcrt
                ends=[]
                for name,child_reads in (('stdin',True),('stdout',False),('stderr',False)):
                    read_fd,write_fd=os.pipe();self._raw_fds.update((read_fd,write_fd))
                    child_fd,parent_fd=(read_fd,write_fd) if child_reads else (write_fd,read_fd)
                    os.set_handle_inheritable(msvcrt.get_osfhandle(child_fd),True)
                    os.set_handle_inheritable(msvcrt.get_osfhandle(parent_fd),False)
                    stream=os.fdopen(parent_fd,'wb' if child_reads else 'rb',buffering=0)
                    self._raw_fds.remove(parent_fd);setattr(self,name,stream)
                    ends.append(msvcrt.get_osfhandle(child_fd))
                child_handles=(wintypes.HANDLE*3)(*ends)
            self.job=k.CreateJobObjectW(None,None)
            if not self.job:raise _error('CreateJobObjectW')
            limits=EXTENDED_LIMIT();limits.BasicLimitInformation.LimitFlags=0x2000
            if not k.SetInformationJobObject(self.job,9,ctypes.byref(limits),ctypes.sizeof(limits)):raise _error('SetInformationJobObject')
            size=ctypes.c_size_t(0);ctypes.set_last_error(0)
            initial=k.InitializeProcThreadAttributeList(None,2 if self.stdio else 1,0,ctypes.byref(size))
            if initial or ctypes.get_last_error()!=122 or not size.value:raise _error('InitializeProcThreadAttributeList size')
            attrs=ctypes.create_string_buffer(size.value)
            if not k.InitializeProcThreadAttributeList(attrs,2 if self.stdio else 1,0,ctypes.byref(size)):raise _error('InitializeProcThreadAttributeList')
            initialized=True
            jobs=(wintypes.HANDLE*1)(self.job)
            if not k.UpdateProcThreadAttribute(attrs,0,0x0002000D,ctypes.cast(jobs,ctypes.c_void_p),ctypes.sizeof(jobs),None,None):raise _error('UpdateProcThreadAttribute JOB_LIST')
            if self.stdio and not k.UpdateProcThreadAttribute(attrs,0,0x00020002,ctypes.cast(child_handles,ctypes.c_void_p),ctypes.sizeof(child_handles),None,None):raise _error('UpdateProcThreadAttribute HANDLE_LIST')
            startup=STARTUPINFOEX();startup.StartupInfo.cb=ctypes.sizeof(startup);startup.lpAttributeList=ctypes.cast(attrs,ctypes.c_void_p)
            if self.stdio:
                startup.StartupInfo.dwFlags|=0x100
                startup.StartupInfo.hStdInput=child_handles[0];startup.StartupInfo.hStdOutput=child_handles[1];startup.StartupInfo.hStdError=child_handles[2]
            pi=self.pi;cmd=ctypes.create_unicode_buffer(subprocess.list2cmdline(argv))
            environment=ctypes.create_unicode_buffer(self.environment_block) if self.environment_block is not None else None
            flags=0x00080000|0x00000004|0x08000000|(0x400 if environment is not None else 0)
            if not k.CreateProcessW(argv[0],cmd,None,None,self.stdio,flags,environment,self.cwd,ctypes.byref(startup),ctypes.byref(pi)):raise _error('CreateProcessW')
            self.process=pi.hProcess;self.thread=pi.hThread;self.pid=pi.dwProcessId
            self._close_raw_fds()
            if not self.in_job():raise RuntimeError('created process not in private job')
            self.membership_confirmed=True
            self.start_complete=True
        except BaseException as exc:
            try:
                had_process=self.process is not None
                try:self._close_raw_fds()
                except OSError as pipe_exc:exc.add_note('pipe cleanup unknown: '+repr(pipe_exc))
                cleanup=self.close()
                streams=self.close_streams() if cleanup.get('process_exited') else {'streams_closed':False,'errors':[]}
                if not cleanup.get('job_closed') or (had_process and not cleanup.get('process_exited')) or cleanup.get('errors') or not streams['streams_closed'] or streams['errors']:
                    exc.add_note('cleanup not confirmed: '+repr({'process':cleanup,'streams':streams}))
            except BaseException as cleanup_exc:exc.add_note('cleanup error: '+repr(cleanup_exc))
            raise
        finally:
            if initialized:k.DeleteProcThreadAttributeList(attrs)
            try:self._close_raw_fds()
            except OSError as exc:
                self.start_complete=False
                pass

    def _close_raw_fds(self):
        failures=[]
        while self._raw_fds:
            fd=self._raw_fds.pop()
            try:os.close(fd)
            except OSError as exc:
                self._unknown_raw_fds.add(fd);self.pipe_close_errors.append({'fd':fd,'type':type(exc).__name__});failures.append(str(exc))
        if failures:raise OSError('unconfirmed pipe closure: '+repr(failures))

    def close_streams(self):
        errors=[]
        for name in ('stdin','stdout','stderr'):
            stream=getattr(self,name)
            if stream is not None and not stream.closed:
                try:stream.close()
                except Exception as exc:errors.append({'stream':name,'type':type(exc).__name__})
        self.stream_close_errors.extend(errors)
        return {'streams_closed':all(getattr(self,n) is None or getattr(self,n).closed for n in ('stdin','stdout','stderr')) and not self._raw_fds and not self._unknown_raw_fds and not self.stream_close_errors,'unresolved_raw_fds':sorted(self._raw_fds | self._unknown_raw_fds),'errors':list(self.stream_close_errors)}

    def in_job(self):
        if not self.job or not self.process:return False
        value=wintypes.BOOL()
        if not k.IsProcessInJob(self.process,self.job,ctypes.byref(value)):raise _error('IsProcessInJob')
        return bool(value.value)

    def resume(self):
        if not self.start_complete or not self.membership_confirmed or self.closing or not self.thread or self.suspended is not True:raise RuntimeError('resume unavailable')
        self.suspended=None
        result=k.ResumeThread(self.thread)
        if result!=1:
            self.suspended=None
            if result==0xffffffff:raise _error('ResumeThread')
            raise RuntimeError('unexpected suspend count')
        self.suspended=False

    def wait(self,timeout_s):
        if not self.process:raise RuntimeError('process handle unavailable')
        if type(timeout_s) not in (int,float) or not math.isfinite(timeout_s) or timeout_s<0:raise ValueError('invalid timeout')
        result=k.WaitForSingleObject(self.process,min(0xfffffffe,math.ceil(timeout_s*1000)))
        if result==258:raise TimeoutError('process wait timed out')
        if result!=0:raise _error('WaitForSingleObject')
        code=wintypes.DWORD()
        if not k.GetExitCodeProcess(self.process,ctypes.byref(code)):raise _error('GetExitCodeProcess')
        return code.value

    def close(self,timeout_s=5):
        self.closing=True
        if not self.process and self.pi.hProcess:self.process=self.pi.hProcess
        if not self.thread and self.pi.hThread:self.thread=self.pi.hThread
        result={'job_closed':self.job is None,'process_exited':self.process is None,'errors':[]}
        if self.process and not self.membership_confirmed:
            if not k.TerminateProcess(self.process,1):
                result['errors'].append({'operation':'TerminateProcess(unconfirmed)','winerror':ctypes.get_last_error()})
        if self.job:
            if k.CloseHandle(self.job):self.job=None;result['job_closed']=True
            else:result['errors'].append({'operation':'CloseHandle(job)','winerror':ctypes.get_last_error()})
        if self.process and result['job_closed']:
            try:self.wait(timeout_s);result['process_exited']=True
            except Exception as exc:result['errors'].append({'operation':'wait','type':type(exc).__name__})
        if self.thread:
            if k.CloseHandle(self.thread):self.thread=None;self.pi.hThread=None
            else:result['errors'].append({'operation':'CloseHandle(thread)','winerror':ctypes.get_last_error()})
        if self.process and result['process_exited']:
            if k.CloseHandle(self.process):self.process=None;self.pi.hProcess=None
            else:result['errors'].append({'operation':'CloseHandle(process)','winerror':ctypes.get_last_error()})
        result['kernel_handles_closed']=self.job is None and self.thread is None and self.process is None
        result['streams_closed']=all(getattr(self,n) is None or getattr(self,n).closed for n in ('stdin','stdout','stderr')) and not self._raw_fds and not self._unknown_raw_fds and not self.stream_close_errors
        result['handles_closed']=result['kernel_handles_closed'] and result['streams_closed']
        result['unresolved_raw_fds']=sorted(self._raw_fds | self._unknown_raw_fds)
        result['pipe_close_errors']=list(self.pipe_close_errors)
        result['stream_close_errors']=list(self.stream_close_errors)
        return result
