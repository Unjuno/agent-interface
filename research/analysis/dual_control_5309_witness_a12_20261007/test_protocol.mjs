import test from 'node:test';
import assert from 'node:assert/strict';

import { makeFixture } from './fixture.mjs';
import { choose } from './candidate.mjs';
import { simulate } from './environment.mjs';
import { audit } from './auditor.mjs';

test('fixture spans three seen and one held-out topology with unique opaque cases', () => {
  const { candidateInput, oracle } = makeFixture();
  assert.equal(candidateInput.rows.length, 192);
  assert.equal(oracle.rows.length, 192);
  assert.equal(new Set(candidateInput.rows.map((row) => row.case_id)).size, 192);
  assert.deepEqual(oracle.topologies.find((topology) => topology.role === 'held_out')?.name,
    'lollipop5');
});

test('candidate input contains predictions and costs but no topology truth or model label', () => {
  const { candidateInput } = makeFixture();
  const serialized = JSON.stringify(candidateInput).toLowerCase();
  for (const forbidden of ['witness_state', 'transition_by_action', 'topology_name',
    'prediction_correct', 'prediction_stratum', 'oracle']) {
    assert.equal(serialized.includes(forbidden), false, `candidate input leaked ${forbidden}`);
  }
});

test('both policies rank the same already-admissible equal-information actions', () => {
  const { candidateInput } = makeFixture();
  const choices = choose(candidateInput);
  for (const row of candidateInput.rows) {
    const pair = choices.rows.filter((choice) => choice.case_id === row.case_id);
    assert.deepEqual(pair.map((choice) => choice.arm).sort(), ['GENERIC_IG', 'WITNESS_AWARE']);
    assert.deepEqual(pair[0].admissible_actions, pair[1].admissible_actions);
    assert.ok(row.admissible_actions.every((action) => row.info_gain[action] === 1));
  }
});

test('auditor counts realized misspecified successes only when an independent receipt supports them', () => {
  const { candidateInput, oracle } = makeFixture();
  const choices = choose(candidateInput);
  const raw = simulate(candidateInput, choices, oracle);
  const result = audit(candidateInput, choices, raw, oracle);
  assert.equal(result.verdict, 'PASS_HELDOUT_EFFECT_SEMANTICS_SCOPED');
  assert.ok(result.strata.misspecified.WITNESS_AWARE.complete > 0);
  assert.equal(result.unsupported_completions, 0);
  assert.equal(result.authority_grants, 0);
  assert.ok(result.held_out.witness_advantage > 0);
});

test('a receipt bound to the wrong action is rejected by the independent auditor', () => {
  const { candidateInput, oracle } = makeFixture();
  const choices = choose(candidateInput);
  const raw = simulate(candidateInput, choices, oracle);
  const target = raw.rows.find((row) => row.receipt?.kind === 'TASK_EFFECT');
  assert.ok(target);
  target.receipt.action = target.receipt.action === 'left' ? 'right' : 'left';
  const result = audit(candidateInput, choices, raw, oracle);
  assert.equal(result.verdict, 'FAIL_RETAINED_EFFECT_AUDIT');
  assert.ok(result.errors.some((error) => error.startsWith('receipt_binding_mismatch:')));
});

test('an information-predictive hint cannot complete an unaffordable or unsupported action', () => {
  const { candidateInput, oracle } = makeFixture();
  const row = candidateInput.rows.find((candidate) => !candidate.prior_witness
    && candidate.predicted_preserving_actions.length > 0);
  row.admissible_actions = [...row.predicted_preserving_actions];
  row.action_cost = Object.fromEntries(row.admissible_actions.map((action) => [action, 2]));
  row.cost_budget = 0;
  const choices = choose(candidateInput);
  const pair = choices.rows.filter((choice) => choice.case_id === row.case_id);
  assert.ok(pair.every((choice) => choice.action === null));
  const raw = simulate(candidateInput, choices, oracle);
  const result = audit(candidateInput, choices, raw, oracle);
  assert.equal(result.unsupported_completions, 0);
  assert.equal(result.authority_grants, 0);
});
