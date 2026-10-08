"""Preparation only, fixed original raw → selected observation view."""
import hashlib,json,sys
from pathlib import Path
raw=Path(sys.argv[1]).read_bytes()
assert hashlib.sha256(raw).hexdigest()=="aafcc9a0b9db97619008dbb446304bf8d6ac703616e4a79329111fc674957643"
records=[]
for i,line in enumerate(raw.splitlines()):
    r=json.loads(line);s=next(s for s in r["samples"]if s["tag"]=="checkpoint");c=r["capability"]
    m={"id":"N%02d"%i,"source_sha256":hashlib.sha256(raw).hexdigest(),"row_sha256":hashlib.sha256(line).hexdigest(),"owner":[c["owner_pid"],c["owner_start_ticks"]],"nonce":c["owner_nonce"],"display":[c["display_pid"],c["display_start_ticks"],c["window_id"]],"keycodes":r["keycodes"],"interval":[s["query_started_ns"],s["at_ns"]],"bystander_required":r["context"]=="crash_bystander"}
    records.append({"case_id":m["id"],"family":"native","meta":m,"observation":{"keymap":s["keymap"],"buttons":s["buttons"],"scoped_verified":r["supervisor"]["result"]["receipt"]["verified"]}})
for i in range(32):
    b=bytearray(32)
    for bit,c in((1,74),(2,75),(4,76)):
        if i&bit:b[c//8]|=1<<(c%8)
    m={"id":"SYNTHETIC_IDENTITY","source_sha256":"finite-state-family-v1","owner":[1,1],"nonce":"synthetic","display":[2,2,3],"keycodes":{"F8":74,"F9":75},"interval":[10,11],"bystander_required":True}
    records.append({"case_id":"S%02d"%i,"family":"synthetic","meta":m,"observation":{"keymap":b.hex(),"buttons":256 if i&8 else 0,"scoped_verified":bool(i&16)}})
print(json.dumps({"raw_sha256":hashlib.sha256(raw).hexdigest(),"records":records},indent=2))
