"""Audit both predeclared WSLc recovery/attack comparison arms."""
import hashlib, json, zipfile
from pathlib import Path
root=Path(__file__).parent
sources=[]
for name,arm in (("ab03","control"),("ab04","attack")):
 with zipfile.ZipFile(root/(name+".zip")) as z:
  def j(path): return json.loads(z.read(path).decode("utf-8-sig"))
  cond,result=j("conditions.json"),j("output/result.json")
  digest=hashlib.sha256(z.read("runner.py")).hexdigest();sources.append(digest)
  assert digest==cond["runner_sha256"] and cond["arm"]==arm
  assert cond["order"]==["ab03:control","ab04:attack"]
  assert result["status"]=="completed" and result["model_calls"]==0 and result["task_success"] is None
  assert result["keys_down_after"]==[] and result["benchmark_frames"]==20
  mon,action=result["cancel_monitor"],result["cancel_result"]
  assert mon["held_observed"] and mon["response"]["status"]=="cancel_requested" and mon["response"]["review_required"]
  rel=action["execution"]["releases"][-1]
  assert action["status"]=="execution_failed" and rel["verified"] and not rel["keys_down"] and not rel["buttons_down"]
  review,stale=j("output/review.json"),j("output/stale.json")
  assert review["status"]=="reviewed" and review["binding_revision"]>review["previous_binding_revision"]
  assert mon["held_ns"]<=mon["request_ns"]<=rel["monotonic_ns"]<=review["started_ns"]
  assert stale["status"]=="refused" and stale["input_dispatched"] is False
  assert len(result["actions"])==(2 if arm=="control" else 3)
  for x in result["actions"]:
   assert x["status"]=="completed" and x["execution"]["releases"]
   assert all(r["verified"] and not r["keys_down"] and not r["buttons_down"] for r in x["execution"]["releases"])
  before=next(s for s in result["samples"] if s["label"]=="before_benchmark_fire")
  after=next(s for s in result["samples"] if s["label"]=="after_benchmark_fire")
  assert before["kills"]==0 and after["kills"]==(0 if arm=="control" else 1)
  if arm=="control":
   wait=result["control_wait"];assert wait["requested_ms"]==1000 and wait["end_ns"]>wait["start_ns"]>=review["ended_ns"]
   assert "output/action-benchmark_fire.json" not in z.namelist()
  else:
   fire=j("output/action-benchmark_fire.json");assert fire==result["actions"][-1]
   assert fire["execution"]["waits"][0]["requested_ms"]==1000 and fire["execution"]["started_ns"]>=review["ended_ns"]
  frames=j("output/benchmark/frames.json");assert len(frames)==20
  for row in frames:
   assert hashlib.sha256(z.read("output/benchmark/frame-%02d.png"%row["index"])).hexdigest()==row["sha256"]
  for i in (0,4):assert any(x["id"]==14 and x["name"]=="Zombieman" for x in frames[i]["labels"])
  for i in (5,19):assert any(x["id"]==14 and x["name"]==("Zombieman" if arm=="control" else "DeadZombieman") for x in frames[i]["labels"])
  final=result["close"]["release"];assert final["verified"] and not final["keys_down"] and not final["buttons_down"]
  print(json.dumps({"allocation":name,"arm":arm,"kills":[before["kills"],after["kills"]],"held":True,"cancel_release":True,"review":"reviewed","stale":"refused","final_keys":result["keys_down_after"],"request_to_release_ms":(rel["monotonic_ns"]-mon["request_ns"])/1e6},indent=2))
assert sources[0]==sources[1]
