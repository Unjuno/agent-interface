import { readFile, writeFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';

const arms = ['GENERIC_IG', 'WITNESS_AWARE'];
const actionOrder = ['left', 'right'];
const same = (left, right) => JSON.stringify(left) === JSON.stringify(right);

function expectedAction(input, arm) {
  if (input.prior_witness) return null;
  const affordable = input.admissible_actions.filter((action) =>
    input.action_cost[action] <= input.cost_budget);
  if (arm === 'GENERIC_IG') return [...affordable].sort()[0] ?? null;
  return affordable
    .filter((action) => input.predicted_preserving_actions.includes(action))
    .sort((left, right) => input.action_cost[left] - input.action_cost[right]
      || left.localeCompare(right))[0] ?? null;
}

function topologySignatures(oracle) {
  return oracle.topologies.map((topology) => {
    const indegree = Object.fromEntries(topology.nodes.map((node) => [node, 0]));
    for (const action of actionOrder) {
      for (const destination of Object.values(topology.transitions[action] ?? {})) {
        if (!(destination in indegree)) return `${topology.name}:invalid-destination`;
        indegree[destination] += 1;
      }
    }
    return `${topology.nodes.length}:${Object.values(indegree).sort((a, b) => a - b).join(',')}`;
  });
}

export function reconcile(input, oracle, choices, raw, formalAudit) {
  const errors = [];
  const inputById = new Map(input.rows.map((row) => [row.case_id, row]));
  const truthById = new Map(oracle.rows.map((row) => [row.case_id, row]));
  const topologyByName = new Map(oracle.topologies.map((row) => [row.name, row]));
  const choicesByKey = new Map(choices.rows.map((row) => [`${row.case_id}:${row.arm}`, row]));
  const rawByKey = new Map(raw.rows.map((row) => [`${row.case_id}:${row.arm}`, row]));
  let policyMismatches = 0;
  let receiptMismatches = 0;
  let equalInformationGain = input.rows.every((row) =>
    row.info_gain.left === 1 && row.info_gain.right === 1);
  const strata = {
    correct: Object.fromEntries(arms.map((arm) => [arm, { cases: 0, complete: 0 }])),
    misspecified: Object.fromEntries(arms.map((arm) => [arm, { cases: 0, complete: 0 }])),
    prior: Object.fromEntries(arms.map((arm) => [arm, { cases: 0, complete: 0 }])),
  };
  let heldoutCases = 0;
  let heldoutGeneric = 0;
  let heldoutWitness = 0;
  let authorityGrants = 0;
  let unsupportedHints = 0;

  if (input.rows.length !== 192 || oracle.rows.length !== 192
      || choices.rows.length !== 384 || raw.rows.length !== 384
      || inputById.size !== input.rows.length || truthById.size !== oracle.rows.length
      || choicesByKey.size !== choices.rows.length || rawByKey.size !== raw.rows.length) {
    errors.push('row_or_identity_count_mismatch');
  }
  const signatures = topologySignatures(oracle);
  if (signatures.length !== 4 || new Set(signatures).size !== 4
      || oracle.topologies.filter((topology) => topology.role === 'held_out').length !== 1) {
    errors.push('heldout_topology_signature_mismatch');
  }
  const candidateText = JSON.stringify(input).toLowerCase();
  const hiddenTerms = ['witness_state', 'transition_by_action', 'prediction_mode',
    'topology_name', 'oracle', ...oracle.topologies.map((topology) => topology.name)];
  if (hiddenTerms.some((term) => candidateText.includes(term))) errors.push('candidate_truth_leak');

  for (const row of input.rows) {
    const truth = truthById.get(row.case_id);
    if (!truth) {
      errors.push(`missing_truth:${row.case_id}`);
      continue;
    }
    const preserving = row.admissible_actions.filter((action) =>
      truth.transition_by_action[action] === truth.witness_state);
    const correct = same([...row.predicted_preserving_actions].sort(), [...preserving].sort());
    const stratum = truth.prior_witness ? 'prior' : correct ? 'correct' : 'misspecified';
    const affordablePreserving = preserving.some((action) => row.action_cost[action] <= row.cost_budget);
    const topology = topologyByName.get(truth.topology);

    for (const arm of arms) {
      const key = `${row.case_id}:${arm}`;
      const choice = choicesByKey.get(key);
      const event = rawByKey.get(key);
      if (!choice || !event) {
        errors.push(`missing_arm:${key}`);
        continue;
      }
      const action = expectedAction(row, arm);
      const expectedHint = truth.prior_witness || (action !== null
        && row.predicted_preserving_actions.includes(action)) ? 'COMPLETE' : 'UNKNOWN';
      if (choice.action !== action || choice.completion_hint !== expectedHint
          || choice.authority_granted !== false) policyMismatches += 1;
      if (event.action !== action || event.case_id !== row.case_id || event.arm !== arm
          || event.completion_hint !== expectedHint) receiptMismatches += 1;
      if (choice.authority_granted || event.authority_granted) authorityGrants += 1;

      const destination = truth.prior_witness ? null
        : action === null ? null : truth.transition_by_action[action] ?? null;
      const expectedReceipt = truth.prior_witness ? {
        kind: 'PRIOR_WITNESS', case_id: row.case_id, action: null,
        destination: truth.state, effect_id: truth.effect_id,
        source: 'independent-effect-channel',
      } : destination === truth.witness_state ? {
        kind: 'TASK_EFFECT', case_id: row.case_id, action,
        destination, effect_id: truth.effect_id,
        source: 'independent-effect-channel',
      } : null;
      const validReceipt = expectedReceipt !== null && same(event.receipt, expectedReceipt);
      if (event.next_state !== destination || (expectedReceipt === null
          ? event.receipt !== null : !validReceipt)) receiptMismatches += 1;
      if (event.completion_decision === 'COMPLETE' && !validReceipt) {
        errors.push(`unsupported_completion:${key}`);
      }
      if (expectedHint === 'COMPLETE' && !validReceipt) unsupportedHints += 1;
      strata[stratum][arm].cases += 1;
      if (validReceipt) strata[stratum][arm].complete += 1;
      if (topology?.role === 'held_out' && !truth.prior_witness && correct && affordablePreserving) {
        if (arm === 'GENERIC_IG') heldoutGeneric += Number(validReceipt);
        else heldoutWitness += Number(validReceipt);
      }
    }
    if (topology?.role === 'held_out' && !truth.prior_witness && correct && affordablePreserving) {
      heldoutCases += 1;
    }
  }

  const heldOut = {
    correct_affordable_cases: heldoutCases,
    generic_complete: heldoutGeneric,
    witness_complete: heldoutWitness,
    witness_advantage: heldoutWitness - heldoutGeneric,
  };
  const formalMetricsMatch = same(strata, formalAudit.strata)
    && same(heldOut, formalAudit.held_out)
    && formalAudit.rows_checked === 384
    && formalAudit.errors.length === 0
    && formalAudit.unsupported_completions === 0
    && formalAudit.authority_grants === 0;
  if (!equalInformationGain) errors.push('information_gain_not_equal');
  if (policyMismatches) errors.push('candidate_policy_mismatch');
  if (receiptMismatches) errors.push('raw_transition_or_receipt_mismatch');
  if (authorityGrants) errors.push('authority_grants_nonzero');
  if (!formalMetricsMatch) errors.push('formal_audit_metric_disagreement');

  return {
    allocation: input.allocation,
    diagnostic_type: 'POSTRUN_READ_ONLY_POLICY_AND_RECEIPT_RECONCILIATION_V1',
    cases_checked: input.rows.length,
    arm_rows_checked: choices.rows.length,
    unique_degree_signatures: [...new Set(signatures)].sort(),
    equal_information_gain: equalInformationGain,
    policy_mismatches: policyMismatches,
    transition_or_receipt_mismatches: receiptMismatches,
    strata,
    held_out: heldOut,
    unverified_non_authoritative_hints: unsupportedHints,
    authority_grants: authorityGrants,
    formal_metrics_match: formalMetricsMatch,
    errors,
    verdict: errors.length === 0 ? 'PASS_POSTRUN_POLICY_AND_RECEIPT_RECONCILIATION'
      : 'FAIL_POSTRUN_POLICY_AND_RECEIPT_RECONCILIATION',
  };
}

async function main() {
  if (process.argv.length !== 8) {
    throw new Error('usage: node postrun_reconcile.mjs INPUT ORACLE CHOICES RAW FORMAL_AUDIT OUTPUT');
  }
  const [input, oracle, choices, raw, formalAudit] = await Promise.all(
    process.argv.slice(2, 7).map(async (path) => JSON.parse(await readFile(path, 'utf8'))),
  );
  const result = reconcile(input, oracle, choices, raw, formalAudit);
  await writeFile(process.argv[7], `${JSON.stringify(result)}\n`);
  console.log(JSON.stringify(result));
  if (!result.verdict.startsWith('PASS_')) process.exitCode = 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => { console.error(error.message); process.exitCode = 2; });
}
