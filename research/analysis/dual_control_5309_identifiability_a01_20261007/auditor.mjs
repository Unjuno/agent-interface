import crypto from 'node:crypto';
import { readFileSync } from 'node:fs';

// Independent raw-only oracle. It reconstructs the fixture from compact
// scenario declarations; it does not import candidate functions or code.
const cases = [
  { id: 'separator', states: ['b0', 'h0'], safe: { b0: 'commit_safe', h0: 'commit_abort' }, allowed: ['repeat', 'separate'], expiry: null, horizon: 2, table: { repeat: ['routine', 'routine'], separate: ['benign_witness', 'hazard_witness'] } },
  { id: 'no_separator', states: ['n0', 'n1'], safe: { n0: 'commit_0', n1: 'commit_1' }, allowed: ['repeat'], expiry: null, horizon: 2, table: { repeat: ['routine', 'routine'] } },
  { id: 'expiry_before_separator', states: ['e0', 'e1'], safe: { e0: 'commit_0', e1: 'commit_1' }, allowed: ['repeat', 'separate'], expiry: 1, horizon: 2, table: { repeat: ['routine', 'routine'], separate: ['expired', 'expired'] } },
  { id: 'one_step_null', states: ['z0', 'z1'], safe: { z0: 'commit_0', z1: 'commit_1' }, allowed: ['separate'], expiry: null, horizon: 1, table: { separate: ['a', 'b'] } },
];
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);

function observed(caseDef, action, side, step) {
  if (!caseDef.allowed.includes(action) || (caseDef.expiry !== null && step >= caseDef.expiry)) return { admitted: false, executed: null, observation: null };
  const values = caseDef.table[action];
  if (!values) return { admitted: true, executed: action, observation: null };
  return { admitted: true, executed: action, observation: values[side] };
}

function distinguishable(caseDef, maxDepth) {
  let frontier = [{ histories: ['', ''], used: [] }];
  for (let depth = 0; depth < maxDepth; depth += 1) {
    const next = [];
    for (const node of frontier) {
      for (const action of caseDef.allowed) {
        const l = observed(caseDef, action, 0, depth);
        const r = observed(caseDef, action, 1, depth);
        if (!l.admitted || !r.admitted || l.executed !== r.executed) continue;
        const histories = [node.histories[0] + JSON.stringify(l.observation), node.histories[1] + JSON.stringify(r.observation)];
        const used = [...node.used, action];
        if (!same(histories, histories.slice().reverse())) return { separated: true, sequence: used, observations: histories };
        next.push({ histories, used });
      }
    }
    frontier = next;
  }
  return { separated: false, sequence: null, observations: null };
}

function main(path) {
  const raw = JSON.parse(readFileSync(path, 'utf8'));
  if (raw.experiment !== 'issue-5309-pairwise-identifiability-a01') throw new Error('wrong experiment');
  if (raw.scenarios.length !== cases.length) throw new Error('scenario count mismatch');
  let pairCount = 0;
  let undistinguished = 0;
  let falseAuthority = 0;
  let refusedCounterfactualObservation = 0;
  let nullControlSeparated = false;
  const results = [];
  for (const c of cases) {
    const row = raw.scenarios.find((x) => x.scenario === c.id);
    if (!row || !same(row.admissible, c.allowed) || row.horizon !== c.horizon) throw new Error(`frozen input mismatch ${c.id}`);
    const oracle = distinguishable(c, c.horizon);
    const incompatible = c.safe[c.states[0]] !== c.safe[c.states[1]];
    const expectedUnknown = incompatible && !oracle.separated;
    const actionRows = row.proposal_admission_execution_observation;
    for (const event of actionRows) {
      if (!event.admitted && (event.executed !== null || event.observation !== null)) refusedCounterfactualObservation += 1;
    }
    if (row.authority_granted !== false) falseAuthority += 1;
    if (incompatible) {
      pairCount += 1;
      if (expectedUnknown) undistinguished += 1;
      if (c.id === 'one_step_null') nullControlSeparated = oracle.separated;
      results.push({ scenario: c.id, incompatible_safe_commits: true, oracle, expected_decision: expectedUnknown ? 'UNKNOWN/YIELD' : 'DISTINGUISHABLE' });
    } else results.push({ scenario: c.id, incompatible_safe_commits: false, oracle });
  }
  if (pairCount !== 4 || undistinguished !== 2 || !nullControlSeparated || falseAuthority || refusedCounterfactualObservation) throw new Error('independent gate failed');
  const out = { status: 'PASS_METHOD_SCOPED', pair_count: pairCount, unseparable_incompatible_pairs: undistinguished, null_control_separated: nullControlSeparated, authority_grants: falseAuthority, refused_counterfactual_observation_errors: refusedCounterfactualObservation, results };
  process.stdout.write(`${JSON.stringify(out)}\n`);
}

if (process.argv.length !== 3) throw new Error('usage: auditor.mjs RAW.json');
main(process.argv[2]);
