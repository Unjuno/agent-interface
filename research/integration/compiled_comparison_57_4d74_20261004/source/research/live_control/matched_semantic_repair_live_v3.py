"""Post-model-refreshed matched local repair versus visual reacquisition."""
import contextlib,hashlib,json,os,shutil,statistics,sys,threading,time
from pathlib import Path
from urllib.parse import parse_qs
from PIL import Image

HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1]
PREREG=HERE/"matched_semantic_repair_live_v3_prereg.json"
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding="utf-8"))
def persist(path,value):
    with Path(path).open("x",encoding="utf-8",newline="\n") as stream:
        stream.write(json.dumps(value,indent=2)+"\n");stream.flush();os.fsync(stream.fileno())
def inside(point,box):return box[0]<=point[0]<box[2] and box[1]<=point[1]<box[3]

def noncompletion_summary(arm):
    if arm.get("status") not in ("TASK_DEFERRED","TASK_BLOCKED") or \
            arm.get("passed") is not False or arm.get("comparison_eligible") is not False or \
            arm.get("retry_count")!=0:
        raise ValueError("exact typed noncompletion arm required")
    key="reacquisition_admission" if "reacquisition_admission" in arm else "initial_admission"
    admission=arm.get(key)
    if type(admission) is not dict or admission.get("status")!=arm["status"] or \
            admission.get("task_mutation_eligible") is not False or \
            admission.get("grants_semantic_authority") is not False or \
            admission.get("grants_input_authority") is not False:
        raise ValueError("no-authority noncompletion admission required")
    return {"status":"DEFERRED" if arm["status"]=="TASK_DEFERRED" else "BLOCKED",
            "stage":"reacquisition" if key=="reacquisition_admission" else "initial_grounding",
            "reason":admission["reason"],"comparison_eligible":False,
            "grants_semantic_authority":False,"grants_input_authority":False}

def verify(plan):
    checks={name:(REPO/name).is_file() and sha(REPO/name)==digest for name,digest in plan["source_sha256"].items()}
    checks.update({"output_absent":not(REPO/plan["output"]).exists(),
        "one_allocation_no_retry":plan["allocations"]==1 and plan["retry_limit"]==0,
        "order":plan["order"]==["local","model","model","local"],
        "same_seed":plan["seed"]==215,"model":plan["model"]=={"name":"gpt-5.6-luna","effort":"low"},
        "calls":plan["expected_arm_model_calls"]=={"local":1,"model":2},
        "noncompletion_policy":plan["noncompletion_policy"]=={
            "initial_grounding":"before_token_entry",
            "capacity":"stop_as_deferred_no_comparison",
            "other_failure":"stop_as_blocked_no_comparison",
            "later_reacquisition":"typed_stop_no_comparison",
            "completed_reacquisition":"passive_exact_refresh_then_patch_revalidation"},
        "thresholds":plan["thresholds"]=={"minimum_input_token_advantage":5000,
            "minimum_recovery_ms_advantage":5000,"feedback_lte_ms":650,
            "probe_compute_lte_ms":5,"post_model_refresh_lte_ms":300,
            "post_model_revalidation_lte_ms":5}})
    return checks

def wait_terminal(events,identifier,timeout=7):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        row=next((x for x in events if x.get("event")=="terminal" and x.get("id")==identifier),None)
        if row is not None:return row
        time.sleep(.001)
    raise RuntimeError("terminal missing: "+identifier)

