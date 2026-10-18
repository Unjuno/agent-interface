import fs from 'node:fs';

const cases = JSON.parse(fs.readFileSync(process.argv[2], 'utf8')).cases;
const oracle = JSON.parse(fs.readFileSync(process.argv[3], 'utf8')).cases;
const choices = JSON.parse(fs.readFileSync(process.argv[4], 'utf8')).choices;
const events = JSON.parse(fs.readFileSync(process.argv[5], 'utf8')).events;
const errors = [];
const rows = [];
for (const c of cases) {
  const truth = oracle.find((x) => x.id === c.id);
  for (const policy of ['TASK_ONLY', 'WITNESS_AWARE']) {
    const id = `${c.id}:${policy}`;
    const choice = choices.find((x) => x.id === id);
    const event = events.find((x) => x.id === id);
    if (!truth || !choice || !event) { errors.push(`missing:${id}`); continue; }
    let expectedAction;
    if (c.urgent_stop) expectedAction = 'YIELD_URGENT_STOP';
    else if (c.prior_receipt) expectedAction = 'NO_ACTION_PRIOR_RECEIPT';
    else {
      const eligible = [...c.actions].filter((a) => a.utility === Math.max(...c.actions.map((x) => x.utility)));
      if (policy === 'WITNESS_AWARE' && !c.independent_readback) {
        const keepers = eligible.filter((a) => a.predicted_witness_route === 'PRESERVED_RECEIPT');
        expectedAction = (keepers.length ? keepers : eligible).map((a) => a.id).sort()[0];
      } else expectedAction = eligible.map((a) => a.id).sort()[0];
    }
    if (choice.action !== expectedAction) errors.push(`policy:${id}`);
    const actionTruth = truth.actions.find((a) => a.id === choice.action);
    const actionTaken = !['YIELD_URGENT_STOP', 'NO_ACTION_PRIOR_RECEIPT'].includes(choice.action);
    const effect = actionTaken && Boolean(actionTruth?.effect);
    const receipt = actionTaken && effect && Boolean(actionTruth?.receipt_survives);
    if (event.effect !== effect) errors.push(`effect:${id}`);
    if (event.receipt !== (receipt || (c.prior_receipt && Boolean(truth.prior_receipt)))) errors.push(`receipt:${id}`);
    const verified = (c.prior_receipt && Boolean(truth.prior_receipt)) || (effect && (receipt || c.independent_readback));
    rows.push({ id, action: choice.action, effect, receipt_backed_completion: verified, candidate_hint_ignored: true, authority_grants: 0 });
  }
}
const primary = rows.filter((r) => cases.find((c) => r.id.startsWith(`${c.id}:`))?.stratum === 'SOLE_WITNESS');
if (rows.length !== 12) errors.push(`row count:${rows.length}`);
const primaryByPolicy = (p) => primary.filter((r) => r.id.endsWith(`:${p}`) && r.receipt_backed_completion).length;
if (!(primaryByPolicy('WITNESS_AWARE') > primaryByPolicy('TASK_ONLY'))) errors.push('no held-out label-balanced sole-witness advantage');
for (const c of cases) {
  const task = rows.find((r) => r.id === `${c.id}:TASK_ONLY`);
  const aware = rows.find((r) => r.id === `${c.id}:WITNESS_AWARE`);
  if (!task || !aware) continue;
  if (c.stratum === 'READBACK_CONTROL' && task.receipt_backed_completion !== aware.receipt_backed_completion) errors.push('readback control differs');
  if (c.urgent_stop && (task.action !== 'YIELD_URGENT_STOP' || aware.action !== 'YIELD_URGENT_STOP' || task.effect || aware.effect)) errors.push('urgent stop not preemptive');
  if (c.prior_receipt && (task.action !== 'NO_ACTION_PRIOR_RECEIPT' || aware.action !== 'NO_ACTION_PRIOR_RECEIPT' || !task.receipt_backed_completion || !aware.receipt_backed_completion)) errors.push('prior receipt not consumed without action');
  if (c.capture_status === 'PERTURBS_STATE') {
    for (const row of [task, aware]) if (!row.effect && row.receipt_backed_completion) errors.push('perturbing capture credited');
  }
}
const result = { verdict: errors.length ? 'FAIL_A13B_GATE' : 'PASS_PRECAPTURE_CONTROL_SCOPED', row_count: rows.length, rows, errors, authority_grants: 0, sole_witness_completions: { task_only: primaryByPolicy('TASK_ONLY'), witness_aware: primaryByPolicy('WITNESS_AWARE') } };
fs.writeFileSync(process.argv[6], JSON.stringify(result, null, 2) + '\n');
if (errors.length) process.exitCode = 1;
