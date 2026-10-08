"""A12 disposable file effect; no crash-durability or authority claim."""
import hashlib
import json
import os
from pathlib import Path
import time

def save_once(directory,token,pid,text):
    if (type(token) is not str or not token or type(pid) is not int or pid<=0
        or type(text) is not str):
        raise ValueError('invalid task identity or text')
    # Serialize before acquiring the output, so encoding failure has no effect.
    blob=(json.dumps(dict(schema='issue5260-a12-task-file-v1',token=token,
         pid=pid,text=text),sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n').encode('utf-8')
    started=time.monotonic_ns()
    path=Path(directory)/'task_result.json'
    with path.open('xb') as stream:
        stream.write(blob)
        stream.flush()
        os.fsync(stream.fileno())
        fsynced=time.monotonic_ns()
    return dict(path=path.name,started_ns=started,fsynced_ns=fsynced,
                completed_ns=time.monotonic_ns(),sha256=hashlib.sha256(blob).hexdigest(),bytes=len(blob))