def run_arm(plan,root,ordinal,mode):
    from executor_v13 import Executor
    from executor_v11 import program_sha256
    from release_event_socket_v3 import ReleaseEventSocket
    from scoped_target_handle_v1 import TargetHandleStore
    from post_model_target_revalidation_v1 import receipt as revalidation_receipt
    from semantic_probe_backend_v3 import Backend,suite
    from semantic_grounding_admission_v1 import admit as admit_grounding
    from semantic_repair_model_v2 import invoke as model_invoke
    from target_handle_semantic_binding_v1 import derive_contract,repair_contract
    from target_relative_crop_semantic_probe_v1 import score_path
    from unix_json_deadline import exchange
    from Xlib import display
    arm=root/f"arm-{ordinal+1:02d}-{mode}";arm.mkdir();(arm/"empty-workspace").mkdir()
    events=[];client={"feedback":[],"exchanges":[]};delivery=ReleaseEventSocket();threads=[]
    session=backend=executor=controller=output=app_server=None;original_geometry=None
    def emit(row):row["runtime_emit_ns"]=time.perf_counter_ns();events.append(row);delivery.append(row)
    def exchange_record(request):
        result={"request":request,"client_started_ns":time.perf_counter_ns()}
        reply=exchange(delivery.path,request,timeout=request["timeout"]+1)
        result.update({"reply":reply,"client_returned_ns":time.perf_counter_ns(),
                       "response_bytes":len((json.dumps(reply)+"\n").encode())});return result
    def receive(action_id):
        after=0
        for index in range(plan["max_positive_exchanges"]):
            row=exchange_record({"after":after,"events":["semantic_probe","terminal"],
                "timeout":4,"action_id":action_id,"request_id":f"arm-{ordinal+1}-{mode}-{index}"})
            client["exchanges"].append(row);boundary=row["reply"]["records"][-1]
            if boundary["event"]=="terminal":break
            client["feedback"].append(boundary)
            if boundary["score"]["success"]:break
            after=row["reply"]["cursor"]
        client["completed_ns"]=time.perf_counter_ns()
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
    def prompt():
        return ("The attached current 1280x800 screenshot is a private Chromium form before "
            "value entry. Identify one point inside the visible text Value field "
            "and the center of the visible Save button. Declare the fixed bounded method exactly "
            "as required by the schema. Return references only; runtime validation controls input.")
    def ground(label,image):
        outcome=model_invoke(arm/label,prompt(),image,arm/"empty-workspace")
        return outcome,admit_grounding(outcome)
    def checked_grounding(record):
        g=record["grounding"]
        if not inside(g["field_point"],plan["field_box"]) or not inside(g["submit_point"],plan["submit_box"]):
            raise RuntimeError("model point outside independent target boxes")
        return g
    def mint_reference(store,grounding,observation,image):
        point=grounding["submit_point"];box=[point[0]-20,point[1]-9,42,18]
        mint=store.mint("save_form","window_content",box,observation,image,
            time.perf_counter_ns(),ttl_ms=60000,freshness_ms=3000,search_radius=0,
            allowed_transformations=("window_translation",))
        relation={"schema":"target-semantic-region-relation-v1","anchor":"target_box_origin",
            "offset":[plan["semantic_screen_box"][0]-box[0],plan["semantic_screen_box"][1]-box[1]],
            "size":[plan["semantic_screen_box"][2]-plan["semantic_screen_box"][0],
                    plan["semantic_screen_box"][3]-plan["semantic_screen_box"][1]]}
        return mint,relation
    def resolve_reference(store,mint,observation,image):
        resolution=store.resolve_point(mint["handle"],[20,9],observation,image,time.perf_counter_ns())
        if not resolution["eligible"]:raise RuntimeError("new handle did not resolve")
        return resolution
    def mint_from_grounding(store,grounding,observation,image):
        mint,relation=mint_reference(store,grounding,observation,image)
        return mint,resolve_reference(store,mint,observation,image),relation
    report={"schema":"matched-semantic-repair-arm-v3","ordinal":ordinal,
            "mode":mode,"seed":plan["seed"],"status":"STARTED","retry_count":0}
    try:
        with (arm/"setup.txt").open("w") as diagnostics,contextlib.redirect_stdout(diagnostics):
            session=suite.Session();goal,output,app_server=suite.prepare(session,"chromium",plan["seed"],plan["chromium"])
            backend=Backend(session,arm,emit);controller=display.Display(session.name)
        executor=Executor(backend,emit);backend.snapshot("initial",0)
        navigate=submit(f"matched-repair-nav-{ordinal+1}",[
            {"op":"chord","modifier":"Control_L","key":"l"},{"op":"text","text":goal["url"]},
            {"op":"key","key":"Return"},{"op":"wait_title","contains":"AI FORM READY","timeout_ms":1500}])
        backend.snapshot("matched-repair-pre-entry",0);pre_entry=events[-1]
        original_geometry=list(pre_entry["pointer_binding"]["geometry"])
        pre_entry_path=arm/Path(pre_entry["image"]).name
        initial_outcome,initial_admission=ground("initial-model",pre_entry_path)
        initial_admission_ns=time.perf_counter_ns()
        report.update({"initial_outcome":initial_outcome,"initial_admission":initial_admission,
                       "initial_admission_ns":initial_admission_ns,
                       "pre_entry_observation":pre_entry,"task_mutation_started":False})
        if not initial_admission["task_mutation_eligible"]:
            report.update({"status":initial_admission["status"],"passed":False,
                           "comparison_eligible":False})
            return report
        initial_model=initial_outcome["result"]
        initial_grounding=checked_grounding(initial_model)
        fill=submit(f"matched-repair-fill-{ordinal+1}",[
            {"op":"pointer_click","x":180,"y":243,"duration_ms":80},
            {"op":"chord","modifier":"Control_L","key":"a"},{"op":"text","text":goal["token"]},{"op":"observe"}])
        report["task_mutation_started"]=True
        backend.snapshot("matched-repair-source",0);source=events[-1]
        source_path=arm/Path(source["image"]).name
        with Image.open(source_path) as opened:source_image=opened.convert("RGB")
        store=TargetHandleStore(f"matched-repair-{ordinal+1}",lambda:f"initial-save-{ordinal+1}")
        mint,resolution,relation=mint_from_grounding(store,initial_grounding,source,source_image)
        initial_binding=derive_contract(f"matched_completion_{ordinal+1}","submission_heading",mint,
            resolution,source,relation,plan["expected_crop_sha256"],"submission_title_exactly_visible")
        window=controller.create_resource_object("window",source["pointer_binding"]["surface"])
        window.configure(width=original_geometry[2]+plan["resize_width_delta"]);controller.sync()
        resized_binding=wait_binding(lambda x:x.get("surface")==source["pointer_binding"]["surface"] and
            x.get("geometry",[0,0,0])[2]==original_geometry[2]+plan["resize_width_delta"],"resize missing")
        emit({"event":"test_surface_resized","before":source["pointer_binding"],"after":resized_binding,
              "grants_input_authority":False})
        backend.snapshot("matched-repair-resized",0);resized=events[-1];resized_path=arm/Path(resized["image"]).name
        old_score=score_path(initial_binding["contract"],resized_path,resized["pointer_binding"])
        recovery_started_ns=time.perf_counter_ns();reacquisition_model=None
        reacquisition_outcome=reacquisition_admission=None
        post_model_observation=post_model_revalidation=None
        post_model_refresh_ms=post_model_revalidation_ms=0
        with Image.open(resized_path) as opened:resized_image=opened.convert("RGB")
        if mode=="local":
            current_resolution=store.resolve_point(mint["handle"],[20,9],resized,resized_image,time.perf_counter_ns())
            recovered=repair_contract(initial_binding["contract"],mint,current_resolution,resized,relation)
            recovery_kind="verified_handle_local_repair"
        else:
            reacquisition_outcome,reacquisition_admission=ground("reacquisition-model",resized_path)
            report.update({"reacquisition_outcome":reacquisition_outcome,
                           "reacquisition_admission":reacquisition_admission})
            if not reacquisition_admission["task_mutation_eligible"]:
                report.update({"status":reacquisition_admission["status"],"passed":False,
                               "comparison_eligible":False,"source_observation":source,
                               "resized_observation":resized,"old_contract_score":old_score})
                return report
            reacquisition_model=reacquisition_outcome["result"]
            reacquired_grounding=checked_grounding(reacquisition_model)
            new_store=TargetHandleStore(f"matched-reacquire-{ordinal+1}",lambda:f"reacquired-save-{ordinal+1}")
            new_mint,new_relation=mint_reference(new_store,reacquired_grounding,resized,resized_image)
            refresh_started_ns=time.perf_counter_ns()
            backend.snapshot("matched-repair-post-model-current",0);post_model_observation=events[-1]
            post_model_refresh_ms=(time.perf_counter_ns()-refresh_started_ns)/1e6
            post_model_path=arm/Path(post_model_observation["image"]).name
            with Image.open(post_model_path) as opened:post_model_image=opened.convert("RGB")
            revalidation_started_ns=time.perf_counter_ns()
            current_resolution=resolve_reference(new_store,new_mint,post_model_observation,post_model_image)
            post_model_revalidation_ms=(time.perf_counter_ns()-revalidation_started_ns)/1e6
            post_model_revalidation=revalidation_receipt(new_mint,current_resolution,resized,
                post_model_observation,reacquisition_model["call_id"])
            recovered=derive_contract(f"matched_completion_{ordinal+1}","submission_heading",new_mint,
                current_resolution,post_model_observation,new_relation,plan["expected_crop_sha256"],"submission_title_exactly_visible")
            recovered["receipt"]={"schema":"model-reacquired-semantic-contract-v1",
                "status":"REACQUIRED_NO_AUTHORITY","model_call_id":reacquisition_model["call_id"],
                "handle_derivation":recovered["receipt"],"grants_input_authority":False}
            recovery_kind="luna_visual_reacquisition"
        recovery_ready_ns=time.perf_counter_ns()
        action_id=f"matched-repair-submit-{ordinal+1}-{mode}"
        registration=backend.register_semantic_probe(action_id,recovered["contract"])
        before_requests=len(delivery.request_receipts());thread=threading.Thread(target=receive,args=(action_id,))
        threads.append(thread);thread.start()
        if not delivery.wait_requests(before_requests+1):raise RuntimeError("semantic client missing")
        registered_ns=delivery.request_receipts()[-1]["received_ns"]
        submit_action=submit(action_id,[{"op":"pointer_click","x":current_resolution["point"][0],
            "y":current_resolution["point"][1],"duration_ms":80},
            {"op":"wait_title","contains":"AI FORM SAVED","timeout_ms":1500},{"op":"observe"}])
        thread.join(4)
        if thread.is_alive():raise RuntimeError("semantic client timed out")
        useful=next((row for row in client["feedback"] if row["score"]["success"]),None)
        if useful is None:raise RuntimeError("semantic success missing")
        useful_index=client["feedback"].index(useful);first_ns=client["exchanges"][0]["client_returned_ns"]
        useful_ns=client["exchanges"][useful_index]["client_returned_ns"]
        reconciliations=[row for row in events if row.get("event")=="semantic_probe_reconciled"]
        useful_recon=next(row for row in reconciliations if row["sequence"]==useful["sequence"])
        model_records=[initial_model]+([] if reacquisition_model is None else[reacquisition_model])
        model_outcomes=[initial_outcome]+([] if reacquisition_outcome is None else[reacquisition_outcome])
        usage={field:sum(row["usage"][field] for row in model_records) for field in initial_model["usage"]}
        actual=parse_qs(output.read_text()) if output.exists() else {}
        metrics={"recovery_from_resized_capture_ms":(recovery_ready_ns-resized["capture_ns"])/1e6,
            "recovery_local_compute_ms":(recovery_ready_ns-recovery_started_ns)/1e6,
            "model_wait_ms":sum(row["caller_elapsed_ms"] for row in model_outcomes),
            "admission_to_first_feedback_ms":(first_ns-submit_action["accepted"]["accepted_ns"])/1e6,
            "admission_to_useful_feedback_ms":(useful_ns-submit_action["accepted"]["accepted_ns"])/1e6,
            "useful_probe_compute_ms":(useful["probe_completed_ns"]-useful["probe_started_ns"])/1e6,
            "useful_probe_to_image_ready_ms":(useful_recon["image_ready_ns"]-useful["probe_completed_ns"])/1e6,
            "useful_client_to_terminal_ms":(submit_action["terminal"]["terminal_ns"]-useful_ns)/1e6,
            "post_model_refresh_ms":post_model_refresh_ms,
            "post_model_revalidation_ms":post_model_revalidation_ms,
            "model_calls":len(model_records),"model_visible_images":sum(
                row["visible_images_submitted"] for row in model_outcomes),
            "input_tokens":usage["input_tokens"],"client_exchanges":len(client["exchanges"])}
        actions=[navigate,fill,submit_action]
        checks={"source_geometry":original_geometry==plan["expected_source_geometry"],
            "initial_model_target":inside(initial_grounding["submit_point"],plan["submit_box"]),
            "initial_admission_before_mutation":initial_admission_ns<=fill["submitted_ns"],
            "old_contract_refusal":old_score["reason"]=="surface_size_changed",
            "expected_model_calls":len(model_records)==plan["expected_arm_model_calls"][mode],
            "current_target":current_resolution["eligible"] is True and inside(current_resolution["point"],plan["submit_box"]),
            "post_model_current_revalidation":mode=="local" or (
                post_model_observation["sequence"]>resized["sequence"] and
                post_model_observation["pointer_binding"]==resized["pointer_binding"] and
                current_resolution["patch_sha256"]==new_mint["patch_sha256"] and
                post_model_revalidation["status"]=="CURRENT_PATCH_MATCH_NO_AUTHORITY" and
                post_model_revalidation["grants_input_authority"] is False),
            "post_model_refresh_bound":mode=="local" or (
                post_model_refresh_ms<=plan["thresholds"]["post_model_refresh_lte_ms"] and
                post_model_revalidation_ms<=plan["thresholds"]["post_model_revalidation_lte_ms"]),
            "recovery_no_authority":recovered["receipt"]["grants_input_authority"] is False,
            "client_registered":registered_ns<=submit_action["submitted_ns"],
            "programs_attested":all(row["accepted"]["program_sha256"]==program_sha256(row["program"]) for row in actions),
            "correct":actual=={"value":[goal["token"]]} and useful["score"]["success"] is True,
            "reconciled":all(row["reconciliation"]["matches"] for row in reconciliations),
            "released":all(row["terminal"]["status"]=="completed" and row["terminal"]["release"]["verified"] is True
                and row["terminal"]["release"]["keys_down"]==[] and row["terminal"]["release"]["buttons_down"]==[] for row in actions),
            "feedback":metrics["admission_to_useful_feedback_ms"]<=plan["thresholds"]["feedback_lte_ms"] and
                       metrics["useful_probe_compute_ms"]<=plan["thresholds"]["probe_compute_lte_ms"],
            "pre_artifact_terminal":metrics["useful_probe_to_image_ready_ms"]>0 and metrics["useful_client_to_terminal_ms"]>0}
        report.update({"status":"COMPLETED","comparison_eligible":True,
            "passed":all(checks.values()),"checks":checks,"goal":goal,
            "initial_model":initial_model,"reacquisition_model":reacquisition_model,
            "model_records":model_records,"model_outcomes":model_outcomes,
            "usage":usage,"source_observation":source,
            "initial_mint":mint,"initial_resolution":resolution,"relation":relation,
            "initial_binding":initial_binding,"resized_observation":resized,"old_contract_score":old_score,
            "current_resolution":current_resolution,"recovered":recovered,"recovery_kind":recovery_kind,
            "post_model_observation":post_model_observation,
            "post_model_revalidation":post_model_revalidation,
            "registration":registration,"submit_action":submit_action,"client":client,
            "reconciliations":reconciliations,"actual":actual,"metrics_ms":metrics,"retry_count":0})
    finally:
        for t in threads:
            if t.is_alive():t.join(1)
        if executor is not None:executor.close()
        if controller is not None and original_geometry is not None:
            try:
                b=backend.binding();w=controller.create_resource_object("window",b["surface"])
                w.configure(x=original_geometry[0],y=original_geometry[1],width=original_geometry[2],height=original_geometry[3]);controller.sync()
            except Exception:pass
            controller.close()
        if backend is not None:
            try:backend.close()
            finally:(arm/"owner-events.json").write_text(json.dumps(backend.owner.records,indent=2)+"\n")
        if output is not None and output.exists():shutil.copy2(output,arm/output.name)
        if app_server is not None:app_server.shutdown();app_server.server_close()
        if session is not None:session.close();shutil.rmtree(session.tmp)
        delivery.close();(arm/"events.json").write_text(json.dumps(events,indent=2)+"\n")
        persist(arm/"report.json",report)
    return report

