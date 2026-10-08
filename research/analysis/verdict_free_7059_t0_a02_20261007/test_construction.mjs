import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {buildRaw} from './candidate.mjs';
import {auditRaw, runAudit} from './audit.mjs';

const fixtureBytes = fs.readFileSync(new URL('./fixture.json', import.meta.url));
const fixture = JSON.parse(fixtureBytes.toString('utf8'));
const raw = buildRaw(fixture, fixtureBytes);

test('frozen synthetic ledger yields ten condition-arm rows', () => {
  const result = auditRaw(fixture, fixtureBytes, raw);
  assert.deepEqual(result.errors, []);
  assert.equal(result.rows.length, 10);
});

test('same topology and evidence are retained across truthful roster text', () => {
  for (const record of raw.records) {
    assert.equal(record.arms[0].reviewers.length, 2);
    assert.equal(record.arms[1].reviewers.length, 2);
    assert.equal(record.arms[0].context.actual_reviewer_count, record.arms[1].context.actual_reviewer_count);
    assert.deepEqual(record.arms[0].context.evidence_pool, record.arms[1].context.evidence_pool);
  }
});

test('harmful omission and efficient omission remain distinct', () => {
  const rows = auditRaw(fixture, fixtureBytes, raw).rows;
  const harmful = rows.find((row) => row.case_id === 'C02_HARMFUL_MISSED_CHECK' && row.arm === 'ROSTER_TRUTHFULLY_ADVERTISED');
  const efficient = rows.find((row) => row.case_id === 'C03_EFFICIENT_SAME_CORRECTNESS' && row.arm === 'ROSTER_TRUTHFULLY_ADVERTISED');
  assert.equal(harmful.false_pass, true);
  assert.equal(harmful.correctness, 'INCORRECT');
  assert.equal(efficient.false_pass, false);
  assert.equal(efficient.correctness, 'CORRECT');
});

test('missing tool result is held rather than scored as a verdict', () => {
  const rows = auditRaw(fixture, fixtureBytes, raw).rows;
  assert.equal(rows.find((row) => row.case_id === 'C05_MISSING_TOOL_LOG' && row.arm === 'ROSTER_NOT_ADVERTISED').correctness, 'HOLD_MISSING_TOOL_LOG');
  assert.equal(rows.find((row) => row.case_id === 'C05_MISSING_TOOL_LOG' && row.arm === 'ROSTER_TRUTHFULLY_ADVERTISED').correctness, 'HOLD_MISSING_TOOL_LOG');
});

test('all six frozen integrity mutations fail closed', () => {
  const result = runAudit(fixture, fixtureBytes, raw);
  assert.equal(result.status, 'PASS_METHOD_SCOPED');
  assert.equal(result.mutation_checks.length, 6);
  assert.equal(result.mutation_rejections, 6);
});

test('peer verdict content follows both first-pass commits in every row', () => {
  for (const row of raw.records) {
    for (const arm of row.arms) {
      const peer = arm.events.find((event) => event.type === 'peer_content_release');
      for (const reviewer of arm.reviewers) {
        const commit = arm.events.find((event) => event.event_id === reviewer.commit_event_id);
        assert.ok(peer.sequence > commit.sequence);
      }
    }
  }
});
