const assert = require("node:assert/strict");
const audit = require("./audit.js");

function fixture({ schedule = false, held = true, includeCost = true } = {}) {
  const events = [
    { event: "input_admission", key: "w", admitted_ns: 10 },
    ...(held ? [{ event: "keys_held", keys: ["w"] }] : []),
    { event: "terminal", release: { event: "owner_release", verified: true, keys_down: [] } }
  ];
  if (schedule) events.push({ event: "stimulus", target_trajectory: [{ t_ns: 1, target: [0, 0] }] });
  const report = {
    source_image: "frame.png", capture_ns: 1, sequence: 1,
    effect_receipts: [{ effect_observed_ns: 20 }],
    ...(includeCost ? { model_ns: 5 } : {})
  };
  return {
    id: "synthetic",
    reportText: JSON.stringify(report),
    eventsText: events.map((x) => JSON.stringify(x)).join("\n"),
    protocolText: JSON.stringify({ direction: "north" })
  };
}

const missingSchedule = audit([fixture()]);
assert.equal(missingSchedule.verdict, "HOLD_NO_ELIGIBLE_TRACE");
assert.equal(missingSchedule.results[0].candidateScheduleMarkers, 0);
assert.equal(missingSchedule.results[0].occupancyCoverageProxy, true);

const markerNeedsReview = audit([fixture({ schedule: true })]);
assert.equal(markerNeedsReview.verdict, "REVIEW_REQUIRED_NOT_ELIGIBLE");
assert.notEqual(markerNeedsReview.verdict, "ELIGIBLE_FOR_T1_REVIEW");

const incompleteOccupancy = audit([fixture({ held: false })]);
assert.equal(incompleteOccupancy.results[0].occupancyCoverageProxy, false);
assert.equal(incompleteOccupancy.verdict, "HOLD_NO_ELIGIBLE_TRACE");

const missingCost = audit([fixture({ includeCost: false })]);
assert.equal(missingCost.results[0].routeCostEvidencePresent, false);
assert.equal(missingCost.verdict, "HOLD_NO_ELIGIBLE_TRACE");

assert.throws(() => audit([{ id: "bad", reportText: "{", eventsText: "", protocolText: "" }]));
process.stdout.write("4 tests passed; no eligibility PASS can be emitted from marker presence alone.\n");
