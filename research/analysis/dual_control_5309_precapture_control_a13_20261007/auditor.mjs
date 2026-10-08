import fs from 'node:fs';

const publicCases = JSON.parse(fs.readFileSync(process.argv[2], 'utf8')).cases;
const choices = JSON.parse(fs.readFileSync(process.argv[3], 'utf8')).choices;
const events = JSON.parse(fs.readFileSync(process.argv[4], 'utf8')).events;
const oracle = JSON.parse(fs.readFileSync(process.argv[5], 'utf8')).cases;
const errors = [];
const rows = [];
for (const c of publicCases) {
  for (const policy of ['TASK_ONLY', 'WITNESS_AWARE']) {
    const choice = choices.find((x) => x.id === `${c.id}:${policy}`);
    const event = events.find((x) => x.id === `${c.id}:${policy}`);
    const truth = oracle.find((x) => x.id === c.id);
    if (!choice || !event || !truth) { errors.push(`missing row ${c.id}:${policy}`); continue; }
    const selectedTruth = truth.actions.find((x) => x.id === choice.action);
    const verified = Boolean(truth.prior_receipt || (selectedTruth?.effect && selectedTruth.receipt_survives) || (selectedTruth?.effect && truth.independent_readback));
    const expected = policy === 'TASK_ONLY' ? c.task_only_action : c.witness_action;
    if (choice.action !== expected) errors.push(`policy choice mismatch ${c.id}:${policy}`);
    if (event.effect !== Boolean(selectedTruth?.effect)) errors.push(`effect mismatch ${c.id}:${policy}`);
    if (event.receipt !== Boolean(selectedTruth?.effect && selectedTruth?.receipt_survives)) errors.push(`receipt mismatch ${c.id}:${policy}`);
    if (c.urgent_stop && choice.action !== 'YIELD_URGENT_STOP') errors.push(`urgent-stop action ${c.id}:${policy}`);
    if (c.prior_receipt && choice.action !== 'NO_ACTION_PRIOR_RECEIPT') errors.push(`prior-receipt action ${c.id}:${policy}`);
    if (truth.capture_status === 'PERTURBING' && event.receipt === false && event.independent_readback !== true && verified) errors.push(`perturbing capture credited ${c.id}:${policy}`);
    rows.push({ case_id: c.id, policy, action: choice.action, realized_effect: Boolean(selectedTruth?.effect), receipt_backed_completion: verified, authority_grants: 0 });
  }
}
const by = (id, policy) => rows.find((r) => r.case_id === id && r.policy === policy);
for (const c of publicCases) {
  const task = by(c.id, 'TASK_ONLY');
  const aware = by(c.id, 'WITNESS_AWARE');
  if (!task || !aware) continue;
  if (c.stratum === 'SOLE_WITNESS' && !(aware.receipt_backed_completion && !task.receipt_backed_completion)) errors.push(`sole-witness contrast absent ${c.id}`);
  if (c.stratum === 'INDEPENDENT_READBACK' && aware.receipt_backed_completion !== task.receipt_backed_completion) errors.push(`readback control advantage ${c.id}`);
  if (c.urgent_stop && (task.action !== 'YIELD_URGENT_STOP' || aware.action !== 'YIELD_URGENT_STOP')) errors.push(`stop not preemptive ${c.id}`);
  if (c.prior_receipt && (task.action !== 'NO_ACTION_PRIOR_RECEIPT' || aware.action !== 'NO_ACTION_PRIOR_RECEIPT')) errors.push(`prior witness caused action ${c.id}`);
}
const verdict = errors.length ? 'FAIL_A13_GATE' : 'PASS_PRECAPTURE_CONTROL_SCOPED';
fs.writeFileSync(process.argv[6], JSON.stringify({ verdict, rows, errors, row_count: rows.length, authority_grants: 0 }, null, 2) + '\n');
if (errors.length) process.exitCode = 1;
