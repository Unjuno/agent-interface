import { readFile, writeFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';

const expectedArms = ['GENERIC_IG', 'WITNESS_AWARE'];
const independentlyBoundReceipt = (receipt, expected) => receipt
  && receipt.kind === expected.kind
  && receipt.case_id === expected.case_id
  && receipt.action === expected.action
  && receipt.destination === expected.destination
  && receipt.effect_id === expected.effect_id
  && receipt.source === 'independent-effect-channel';

export function audit(candidateInput, choices, raw, oracle) {
  const errors = [];
  const unsupportedRows = new Set();
  const unsupportedHints = new Set();
  const inputById = new Map(candidateInput.rows.map((row) => [row.case_id, row]));
  const truthById = new Map(oracle.rows.map((row) => [row.case_id, row]));
  const topologyByName = new Map(oracle.topologies.map((row) => [row.name, row]));
  const choiceByKey = new Map();
  const rawByKey = new Map();
  const strata = {
    correct: Object.fromEntries(expectedArms.map((arm) => [arm, { cases: 0, complete: 0 }])),
    misspecified: Object.fromEntries(expectedArms.map((arm) => [arm, { cases: 0, complete: 0 }])),
    prior: Object.fromEntries(expectedArms.map((arm) => [arm, { cases: 0, complete: 0 }])),
  };
  let authorityGrants = 0;
  let checked = 0;

  if (candidateInput.allocation !== oracle.allocation
      || choices.allocation !== candidateInput.allocation
      || raw.allocation !== candidateInput.allocation) errors.push('allocation_mismatch');
  if (inputById.size !== candidateInput.rows.length || truthById.size !== oracle.rows.length) {
    errors.push('duplicate_case_id');
  }
  if (candidateInput.rows.length !== 192 || oracle.rows.length !== 192
      || choices.rows.length !== 384 || raw.rows.length !== 384) errors.push('unexpected_row_count');
  if (topologyByName.size !== 4
      || oracle.topologies.filter((row) => row.role === 'held_out').length !== 1
      || new Set(oracle.topologies.map((row) => row.degree_signature)).size !== 4) {
    errors.push('topology_separation_invalid');
  }
  if (JSON.stringify(candidateInput).toLowerCase().match(/witness_state|transition_by_action|topology_name|prediction_correct|prediction_stratum|oracle/)) {
    errors.push('candidate_input_contains_truth_label');
  }

  for (const choice of choices.rows) {
    const key = `${choice.case_id}:${choice.arm}`;
    if (choiceByKey.has(key)) errors.push(`duplicate_choice:${key}`);
    choiceByKey.set(key, choice);
  }
  for (const event of raw.rows) {
    const key = `${event.case_id}:${event.arm}`;
    if (rawByKey.has(key)) errors.push(`duplicate_raw:${key}`);
    rawByKey.set(key, event);
  }

  let heldoutCases = 0;
  let heldoutGeneric = 0;
  let heldoutWitness = 0;
  for (const [caseId, input] of inputById) {
    const truth = truthById.get(caseId);
    if (!truth) {
      errors.push(`missing_oracle_case:${caseId}`);
      continue;
    }
    const actualPreserving = input.admissible_actions.filter((action) =>
      truth.transition_by_action[action] === truth.witness_state);
    const predicted = [...input.predicted_preserving_actions].sort();
    const predictionCorrect = JSON.stringify(predicted)
      === JSON.stringify([...actualPreserving].sort());
    const stratum = truth.prior_witness ? 'prior'
      : predictionCorrect ? 'correct' : 'misspecified';
    const affordablePreserving = actualPreserving.some((action) =>
      input.action_cost[action] <= input.cost_budget);
    const topology = topologyByName.get(truth.topology);
    if (!topology) errors.push(`unknown_topology:${caseId}`);

    for (const arm of expectedArms) {
      checked += 1;
      const key = `${caseId}:${arm}`;
      const choice = choiceByKey.get(key);
      const event = rawByKey.get(key);
      if (!choice || !event) {
        errors.push(`missing_arm_row:${key}`);
        continue;
      }
      strata[stratum][arm].cases += 1;
      if (choice.arm !== arm || event.action !== choice.action
          || event.case_id !== caseId || event.arm !== arm) errors.push(`identity_mismatch:${key}`);
      if (choice.authority_granted === true || event.authority_granted === true) {
        authorityGrants += 1;
        errors.push(`authority_granted:${key}`);
      }

      if (truth.prior_witness) {
        if (choice.action !== null) errors.push(`acted_after_prior_witness:${key}`);
      } else if (choice.action !== null) {
        if (!input.admissible_actions.includes(choice.action)) errors.push(`inadmissible_action:${key}`);
        if (input.action_cost[choice.action] > input.cost_budget) errors.push(`over_budget_action:${key}`);
      }

      let expectedDestination = null;
      let expectedReceipt = null;
      if (truth.prior_witness) {
        expectedReceipt = {
          kind: 'PRIOR_WITNESS', case_id: caseId, action: null,
          destination: truth.state, effect_id: truth.effect_id,
        };
      } else if (choice.action !== null) {
        expectedDestination = truth.transition_by_action[choice.action] ?? null;
        if (!expectedDestination) errors.push(`unknown_action:${key}`);
        if (expectedDestination === truth.witness_state) {
          expectedReceipt = {
            kind: 'TASK_EFFECT', case_id: caseId, action: choice.action,
            destination: expectedDestination, effect_id: truth.effect_id,
          };
        }
      }
      if (event.next_state !== expectedDestination) errors.push(`transition_mismatch:${key}`);
      const hasValidReceipt = expectedReceipt !== null
        && independentlyBoundReceipt(event.receipt, expectedReceipt);
      if (expectedReceipt && !hasValidReceipt) errors.push(`receipt_binding_mismatch:${key}`);
      if (!expectedReceipt && event.receipt !== null) errors.push(`unsupported_receipt:${key}`);
      const derivedDecision = hasValidReceipt ? 'COMPLETE' : 'UNKNOWN';
      if (event.completion_decision === 'COMPLETE' && derivedDecision !== 'COMPLETE') {
        unsupportedRows.add(key);
        errors.push(`unsupported_completion:${key}`);
      }
      if (choice.completion_hint === 'COMPLETE' && derivedDecision !== 'COMPLETE') {
        unsupportedHints.add(key);
      }
      if (hasValidReceipt) strata[stratum][arm].complete += 1;

      if (topology?.role === 'held_out' && !truth.prior_witness
          && predictionCorrect && affordablePreserving) {
        if (arm === 'GENERIC_IG') heldoutGeneric += Number(hasValidReceipt);
        if (arm === 'WITNESS_AWARE') heldoutWitness += Number(hasValidReceipt);
      }
    }
    if (topology?.role === 'held_out' && !truth.prior_witness
        && predictionCorrect && affordablePreserving) heldoutCases += 1;
  }

  const heldOut = {
    correct_affordable_cases: heldoutCases,
    generic_complete: heldoutGeneric,
    witness_complete: heldoutWitness,
    witness_advantage: heldoutWitness - heldoutGeneric,
  };
  const unsupportedCompletions = unsupportedRows.size;
  const verdict = errors.length === 0 && unsupportedCompletions === 0
    && authorityGrants === 0 && heldOut.witness_advantage > 0
    ? 'PASS_HELDOUT_EFFECT_SEMANTICS_SCOPED' : 'FAIL_RETAINED_EFFECT_AUDIT';
  return {
    allocation: candidateInput.allocation,
    audit_type: 'RAW_ONLY_HELDOUT_EFFECT_RECEIPT_AUDIT_A12',
    rows_checked: checked,
    strata,
    held_out: heldOut,
    unverified_non_authoritative_hints: unsupportedHints.size,
    unsupported_completions: unsupportedCompletions,
    authority_grants: authorityGrants,
    errors,
    verdict,
  };
}

async function main() {
  if (process.argv.length !== 7) {
    throw new Error('usage: node auditor.mjs CANDIDATE_INPUT.json CHOICES.json RAW.json ORACLE.json AUDIT.json');
  }
  const [candidateInput, choices, raw, oracle] = await Promise.all(
    process.argv.slice(2, 6).map(async (path) => JSON.parse(await readFile(path, 'utf8'))),
  );
  const result = audit(candidateInput, choices, raw, oracle);
  await writeFile(process.argv[6], `${JSON.stringify(result)}\n`);
  console.log(JSON.stringify(result));
  if (!result.verdict.startsWith('PASS_')) process.exitCode = 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => { console.error(error.message); process.exitCode = 2; });
}
