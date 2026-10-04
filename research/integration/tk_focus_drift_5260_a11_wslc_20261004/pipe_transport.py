"""Private pipe ownership boundary, under test before allocation."""
import hashlib
import os
import time
from pipe_receipt import FrameDecoder


class PipeSession:
    def __init__(self):
        self.read_fd, self.write_fd=os.pipe()
        self.reads=[]
        self.frames=[]
        self.closes=[]
        self.eof=False
        self.decoder=FrameDecoder()
        try:
            os.set_blocking(self.read_fd, False)
            os.set_blocking(self.write_fd, False)
            self.identity={'read_fd':self.read_fd, 'write_fd':self.write_fd,
                'read_inode':os.fstat(self.read_fd).st_ino,
                'write_inode':os.fstat(self.write_fd).st_ino,
                'pipe_buf':os.fpathconf(self.write_fd, 'PC_PIPE_BUF') if hasattr(os,'fpathconf') else None}
            if self.identity['pipe_buf'] is not None and self.identity['pipe_buf']<512:
                raise ValueError('pipe atomic write bound too small')
        except BaseException:
            self.close()
            raise

    def _close_owned(self, name):
        fd=getattr(self,name)
        if fd is None:return
        setattr(self,name,None)
        record={'name':name,'fd':fd,'started_ns':time.monotonic_ns()}
        self.closes.append(record)
        try:os.close(fd)
        except OSError as error:
            record['error']=repr(error)
            raise
        finally:record['completed_ns']=time.monotonic_ns()

    def release_parent_writer(self):
        self._close_owned('write_fd')

    def drain(self):
        result=[]
        while not self.eof:
            record={'started_ns':time.monotonic_ns()}
            self.reads.append(record)
            try:chunk=os.read(self.read_fd,4096)
            except BlockingIOError:
                record.update(status='EAGAIN',completed_ns=time.monotonic_ns())
                break
            except OSError as error:
                record.update(status='ERROR',error=repr(error),completed_ns=time.monotonic_ns())
                raise
            record.update(status='DATA' if chunk else 'EOF',completed_ns=time.monotonic_ns(),
                hex=chunk.hex(),bytes=len(chunk),sha256=hashlib.sha256(chunk).hexdigest())
            if not chunk:
                self.eof=True
                self.decoder.finish()
                break
            values=self.decoder.feed(chunk)
            self.frames.extend({'value':value,'seen_ns':record['completed_ns']} for value in values)
            result.extend(values)
        return result

    def finish(self):
        if not self.eof:raise ValueError('pipe EOF not observed')
        return self.decoder.finish()

    def close(self):
        try:self._close_owned('write_fd')
        finally:self._close_owned('read_fd')

    def __enter__(self):return self

    def __exit__(self, *args):self.close()
