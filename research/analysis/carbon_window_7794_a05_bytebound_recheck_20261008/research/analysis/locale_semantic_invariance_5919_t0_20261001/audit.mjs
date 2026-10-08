function audit(fixture, candidate) {
  var errors = [];
  var expectedRows = [];
  for (var i = 0; i < fixture.cases.length; i++) {
    var c = fixture.cases[i];
    var row = candidate.cases.find(function(x) { return x.id === c.id; });
    if (!row) { errors.push("missing case " + c.id); continue; }
    function expected(trace, allowAmbiguous) {
      if (allowAmbiguous && c.translation_equivalence === "ambiguous")
        return { decision: "UNKNOWN", stage: "translation_equivalence" };
      if (trace.perception.status !== "ok") return { decision: "FAIL", stage: "perception" };
      if (trace.input.logical_intent !== c.oracle.logical_input) return { decision: "FAIL", stage: "input_encoding" };
      if (trace.target_id !== c.oracle.target_id) return { decision: "FAIL", stage: "target_selection" };
      if (trace.value !== c.oracle.value || trace.authority !== c.oracle.authority ||
          trace.effect_count !== c.oracle.effect_count || trace.effect_status !== c.oracle.effect_status ||
          trace.lineage_root !== c.oracle.lineage_root)
        return { decision: "FAIL", stage: "effect_verification" };
      return { decision: "PASS", stage: "equivalent_effect" };
    }
    var eb = expected(c.baseline, false);
    var el = expected(c.localized, true);
    if (row.baseline.decision !== eb.decision || row.baseline.stage !== eb.stage)
      errors.push(c.id + ": baseline expected " + eb.decision + "/" + eb.stage);
    if (row.localized.decision !== el.decision || row.localized.stage !== el.stage)
      errors.push(c.id + ": localized expected " + el.decision + "/" + el.stage);
    if (row.exact_rendered_equal !== (c.baseline.presentation.rendered === c.localized.presentation.rendered))
      errors.push(c.id + ": exact-string baseline mismatch");
    if (row.english_only_baseline_pass !== (eb.decision === "PASS"))
      errors.push(c.id + ": English-only baseline mismatch");
    var visualMiss = c.kind === "injected_fault" && el.decision === "FAIL" &&
      c.localized.presentation.visual_proxy_similar === true && eb.decision === "PASS";
    if (row.visual_proxy_missed_regression !== visualMiss)
      errors.push(c.id + ": visual-proxy comparison mismatch");
    expectedRows.push({ id: c.id, kind: c.kind, expected_localized: el.decision, stage: el.stage, visual_missed: visualMiss });
  }
  if (candidate.fixture_id !== fixture.id || candidate.candidate_invocations !== 1)
    errors.push("candidate identity/invocation count mismatch");
  if (fixture.cases.length !== 8) errors.push("fixture size mismatch");
  var benign = expectedRows.filter(function(x) { return x.kind === "benign"; });
  var faults = expectedRows.filter(function(x) { return x.kind === "injected_fault"; });
  var amb = expectedRows.filter(function(x) { return x.kind === "ambiguous"; });
  var allBenignPass = benign.length === 2 && benign.every(function(x) { return x.expected_localized === "PASS"; });
  var everyFaultRejected = faults.length === 5 && faults.every(function(x) { return x.expected_localized === "FAIL"; });
  var ambiguousUnknown = amb.length === 1 && amb[0].expected_localized === "UNKNOWN";
  var hScoped = faults.some(function(x) { return x.visual_missed; });
  var corruptionsRejected = fixture.corruption_controls.length === 3 &&
    fixture.corruption_controls.every(function(ctrl) {
      var row = candidate.corruption_probes.find(function(x) { return x.id === ctrl.id; });
      var expectedSource = expectedRows.find(function(x) { return x.id === ctrl.case_id; });
      var corrupted = ctrl.id === "corrupt_benign_to_fail" ? "FAIL" : "PASS";
      return !!row && !!expectedSource && row.source_decision === expectedSource.expected_localized &&
        row.corrupted_decision === corrupted && row.corrupted_decision !== expectedSource.expected_localized;
    });
  if (!allBenignPass) errors.push("benign relation acceptance failed");
  if (!everyFaultRejected) errors.push("injected fault rejection failed");
  if (!ambiguousUnknown) errors.push("ambiguous translation not UNKNOWN");
  if (!corruptionsRejected) errors.push("corruption-control gate failed");
  if (!hScoped) errors.push("no seeded regression missed by both frozen simple baselines");
  return {
    schema: "locale-semantic-invariance-independent-audit/v1",
    fixture_id: fixture.id,
    auditor_invocations: 1,
    rows: expectedRows,
    errors: errors,
    checks: { all_benign_pass: allBenignPass, every_injected_fault_rejected: everyFaultRejected,
      ambiguous_is_unknown: ambiguousUnknown, corruption_controls_rejected: corruptionsRejected,
      h_pass_scoped: hScoped, exact_rendered_false_alarms: candidate.baselines.exact_rendered_unequal_count },
    outcome: errors.length === 0 ? "H_PASS_SCOPED_METHOD_PASS" : "FAIL"
  };
}
