#!/usr/bin/env node
'use strict';

const fs = require('node:fs');

const POLICIES = ['immediate', 'latest_safe', 'low_cost_window'];

function plan(request, policy) {
  if (!request.deferrable) {
    return {
      request_id: request.id,
      policy,
      planned_tick: request.created_tick,
      disposition: 'IMMEDIATE_NONDEFERRABLE',
      signal_tick: null,
    };
  }

  const latestAnswer = Math.min(
    request.latest_useful_answer_tick,
    request.commitment_tick - 1,
  );
  const latestDelivery = Math.min(
    request.safe_wait_through_tick,
    latestAnswer - request.response_latency_bound,
  );
  if (latestDelivery < request.created_tick) {
    return {
      request_id: request.id,
      policy,
      planned_tick: null,
      disposition: 'YIELD_NOW',
      signal_tick: null,
    };
  }

  if (policy === 'immediate') {
    return {
      request_id: request.id,
      policy,
      planned_tick: request.created_tick,
      disposition: 'IMMEDIATE_DEFERRABLE',
      signal_tick: null,
    };
  }
  if (policy === 'latest_safe') {
    return {
      request_id: request.id,
      policy,
      planned_tick: latestDelivery,
      disposition: 'LATEST_SAFE',
      signal_tick: null,
    };
  }
  if (policy === 'low_cost_window') {
    const ticks = request.availability_signal_authorized
      && Array.isArray(request.authorized_low_cost_ticks)
      ? request.authorized_low_cost_ticks.filter(
        (tick) => Number.isInteger(tick)
          && tick >= request.created_tick
          && tick <= latestDelivery,
      )
      : [];
    if (ticks.length > 0) {
      const signalTick = Math.max(...ticks);
      return {
        request_id: request.id,
        policy,
        planned_tick: signalTick,
        disposition: 'AUTHORIZED_LOW_COST_WINDOW',
        signal_tick: signalTick,
      };
    }
    return {
      request_id: request.id,
      policy,
      planned_tick: latestDelivery,
      disposition: 'LATEST_SAFE_FALLBACK',
      signal_tick: null,
    };
  }
  throw new Error(`unknown policy ${policy}`);
}

function runCandidate(input) {
  if (input.schema !== 'clarification-timing-candidate-input-v1'
      || input.issue !== 5959
      || input.allocation !== 'CLARIFICATION-TIMING-5959-T0-A01-20261008'
      || JSON.stringify(input.policies) !== JSON.stringify(POLICIES)) {
    throw new Error('candidate input identity/schema mismatch');
  }
  const policyRows = [];
  const mandatoryRoutes = [];
  for (const request of input.requests) {
    for (const policy of POLICIES) policyRows.push(plan(request, policy));
    for (const event of request.mandatory_events) {
      mandatoryRoutes.push({
        request_id: request.id,
        event_id: event.id,
        arrival_tick: event.arrival_tick,
        delivery_tick: event.arrival_tick,
        bypass: true,
      });
    }
  }
  return {
    schema: 'clarification-timing-candidate-output-v1',
    allocation: input.allocation,
    policy_rows: policyRows,
    mandatory_routes: mandatoryRoutes,
  };
}

if (require.main === module) {
  if (process.argv[2] !== '--formal' || !process.argv[3]) {
    process.stderr.write('usage: node candidate.js --formal candidate_inputs.json\n');
    process.exitCode = 2;
  } else {
    try {
      const input = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
      process.stdout.write(`${JSON.stringify(runCandidate(input), null, 2)}\n`);
    } catch (error) {
      process.stderr.write(`${error.stack || error}\n`);
      process.exitCode = 1;
    }
  }
}

module.exports = { runCandidate };
