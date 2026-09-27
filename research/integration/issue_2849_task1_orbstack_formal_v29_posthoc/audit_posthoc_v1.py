from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
RUN=ROOT/"research/integration/issue_2849_task1_orbstack_formal_v29/evidence/task1-seed-284929"
OUT=RUN/"task-run"
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_text())
def main():
    frozen=read(OUT/"pre-call-source-manifest.json"); source_checks={}; main_checks={}
    for row in frozen["source_files"]:
        path=ROOT/row["path"]
        source_checks[row["path"]]=path.is_file() and sha(path)==row["sha256"]
        if row.get("origin")=="main":
            try: blob=subprocess.check_output(["git","show",f"{frozen['main_commit']}:{row['path']}"],cwd=ROOT,stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError: main_checks[row["path"]]=False
            else: main_checks[row["path"]]=hashlib.sha256(blob).hexdigest()==row["sha256"]
    req=sorted((RUN/"ipc").glob("*.request.json")); rsp=sorted((RUN/"ipc").glob("*.response.jsonl")); brokers=sorted((RUN/"ipc").glob("*.broker.json"))
    launch=read(RUN/"launch-result.json"); receipt=read(RUN/"outer-runtime-receipt.json")
    task=read(OUT/"frozen-task.json"); trace=read(OUT/"task-trace.json"); scope=read(OUT/"task1-scope-result.json")
    history=read(OUT/"submission-history.snapshot.json"); fixture=read(OUT/"six-task-fixture-evaluation.json")
    releases=read(OUT/"runtime/runtime/owner-events.json")
    process=read(OUT/"model-calls/plain/task-1/anchor/runner/process.json")
    events=[json.loads(line) for line in (OUT/"model-calls/plain/task-1/anchor/runner/events.jsonl").read_text().splitlines() if line.strip()]
    task_record=history[0] if len(history)==1 else {}
    check={
      "frozen_source_file_count_matches":len(source_checks)==frozen.get("source_file_count")==121,
      "all_frozen_source_hashes_match":all(source_checks.values()),
      "all_main_origin_sources_match_frozen_commit":bool(main_checks) and all(main_checks.values()),
      "one_ipc_request_response_and_broker_receipt":len(req)==len(rsp)==len(brokers)==1 and launch.get("counts")=={"requests":1,"responses":1,"broker_receipts":1},
      "one_host_codex_call_returned":read(brokers[0]).get("host_cli_invoked") is True and read(brokers[0]).get("returncode")==0 if brokers else False,
      "corrected_runner_processed_one_assistant_turn":process.get("exit_code")==0 and process.get("assistant_message_count")==1 and process.get("completed_turn_count")==1 and sum(e.get("type")=="item.completed" and e.get("item",{}).get("type")=="agent_message" for e in events)==1,
      "formal_task_identity_matches_seed":(task.get("seed"),task.get("task_id"),task.get("layout"),task.get("phase"),task.get("route"))==(284929,"task-1","A","cold","plain"),
      "runtime_history_has_one_exact_token_submission":len(history)==1 and task_record.get("exact") is True and task_record.get("submitted_values")==[task.get("token")] and task_record.get("expected_token")==task.get("token"),
      "runtime_terminal_and_release_verification_present":trace.get("typed_outcome")=="completed" and trace.get("releases_verified") is True and bool(releases) and all(e.get("verified") is True and e.get("buttons_down")==[] and e.get("keys_down")==[] for e in releases),
      "trace_scope_conflict_preserved":trace.get("submission_count")==0 and trace.get("exact_submission") is False and scope.get("status")=="FAIL_TASK1_SCOPED" and scope.get("exact_submission_count")==1,
      "outer_formal_gate_failed_and_no_retry":launch.get("outer_returncode")==1 and receipt.get("main_return")==1 and launch.get("counts",{}).get("requests")==1 and launch.get("max_host_model_calls")==1,
      "six_task_evaluation_not_success":fixture.get("success") is False and fixture.get("record_count")==1 and len(fixture.get("missing",[]))==5,
      "original_sha256_manifest_absent":not (RUN/"SHA256SUMS").exists(),
      "original_task_outcome_remains_failure":scope.get("status")=="FAIL_TASK1_SCOPED" and not all((trace.get("submission_count")==1,trace.get("exact_submission") is True)),
    }
    prior=sorted(p for p in RUN.rglob("*") if p.is_file() and p.name not in {"posthoc-independent-audit.json","posthoc-SHA256SUMS"})
    inventory={str(p.relative_to(RUN)):sha(p) for p in prior}
    result={"issue":2849,"seed":284929,"status":"POSTHOC_AUDIT_PASS_FAILURE_CLASSIFICATION" if all(check.values()) else "POSTHOC_AUDIT_STOP_INCOMPLETE","accepted_formal_outcome":"FAIL_TASK1_SCOPED","scope":"evidence consistency audit only; no task, model, GUI, IPC, or authority action","checks":check,"frozen_source_hash_checks":source_checks,"main_commit_blob_checks":main_checks,"counts":{"frozen_source_files":len(source_checks),"main_origin_source_files":len(main_checks),"ipc_requests":len(req),"ipc_responses":len(rsp),"broker_receipts":len(brokers),"model_calls":len(trace.get("model_calls",[])),"history_records":len(history),"verified_releases":sum(e.get("verified") is True for e in releases)},"submission_history_record":task_record,"trace_summary":{"submission_count":trace.get("submission_count"),"exact_submission":trace.get("exact_submission"),"typed_outcome":trace.get("typed_outcome"),"releases_verified":trace.get("releases_verified")},"scope_summary":scope,"six_task_evaluation":fixture,"original_sha256_manifest":"absent; this supplemental manifest does not claim an original manifest was verified","auditor_sha256":sha(Path(__file__)),"preexisting_evidence_file_sha256":inventory}
    audit_path=RUN/"posthoc-independent-audit.json"; audit_path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    files=sorted(p for p in RUN.rglob("*") if p.is_file() and p.name!="posthoc-SHA256SUMS")
    (RUN/"posthoc-SHA256SUMS").write_text("".join(f"{sha(p)}  {p.relative_to(RUN)}\n" for p in files))
    print(json.dumps({"status":result["status"],"accepted_formal_outcome":result["accepted_formal_outcome"],"checks":check,"file_count_in_supplemental_manifest":len(files),"auditor_sha256":result["auditor_sha256"]},sort_keys=True))
    return 0 if result["status"]=="POSTHOC_AUDIT_PASS_FAILURE_CLASSIFICATION" else 1
if __name__=="__main__": raise SystemExit(main())
