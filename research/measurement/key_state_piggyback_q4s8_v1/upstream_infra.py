"""Minimal local harness utilities required by the unchanged server helper."""
import hashlib,json,time

def now():return time.monotonic_ns()
def sha(b):return hashlib.sha256(b).hexdigest()
def save(path,value):path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
