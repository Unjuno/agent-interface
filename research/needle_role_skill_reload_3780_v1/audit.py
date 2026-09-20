"""Independent raw-evidence audit. Does not import the trainer or loader."""
import hashlib,json,math,sys
def fail(x): raise SystemExit("STOP:"+x)
def canonical(x): return json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
def main():
    root=sys.argv[1]; freeze=json.load(open(root+"/freeze.json",encoding="utf-8")); results=[]; errors=[]
    for seed in freeze["seeds"]:
        d=f"{root}/seed-{seed}"; artifact=json.load(open(d+"/skill.json",encoding="utf-8")); expected=json.load(open(d+"/expected.json",encoding="utf-8"))
        payload=artifact.pop("payload_sha256",None)
        if payload!=hashlib.sha256(canonical(artifact)).hexdigest(): errors.append(f"{seed}:artifact_digest")
        artifact["payload_sha256"]=payload
        if artifact["schema"]!="unjuno.role-skill.numeric-json.v1" or artifact["generation"]!=seed: errors.append(f"{seed}:artifact_identity")
        if expected.get("base_immutable") is not True: errors.append(f"{seed}:base_mutated")
        for role,rows in expected["roles"].items():
            pred=rows["pred"]; gold=rows["expected"]
            if len(pred)!=4096 or len(gold)!=4096: errors.append(f"{seed}:{role}:rows")
            acc=sum(a==b for a,b in zip(pred,gold))/4096
            if acc<.90: errors.append(f"{seed}:{role}:competence")
            if len(set(pred))<2: errors.append(f"{seed}:{role}:collapsed")
        for run in ("load-1","load-2"):
            loaded=json.load(open(f"{d}/{run}.json",encoding="utf-8"))
            if loaded.get("predictions")!= {r:x["pred"] for r,x in expected["roles"].items()}: errors.append(f"{seed}:{run}:prediction_mismatch")
            if loaded.get("accepted") is not True: errors.append(f"{seed}:{run}:not_loaded")
            if loaded.get("graph")!="A>B>C" or loaded.get("old_receipt")!="YIELD": errors.append(f"{seed}:{run}:graph")
            if loaded.get("negative_controls")!={"tampered_digest":"YIELD","truncated":"YIELD","unknown_schema":"YIELD","wrong_adapter_version":"YIELD","stale_receipt":"YIELD","skipped_edge":"YIELD","wrong_scope":"YIELD","duplicate_receipt":"YIELD","unverified_outcome":"YIELD","unknown_destination":"YIELD"}: errors.append(f"{seed}:{run}:controls")
            if loaded.get("fixture_emissions")!=2: errors.append(f"{seed}:{run}:emissions")
        results.append({"seed":seed,"artifact_bytes":len(canonical(artifact)),"per_role":{r:sum(a==b for a,b in zip(x["pred"],x["expected"]))/4096 for r,x in expected["roles"].items()}})
    out={"disposition":"PASS_AUDIT_SCOPED" if not errors else "FAIL_AUDIT","errors":errors,"results":results}
    open(root+"/audit.json","w",encoding="utf-8").write(json.dumps(out,sort_keys=True,separators=(",",":")))
    print(json.dumps(out,sort_keys=True,separators=(",",":")))
    if errors: raise SystemExit(1)
if __name__=="__main__": main()
