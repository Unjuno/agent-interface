#!/usr/bin/env python3
import gzip, hashlib, json, re
from pathlib import Path
packet=Path(__file__).resolve().parent
rows=[]
for line in (packet/'RAW_LOGS.md').read_text(encoding='utf-8').splitlines():
    match=re.match(r'^\| `([^`]+)` \| `([^`]+)` \| `([0-9a-f]{64})` \|$',line)
    if not match: continue
    source,archive,expected=match.groups()
    with gzip.open(packet/archive,'rb') as stream: raw=stream.read()
    actual=hashlib.sha256(raw).hexdigest()
    if actual != expected: raise RuntimeError(f'raw log hash mismatch: {source}')
    rows.append({'source':source,'archive':archive,'sha256':actual,'bytes':len(raw)})
if not rows: raise RuntimeError('RAW_LOGS.md has no log entries')
print(json.dumps({'status':'RAW_LOG_BYTES_VERIFIED','entries':rows},indent=2))