"""Frozen live resize repair from a verified target handle."""
import contextlib,hashlib,json,os,shutil,sys,threading,time
from pathlib import Path
from urllib.parse import parse_qs
from PIL import Image

HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1]
PREREG=HERE/"target_handle_semantic_repair_live_v1_prereg.json"
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding="utf-8"))
def persist(path,value):
    with Path(path).open("x",encoding="utf-8",newline="\n") as stream:
        stream.write(json.dumps(value,indent=2)+"\n");stream.flush();os.fsync(stream.fileno())

def verify(plan):
    checks={name:(REPO/name).is_file() and sha(REPO/name)==digest
            for name,digest in plan["source_sha256"].items()}
    checks.update({"output_absent":not(REPO/plan["output"]).exists(),
        "one_no_retry":plan["allocations"]==1 and plan["retry_limit"]==0,
        "zero_model":plan["model_calls"]==0,"seed":plan["seed"]==212,
        "resize":plan["resize_width_delta"]==-120,
        "handle":plan["handle_box"]==[250,234,42,18] and plan["handle_offset"]==[20,9],
        "relation":plan["relation"]=={"schema":"target-semantic-region-relation-v1",
            "anchor":"target_box_origin","offset":[-235,-64],"size":[315,45]},
        "thresholds":plan["thresholds_ms"]=={"handle_resolution_lte":50,
            "contract_repair_lte":5,"first_feedback_lte":300,
            "useful_feedback_lte":650,"probe_compute_lte":5}})
    return checks

def wait_terminal(events,identifier,timeout=7):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        row=next((item for item in events if item.get("event")=="terminal" and
                  item.get("id")==identifier),None)
        if row is not None:return row
        time.sleep(.001)
    raise RuntimeError("terminal missing: "+identifier)

