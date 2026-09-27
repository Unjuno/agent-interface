"""Inner no-retry six-task allocation driver. Runs only inside isolated OrbStack."""
from __future__ import annotations
import hashlib, importlib.util, json, os, sys
from pathlib import Path
ROOT=Path(os.environ["ISSUE3824_REPO"]);LIVE=Path(os.environ["ISSUE3824_LIVE_SOURCE"])
OUT=Path(os.environ["ISSUE3824_OUT"])/"formal-output"
sys.path[:0]=[str(LIVE),str(ROOT),str(ROOT/"runtime"),str(Path(__file__).resolve().parent)]
import integrated_efficiency_client_v1 as client_module
client_module.HERE=Path(__file__).resolve().parent
import run_integrated_efficiency_live_v1 as live
from integrated_efficiency_protocol_v1 import ARMS
import issue3864_model_backend_v1 as backend
live.OUT=OUT

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(path, value): Path(path).write_text(json.dumps(value,indent=2)+"\n")

LOCK=json.loads((Path(__file__).resolve().parent/"formal-source-lock.json").read_text())
for name,digest in LOCK["protocol_sources"].items():
    if sha(LIVE/name)!=digest: raise RuntimeError("STOP_SOURCE_HASH_BEFORE_CALL:"+name)
for name,digest in LOCK["harness_sources"].items():
    if name in {"run_formal_inner_v1.py","issue3824_model_backend_v1.py",
            "issue3864_model_backend_v1.py","preflight_response_v1.py",
            "integrated_efficiency_socket_v1.py"}:
        if sha(Path(__file__).resolve().parent/name)!=digest: raise RuntimeError("STOP_HARNESS_HASH_BEFORE_CALL:"+name)
for name,digest in LOCK["support_sources"].items():
    if sha(ROOT/name)!=digest: raise RuntimeError("STOP_SUPPORT_HASH_BEFORE_CALL:"+name)
for name,digest in LOCK["environment_sources"].items():
    if sha(ROOT/name)!=digest: raise RuntimeError("STOP_ENVIRONMENT_HASH_BEFORE_CALL:"+name)
if sha(Path(__file__).resolve().parent/"construction-audit.py")!=LOCK["construction_audit"]["source_sha256"]:
    raise RuntimeError("STOP_CONSTRUCTION_AUDITOR_HASH_BEFORE_CALL")
if sha(Path(__file__).resolve().parent/"evidence/construction-audit.json")!=LOCK["construction_audit"]["result_sha256"]:
    raise RuntimeError("STOP_CONSTRUCTION_AUDIT_RESULT_HASH_BEFORE_CALL")

def run_preflight(arm, contract):
    root=OUT/"preflight"/arm; root.mkdir(parents=True,exist_ok=False)
    workspace=OUT/"workspaces"/arm
    schema=(LIVE/("plain_form_points_schema_v1.json" if contract=="plain" else "compiled_form_grounding_schema_v1.json"))
    prompt="Schema compatibility probe. Produce any object accepted by the supplied schema."
    result=backend.call(root/"model-call",prompt,None,contract,workspace)
    events=[json.loads(line) for line in (Path(result["request_directory"])/"container-output/run/events.jsonl").read_text().splitlines()]
    threads=[r["thread_id"] for r in events if r.get("type")=="thread.started"]
    return {"call_id":threads[0],"stage":"schema_preflight","requested_model":"gpt-5.6-luna",
        "requested_effort":"low","usage":result["usage"],"model_visible_images":0}

def run_arm(arm, seed, workspace):
    return original_run_arm(arm,seed,workspace,model_call=backend.call)
original_run_arm=live.run_arm
live.run_arm=run_arm
live.preflight_call=run_preflight
plan=json.loads((OUT/"preregistration.json").read_text())
if set(plan)!={"schema","status","study","seed","arm_order","task_calls",
        "no_image_schema_preflights","maximum_host_model_calls","retry","model","effort",
        "coordinate_click_actions_authorized","host_OS_Gui_authority","sources","scope"}:
    raise RuntimeError("STOP_PREREGISTRATION_FIELDS")
if plan["seed"]!=284937 or plan["maximum_host_model_calls"]!=17 or plan["retry"] is not False:
    raise RuntimeError("STOP_PREREGISTRATION_SEED_OR_BUDGET")
if plan["sources"]!=LOCK["protocol_sources"]:
    raise RuntimeError("STOP_PREREGISTRATION_SOURCE_LOCK_MISMATCH")
if os.environ.get("ISSUE3824_RUNNER_IMAGE")!=LOCK["model_runner_image"]:
    raise RuntimeError("STOP_MODEL_RUNNER_IMAGE_WIRING")
if os.environ.get("ISSUE3824_OUTER_IMAGE")!=LOCK["outer_image"]:
    raise RuntimeError("STOP_OUTER_IMAGE_WIRING")
if sum(sum(v) for v in __import__("integrated_efficiency_protocol_v1").EXPECTED_MODEL_CALLS.values())!=14:
    raise RuntimeError("STOP_PROTOCOL_TASK_CALL_ARITHMETIC")
if plan["no_image_schema_preflights"]!=3 or 14+plan["no_image_schema_preflights"]!=17:
    raise RuntimeError("STOP_PROTOCOL_TOTAL_CALL_ARITHMETIC")
preflight_test=json.loads((Path(__file__).resolve().parent/
    "evidence/preflight-parser-test/run-01/preflight-parser-test-result.json").read_text())
if preflight_test.get("status")!="PASS_SCHEMA_ONLY_SEPARATE_FROM_TASK_SEMANTICS" or preflight_test.get("host_model_calls")!=0:
    raise RuntimeError("STOP_PREFLIGHT_PARSER_REGRESSION_GATE")
if sha(Path(__file__).resolve().parent/"evidence/preflight-parser-test/run-01/preflight-parser-test-result.json")!=LOCK["smoke_evidence"]["files"]["evidence/preflight-parser-test/run-01/preflight-parser-test-result.json"]:
    raise RuntimeError("STOP_PREFLIGHT_EVIDENCE_HASH")
for name,digest in plan["sources"].items():
    if sha(LIVE/name)!=digest: raise RuntimeError("STOP_SOURCE_HASH:"+name)
preflights={}
for arm in ARMS:
    preflights[arm]=run_preflight(arm,"plain" if arm=="plain" else "compiled")
arms={}; independent={}
for arm in ARMS:
    arms[arm],independent[arm]=live.run_arm(arm,plan["seed"],OUT/"workspaces"/arm)
trace={"schema":"integrated_efficiency_trace_v1","arms":arms,"preflight_calls":preflights,
    "integration_discoveries":json.loads((LIVE/"integrated_efficiency_discoveries_v1.json").read_text())}
dump(OUT/"trace.json",trace)
evaluation=live.evaluate(trace)
dump(OUT/"evaluation.json",evaluation)
dump(OUT/"independent-evaluations.json",independent)
print(json.dumps({"status":"RUN_RETURNED","disposition":evaluation["disposition"],
    "correct":{a:evaluation["arms"][a]["correct"] for a in ARMS}},sort_keys=True))
