// Post-merge raw-only audit review for Issue #5919; candidate is never invoked.
"use strict";
function reviewAudit(fixture, candidate) {
  function assess(trace, oracle, ambiguity) {
    if (ambiguity === "ambiguous") return {decision:"UNKNOWN",stage:"translation_equivalence"};
    if (trace.perception.status !== "ok") return {decision:"FAIL",stage:"perception"};
    if (trace.input.logical_intent !== oracle.logical_input) return {decision:"FAIL",stage:"input_encoding"};
    if (trace.target_id !== oracle.target_id) return {decision:"FAIL",stage:"target_selection"};
    if (trace.value !== oracle.value || trace.authority !== oracle.authority ||
        trace.effect_count !== oracle.effect_count || trace.effect_status !== oracle.effect_status ||
        trace.lineage_root !== oracle.lineage_root) return {decision:"FAIL",stage:"effect_verification"};
    return {decision:"PASS",stage:"equivalent_effect"};
  }
  function validate(f, result) {
    const errors = [];
    const fixtureIds = f.cases.map(x=>x.id);
    const resultIds = (result.cases||[]).map(x=>x.id);
    if (fixtureIds.length !== 8 || new Set(fixtureIds).size !== 8) errors.push("fixture_case_identity");
    if (resultIds.length !== fixtureIds.length || new Set(resultIds).size !== resultIds.length) errors.push("result_case_cardinality_or_duplicate");
    const missing = fixtureIds.filter(id=>!resultIds.includes(id));
    const extra = resultIds.filter(id=>!fixtureIds.includes(id));
    if (missing.length) errors.push("missing:"+missing.join(","));
    if (extra.length) errors.push("extra:"+extra.join(","));
    if (result.fixture_id !== f.id || result.candidate_invocations !== 1) errors.push("candidate_identity_or_invocation");
    const byId = new Map((result.cases||[]).map(x=>[x.id,x]));
    for (const c of f.cases) {
      const row = byId.get(c.id);
      if (!row) continue;
      const eb=assess(c.baseline,c.oracle,"equivalent");
      const el=assess(c.localized,c.oracle,c.translation_equivalence||"equivalent");
      if (row.kind!==c.kind) errors.push(c.id+":kind");
      if (row.baseline?.decision!==eb.decision || row.baseline?.stage!==eb.stage) errors.push(c.id+":baseline");
      if (row.localized?.decision!==el.decision || row.localized?.stage!==el.stage) errors.push(c.id+":localized");
      if (row.exact_rendered_equal!==(c.baseline.presentation.rendered===c.localized.presentation.rendered)) errors.push(c.id+":exact_rendered");
      if (row.english_only_baseline_pass!==(eb.decision==="PASS")) errors.push(c.id+":english_baseline");
      const visualMiss=c.kind==="injected_fault" && el.decision==="FAIL" &&
        c.localized.presentation.visual_proxy_similar===true && eb.decision==="PASS";
      if (row.visual_proxy_missed_regression!==visualMiss) errors.push(c.id+":visual_proxy");
    }
    const exactEqual=f.cases.filter(c=>c.baseline.presentation.rendered===c.localized.presentation.rendered).length;
    const missed=f.cases.filter(c=>c.kind==="injected_fault" &&
      c.localized.presentation.visual_proxy_similar===true &&
      assess(c.localized,c.oracle,"equivalent").decision==="FAIL" &&
      assess(c.baseline,c.oracle,"equivalent").decision==="PASS").map(c=>c.id);
    if (result.baselines?.exact_rendered_equal_count!==exactEqual) errors.push("aggregate_exact_equal");
    if (result.baselines?.exact_rendered_unequal_count!==f.cases.length-exactEqual) errors.push("aggregate_exact_unequal");
    if (result.baselines?.english_only_pass_count!==f.cases.filter(c=>assess(c.baseline,c.oracle,"equivalent").decision==="PASS").length) errors.push("aggregate_english");
    if (JSON.stringify(result.baselines?.injected_faults_missed_by_visual_proxy)!==JSON.stringify(missed)) errors.push("aggregate_visual");
    return errors;
  }
  const originalErrors=validate(fixture,candidate);
  if (originalErrors.length) throw Error("original_raw_candidate_invalid:"+originalErrors.join("|"));
  const corruptionControls=fixture.corruption_controls.map(ctrl=>{
    const copy=JSON.parse(JSON.stringify(candidate));
    const row=copy.cases.find(x=>x.id===ctrl.case_id);
    if (!row) throw Error("corruption_target_missing:"+ctrl.id);
    row.localized.decision=ctrl.id==="corrupt_benign_to_fail"?"FAIL":"PASS";
    return {id:ctrl.id,rejected:validate(fixture,copy).length>0};
  });
  const structural=[
    {id:"duplicate-case",make:c=>{c.cases.push(JSON.parse(JSON.stringify(c.cases[0])));}},
    {id:"missing-case",make:c=>{c.cases.pop();}},
    {id:"extra-case",make:c=>{c.cases.push({...JSON.parse(JSON.stringify(c.cases[0])),id:"unexpected-case"});}}
  ].map(test=>{
    const copy=JSON.parse(JSON.stringify(candidate)); test.make(copy);
    return {id:test.id,rejected:validate(fixture,copy).length>0};
  });
  const metadata = fixture.corruption_controls.map(ctrl=>{
    const row=candidate.corruption_probes.find(x=>x.id===ctrl.id);
    const source=candidate.cases.find(x=>x.id===ctrl.case_id);
    const expectedForced=ctrl.id==="corrupt_benign_to_fail"?"FAIL":"PASS";
    return !!row && row.source_decision===source?.localized?.decision &&
      row.corrupted_decision===expectedForced && row.corrupted_decision!==source?.localized?.decision;
  });
  const benign=fixture.cases.filter(c=>c.kind==="benign");
  const faults=fixture.cases.filter(c=>c.kind==="injected_fault");
  const ambiguous=fixture.cases.filter(c=>c.kind==="ambiguous");
  const gates={
    all_benign_pass:benign.length===2&&benign.every(c=>assess(c.localized,c.oracle,c.translation_equivalence).decision==="PASS"),
    all_faults_fail:faults.length===5&&faults.every(c=>assess(c.localized,c.oracle,c.translation_equivalence).decision==="FAIL"),
    ambiguity_unknown:ambiguous.length===1&&ambiguous.every(c=>assess(c.localized,c.oracle,c.translation_equivalence).decision==="UNKNOWN"),
    missed_faults:faults.filter(c=>c.localized.presentation.visual_proxy_similar===true &&
      assess(c.localized,c.oracle,c.translation_equivalence).decision==="FAIL" &&
      assess(c.baseline,c.oracle,"equivalent").decision==="PASS").map(c=>c.id)
  };
  return {
    schema:"locale-semantic-invariance-postmerge-raw-audit-review/v1",
    candidate_invocations:0,
    postmerge_audit_invocations:1,
    original_raw_candidate_accepted:true,
    rows:fixture.cases.map(c=>({id:c.id,kind:c.kind,expectedBaseline:assess(c.baseline,c.oracle,"equivalent"),
      expectedLocalized:assess(c.localized,c.oracle,c.translation_equivalence||"equivalent")})),
    gates,
    original_probe_metadata_consistent:metadata.every(Boolean),
    actual_corrupted_candidate_copies_rejected:corruptionControls,
    duplicate_missing_extra_result_copies_rejected:structural,
    original_audit_claim_scope:"The original audit checked corruption-probe metadata; this post-merge audit separately mutates candidate copies and validates them.",
    disposition:corruptionControls.every(x=>x.rejected)&&structural.every(x=>x.rejected)?"PASS_RAW_REVIEW":"FAIL_AUDIT_REVIEW",
    scope:"read-only audit of already-retained synthetic T0 files; no new scientific allocation, candidate invocation, rendering or locale adjudication"
  };
}