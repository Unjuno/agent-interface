from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; RUN=ROOT/"research/integration/issue_2849_task1_orbstack_formal_v26/evidence/task1-seed-284926"; OUT=RUN/"task-run"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())
def main():
    req=sorted((RUN/"ipc").glob("*.request.json")); rsp=sorted((RUN/"ipc").glob("*.response.jsonl")); br=sorted((RUN/"ipc").glob("*.broker.json"))
    pre=read(OUT/"pre-call-source-manifest.json"); launch=read(RUN/"launch-result.json"); scope=read(OUT/"task1-scope-result.json")
    task=read(OUT/"frozen-task.json"); trace=read(OUT/"task-trace.json"); history=read(OUT/"submission-history.snapshot.json"); fixture=read(OUT/"six-task-fixture-evaluation.json")
    checks={"one_ipc_request_response_broker":len(req)==len(rsp)==len(br)==1,
      "host_cli_identity_matches_freeze":read(br[0]).get("host_cli_identity",{}).get("sha256")==pre["host_model_cli"]["sha256"] if br else False,
      "one_host_codex_cli_invocation":read(br[0]).get("host_cli_invoked") is True if br else False,
      "model_asset_hashes_match_mirror":False,
      "task_seed_identity_correct":task.get("seed")==284926 and (task.get("task_id"),task.get("layout"),task.get("phase"),task.get("route"))==("task-1","A","cold","plain"),
      "one_exact_submission_and_empty_verified_releases":scope.get("status")=="PASS_TASK1_SCOPED" and scope.get("exact_submission_count")==1 and scope.get("total_fixture_submission_count")==1 and scope.get("runtime_releases_verified") is True and trace.get("releases_verified") is True,
      "trace_one_image_call_completed":trace.get("typed_outcome")=="completed" and trace.get("model_visible_images")==1 and len(trace.get("model_calls",[]))==1 and trace.get("submission_count")==1 and trace.get("exact_submission") is True,
      "independent_history_exact_token":len(history)==1 and history[0].get("exact") is True and history[0].get("submitted_values")==[task.get("token")] and history[0].get("layout")=="A",
      "six_task_evaluation_boundary_not_success":fixture.get("success") is False and fixture.get("record_count")==1,
      "outer_launcher_returned_zero":launch.get("status")=="OUTER_RETURNED" and launch.get("outer_returncode")==0,
      "authority_false_and_one_call":scope.get("authority_granted") is False and scope.get("model_call_count")==1 and launch.get("counts",{}).get("requests")==1,
      "baseline_main_matches_prereg":pre.get("main_commit")=="4b2e84b79633281138b6f72c70e98d5fe9a5bf95"}
    if len(req)==len(br)==1:
      q=read(req[0]); mirror=RUN/"host-model-mirror"
      checks["model_asset_hashes_match_mirror"]=(sha(mirror/"schema.json")==q.get("schema_sha256") and sha(mirror/"instructions.txt")==q.get("instructions_sha256") and sha(mirror/"image.png")==q.get("image_sha256"))
    audit={"seed":284926,"status":"PASS_TASK1_SCOPED" if all(checks.values()) else "STOP_OR_FAIL_TASK1_SCOPED","checks":checks,
      "counts":{"requests":len(req),"responses":len(rsp),"broker_receipts":len(br)},"authority_granted":False,
      "scope":"single task-1/layout-A/cold/plain only; no six-task or efficiency claim",
      "evidence_sha256":{"request":sha(req[0]) if req else None,"response":sha(rsp[0]) if rsp else None,"broker":sha(br[0]) if br else None}}
    (RUN/"independent-audit.json").write_text(json.dumps(audit,indent=2,sort_keys=True)+"\n")
    files=sorted(p for p in RUN.rglob("*") if p.is_file() and p.name!="SHA256SUMS")
    (RUN/"SHA256SUMS").write_text("".join(f"{sha(p)}  {p.relative_to(RUN)}\n" for p in files))
    return 0 if all(checks.values()) else 1
if __name__=="__main__": raise SystemExit(main())
