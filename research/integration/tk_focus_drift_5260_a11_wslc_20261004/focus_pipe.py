"""Bounded focus-event publication for the A09 private app."""
import copy
import os
import time
from pipe_receipt import write_once,PipeWriteError


class FocusPipe:
    def __init__(self,fd,binding):
        self.fd=fd
        self.binding=copy.deepcopy(binding)
        self.publications=[]
        self.first_error=None
        self.close_trace=None
        os.set_blocking(fd,False)
        self.identity={'fd':fd,'inode':os.fstat(fd).st_ino,
            'nonblocking':not os.get_blocking(fd),
            'pipe_buf':os.fpathconf(fd,'PC_PIPE_BUF') if hasattr(os,'fpathconf') else None}
        if self.identity['pipe_buf'] is not None and self.identity['pipe_buf']<512:
            raise ValueError('pipe atomic write bound too small')

    def publish(self,event,focus_get):
        if self.first_error is not None:return False
        value={**self.binding,'schema':'issue5260-a09-focus-pipe-v1',
            'kind':event['kind'],'widget':event['widget'],'focus_get':focus_get,
            'sequence':event['sequence'],'event_ns':event['monotonic_ns'],
            'written_ns':time.monotonic_ns()}
        try:
            trace=write_once(self.fd,value)
        except PipeWriteError as error:
            trace=error.trace
            self.first_error=copy.deepcopy(trace)
            self.publications.append({'value':value,'trace':trace})
            return False
        except (ValueError,OSError) as error:
            self.first_error={'type':type(error).__name__,'message':str(error),
                              'observed_ns':time.monotonic_ns()}
            self.publications.append({'value':value,'error':copy.deepcopy(self.first_error)})
            return False
        self.publications.append({'value':value,'trace':trace})
        return True

    def close(self):
        if self.fd is None:return
        fd=self.fd
        self.fd=None
        self.close_trace={'fd':fd,'started_ns':time.monotonic_ns()}
        try:os.close(fd)
        except OSError as error:
            self.close_trace['error']=repr(error)
            raise
        finally:self.close_trace['completed_ns']=time.monotonic_ns()

    def snapshot(self):
        return copy.deepcopy({'identity':self.identity,'publications':self.publications,
            'first_error':self.first_error,'close':self.close_trace})
