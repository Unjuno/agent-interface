import assert from 'node:assert/strict';
import fs from 'node:fs';

const pub = JSON.parse(fs.readFileSync(new URL('./candidate_cases.json', import.meta.url), 'utf8'));
const oracle = JSON.parse(fs.readFileSync(new URL('./oracle.json', import.meta.url), 'utf8'));
assert.equal(pub.cases.length, 6);
assert.equal(oracle.cases.length, 6);
assert.deepEqual(pub.cases.map((x) => x.id), oracle.cases.map((x) => x.id));
for (const c of pub.cases) {
  assert.equal(c.actions.length, 2);
  assert.equal(c.actions[0].utility, c.actions[1].utility);
  assert.equal(c.actions[0].cost, c.actions[1].cost);
  assert.equal(c.actions[0].predicted_information_gain, c.actions[1].predicted_information_gain);
}
assert.equal(pub.cases.filter((x) => x.stratum === 'SOLE_WITNESS').length, 2);
assert.equal(pub.cases.filter((x) => x.stratum === 'INDEPENDENT_READBACK').length, 1);
assert.equal(pub.cases.filter((x) => x.stratum === 'PERTURBING_CAPTURE').length, 1);
assert.equal(pub.cases.filter((x) => x.urgent_stop).length, 1);
assert.equal(pub.cases.filter((x) => x.prior_receipt).length, 1);
console.log('construction assertions: PASS (8)');
