import assert from 'node:assert/strict';
import fs from 'node:fs';

const pub = JSON.parse(fs.readFileSync(new URL('./candidate_stage/cases.json', import.meta.url), 'utf8')).cases;
const aud = JSON.parse(fs.readFileSync(new URL('./auditor_stage/cases.json', import.meta.url), 'utf8')).cases;
const oracle = JSON.parse(fs.readFileSync(new URL('./auditor_stage/oracle.json', import.meta.url), 'utf8')).cases;
const envOracle = JSON.parse(fs.readFileSync(new URL('./environment_stage/oracle.json', import.meta.url), 'utf8')).cases;
assert.equal(pub.length, 6);
assert.deepEqual(pub, aud);
assert.deepEqual(pub.map((x) => x.id), oracle.map((x) => x.id));
assert.deepEqual(envOracle, oracle);
for (const c of pub) {
  assert.equal(c.actions.length, 2);
  for (const key of ['utility', 'cost', 'predicted_information_gain']) assert.equal(c.actions[0][key], c.actions[1][key]);
  assert.deepEqual(c.actions.map((a) => a.id).sort(), oracle.find((x) => x.id === c.id).actions.map((a) => a.id).sort());
}
assert.notEqual(pub[0].actions[0].predicted_witness_route, pub[1].actions[0].predicted_witness_route);
assert.equal(pub.filter((x) => x.stratum === 'SOLE_WITNESS').length, 2);
assert.equal(pub.filter((x) => x.stratum === 'READBACK_CONTROL').length, 1);
assert.equal(pub.filter((x) => x.stratum === 'PERTURBATION_CONTROL').length, 1);
assert.equal(pub.filter((x) => x.urgent_stop).length, 1);
assert.equal(pub.filter((x) => x.prior_receipt).length, 1);
console.log('A13B construction checks passed');
