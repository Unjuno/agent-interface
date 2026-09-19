"""Linux nonblocking pipe write candidate; caller serializes commands.

Exclusive unbuffered fd required. A failed attempt permanently poisons this writer.
"""
import os,select,time


class WriteUncertain(OSError):
    def __init__(self,sent,total,reason):
        self.sent=sent;self.total=total;self.reason=reason
        super().__init__(f'{reason}: {sent}/{total} bytes; channel poisoned')


class WriteRejected(ValueError):pass


class BoundedPipeWriter:
    def __init__(self,fd,timeout=.1,max_bytes=16384):
        if type(timeout) not in (int,float) or not 0<timeout<=1:raise ValueError('timeout 0..1 second required')
        if type(max_bytes)is not int or not 1<=max_bytes<=65536:raise ValueError('bounded byte size required')
        self.fd=fd;self.timeout=timeout;self.max_bytes=max_bytes;self.poisoned=False;self.records=[]
        os.set_blocking(fd,False)

    def __call__(self,line):
        if self.poisoned:raise WriteUncertain(0,0,'previous failure')
        if not isinstance(line,str) or not line.endswith('\n') or '\n' in line[:-1]:raise WriteRejected('one newline-terminated record required')
        data=line.encode('utf-8')
        if len(data)>self.max_bytes:raise WriteRejected('record too large')
        started=time.perf_counter_ns();deadline=time.monotonic()+self.timeout;sent=0;reason=None
        try:
            while sent<len(data):
                if time.monotonic()>=deadline:raise TimeoutError('write deadline')
                try:
                    n=os.write(self.fd,data[sent:])
                    if n<=0:raise OSError('zero write')
                    sent+=n
                except BlockingIOError:
                    select.select([], [self.fd], [], max(0,deadline-time.monotonic()))
        except Exception as exc:
            self.poisoned=True;reason=type(exc).__name__
            raise WriteUncertain(sent,len(data),reason) from exc
        finally:
            self.records.append(dict(started_ns=started,finished_ns=time.perf_counter_ns(),sent=sent,total=len(data),
                                     outcome='pipe_written' if reason is None else 'uncertain',reason=reason))
