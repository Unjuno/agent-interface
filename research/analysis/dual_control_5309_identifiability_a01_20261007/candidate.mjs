import crypto from 'node:crypto';

// Candidate sees only admissible actions and observations. Hidden state and
// required commit are intentionally confined to the experiment specification.
const states = ['benign', 'hazard'];
const spec = {
  horizon: 2,
  requiredCommit: { benign: 'commit_safe', hazard: 'commit_abort' },
  transitions: {
    benign: {
      repeat: { next: 'benign', observation: 'routine', opportunity: 'kept' },
      separate: { next: 'benign', observation: 'benign_witness', opportunity: 'kept' },
      commit_safe: { next: 'benign', observation: 'committed', opportunity: 'consumed' },
      commit_abort: { next: 'benign', observation: 'aborted', opportunity: 'consumed' },
    },
    hazard: {
      repeat: { next: 'hazard', observation: 'routine', opportunity: 'kept' },
      separate: { next: 'hazard', observation: 'hazard_witness', opportunity: 'kept' },
      commit_safe: { next: 'hazard', observation: 'committed', opportunity: 'consumed' },
      commit_abort: { next: 'hazard', observation: 'aborted', opportunity: 'consumed' },
    },
    null_a: { separate: { next: 'null_a', observation: 'a', opportunity: 'kept' } },
    null_b: { separate: { next: 'null_b', observation: 'b', opportunity: 'kept' } },
    nosep_a: { repeat: { next: 'n osep_a', observation: 'routine', opportunity: 'kept' } },
    nosep_b: { repeat: { next: 'n osep_b', observation: 'routine', opportunity: 'kept' } },
    expired_a: { repeat: { next: 'expired_a', observation: 'routine', opportunity: 'expired' } },
    expired_b: { repeat: { next: 'expired_b', observation: 'routine', opportunity: 'expired' } },
  },
};
// Correct fixture IDs after literal construction, keeping the table explicit.
spec.transitions.nosep_a = spec.transitions['n osep_a'];
spec.transitions.nosep_b = spec.transitions['n osep_b'];
delete spec.transitions['n osep_a'];
delete spec.transitions['n osep_b'];

const scenarios = [
  { id: 'separator', pair: ['benign', 'hazard'], admissible: ['repeat', 'separate'], horizon: 2, expiryAt: null },
  { id: 'no_separator', pair: ['nosep_a', 'nosep_b'], admissible: ['repeat'], horizon: 2, expiryAt: null },
  { id: 'expiry_before_separator', pair: ['expired_a', 'expired_b'], admissible: ['repeat', 'separate'], horizon: 2, expiryAt: 1 },
  { id: 'one_step_null', pair: ['null_a', 'null_b'], admissible: ['separate'], horizon: 1, expiryAt: null },
];
const opportunityStream = ['slot-1', 'slot-2'];

function walk(state, actions, scenario, arm) {
  let current = state;
  let expired = false;
  const trace = [];
  for (let step = 0; step < actions.length; step += 1) {
    const proposal = actions[step];
    const admitted = scenario.admissible.includes(proposal) && !expired;
    const executed = admitted ? proposal : null;
    const row = executed === null ? null : spec.transitions[current]?.[executed];
    if (row) current = row.next;
    if (scenario.expiryAt === step + 1) expired = true;
    trace.push({ slot: opportunityStream[step], proposal, admitted, executed, observation: row?.observation ?? null, opportunity: row?.opportunity ?? null, arm });
  }
  return trace;
}

function entropyScore(observations) {
  // Uniform binary entropy proxy: a generic one-step score favors "separate".
  return observations.includes('routine') ? 0 : 1;
}

function main() {
  const rows = [];
  for (const scenario of scenarios) {
    const [left, right] = scenario.pair;
    const benignTrace = walk(left, ['repeat', 'repeat'], scenario, 'repeat_same_action');
    const oneStep = walk(left, [scenario.admissible.includes('separate') ? 'separate' : 'repeat'], scenario, 'one_step_information');
    const separatorTraceL = walk(left, ['separate'], scenario, 'pairwise_oracle');
    const separatorTraceR = walk(right, ['separate'], scenario, 'pairwise_oracle');
    rows.push({
      scenario: scenario.id,
      admissible: scenario.admissible,
      horizon: scenario.horizon,
      expiry_at: scenario.expiryAt,
      one_step_information_score: entropyScore(oneStep.flatMap((x) => x.observation ? [x.observation] : [])),
      repeated_same_action_observations: benignTrace.filter((x) => x.observation).map((x) => x.observation),
      repeated_branch_preserves_pair_alias: benignTrace.every((x) => x.observation === 'routine'),
      pairwise_separator_observations: [separatorTraceL[0].observation, separatorTraceR[0].observation],
      pairwise_separator_admitted: separatorTraceL[0].admitted && separatorTraceR[0].admitted,
      proposal_admission_execution_observation: oneStep,
      counterfactual_opportunity_stream: opportunityStream,
      state_displacement: {
        task_only: { terminal: left, opportunity_consumed: false, harmful_effect: false },
        selected_action: { terminal: left, opportunity_consumed: oneStep.some((x) => x.opportunity === 'consumed'), harmful_effect: false },
      },
      authority_granted: false,
    });
  }
  const raw = { experiment: 'issue-5309-pairwise-identifiability-a01', scope: 'finite deterministic method fixture only', scenarios: rows };
  const canonical = JSON.stringify(raw, Object.keys(raw).sort());
  raw.input_sha256 = crypto.createHash('sha256').update(canonical).digest('hex');
  process.stdout.write(`${JSON.stringify(raw)}\n`);
}

main();
