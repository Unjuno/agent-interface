import fs from 'node:fs';

const cases = JSON.parse(fs.readFileSync(process.argv[2], 'utf8')).cases;
const choices = [];
for (const c of cases) {
  for (const policy of ['TASK_ONLY', 'WITNESS_AWARE']) {
    const rowId = `${c.id}:${policy}`;
    if (c.urgent_stop) {
      choices.push({ id: rowId, action: 'YIELD_URGENT_STOP', completion_hint: false });
      continue;
    }
    if (c.prior_receipt) {
      choices.push({ id: rowId, action: 'NO_ACTION_PRIOR_RECEIPT', completion_hint: true });
      continue;
    }
    const eligible = c.actions.filter((a) => a.utility === Math.max(...c.actions.map((x) => x.utility)));
    const ranked = eligible.sort((a, b) => {
      if (policy === 'WITNESS_AWARE' && !c.independent_readback) {
        return Number(b.predicted_witness_route === 'PRESERVED_RECEIPT') - Number(a.predicted_witness_route === 'PRESERVED_RECEIPT') || a.id.localeCompare(b.id);
      }
      return a.id.localeCompare(b.id);
    });
    choices.push({ id: rowId, action: ranked[0].id, completion_hint: true });
  }
}
fs.writeFileSync(process.argv[3], JSON.stringify({ choices }, null, 2) + '\n');
