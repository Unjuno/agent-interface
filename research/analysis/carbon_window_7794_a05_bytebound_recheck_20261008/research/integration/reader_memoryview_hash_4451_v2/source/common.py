import hashlib, json
from pathlib import Path

RECORD_BYTES=256
SCHEMA='agent-interface/experimental-read-cursor-v1'

def make_line(i:int)->bytes:
    obj={'event':'observation','delivery_id':f'delivery:{i}','payload':''}
    base=(json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n').encode()
    n=RECORD_BYTES-len(base)
    if n < 0: raise ValueError('record header too large')
    obj['payload']='x'*n
    line=(json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n').encode()
    if len(line)!=RECORD_BYTES: raise AssertionError((i,len(line)))
    return line

def corpus_bytes(records:int)->bytes:
    return b''.join(make_line(i) for i in range(1,records+1))

def cursor_for(data:bytes, records:int, stream='formal-stream'):
    offset=records*RECORD_BYTES
    prefix=data[:offset]
    return {'schema':SCHEMA,'stream_id':stream,'offset':offset,
            'prefix_sha256':hashlib.sha256(prefix).hexdigest(),'next_sequence':records+1}

def sha256_bytes(b:bytes): return hashlib.sha256(b).hexdigest()
def sha256_path(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
