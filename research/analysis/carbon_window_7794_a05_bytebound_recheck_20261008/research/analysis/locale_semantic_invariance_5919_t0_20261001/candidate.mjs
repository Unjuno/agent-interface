function run(fixture) {
  function assess(trace, oracle, equivalence) {
    if (equivalence === "ambiguous") return { decision: "UNKNOWN", stage: "translation_equivalence" };
    if (trace.perception.status !== "ok") return { decision: "FAIL", stage: "perception" };
    if (trace.input.logical_intent !== oracle.logical_input) return { decision: "FAIL", stage: "input_encoding" };
    if (trace.target_id !== oracle.target_id) return { decision: "FAIL", stage: "target_selection" };
    if (trace.authority !== oracle.authority) return { decision: "FAIL", stage: "effect_verification" };
    if (trace.value !== oracle.value) return { decision: "FAIL", stage: "effect_verification" };
    if (trace.effect_count !== oracle.effect_count || trace.effect_status !== oracle.effect_status ||
        trace.lineage_root !== oracle.lineage_root) return { decision: "FAIL", stage: "effect_verification" };
    return { decision: "PASS", stage: "equivalent_effect" };
  }
  var cases = fixture.cases.map(function(c) {
    var baseline = assess(c.baseline, c.oracle, "equivalent");
    var localized = assess(c.localized, c.oracle, c.translation_equivalence || "equivalent");
    return {
      id: c.id,
      kind: c.kind,
      baseline: baseline,
      localized: localized,
      exact_rendered_equal: c.baseline.presentation.rendered === c.localized.presentation.rendered,
      visual_proxy_missed_regression: c.kind === "injected_fault" &&
        localized.decision === "FAIL" && c.localized.presentation.visual_proxy_similar === true,
      english_only_baseline_pass: baseline.decision === "PASS"
    };
  });
  var byId = Object.fromEntries(cases.map(function(x) { return [x.id, x]; }));
  var corruptions = fixture.corruption_controls.map(function(c) {
    var source = byId[c.case_id].localized.decision;
    var forced = c.id === "corrupt_benign_to_fail" ? "FAIL" : "PASS";
    return { id: c.id, case_id: c.case_id, source_decision: source, corrupted_decision: forced };
  });
  return {
    schema: "locale-semantic-invariance-candidate-result/v1",
    fixture_id: fixture.id,
    candidate_invocations: 1,
    cases: cases,
    baselines: {
      exact_rendered_equal_count: cases.filter(function(x) { return x.exact_rendered_equal; }).length,
      exact_rendered_unequal_count: cases.filter(function(x) { return !x.exact_rendered_equal; }).length,
      english_only_pass_count: cases.filter(function(x) { return x.english_only_baseline_pass; }).length,
      injected_faults_missed_by_visual_proxy: cases.filter(function(x) { return x.visual_proxy_missed_regression; }).map(function(x) { return x.id; })
    },
    corruption_probes: corruptions
  };
}
