#!/usr/bin/env node
'use strict';

const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');

const POLICIES = ['immediate', 'latest_safe', 'low_cost_window'];

function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonical(value[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

function independentPlan(request, policy) {
  const common = { request_id: request.id, policy };
  if (request.deferrable === false) {
    return { ...common, planned_tick: request.created_tick,
      disposition: 'IMMEDIATE_NONDEFERRABLE', signal_tick: null };
  }
  const usefulBy = request.latest_useful_answer_tick < request.commitment_tick
    ? request.latest_useful_answer_tick
    : request.commitment_tick - 1;
  const responseStartBy = usefulBy - request.response_latency_bound;
  const dueBy = request.safe_wait_through_tick < responseStartBy
    ? request.safe_wait_through_tick : responseStartBy;
  if (dueBy < request.created_tick) {
    return { ...common, planned_tick: null, disposition: 'YIELD_NOW', signal_tick: null };
  }
  if (policy === 'immediate') {
    return { ...common, planned_tick: request.created_tick,
      disposition: 'IMMEDIATE_DEFERRABLE', signal_tick: null };
  }
  if (policy === 'latest_safe') {
    return { ...common, planned_tick: dueBy, disposition: 'LATEST_SAFE', signal_tick: null };
  }
  if (policy !== 'low_cost_window') throw new Error(`unknown policy ${policy}`);
  let chosen = null;
  if (request.availability_signal_authorized === true
      && Array.isArray(request.authorized_low_cost_ticks)) {
    for (const tick of request.authorized_low_cost_ticks) {
      if (Number.isInteger(tick) && tick >= request.created_tick && tick <= dueBy
          && (chosen === null || tick > chosen)) chosen = tick;
    }
  }
  if (chosen !== null) {
    return { ...common, planned_tick: chosen,
      disposition: 'AUTHORIZED_LOW_COST_WINDOW', signal_tick: chosen };
  }
  return { ...common, planned_tick: dueBy,
    disposition: 'LATEST_SAFE_FALLBACK', signal_tick: null };
}

function versionAt(request, oracleCase, tick) {
  let version = request.decision_version;
  for (const change of oracleCase.version_changes) {
    if (change.tick <= tick && change.tick >= request.created_tick) version = change.version;
  }
  return version;
}

function assessOutcome(request, oracleCase, planRow) {
  if (planRow.planned_tick === null) return 'YIELD_NO_SAFE_RESPONSE_WINDOW';
  const deliveredAt = planRow.planned_tick;
  if (versionAt(request, oracleCase, deliveredAt) !== request.decision_version) {
    return 'CANCEL_STALE_BEFORE_DELIVERY';
  }
  if (oracleCase.reply === null) return 'NO_RESPONSE_YIELD';
  const answerAt = deliveredAt + oracleCase.reply.delay_ticks;
  const lastUseful = Math.min(request.latest_useful_answer_tick, request.commitment_tick - 1);
  if (oracleCase.reply.delay_ticks > request.response_latency_bound
      || answerAt > lastUseful || answerAt >= request.commitment_tick) {
    return 'LATE_REPLY_YIELD';
  }
  if (versionAt(request, oracleCase, answerAt) !== request.decision_version) {
    return 'STALE_ANSWER_YIELD';
  }
  if (oracleCase.reply.kind === 'REFUSAL') return 'REFUSAL_YIELD';
  if (oracleCase.reply.kind !== 'AUTHORIZED_CHOICE'
      || !oracleCase.authorized_choices.includes(oracleCase.reply.choice)) {
    return 'INVALID_ANSWER_YIELD';
  }
  return 'AUTHORIZED_EFFECT';
}

function audit(input, oracle, raw) {
  if (input.schema !== 'clarification-timing-candidate-input-v1'
      || oracle.schema !== 'clarification-timing-audit-oracle-v1'
      || raw.schema !== 'clarification-timing-candidate-output-v1'
      || raw.allocation !== input.allocation) throw new Error('schema/allocation mismatch');
  const oracleById = new Map(oracle.cases.map((row) => [row.request_id, row]));
  if (oracleById.size !== input.requests.length) throw new Error('oracle row cardinality mismatch');
  const expectedRows = [];
  const outcomes = [];
  const expectedRoutes = [];
  for (const request of input.requests) {
    const oracleCase = oracleById.get(request.id);
    if (!oracleCase) throw new Error(`missing audit-only case ${request.id}`);
    for (const policy of POLICIES) {
      const expected = independentPlan(request, policy);
      expectedRows.push(expected);
      const got = raw.policy_rows.find((row) => row.request_id === request.id && row.policy === policy);
      if (!got || canonical(got) !== canonical(expected)) {
        throw new Error(`candidate/oracle schedule mismatch ${request.id}/${policy}`);
      }
      const outcome = assessOutcome(request, oracleCase, expected);
      const promptDelivery = outcome === 'CANCEL_STALE_BEFORE_DELIVERY'
        || outcome === 'YIELD_NO_SAFE_RESPONSE_WINDOW' ? null : expected.planned_tick;
      const answerTick = promptDelivery !== null && oracleCase.reply !== null
        ? promptDelivery + oracleCase.reply.delay_ticks : null;
      const lastUseful = Math.min(request.latest_useful_answer_tick, request.commitment_tick - 1);
      const missedDeadline = answerTick !== null && (oracleCase.reply.delay_ticks > request.response_latency_bound
        || answerTick > lastUseful || answerTick >= request.commitment_tick);
      const deliveryCost = promptDelivery === null ? null
        : (Object.hasOwn(oracleCase.synthetic_cost_by_tick, String(promptDelivery))
          ? oracleCase.synthetic_cost_by_tick[String(promptDelivery)] : null);
      outcomes.push({ request_id: request.id, policy, outcome,
        prompt_delivery_tick: promptDelivery,
        answer_tick: answerTick,
        response_deadline_missed: missedDeadline,
        synthetic_interruption_cost: deliveryCost,
        modeled_effect: outcome === 'AUTHORIZED_EFFECT' });
    }
    for (const event of request.mandatory_events) {
      expectedRoutes.push({ request_id: request.id, event_id: event.id,
        arrival_tick: event.arrival_tick, delivery_tick: event.arrival_tick, bypass: true });
    }
  }
  if (raw.policy_rows.length !== expectedRows.length) throw new Error('policy row count mismatch');
  if (canonical(raw.mandatory_routes) !== canonical(expectedRoutes)) {
    throw new Error('mandatory bypass route mismatch');
  }
  if (Object.keys(raw).sort().join(',') !== 'allocation,mandatory_routes,policy_rows,schema') {
    throw new Error('unexpected candidate output fields');
  }

  const row = (id, policy) => outcomes.find((item) => item.request_id === id && item.policy === policy);
  const c01 = ['immediate', 'latest_safe', 'low_cost_window'].map((policy) => row('C01-low-window-tradeoff', policy));
  const lowCost = c01.find((item) => item.policy === 'low_cost_window');
  const immediateCost = c01.find((item) => item.policy === 'immediate');
  const latestCost = c01.find((item) => item.policy === 'latest_safe');
  const mutationChecks = {
    allRowsReconstructed: outcomes.length === input.requests.length * POLICIES.length,
    mandatoryBypassZeroDelay: expectedRoutes.every((event) => event.delivery_tick === event.arrival_tick),
    zeroSlackYields: POLICIES.every((policy) => row('C04-zero-slack', policy).outcome === 'YIELD_NO_SAFE_RESPONSE_WINDOW'),
    noResponseDoesNotAct: POLICIES.every((policy) => !row('C08-no-response', policy).modeled_effect),
    refusalDoesNotAct: POLICIES.every((policy) => !row('C09-refusal', policy).modeled_effect),
    unauthorizedChoiceDoesNotAct: POLICIES.every((policy) => row('C15-unauthorized-choice', policy).outcome === 'INVALID_ANSWER_YIELD'),
    lateReplyDoesNotAct: POLICIES.every((policy) => !row('C10-response-exceeds-bound', policy).modeled_effect),
    staleAnswerDoesNotAct: POLICIES.every((policy) => !row('C12-version-changes-after-delivery', policy).modeled_effect),
    canceledPromptHasNoInterruptionCost: ['C06-version-changes-before-delivery', 'C07-version-changes-at-delivery']
      .every((id) => ['latest_safe', 'low_cost_window'].every((policy) =>
        row(id, policy).prompt_delivery_tick === null && row(id, policy).synthetic_interruption_cost === null)),
    staleQuestionCanceledBeforeDelivery: ['C06-version-changes-before-delivery', 'C07-version-changes-at-delivery']
      .every((id) => ['latest_safe', 'low_cost_window'].every((policy) =>
        row(id, policy).outcome === 'CANCEL_STALE_BEFORE_DELIVERY')),
    exactDeadlineAccepted: row('C11-answer-at-inclusive-deadline', 'latest_safe').outcome === 'AUTHORIZED_EFFECT',
    syntheticCostDiscriminator: lowCost.synthetic_interruption_cost !== null
      && lowCost.synthetic_interruption_cost < immediateCost.synthetic_interruption_cost
      && lowCost.synthetic_interruption_cost < latestCost.synthetic_interruption_cost,
  };
  const failed = Object.entries(mutationChecks).filter(([, value]) => value !== true).map(([key]) => key);
  if (failed.length) throw new Error(`decision gate failure: ${failed.join(',')}`);
  return {
    schema: 'clarification-timing-independent-audit-v1',
    disposition: 'PASS_METHOD_SCOPED',
    requests_reconstructed: input.requests.length,
    policy_rows_reconstructed: outcomes.length,
    mandatory_events_reconstructed: expectedRoutes.length,
    mutation_checks: mutationChecks,
    outcomes,
    mandatory_routes: expectedRoutes,
    scope: 'synthetic finite event semantics and authored interruption-cost scoring only; no human measurement or runtime scheduler claim',
  };
}

function verifyFreeze(folder) {
  const freeze = JSON.parse(fs.readFileSync(path.join(folder, 'FREEZE.json'), 'utf8'));
  const mismatches = [];
  for (const [file, expected] of Object.entries(freeze.source_sha256)) {
    const actual = crypto.createHash('sha256').update(fs.readFileSync(path.join(folder, file))).digest('hex');
    if (actual !== expected) mismatches.push(file);
  }
  if (mismatches.length) throw new Error(`frozen source hash mismatch: ${mismatches.join(',')}`);
  return freeze;
}

if (require.main === module) {
  if (process.argv[2] !== '--formal' || !process.argv[3] || !process.argv[4]) {
    process.stderr.write('usage: node auditor.js --formal PACKAGE_DIR RAW.json\n');
    process.exitCode = 2;
  } else {
    try {
      const folder = process.argv[3];
      const freeze = verifyFreeze(folder);
      const input = JSON.parse(fs.readFileSync(path.join(folder, 'candidate_inputs.json'), 'utf8'));
      const oracle = JSON.parse(fs.readFileSync(path.join(folder, 'audit_oracle.json'), 'utf8'));
      const raw = JSON.parse(fs.readFileSync(process.argv[4], 'utf8'));
      const result = audit(input, oracle, raw);
      result.freeze_allocation = freeze.allocation;
      process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
    } catch (error) {
      process.stderr.write(`${error.stack || error}\n`);
      process.exitCode = 1;
    }
  }
}

module.exports = { audit, independentPlan, verifyFreeze };
