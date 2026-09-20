"""Independent auditor for frozen GPU rank-4 online LoRA experiment."""
import base64,gzip,hashlib,json,math,statistics,sys
SEEDS=[3451,3452,3453,3454,3455]; N=4096
YIELDS={"unknown_role":"YIELD","stale_epoch":"YIELD","wrong_version":"YIELD","missing_adapter":"YIELD","missing_epoch":"YIELD"}
def audit(envelope):
 raw=gzip.decompress(base64.b64decode(envelope["gzip_b64"],validate=True))
 assert hashlib.sha256(raw).hexdigest()==envelope["sha256"]
 d=json.loads(raw);assert d["allocation"]=="needle-lora-3441-rank4-online-multiseed-gpu-v1"
 e=d["environment"];assert e["device"]=="NVIDIA GeForce RTX 3080 Laptop GPU" and e["cuda"]=="12.1"
 assert e["deterministic"] is True and e["cublas_workspace_config"]=="4096:8"
 assert [x["seed"] for x in d["seeds"]]==SEEDS
 means={};lat=[]
 for s in d["seeds"]:
  assert s["base_immutable"] is True
  assert s["snapshot"]["roundtrip_exact"] and s["snapshot"]["rollback_exact"]
  assert s["invalid_routes"]==YIELDS
  m=s["metrics"]
  for key in ("A","rank2_online","rank4_online","rank4_batch"):
   row=m[key];assert row["n"]==N and len(row["expected"])==N and len(row["predictions"])==N
   c=sum(a==b for a,b in zip(row["expected"],row["predictions"]))
   assert c==row["correct"] and c/N==row["correct"]/N
  lat.extend(s["feedback_ms"]["rank4_online"])
  means.setdefault("A",[]).append(m["A"]["correct"]/N)
  for key in ("rank2_online","rank4_online","rank4_batch"):means.setdefault(key,[]).append(m[key]["correct"]/N)
 p95=sorted(lat)[math.ceil(.95*len(lat))-1]
 lift=statistics.mean(means["rank4_online"])-statistics.mean(means["rank2_online"])
 quality=all(x>=.90 for x in means["A"]) and all(x>=.90 for x in means["rank4_online"])
 batch=all(abs(a-b)<=.03 for a,b in zip(means["rank4_online"],means["rank4_batch"]))
 integrity=all(s["base_immutable"] and s["snapshot"]["roundtrip_exact"] and s["snapshot"]["rollback_exact"] and s["invalid_routes"]==YIELDS for s in d["seeds"])
 disposition=("FAIL_ROUTE_OR_SNAPSHOT_INTEGRITY_GPU" if not integrity else
  "PASS_RANK4_ONLINE_RESCUE_GPU_SCOPED" if quality and lift>=.03 and batch and p95<=60 else "FAIL_ONLINE_RANK_CAPACITY_GPU")
 return {"disposition":disposition,"result_sha256":envelope["sha256"],"row_counts":{"seeds":5,"rows_per_role_seed":N},"means":means,"rank4_minus_rank2_mean":lift,"rank4_online_vs_batch_abs_by_seed":[abs(a-b) for a,b in zip(means["rank4_online"],means["rank4_batch"])],"feedback_p95_ms":p95,"integrity":integrity,"source_hash_note":"Runner hash is independently pinned in FREEZE.json; auditor must compare it before formal result acceptance."}
if __name__=="__main__":print(json.dumps(audit(json.load(sys.stdin)),sort_keys=True,separators=(",",":")))
