"""Owned per-app Fontconfig cache; no host/global cache mutation."""
import copy
import os
from pathlib import Path
import tempfile
import time

class PrivateCache:
    def __init__(self,token):
        if not isinstance(token,str) or not token:raise ValueError('empty cache token')
        self.temporary=tempfile.TemporaryDirectory(prefix='5260-a08-cache-')
        self.path=Path(self.temporary.name).resolve()
        self.parent=self.path.parent
        self.path.chmod(0o700)
        stat=self.path.stat()
        self.receipt={'token':token,'path':str(self.path),'created_ns':time.monotonic_ns(),
                      'mode':stat.st_mode&0o777,'uid':stat.st_uid,'removed':False,
                      'cleanup_started_ns':None,'cleanup_finished_ns':None}
        self.attempted_cleanup=False

    def environment(self,base):
        return {**dict(base),'XDG_CACHE_HOME':str(self.path)}

    def snapshot(self):
        return copy.deepcopy(self.receipt)

    def cleanup(self):
        if self.attempted_cleanup:raise RuntimeError('cache cleanup already attempted')
        resolved=self.path.resolve()
        if resolved.parent!=self.parent or not resolved.name.startswith('5260-a08-cache-'):
            raise RuntimeError('STOP_CACHE_CLEANUP_TARGET')
        self.attempted_cleanup=True
        self.receipt['cleanup_started_ns']=time.monotonic_ns()
        try:self.temporary.cleanup()
        finally:
            self.receipt['removed']=not self.path.exists()
            self.receipt['cleanup_finished_ns']=time.monotonic_ns()

