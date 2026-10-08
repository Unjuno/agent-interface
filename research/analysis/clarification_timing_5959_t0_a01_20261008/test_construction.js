'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { runCandidate } = require('./candidate');
const { audit, verifyFreeze } = require('./auditor');

const root = __dirname;
const input = JSON.parse(fs.readFileSync(path.join(root, 'candidate_inputs.json'), 'utf8'));
const oracle = JSON.parse(fs.readFileSync(path.join(root, 'audit_oracle.json'), 'utf8'));

function auditMutant(raw, mutate) {
  const copy = structuredClone(raw);
  mutate(copy);
  assert.throws(() => audit(input, oracle, copy));
}

const raw = runCandidate(input);
const report = audit(input, oracle, raw);
assert.equal(verifyFreeze(root).allocation, input.allocation);
assert.equal(report.disposition, 'PASS_METHOD_SCOPED');
assert.equal(report.requests_reconstructed, 15);
assert.equal(report.policy_rows_reconstructed, 45);
assert.equal(report.mandatory_events_reconstructed, 1);

auditMutant(raw, (copy) => { copy.policy_rows[0].planned_tick += 1; });
auditMutant(raw, (copy) => { copy.mandatory_routes.length = 0; });
auditMutant(raw, (copy) => {
  const row = copy.policy_rows.find((item) => item.request_id === 'C02-unavailable-signal' && item.policy === 'low_cost_window');
  row.signal_tick = 4;
  row.disposition = 'AUTHORIZED_LOW_COST_WINDOW';
});
auditMutant(raw, (copy) => {
  const row = copy.policy_rows.find((item) => item.request_id === 'C04-zero-slack' && item.policy === 'immediate');
  row.planned_tick = 4;
  row.disposition = 'IMMEDIATE_DEFERRABLE';
});
auditMutant(raw, (copy) => { copy.policy_rows.pop(); });

const noResponse = report.outcomes.filter((item) => item.request_id === 'C08-no-response');
assert.equal(noResponse.length, 3);
assert.ok(noResponse.every((item) => item.outcome === 'NO_RESPONSE_YIELD' && !item.modeled_effect));
const refusal = report.outcomes.filter((item) => item.request_id === 'C09-refusal');
assert.ok(refusal.every((item) => item.outcome === 'REFUSAL_YIELD' && !item.modeled_effect));
const unauthorized = report.outcomes.filter((item) => item.request_id === 'C15-unauthorized-choice');
assert.ok(unauthorized.every((item) => item.outcome === 'INVALID_ANSWER_YIELD' && !item.modeled_effect));
const staleBefore = report.outcomes.filter((item) => item.request_id === 'C07-version-changes-at-delivery' && item.policy !== 'immediate');
assert.ok(staleBefore.every((item) => item.outcome === 'CANCEL_STALE_BEFORE_DELIVERY'));
const exactDeadline = report.outcomes.find((item) => item.request_id === 'C11-answer-at-inclusive-deadline' && item.policy === 'latest_safe');
assert.equal(exactDeadline.outcome, 'AUTHORIZED_EFFECT');
assert.equal(exactDeadline.response_deadline_missed, false);
assert.ok(report.outcomes.filter((item) => item.request_id === 'C06-version-changes-before-delivery' && item.policy !== 'immediate')
  .every((item) => item.prompt_delivery_tick === null && item.synthetic_interruption_cost === null));
const urgent = raw.policy_rows.filter((item) => item.request_id === 'C05-nondeferrable-urgent');
assert.ok(urgent.every((item) => item.planned_tick === 5 && item.disposition === 'IMMEDIATE_NONDEFERRABLE'));
assert.equal(fs.readFileSync(path.join(root, 'auditor.js'), 'utf8').includes("require('./candidate')"), false);

process.stdout.write('CONSTRUCTION_PASS requests=15 rows=45 mandatory=1 mutations=5\n');
