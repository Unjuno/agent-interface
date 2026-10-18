import base64, gzip, hashlib, json, pathlib, sys

source=pathlib.Path("/src")
transport=pathlib.Path("/transport")
out=pathlib.Path("/input")
manifest=json.loads((source/"RAW_MANIFEST.json").read_text(encoding="utf-8"))
parts=manifest["transport"]["ordered_parts"]
joined="".join((transport/name).read_text(encoding="ascii") for name in parts)
assert len(joined)==manifest["transport"]["characters"]
assert hashlib.sha256(joined.encode("ascii")).hexdigest()==manifest["transport"]["base64_sha256"]
compressed=base64.b64decode(joined,validate=True)
assert len(compressed)==manifest["transport"]["gzip_bytes"]
assert hashlib.sha256(compressed).hexdigest()==manifest["transport"]["gzip_sha256"]
raw=gzip.decompress(compressed)
assert len(raw)==manifest["raw"]["bytes"]
assert hashlib.sha256(raw).hexdigest()==manifest["raw"]["sha256"]
lines=raw.splitlines(keepends=True)
rows=[json.loads(line) for line in lines if line.strip()]
assert len(rows)==manifest["raw"]["rows"]==204
iid=[r for r in rows if r.get("kind")=="iid"]
assert len(iid)==200 and sorted(r["seed"] for r in iid)==list(range(5665001,5665201))
out.mkdir(parents=True,exist_ok=True)
(out/"base.jsonl").write_bytes(raw)
target_seed=5665002
idx=next(i for i,r in enumerate(rows) if r.get("kind")=="iid" and r.get("seed")==target_seed)
target=dict(rows[idx])
old_id=target["case_id"]
old_stratum=target["validation_stratum"]
target["validation_stratum"]="mutation-shifted-validation-stratum"
target["candidate"]=dict(target["candidate"])
target["candidate"]["disposition"]="HOLD_NONEXCHANGEABLE"
ending=b"\n" if lines[idx].endswith(b"\n") else b""
new_line=json.dumps(target,separators=(",",":"),ensure_ascii=False).encode("utf-8")+ending
mut_lines=list(lines); mut_lines[idx]=new_line
mutated=b"".join(mut_lines)
mutrows=[json.loads(line) for line in mutated.splitlines() if line.strip()]
assert len(mutrows)==204
changed=[i for i,(a,b) in enumerate(zip(rows,mutrows)) if a!=b]
assert changed==[idx]
assert mutrows[idx]["case_id"]==old_id and mutrows[idx]["seed"]==target_seed
assert len([r for r in mutrows if r.get("kind")=="iid"])==200
def independent_eligible(r):
    return (r.get("kind")=="iid" and r.get("train_planned_n")==len(r.get("train",[]))+r.get("train_unknown_n",0)
      and r.get("train_unknown_n")==0 and r.get("validation_planned_n")==len(r.get("validation",[]))+r.get("validation_unknown_n",0)
      and r.get("validation_unknown_n")==0 and len(r.get("train_unit_ids",[]))==len(r.get("train",[]))
      and len(set(r.get("train_unit_ids",[])))==len(r.get("train_unit_ids",[]))
      and len(r.get("validation_unit_ids",[]))==len(r.get("validation",[]))
      and len(set(r.get("validation_unit_ids",[])))==len(r.get("validation_unit_ids",[]))
      and r.get("train_taxonomy")==r.get("validation_taxonomy")
      and r.get("train_stratum")==r.get("validation_stratum"))
assert sum(independent_eligible(r) for r in rows)==200
assert sum(independent_eligible(r) for r in mutrows)==199
(out/"mutated.jsonl").write_bytes(mutated)
print(json.dumps({"status":"PREPARED","raw_bytes":len(raw),"raw_sha256":hashlib.sha256(raw).hexdigest(),"rows":len(rows),"iid":len(iid),"target_case_id":old_id,"target_seed":target_seed,"original_validation_stratum":old_stratum,"mutated_validation_stratum":target["validation_stratum"],"candidate_disposition":target["candidate"]["disposition"],"changed_record_count":len(changed),"independent_eligible_base":200,"independent_eligible_mutated":199,"base_sha256":hashlib.sha256(raw).hexdigest(),"mutated_sha256":hashlib.sha256(mutated).hexdigest()},sort_keys=True))
