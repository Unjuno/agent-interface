module.exports = function audit(runs) {
  const pattern = /(?:target_trajectory|disturbance_schedule|external_target_schedule|target_generation_schedule)/i;
  const results = [];
  for (const run of runs) {
    const parseLines = (text) => text.trim().split(/\r?\n/).map((line) => JSON.parse(line));
    const events = parseLines(run.eventsText);
    const protocol = parseLines(run.protocolText);
    const report = JSON.parse(run.reportText);
    const counts = {};
    for (const row of events) {
      const type = row.event || row.type || "unknown";
      counts[type] = (counts[type] || 0) + 1;
    }
    let scheduleMatches = 0;
    const scan = (value) => {
      if (value && typeof value === "object") {
        for (const [key, child] of Object.entries(value)) {
          if (pattern.test(key)) scheduleMatches++;
          scan(child);
        }
      } else if (typeof value === "string" && pattern.test(value)) scheduleMatches++;
    };
    scan(events);
    scan(protocol);
    const reportKeys = new Set();
    scanKeys(report, reportKeys);
    function scanKeys(value, out) {
      if (value && typeof value === "object") {
        for (const [key, child] of Object.entries(value)) {
          out.add(key);
          scanKeys(child, out);
        }
      }
    }
    const evidence = {
      sourceCapture: ["source_image", "capture_ns", "sequence"].some((key) => reportKeys.has(key)),
      heldInputOrRelease: ["input_admission", "keys_held", "input_released", "physical_release_verified"].some((key) => reportKeys.has(key)) || Object.keys(counts).some((key) => ["input_admission", "keys_held", "input_released"].includes(key)),
      independentEffect: ["effect_receipts", "post_control_score", "effect_observed_ns"].some((key) => reportKeys.has(key)),
      routeCost: ["model_ns", "model_wall_seconds", "totalTokens", "wall_control_ns"].some((key) => reportKeys.has(key))
    };
    const eligible = Object.values(evidence).every(Boolean) && scheduleMatches > 0;
    results.push({ id: run.id, eventRows: events.length, protocolRows: protocol.length, eventCounts: counts, scheduleMatches, evidence, verdict: eligible ? "ELIGIBLE_FOR_T1_REVIEW" : "HOLD_NO_ELIGIBLE_TRACE" });
  }
  const verdict = results.every((result) => result.verdict === "ELIGIBLE_FOR_T1_REVIEW") ? "ELIGIBLE_FOR_T1_REVIEW" : "HOLD_NO_ELIGIBLE_TRACE";
  return { schema: "map01-trace-eligibility-audit-v1", verdict, results };
};
