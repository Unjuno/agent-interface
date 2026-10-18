import { readFile, writeFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';

export const ALLOCATION = '5309-EVIDENCE-SEMANTICS-HELDOUT-A12-20261007';

const actions = ['left', 'right'];
const definitions = [
  { name: 'cycle3', role: 'seen', left: [1, 2, 0], right: [2, 0, 1] },
  { name: 'branch_merge4', role: 'seen', left: [1, 3, 3, 0], right: [2, 2, 0, 3] },
  { name: 'asymmetric4', role: 'seen', left: [1, 2, 3, 0], right: [2, 0, 0, 2] },
  { name: 'lollipop5', role: 'held_out', left: [1, 2, 3, 4, 4], right: [2, 3, 4, 1, 0] },
];

function topologyRows() {
  return definitions.map((definition) => {
    const nodeCount = definition.left.length;
    const indegree = Array(nodeCount).fill(0);
    for (const action of actions) {
      for (const destination of definition[action]) indegree[destination] += 1;
    }
    return {
      name: definition.name,
      role: definition.role,
      nodes: Array.from({ length: nodeCount }, (_, index) => `n${index}`),
      transitions: Object.fromEntries(actions.map((action) => [
        action,
        Object.fromEntries(definition[action].map((destination, index) => [
          `n${index}`, `n${destination}`,
        ])),
      ])),
      degree_signature: `${nodeCount}:${indegree.sort((a, b) => a - b).join(',')}`,
    };
  });
}

export function makeFixture() {
  const candidateInput = { allocation: ALLOCATION, rows: [] };
  const oracle = { allocation: ALLOCATION, topologies: topologyRows(), rows: [] };
  let sequence = 0;

  definitions.forEach((definition, topologyIndex) => {
    const count = definition.left.length;
    for (let stateIndex = 0; stateIndex < count; stateIndex += 1) {
      const state = `n${stateIndex}`;
      const selectedTruthAction = (topologyIndex + stateIndex) % 2 === 0 ? 'left' : 'right';
      const witnessIndex = definition[selectedTruthAction][stateIndex];
      const destinations = Object.fromEntries(actions.map((action) => [
        action, `n${definition[action][stateIndex]}`,
      ]));
      const preserving = actions.filter((action) => destinations[action] === `n${witnessIndex}`);
      const admissible = (topologyIndex + stateIndex) % 7 === 0 ? ['left'] : [...actions];

      for (const predictionMode of ['correct', 'misspecified']) {
        for (const costBudget of [0, 1, 2]) {
          for (const priorWitness of [false, true]) {
            sequence += 1;
            const caseId = `c${String(sequence).padStart(3, '0')}`;
            const actionCost = {
              left: (topologyIndex + stateIndex) % 3,
              right: (topologyIndex + stateIndex + 1) % 3,
            };
            let predicted = [...preserving];
            if (predictionMode === 'misspecified') {
              if (predicted.length === 1) {
                predicted = [...actions];
              } else if (predicted.length === 2) {
                predicted = ['right'];
              } else {
                predicted = ['left'];
              }
            }

            candidateInput.rows.push({
              case_id: caseId,
              observation_ref: `obs-${String(sequence).padStart(4, '0')}`,
              prior_witness: priorWitness,
              predicted_preserving_actions: predicted.filter((action) => admissible.includes(action)),
              action_cost: actionCost,
              cost_budget: costBudget,
              admissible_actions: admissible,
              info_gain: { left: 1, right: 1 },
            });
            oracle.rows.push({
              case_id: caseId,
              topology: definition.name,
              prediction_mode: predictionMode,
              state,
              witness_state: `n${witnessIndex}`,
              prior_witness: priorWitness,
              admissible_actions: admissible,
              action_cost: actionCost,
              cost_budget: costBudget,
              transition_by_action: destinations,
              effect_id: `effect-${caseId}`,
            });
          }
        }
      }
    }
  });

  return { candidateInput, oracle };
}

async function main() {
  if (process.argv.length !== 4) {
    throw new Error('usage: node fixture.mjs CANDIDATE_INPUT.json ORACLE.json');
  }
  const { candidateInput, oracle } = makeFixture();
  await writeFile(process.argv[2], `${JSON.stringify(candidateInput)}\n`);
  await writeFile(process.argv[3], `${JSON.stringify(oracle)}\n`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => { console.error(error.message); process.exitCode = 2; });
}
