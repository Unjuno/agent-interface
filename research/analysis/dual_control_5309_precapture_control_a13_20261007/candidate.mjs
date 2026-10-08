import fs from 'node:fs';

const input = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const choices = input.cases.flatMap((c) => ['TASK_ONLY', 'WITNESS_AWARE'].map((policy) => {
  const id = `${c.id}:${policy}`;
  if (c.urgent_stop) return { id, action: 'YIELD_URGENT_STOP', predicted_completion: false };
  if (c.prior_receipt) return { id, action: 'NO_ACTION_PRIOR_RECEIPT', predicted_completion: true };
  const ranked = [...c.actions].sort((a, b) => {
    if (policy === 'WITNESS_AWARE' && !c.independent_readback) {
      return Number(b.preserves_witness) - Number(a.preserves_witness) || a.id.localeCompare(b.id);
    }
    return a.id.localeCompare(b.id);
  });
  const selected = ranked[0];
  return { id, action: selected.id, predicted_completion: true };
}));
fs.writeFileSync(process.argv[3], JSON.stringify({ choices }, null, 2) + '\n');
