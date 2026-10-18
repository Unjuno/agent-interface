import fs from 'node:fs';

const choices = JSON.parse(fs.readFileSync(process.argv[2], 'utf8')).choices;
const oracle = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const events = choices.map((choice) => {
  const caseId = choice.id.slice(0, choice.id.lastIndexOf(':'));
  const truth = oracle.cases.find((c) => c.id === caseId);
  if (!truth) throw new Error(`unknown case ${choice.id}`);
  if (choice.action.startsWith('YIELD_') || choice.action.startsWith('NO_ACTION_')) {
    return { id: choice.id, action: choice.action, effect: false, receipt: truth.prior_receipt };
  }
  const action = truth.actions.find((a) => a.id === choice.action);
  if (!action) throw new Error(`unknown action ${choice.action}`);
  return {
    id: choice.id,
    action: choice.action,
    effect: action.effect,
    receipt: action.effect && action.receipt_survives,
    capture_status: truth.capture_status,
    independent_readback: truth.independent_readback,
  };
});
fs.writeFileSync(process.argv[4], JSON.stringify({ events }, null, 2) + '\n');