def main():
    plan=read(PREREG);verification=verify(plan)
    if "--verify-only" in sys.argv:
        print(json.dumps({"passed":all(verification.values()),"checks":verification},indent=2))
        return 0 if all(verification.values()) else 1
    if not all(verification.values()):raise RuntimeError(verification)
    if os.name=="nt" or not Path("/mnt/c").is_dir():raise RuntimeError("run from WSL")
    from executor_v13 import Executor
    from executor_v11 import program_sha256
    from release_event_socket_v3 import ReleaseEventSocket
    from scoped_target_handle_v1 import TargetHandleStore
    from semantic_probe_backend_v3 import Backend,suite
    from target_handle_semantic_binding_v1 import derive_contract,repair_contract
    from target_relative_crop_semantic_probe_v1 import score_path
    from unix_json_deadline import exchange
    from Xlib import display

    root=REPO/plan["output"];root.mkdir(parents=True,exist_ok=False)
    events=[];clients={};threads=[];delivery=ReleaseEventSocket()
    session=backend=executor=controller=output=app_server=None;original_geometry=None
    def emit(row):row["runtime_emit_ns"]=time.perf_counter_ns();events.append(row);delivery.append(row)
    def exchange_record(request):
        row={"request":request,"client_started_ns":time.perf_counter_ns()}
        reply=exchange(delivery.path,request,timeout=request["timeout"]+1)
        row.update({"reply":reply,"client_returned_ns":time.perf_counter_ns(),
                    "response_bytes":len((json.dumps(reply)+"\n").encode())});return row
    def semantic_client(action_id):
        result={"feedback":[],"exchanges":[]};after=0
        for ordinal in range(plan["max_positive_exchanges"]):
            request={"after":after,"events":["semantic_probe","terminal"],"timeout":4,
                     "action_id":action_id,"request_id":f"repair-positive-{ordinal}"}
            exchange_row=exchange_record(request);result["exchanges"].append(exchange_row)
            boundary=exchange_row["reply"]["records"][-1]
            if boundary["event"]=="terminal":break
            result["feedback"].append(boundary)
            if boundary["score"]["success"]:break
            after=exchange_row["reply"]["cursor"]
        result["completed_ns"]=time.perf_counter_ns();clients["positive"]=result
    def submit(identifier,program):
        submitted_ns=time.perf_counter_ns();executor.submit(identifier,program,backend.sequence,
            time.perf_counter_ns()+8_000_000_000)
        accepted=next(row for row in events if row.get("event")=="accepted" and row.get("id")==identifier)
        return {"id":identifier,"program":program,"submitted_ns":submitted_ns,
                "accepted":accepted,"terminal":wait_terminal(events,identifier)}
    def wait_binding(predicate,message):
        deadline=time.monotonic()+2;value=backend.binding()
        while not predicate(value) and time.monotonic()<deadline:
            time.sleep(.01);value=backend.binding()
        if not predicate(value):raise RuntimeError(message)
        return value

    report={"schema":"target-handle-semantic-repair-live-v1",
            "allocation_id":plan["allocation_id"],"verification":verification,"scope":plan["scope"]}
    try:
        with (root/"setup.txt").open("w") as diagnostics,contextlib.redirect_stdout(diagnostics):
            session=suite.Session();goal,output,app_server=suite.prepare(
                session,"chromium",plan["seed"],plan["chromium"])
            backend=Backend(session,root,emit);controller=display.Display(session.name)
        executor=Executor(backend,emit);backend.snapshot("initial",0)
        navigate=submit("handle-repair-navigate",[
            {"op":"chord","modifier":"Control_L","key":"l"},
            {"op":"text","text":goal["url"]},{"op":"key","key":"Return"},
            {"op":"wait_title","contains":"AI FORM READY","timeout_ms":1500}])
        fill=submit("handle-repair-fill",[
            {"op":"pointer_click","x":180,"y":243,"duration_ms":80},
            {"op":"chord","modifier":"Control_L","key":"a"},
            {"op":"text","text":goal["token"]},{"op":"observe"}])
        backend.snapshot("handle-repair-source",0);source=events[-1]
        original_geometry=list(source["pointer_binding"]["geometry"])
        source_path=root/Path(source["image"]).name
        with Image.open(source_path) as opened:source_image=opened.convert("RGB")
        store=TargetHandleStore("chromium-handle-semantic-repair",lambda:"save-handle-01")
        mint=store.mint("save_form","window_content",plan["handle_box"],source,
            source_image,time.perf_counter_ns(),ttl_ms=60000,freshness_ms=3000,
            search_radius=0,allowed_transformations=("window_translation",))
        source_resolution=store.resolve_point(mint["handle"],plan["handle_offset"],source,
            source_image,time.perf_counter_ns())
        initial_binding=derive_contract("submission_from_save_handle","submission_heading",
            mint,source_resolution,source,plan["relation"],plan["expected_crop_sha256"],
            "submission_title_exactly_visible")

        window=controller.create_resource_object("window",source["pointer_binding"]["surface"])
        window.configure(width=original_geometry[2]+plan["resize_width_delta"]);controller.sync()
        resized_binding=wait_binding(lambda value:value.get("surface")==source["pointer_binding"]["surface"]
            and value.get("geometry",[0,0,0])[2]==original_geometry[2]-120,"resize missing")
        resized_event={"event":"test_surface_resized","before":source["pointer_binding"],
            "after":resized_binding,"grants_input_authority":False,
            "runtime_emit_ns":time.perf_counter_ns()};events.append(resized_event);delivery.append(resized_event)
        backend.snapshot("handle-repair-resized",0);resized=events[-1]
        resized_path=root/Path(resized["image"]).name
        old_contract_score=score_path(initial_binding["contract"],resized_path,
                                      resized["pointer_binding"])
        with Image.open(resized_path) as opened:resized_image=opened.convert("RGB")
        resolution_started_ns=time.perf_counter_ns()
        resized_resolution=store.resolve_point(mint["handle"],plan["handle_offset"],resized,
            resized_image,time.perf_counter_ns())
        resolution_completed_ns=time.perf_counter_ns()
        repair_started_ns=time.perf_counter_ns()
        repaired=repair_contract(initial_binding["contract"],mint,resized_resolution,
                                 resized,plan["relation"])
        repair_completed_ns=time.perf_counter_ns()

        action_id="handle-repaired-submit"
        registration=backend.register_semantic_probe(action_id,repaired["contract"])
        request_count=len(delivery.request_receipts())
        client_thread=threading.Thread(target=semantic_client,args=(action_id,));threads.append(client_thread)
        client_thread.start()
        if not delivery.wait_requests(request_count+1):raise RuntimeError("semantic client missing")
        registered_ns=delivery.request_receipts()[-1]["received_ns"]
        submit_action=submit(action_id,[
            {"op":"pointer_click","x":resized_resolution["point"][0],
             "y":resized_resolution["point"][1],"duration_ms":80},
            {"op":"wait_title","contains":"AI FORM SAVED","timeout_ms":1500},{"op":"observe"}])
        client_thread.join(4)
        if client_thread.is_alive():raise RuntimeError("semantic client timed out")
        positive=clients["positive"];useful=next((row for row in positive["feedback"]
                                                  if row["score"]["success"]),None)
        if useful is None:raise RuntimeError("repaired semantic success missing")
        useful_index=positive["feedback"].index(useful)
        first_ns=positive["exchanges"][0]["client_returned_ns"]
        useful_ns=positive["exchanges"][useful_index]["client_returned_ns"]
        reconciliations=[row for row in events if row.get("event")=="semantic_probe_reconciled"]
        useful_reconciliation=next(row for row in reconciliations if row["sequence"]==useful["sequence"])
        actual=parse_qs(output.read_text()) if output.exists() else {}
        metrics={"handle_resolution_ms":(resolution_completed_ns-resolution_started_ns)/1e6,
            "contract_repair_ms":(repair_completed_ns-repair_started_ns)/1e6,
            "resize_capture_to_repair_ready_ms":(repair_completed_ns-resized["capture_ns"])/1e6,
            "admission_to_first_feedback_ms":(first_ns-submit_action["accepted"]["accepted_ns"])/1e6,
            "admission_to_useful_feedback_ms":(useful_ns-submit_action["accepted"]["accepted_ns"])/1e6,
            "useful_probe_compute_ms":(useful["probe_completed_ns"]-useful["probe_started_ns"])/1e6,
            "useful_probe_to_image_ready_ms":(useful_reconciliation["image_ready_ns"]-
                                                useful["probe_completed_ns"])/1e6,
            "useful_client_to_terminal_ms":(submit_action["terminal"]["terminal_ns"]-useful_ns)/1e6,
            "positive_exchanges":len(positive["exchanges"]),"frontier_model_resumptions":0}
        actions=[navigate,fill,submit_action]
        checks={"source_geometry":original_geometry==plan["expected_source_geometry"],
            "minted_verified_handle":mint["status"]=="VALID" and source_resolution["eligible"] is True,
            "resize_exact":resized["pointer_binding"]["geometry"][2]==original_geometry[2]-120,
            "old_contract_refuses_resize":old_contract_score["reason"]=="surface_size_changed" and
                                          old_contract_score["observed_crop_sha256"] is None,
            "handle_revalidated_after_resize":resized_resolution["eligible"] is True and
                                               resized_resolution["point"]==[270,243],
            "local_repair_no_authority":repaired["receipt"]["status"]=="REPAIRED_NO_AUTHORITY" and
                repaired["receipt"]["model_calls"]==0 and repaired["receipt"]["grants_input_authority"] is False,
            "repaired_geometry":repaired["contract"]["source_geometry"]==resized["pointer_binding"]["geometry"],
            "client_registered":registered_ns<=submit_action["submitted_ns"],
            "programs_attested":all(row["accepted"]["program_sha256"]==program_sha256(row["program"])
                                    for row in actions),
            "semantic_success":useful["score"]["success"] is True and
                               useful["score"]["binding_status"]=="CURRENT_EXACT",
            "independent_saved_value":actual=={"value":[goal["token"]]},
            "exact_reconciliation":all(row["reconciliation"]["matches"] for row in reconciliations),
            "empty_release":all(row["terminal"]["status"]=="completed" and
                row["terminal"]["release"]["verified"] is True and
                row["terminal"]["release"]["keys_down"]==[] and
                row["terminal"]["release"]["buttons_down"]==[] for row in actions),
            "local_cost_limits":metrics["handle_resolution_ms"]<=plan["thresholds_ms"]["handle_resolution_lte"] and
                metrics["contract_repair_ms"]<=plan["thresholds_ms"]["contract_repair_lte"],
            "feedback_limits":metrics["admission_to_first_feedback_ms"]<=plan["thresholds_ms"]["first_feedback_lte"] and
                metrics["admission_to_useful_feedback_ms"]<=plan["thresholds_ms"]["useful_feedback_lte"] and
                metrics["useful_probe_compute_ms"]<=plan["thresholds_ms"]["probe_compute_lte"],
            "pre_artifact_terminal":metrics["useful_probe_to_image_ready_ms"]>0 and
                                    metrics["useful_client_to_terminal_ms"]>0,
            "zero_model_retry":metrics["frontier_model_resumptions"]==plan["model_calls"]==plan["retry_limit"]==0}
        report.update({"passed":all(checks.values()),"checks":checks,"goal":goal,
            "navigate":navigate,"fill":fill,"source_observation":source,"mint":mint,
            "source_resolution":source_resolution,"initial_binding":initial_binding,
            "resized_binding":resized_binding,"resized_observation":resized,
            "old_contract_score":old_contract_score,"resized_resolution":resized_resolution,
            "repaired":repaired,"registration":registration,"submit_action":submit_action,
            "clients":clients,"useful_probe":useful,"reconciliations":reconciliations,
            "actual":actual,"metrics_ms":metrics,"model_calls":0,"retry_count":0})
    finally:
        for thread in threads:
            if thread.is_alive():thread.join(1)
        if executor is not None:executor.close()
        if controller is not None and original_geometry is not None:
            try:
                binding=backend.binding();window=controller.create_resource_object("window",binding["surface"])
                window.configure(x=original_geometry[0],y=original_geometry[1],
                                 width=original_geometry[2],height=original_geometry[3]);controller.sync()
            except Exception:pass
            controller.close()
        if backend is not None:
            try:backend.close()
            finally:(root/"owner-events.json").write_text(json.dumps(backend.owner.records,indent=2)+"\n")
        if output is not None and output.exists():shutil.copy2(output,root/output.name)
        if app_server is not None:app_server.shutdown();app_server.server_close()
        if session is not None:session.close();shutil.rmtree(session.tmp)
        delivery.close();(root/"events.json").write_text(json.dumps(events,indent=2)+"\n")
        if len(report)>4:persist(root/"report.json",report)
    print(json.dumps({"passed":report.get("passed"),"checks":report.get("checks"),
                      "metrics_ms":report.get("metrics_ms"),"scope":report["scope"]},indent=2))
    return 0 if report.get("passed") else 1
if __name__=="__main__":raise SystemExit(main())
