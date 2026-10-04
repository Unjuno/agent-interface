"""One codec experiment on fixed native-record view and synthetic challenge."""
import argparse,hashlib,json,sys
from pathlib import Path
from codec import encode,decode
def wire(v):return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
p=argparse.ArgumentParser();p.add_argument("input");p.add_argument("output");a=p.parse_args()
raw=Path(a.input).read_bytes();data=json.loads(raw)
out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
with(out/"packets.jsonl").open("x")as f:
    for r in data["records"]:
        for policy in("RAW_CHECKPOINT","RECEIPT_TRUST","KEY_SUBSET","CONSERVATIVE_PROFILE"):
            packet=encode(policy,r);encoded=wire(packet)
            f.write(json.dumps({"case_id":r["case_id"],"family":r["family"],"policy":policy,"packet":packet,"wire_hex":encoded.hex(),"bytes":len(encoded),"decision":decode(policy,packet)})+"\n")
env={"python":sys.version,"input_sha256":hashlib.sha256(raw).hexdigest(),"cgroup":{n:Path("/sys/fs/cgroup",n).read_text().strip()for n in("cpu.max","memory.max","memory.swap.max","pids.max")},"native_inputs":0}
with(out/"ENVIRONMENT.json").open("x")as f:json.dump(env,f,indent=2);f.write("\n")
print(json.dumps({"records":len(data["records"]),"packets":len(data["records"])*4,"native_inputs":0}))
