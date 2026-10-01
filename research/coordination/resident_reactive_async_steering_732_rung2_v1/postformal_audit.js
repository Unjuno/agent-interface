function audit(obj) {
  const errors = [];
  if (obj.schema !== "resident_async_steering_contract_v1") errors.push("schema");
  const phases=["RUNNING","PAUSED","REVOKED","YIELDED"];
  const owners=["FREE","RESIDENT","EXTERNAL"];
  const commands=["BOUNDED_UPDATE","PARALLEL_ONESHOT","SAME_RESOURCE_ONESHOT","RESUME","REVOKE","UNKNOWN"];
  function expected(p,o,c,g,s,b) {
    if (!g) return "STALE_GENERATION";
    if (c==="REVOKE") return (p==="REVOKED"||p==="YIELDED") ? "TERMINAL_PROGRAM" : "REVOKED_IMMEDIATE";
    if (p==="REVOKED"||p==="YIELDED") return "TERMINAL_PROGRAM";
    if (c==="UNKNOWN") return "UNKNOWN_COMMAND";
    if (c==="BOUNDED_UPDATE") {
      if (p!=="RUNNING") return "NOT_RUNNING";
      if (!b) return "PARAM_OUT_OF_BOUNDS";
      return s ? "UPDATE_APPLIED" : "UPDATE_QUEUED_SAFE_POINT";
    }
    if (c==="PARALLEL_ONESHOT") {
      if (p!=="RUNNING") return "NOT_RUNNING";
      return o==="FREE" ? "PARALLEL_ACCEPTED" : "RESOURCE_BUSY";
    }
    if (c==="SAME_RESOURCE_ONESHOT") {
      if (p!=="RUNNING") return "NOT_RUNNING";
      if (o==="EXTERNAL") return "RESOURCE_BUSY";
      if (o==="RESIDENT") return s ? "HANDOFF_READY" : "HANDOFF_QUEUED_SAFE_POINT";
      return "SAME_RESOURCE_ACCEPTED";
    }
    if (c==="RESUME") {
      if (p!=="PAUSED") return "NOT_PAUSED";
      if (!s) return "RESUME_QUEUED_SAFE_POINT";
      return o==="FREE" ? "RESUMED" : "RESOURCE_BUSY";
    }
    throw new Error("unrecognized command");
  }
  const all = new Set();
  const counts = Object.create(null);
  for (const p of phases) for (const o of owners) for (const c of commands)
    for (const g of [false,true]) for (const s of [false,true]) for (const b of [false,true]) {
      const k=JSON.stringify([p,o,c,g,s,b]); all.add(k);
      const want=expected(p,o,c,g,s,b);
      counts[want]=(counts[want]||0)+1;
    }
  const seen=new Set();
  for (const row of obj.rows||[]) {
    const k=JSON.stringify(row.slice(0,6));
    if (seen.has(k)) { errors.push("duplicate_case"); break; }
    seen.add(k);
    if (row[6]!==expected(...row.slice(0,6))) { errors.push("oracle_mismatch"); break; }
  }
  if (seen.size!==576 || all.size!==576 || [...all].some(k=>!seen.has(k))) errors.push("cartesian_coverage");
  const sort=o=>JSON.stringify(Object.fromEntries(Object.entries(o||{}).sort(([a],[b])=>a.localeCompare(b))));
  if (sort(counts)!==sort(obj.outcome_counts)) errors.push("outcome_counts");
  if (obj.source_sha256!=="4d3899db4908fb0898a9c35e4ef075a9f478834420b85ef55b5e087b602fadc7")
    errors.push("runner_source_sha256");
  const tr=obj.stateful_traces||{}, ev=tr.events||[];
  const names=["update","update","parallel_keyboard","same_pointer","same_pointer","update","update","revoke","revoke","after_revoke"];
  if (JSON.stringify(ev.map(e=>e[0]))!==JSON.stringify(names)) errors.push("trace_event_order");
  if (ev.length===10) {
    const actual=ev.map(e=>e[0]==="update"?e[4]:e[0]==="parallel_keyboard"?e[2]:e[0]==="same_pointer"?e[3]:e[0]==="revoke"?e[3]:e[2]);
    const wanted=["UPDATE_QUEUED_SAFE_POINT","UPDATE_APPLIED","PARALLEL_ACCEPTED","HANDOFF_QUEUED_SAFE_POINT","HANDOFF_READY","STALE_GENERATION","PARAM_OUT_OF_BOUNDS","STALE_GENERATION","REVOKED_IMMEDIATE","TERMINAL_PROGRAM"];
    if (JSON.stringify(actual)!==JSON.stringify(wanted)) errors.push("trace_outcomes");
  }
  if (JSON.stringify(tr.final_state)!==JSON.stringify({gain:2,generation:2,keyboard:"FREE",phase:"REVOKED",pointer:"FREE"})) errors.push("trace_final_state");
  if (JSON.stringify(tr.handoff_owner_timeline)!==JSON.stringify(["RESIDENT","FREE","EXTERNAL","FREE","RESIDENT"])) errors.push("handoff_timeline");
  if (Object.keys(tr.checks||{}).length!==8 || !Object.values(tr.checks||{}).every(Boolean)) errors.push("trace_invariants");
  const expectedNeg={revoke_waits_for_safe_point:true,same_resource_off_safe_point_overlaps:true,stale_generation_admitted:true};
  if (sort(obj.negative_controls)!==sort(expectedNeg)) errors.push("negative_controls");
  return {audit:errors.length?"FAIL":"PASS",auditor:"postformal independent JavaScript oracle; does not import runner",rows_recomputed:(obj.rows||[]).length,unique_cases:seen.size,outcome_counts:counts,stateful_trace_events:ev.length,negative_controls:obj.negative_controls,errors,decision:errors.length?"HOLD":"PASS_ASYNC_STEERING_CONTRACT_SCOPED"};
}
