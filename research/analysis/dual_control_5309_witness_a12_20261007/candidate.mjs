import { readFile, writeFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';

const arms = ['GENERIC_IG', 'WITNESS_AWARE'];

export function choose(candidateInput) {
  const rows = [];
  for (const input of candidateInput.rows) {
    for (const arm of arms) {
      let action = null;
      if (!input.prior_witness) {
        const eligible = input.admissible_actions.filter((candidate) =>
          input.action_cost[candidate] <= input.cost_budget);
        if (arm === 'GENERIC_IG') {
          action = [...eligible].sort()[0] ?? null;
        } else {
          action = eligible
            .filter((candidate) => input.predicted_preserving_actions.includes(candidate))
            .sort((left, right) => input.action_cost[left] - input.action_cost[right]
              || left.localeCompare(right))[0] ?? null;
        }
      }

      rows.push({
        case_id: input.case_id,
        arm,
        action,
        completion_hint: input.prior_witness || (action !== null
          && input.predicted_preserving_actions.includes(action)) ? 'COMPLETE' : 'UNKNOWN',
        authority_granted: false,
      });
    }
  }
  return { allocation: candidateInput.allocation, rows };
}

async function main() {
  if (process.argv.length !== 4) {
    throw new Error('usage: node candidate.mjs CANDIDATE_INPUT.json CHOICES.json');
  }
  const candidateInput = JSON.parse(await readFile(process.argv[2], 'utf8'));
  const output = choose(candidateInput);
  await writeFile(process.argv[3], `${JSON.stringify(output)}\n`);
  console.log(`candidate_rows=${output.rows.length}`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => { console.error(error.message); process.exitCode = 2; });
}
