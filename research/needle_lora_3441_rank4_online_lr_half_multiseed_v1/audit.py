"""Independent row/curve auditor; regenerates seed data without importing runner."""
import base64,gzip,hashlib,json,math,statistics
import torch
SEEDS=(3461,3462,3463,3464,3465);N=4096
YIELDS={"unknown_role":"YIELD","stale_epoch":"YIELD","wrong_version":"YIELD","missing_adapter":"YIELD","missing_epoch":"YIELD"}
CURVE_ARMS=("rank2_online","rank4_online_04","rank4_online_02")
def regen(seed):
 def data(n,s):
  return torch.randn(n,8,generator=torch.Generator(device="cpu").manual_seed(s))
 def labels(x,flip=False):
  a=(x[:,0]>0).long()
  if flip:a=1-a
  return (a*2+(x[:,1]>0).long()).tolist()
 return labels(data(N,seed+3)),labels(data(N,seed+4),True)
def accuracy(pred,expected):
 return sum(int(a==b) for a,b in zip(pred,expected))/len(expected)
def audit(envelope):
 raw=gzip.decompress(base64.b64decode(envelope["gzip_b64"],validate=True))
 digest=hashlib.sha256(raw).hexdigest()
 assert digest==envelope["sha256"]
 d=json.loads(raw);assert d["allocation"]=="needle-lora-rank4-online-lr-half-multiseed-v1"
 e=d["environment"]
 assert e["device"]=="NVIDIA GeForce RTX 3080 Laptop GPU" and e["cuda"]=="12.1"
 assert e["deterministic"] is True and e["cublas_workspace_config"]=="4096:8"
 assert tuple(x["seed"] for x in d["seeds"])==SEEDS
 means={k:[] for k in ("A","rank2_online","rank4_online_04","rank4_online_02","rank4_batch_04")}
 lat=[];curve_rows=0;integrity=True
 for s in d["seeds"]:
  ya,yb=regen(s["seed"])
  assert s["expected_A"]==ya and s["expected_B"]==yb
  assert s["rank4_initial_states_identical"] is True
  assert s["base_immutable"] is True and s["invalid_routes"]==YIELDS
  snap=s["rank4_intervention_snapshot"]
  assert snap["roundtrip_exact"] and snap["rollback_exact"]
  f=s["final"]
  for role,key,expected in (("A","A",ya),("B_R2_ONLINE","rank2_online",yb),
    ("B_R4_ONLINE_04","rank4_online_04",yb),("B_R4_ONLINE_02","rank4_online_02",yb),
    ("B_R4_BATCH_04","rank4_batch_04",yb)):
   row=f[role];pred=row["predictions"]
   assert row["route"]=="PROPOSE" and row["expected"]==expected and len(pred)==N
   assert row["correct"]==sum(a==b for a,b in zip(pred,expected))
   assert row["accuracy"]==accuracy(pred,expected)
   means[key].append(row["accuracy"])
  for arm in CURVE_ARMS:
   rows=s["curves"][arm];assert len(rows)==16
   for i,row in enumerate(rows,1):
    assert row["feedback_count"]==i and row["route"]=="PROPOSE" and row["role"]==arm
    pred=row["predictions"];assert len(pred)==N
    correct=sum(a==b for a,b in zip(pred,yb))
    assert row["correct"]==correct and row["accuracy"]==correct/N and row["n"]==N
    curve_rows+=N
   assert rows[-1]["predictions"]==f[{"rank2_online":"B_R2_ONLINE","rank4_online_04":"B_R4_ONLINE_04","rank4_online_02":"B_R4_ONLINE_02"}[arm]]["predictions"]
   ts=s["feedback_ms"][arm];assert len(ts)==16 and all(isinstance(x,(int,float)) and x>=0 for x in ts)
   if arm=="rank4_online_02":lat.extend(ts)
  for name in ("rank2_online","rank4_online_04","rank4_online_02","rank4_batch_04","rank4_template",
               "rank2_online_optimizer","rank4_online_04_optimizer","rank4_online_02_optimizer","rank4_batch_04_optimizer"):
   value=s["setup_ms"][name]
   assert isinstance(value,(int,float)) and value>=0
  assert isinstance(s["batch_128_updates_ms"],(int,float)) and s["batch_128_updates_ms"]>=0
 p95=sorted(lat)[math.ceil(.95*len(lat))-1]
 lift=statistics.mean(means["rank4_online_02"])-statistics.mean(means["rank4_online_04"])
 within_batch=all(abs(a-b)<=.03 for a,b in zip(means["rank4_online_02"],means["rank4_batch_04"]))
 quality=all(all(x>=.90 for x in means[k]) for k in ("A","rank2_online","rank4_online_02"))
 integrity=all(s["rank4_initial_states_identical"] and s["base_immutable"] and
   s["rank4_intervention_snapshot"]["roundtrip_exact"] and s["rank4_intervention_snapshot"]["rollback_exact"] and s["invalid_routes"]==YIELDS
   for s in d["seeds"])
 if not integrity:disp="FAIL_ROUTE_OR_SNAPSHOT_INTEGRITY"
 elif quality and lift>=.50 and within_batch and p95<=60 and curve_rows==5*3*16*N:disp="PASS_RANK4_ONLINE_LR_HALF_RESCUE_SCOPED"
 else:disp="FAIL_LR_HALF_RESCUE"
 return {"disposition":disp,"result_sha256":digest,"mean_accuracy":means,"rank4_lr02_minus_lr04_mean":lift,
   "rank4_lr02_vs_batch_abs_by_seed":[abs(a-b) for a,b in zip(means["rank4_online_02"],means["rank4_batch_04"])],
   "rank4_lr02_feedback_p95_ms":p95,"audited_curve_predictions":curve_rows,
   "curve_counts_per_arm_per_seed":16,"regenerated_seed_labels":True,"integrity":integrity}
