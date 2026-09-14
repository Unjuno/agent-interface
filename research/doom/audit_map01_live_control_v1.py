"""Audit pre-formal MAP01 live-control, context, and scorer evidence."""
import hashlib,json,statistics
from pathlib import Path
HERE=Path(__file__).resolve().parent;RESULTS=HERE/"results";REPO=HERE.parents[1]
def read(p):return json.loads(p.read_text())
def events(root):return [json.loads(x) for x in (root/"runtime/events.jsonl").read_text().splitlines()]
def arm(name):
 r=read(RESULTS/name/"report.json");rows=r["decisions"]
 times=[x["model_ns"]/1e9 for x in rows];total=sum(x["usage"]["input_tokens"] for x in rows);cached=sum(x["usage"]["cached_input_tokens"] for x in rows)
 return {"turns":len(rows),"input_tokens":total,"cached_input_tokens":cached,
         "uncached_input_tokens":total-cached,"model_seconds":sum(times),
         "model_seconds_median":statistics.median(times),"score":r["score"]}
ephemeral=arm("map01-overlap-contract-luna-01");persistent=arm("map01-overlap-persistent-luna-01");hybrid=arm("map01-overlap-hybrid-luna-01")
probe=read(RESULTS/"map01-persistent-model-probe-01/report.json");assert probe["same_model_session"]
assert probe["calls"][0]["thread_id"]==probe["calls"][1]["thread_id"]
coast=read(RESULTS/"map01-coast-probe-03/report.json");assert coast["passed"] and coast["input_admissions"]==0
death=read(RESULTS/"map01-death-count-probe-03/report.json");assert death["death_count_detected"] and death["score"]["death_count"]==1
overlap={}
for name in ("map01-overlap-persistent-luna-01","map01-overlap-hybrid-luna-01"):
 root=RESULTS/name;r=read(root/"report.json");rows=events(root)
 covered=total=0
 for d in r["decisions"]:
  a=next(x for x in rows if x["event"]=="accepted" and x.get("id")==f'cover-{d["iteration"]}')
  t=next(x for x in rows if x["event"]=="terminal" and x.get("id")==f'cover-{d["iteration"]}')
  assert a["accepted_ns"]<=d["controller_model_started_ns"]<d["controller_model_ended_ns"]
  total+=d["controller_model_ended_ns"]-d["controller_model_started_ns"]
  covered+=max(0,min(t["terminal_ns"],d["controller_model_ended_ns"])-d["controller_model_started_ns"])
 overlap[name]=covered/total
sources=read(RESULTS/"map01-overlap-hybrid-luna-01/runtime/sources.json")
for relative,expected in sources.items():
 path=REPO/"research"/relative;assert hashlib.sha256(path.read_bytes()).hexdigest()==expected,relative
bad=read(RESULTS/"map01-overlap-temporal-luna-01/report.json")
assert all(x["observation_to_plan_accept_ns"]<0 for x in bad["decisions"])
summary={"audit_passed":True,"scope":"pre-formal normal MAP01; no clear claim",
 "ephemeral_12":ephemeral,"persistent_12":persistent,"hybrid_20":hybrid,
 "persistent_uncached_reduction_vs_ephemeral_percent":round((1-persistent["uncached_input_tokens"]/ephemeral["uncached_input_tokens"])*100,3),
 "persistent_model_time_change_vs_ephemeral_percent":round((persistent["model_seconds"]/ephemeral["model_seconds"]-1)*100,3),
 "coast_composed_over_existing_pointer_drag_backend":True,"deathcount_calibrated_on_terminal_death":True,
 "model_time_covered_by_bounded_program_percent":{k:round(v*100,3) for k,v in overlap.items()},
 "invalid_metric_retained":"map01-overlap-temporal-luna-01 observation_to_plan_accept_ns is negative and unusable",
 "limitations":["allocations use different seeds and are descriptive, not a matched causal comparison","no MAP01 exit","post-control deathcount persistence after an in-session restart is untested"]}
(RESULTS/"map01-live-control-v1-audit.json").write_text(json.dumps(summary,indent=2)+"\n");print(json.dumps(summary,indent=2))