def main():
    plan=read(PREREG);verification=verify(plan)
    if "--verify-only" in sys.argv:
        print(json.dumps({"passed":all(verification.values()),"checks":verification},indent=2));return 0 if all(verification.values()) else 1
    if not all(verification.values()):raise RuntimeError(verification)
    if os.name=="nt" or not Path("/mnt/c").is_dir():raise RuntimeError("run from WSL")
    from schema_preflight_gate_v1 import require_compatible
    root=REPO/plan["output"];root.mkdir(parents=True,exist_ok=False);(root/"empty-workspace").mkdir()
    preflight=require_compatible([{"name":"compiled-grounding","schema":HERE/"compiled_form_grounding_schema_v1.json"}],
        HERE/"results/schema-preflight-cache-v1",root/"preflight",root/"empty-workspace")
    arms=[]
    for index,mode in enumerate(plan["order"]):
        arm=run_arm(plan,root,index,mode);arms.append(arm)
        if arm["status"]!="COMPLETED":
            stopped=noncompletion_summary(arm);status=stopped["status"]
            checks={"preflight":preflight["accepted"] is True,
                "prefix_order":[row["mode"] for row in arms]==plan["order"][:len(arms)],
                "comparison_not_computed":True,"zero_retry":all(row["retry_count"]==0 for row in arms),
                "typed_noncompletion":stopped["comparison_eligible"] is False,
                "no_authority":stopped["grants_semantic_authority"] is False and
                    stopped["grants_input_authority"] is False}
            report={"schema":"matched-semantic-repair-live-v2","allocation_id":plan["allocation_id"],
                "status":status,"stopped":stopped,"verification":verification,"passed":False,"checks":checks,
                "preflight":preflight,"arms":arms,"metrics":None,"scope":plan["scope"]}
            persist(root/"report.json",report)
            print(json.dumps({"passed":False,"status":status,"checks":checks,
                              "metrics":None,"scope":plan["scope"]},indent=2))
            return 2 if status=="DEFERRED" else 1
    samples={mode:{"tokens":[arm["metrics_ms"]["input_tokens"] for arm in arms if arm["mode"]==mode],
                   "recovery_ms":[arm["metrics_ms"]["recovery_from_resized_capture_ms"] for arm in arms if arm["mode"]==mode]}
             for mode in("local","model")}
    medians={mode:{name:statistics.median(values) for name,values in data.items()} for mode,data in samples.items()}
    metrics={"samples":samples,"medians":medians,
        "input_token_advantage":medians["model"]["tokens"]-medians["local"]["tokens"],
        "recovery_ms_advantage":medians["model"]["recovery_ms"]-medians["local"]["recovery_ms"],
        "total_model_calls":sum(len(arm["model_records"]) for arm in arms)+preflight["model_calls"],
        "preflight_model_calls":preflight["model_calls"]}
    call_ids=[record["call_id"] for arm in arms for record in arm["model_records"]]
    checks={"preflight":preflight["accepted"] is True,"all_arms_pass":all(arm["passed"] for arm in arms),
        "order":[arm["mode"] for arm in arms]==plan["order"],"balanced":all(len(samples[m]["tokens"])==2 for m in samples),
        "call_counts":all(len(arm["model_records"])==plan["expected_arm_model_calls"][arm["mode"]] for arm in arms),
        "unique_calls":len(call_ids)==len(set(call_ids))==6,
        "same_model":all(record["requested_model"]==plan["model"]["name"] and record["requested_effort"]==plan["model"]["effort"] for arm in arms for record in arm["model_records"]),
        "token_advantage":metrics["input_token_advantage"]>=plan["thresholds"]["minimum_input_token_advantage"],
        "recovery_advantage":metrics["recovery_ms_advantage"]>=plan["thresholds"]["minimum_recovery_ms_advantage"],
        "zero_retry":all(arm["retry_count"]==0 for arm in arms)}
    report={"schema":"matched-semantic-repair-live-v2","allocation_id":plan["allocation_id"],
        "status":"COMPLETED","verification":verification,"passed":all(checks.values()),"checks":checks,"preflight":preflight,
        "arms":arms,"metrics":metrics,"scope":plan["scope"]}
    persist(root/"report.json",report)
    print(json.dumps({"passed":report["passed"],"checks":checks,"metrics":metrics,"scope":plan["scope"]},indent=2))
    return 0 if report["passed"] else 1
if __name__=="__main__":raise SystemExit(main())
