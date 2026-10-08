import fs from 'node:fs';

const choices = JSON.parse(fs.readFileSync(process.argv[2], 'utf8')).choices;
const truth = JSON.parse(fs.readFileSync(process.argv[3], 'utf8')).cases;
const events = choices.map((choice) => {
  const caseId = choice.id.slice(0, choice.id.lastIndexOf(':'));
  const c = truth.find((x) => x.id === caseId);
  if (!c) throw new Error(`unknown case ${caseId}`);
  const action = c.actions.find((x) => x.id === choice.action);
  if (!action) return { id: choice.id, action: choice.action, effect: false, receipt: c.prior_receipt, capture_status: c.capture_status, independent_readback: c.independent_readback };
  return { id: choice.id, action: action.id, effect: action.effect, receipt: action.effect && action.receipt_survives, capture_status: c.capture_status, independent_readback: c.independent_readback };
});
fs.writeFileSync(process.argv[4], JSON.stringify({ events }, null, 2) + '\n');
