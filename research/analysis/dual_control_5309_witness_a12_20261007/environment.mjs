import { readFile, writeFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';

export function simulate(candidateInput, choices, oracle) {
  const inputs = new Map(candidateInput.rows.map((row) => [row.case_id, row]));
  const truth = new Map(oracle.rows.map((row) => [row.case_id, row]));
  const rawRows = choices.rows.map((choice) => {
    const input = inputs.get(choice.case_id);
    const actual = truth.get(choice.case_id);
    let nextState = null;
    let receipt = null;
    if (input?.prior_witness && actual?.prior_witness) {
      receipt = {
        kind: 'PRIOR_WITNESS',
        case_id: choice.case_id,
        action: null,
        destination: actual.state,
        effect_id: actual.effect_id,
        source: 'independent-effect-channel',
      };
    } else if (choice.action !== null && actual) {
      nextState = actual.transition_by_action[choice.action] ?? null;
      if (nextState === actual.witness_state) {
        receipt = {
          kind: 'TASK_EFFECT',
          case_id: choice.case_id,
          action: choice.action,
          destination: nextState,
          effect_id: actual.effect_id,
          source: 'independent-effect-channel',
        };
      }
    }
    return {
      case_id: choice.case_id,
      arm: choice.arm,
      action: choice.action,
      next_state: nextState,
      completion_hint: choice.completion_hint,
      authority_granted: choice.authority_granted,
      receipt,
    };
  });
  return { allocation: choices.allocation, rows: rawRows };
}

async function main() {
  if (process.argv.length !== 6) {
    throw new Error('usage: node environment.mjs CANDIDATE_INPUT.json CHOICES.json ORACLE.json RAW.json');
  }
  const [candidateInput, choices, oracle] = await Promise.all(
    process.argv.slice(2, 5).map(async (path) => JSON.parse(await readFile(path, 'utf8'))),
  );
  const raw = simulate(candidateInput, choices, oracle);
  await writeFile(process.argv[5], `${JSON.stringify(raw)}\n`);
  console.log(`environment_rows=${raw.rows.length}`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => { console.error(error.message); process.exitCode = 2; });
}
