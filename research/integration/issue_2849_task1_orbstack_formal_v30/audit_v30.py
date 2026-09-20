from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; RUN=ROOT/"research/integration/issue_2849_task1_orbstack_formal_v30/evidence/task1-seed-284930"; OUT=RUN/"task-run"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())
def main():
    pre=read(OUT/"pre-call-source-manifest.json"); launch=read(RUN/"launch-result.json"); receipt=read(RUN/"outer-runtime-receipt.json")
    req=sorted((RUN/"ipc").glob("*.request.json")); rsp=sorted((RUN/"ipc").glob("*.response.jsonl")); br=sorted((RUN/"ipc").glob("*.broker.json"))
    row=read(OUT/"task-trace.json"); before=read(OUT/"trace-pre-finish.json"); scope=read(OUT/"task1-scope-result.json"); task=read(OUT/"frozen-task.json"); history=read(OUT/"submission-history.snapshot.json"); fixture=read(OUT/"six-task-fixture-evaluation.json")
    runner=read(OUT/"model-calls/plain/task-1/anchor/runner/process.json"); releases=read(OUT/"runtime/runtime/owner-events.json")
    checks={"all_frozen_sources_match":all((ROOT/x["path"]).is_file() and sha(ROOT/x["path"])==x["sha256"] for x in pre["source_files"]),
      "one_request_response_broker":len(req)==len(rsp)==len(br)==1 and launch.get("counts")=={"requests":1,"responses":1,"broker_receipts":1},
      "one_host_model_call_and_corrected_runner":read(br[0]).get("host_cli_invoked") is True and runner.get("exit_code")==0 and runner.get("assistant_message_count")==1 and runner.get("completed_turn_count")==1 if br else False,
      "task_identity_frozen":(task.get("seed"),task.get("task_id"),task.get("layout"),task.get("phase"),task.get("route"))==(284930,"task-1","A","cold","plain"),
      "pre_finish_trace_was_not_authoritative":before.get("submission_count")==0 and before.get("exact_submission") is False,
      "post_finish_trace_matches_exact_history":row.get("submission_count")==1 and row.get("exact_submission") is True and len(history)==1 and history[0].get("exact") is True and history[0].get("submitted_values")==[task.get("token")],
      "task1_scoped_gate_passes":scope.get("status")=="PASS_TASK1_SCOPED" and scope.get("model_call_count")==1 and scope.get("runtime_releases_verified") is True,
      "all_runtime_releases_verified":bool(releases) and all(x.get("verified") is True and x.get("keys_down")==[] and x.get("buttons_down")==[] for x in releases),
      "six_task_boundary_is_not_success":fixture.get("success") is False and fixture.get("record_count")==1 and len(fixture.get("missing",[]))==5,
      "outer_formal_returned_zero_and_no_retry":launch.get("outer_returncode")==0 and receipt.get("main_return")==0 and launch.get("max_host_model_calls")==1 and launch.get("counts",{}).get("requests")==1,
      "authority_remained_false":scope.get("authority_granted") is False and receipt.get("authority_granted") is False and launch.get("authority_granted") is False}
    audit={"issue":2849,"successor_issue":3798,"seed":284930,"status":"PASS_TASK1_SCOPED" if all(checks.values()) else "FAIL_OR_STOP_TASK1_SCOPED","checks":checks,"counts":{"requests":len(req),"responses":len(rsp),"broker_receipts":len(br),"model_calls":len(row.get("model_calls",[]))},"scope":"one task-1/layout-A/cold/plain only; no six-task or efficiency claim","authority_granted":False}
    (RUN/"independent-audit.json").write_text(json.dumps(audit,indent=2,sort_keys=True)+"\n")
    files=sorted(p for p in RUN.rglob("*") if p.is_file() and p.name!="SHA256SUMS")
    (RUN/"SHA256SUMS").write_text("".join(f"{sha(p)}  {p.relative_to(RUN)}\n" for p in files))
    return 0 if audit["status"]=="PASS_TASK1_SCOPED" else 1
if __name__=="__main__": raise SystemExit(main())
