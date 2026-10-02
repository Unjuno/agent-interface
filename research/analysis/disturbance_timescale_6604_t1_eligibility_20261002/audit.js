module.exports = function audit(runs) {
  const schedulePattern = /(?:target_trajectory|disturbance_schedule|external_target_schedule|target_generation_schedule)/i;
  const output = [];
  function keysOf(value, keys) {
    if (value && typeof value === "object") {
      for (const [key, child] of Object.entries(value)) { keys.add(key); keysOf(child, keys); }
    }
  }
  function matchesOf(value) {
    let count = 0;
    function walk(node) {
      if (node && typeof node === "object") {
        for (const [key, child] of Object.entries(node)) { if (schedulePattern.test(key)) count++; walk(child); }
      } else if (typeof node === "string" && schedulePattern.test(node)) count++;
    }
    walk(value);
    return count;
  }
  function releaseReceipts(value) {
    let count = 0;
    function walk(node) {
      if (node && typeof node === "object") {
        if (node.event === "owner_release" && node.verified === true) count++;
        for (const child of Object.values(node)) walk(child);
      }
    }
    walk(value);
    return count;
  }
  for (const run of runs) {
    const parseLines = (text) => text.trim().split(/\r?\n/).map((line) => JSON.parse(line));
    const events = parseLines(run.eventsText);
    const protocol = parseLines(run.protocolText);
    const report = JSON.parse(run.reportText);
    const eventCounts = {};
    for (const row of events) {
      const type = row.event || row.type || "unknown";
      eventCounts[type] = (eventCounts[type] || 0) + 1;
    }
    const reportKeys = new Set();
    keysOf(report, reportKeys);
    const candidateScheduleMarkers = matchesOf(events) + matchesOf(protocol) + matchesOf(report);
    const admissions = eventCounts.input_admission || 0;
    const heldReceipts = eventCounts.keys_held || 0;
    const verifiedReleaseReceipts = releaseReceipts(events) + releaseReceipts(report);
    const sourceEvidencePresent = ["source_image", "capture_ns", "sequence"].some((key) => reportKeys.has(key));
    const effectEvidencePresent = ["effect_receipts", "post_control_score", "effect_observed_ns"].some((key) => reportKeys.has(key));
    const routeCostEvidencePresent = ["model_ns", "model_wall_seconds", "totalTokens", "wall_control_ns"].some((key) => reportKeys.has(key));
    const occupancyCoverageProxy = admissions > 0 && heldReceipts >= admissions && verifiedReleaseReceipts > 0;
    const verdict = candidateScheduleMarkers === 0 ? "HOLD_NO_ELIGIBLE_TRACE" : "REVIEW_REQUIRED_NOT_ELIGIBLE";
    output.push({
      id: run.id, eventRows: events.length, protocolRows: protocol.length, eventCounts,
      candidateScheduleMarkers, admissions, heldReceipts, verifiedReleaseReceipts,
      sourceEvidencePresent, occupancyCoverageProxy, effectEvidencePresent, routeCostEvidencePresent,
      verdict
    });
  }
  return {
    schema: "map01-trace-eligibility-prescreen-v3",
    verdict: output.every((item) => item.verdict === "HOLD_NO_ELIGIBLE_TRACE") ? "HOLD_NO_ELIGIBLE_TRACE" : "REVIEW_REQUIRED_NOT_ELIGIBLE",
    results: output
  };
};
