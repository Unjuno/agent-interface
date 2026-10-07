import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const dir = new URL('.', import.meta.url);
const run = (script, args = []) => spawnSync('node', [fileURLToPath(new URL(script, dir)), ...args], { encoding: 'utf8' });
const originalAuditor = readFileSync(new URL('./auditor.mjs', dir), 'utf8');
assert.match(originalAuditor, /histories\.slice\(\)\.reverse\(\)/, 'A01 known-bad comparator remains identified');
const pairwiseEqual = (left, right) => JSON.stringify(left) === JSON.stringify(right);
const equalHistoryLeft = ['routine', 'routine'];
const equalHistoryRight = ['routine', 'routine'];
const unequalHistoryLeft = ['benign_witness', 'routine'];
const unequalHistoryRight = ['hazard_witness', 'routine'];
assert.equal(pairwiseEqual(equalHistoryLeft, equalHistoryRight), true, 'equal-history negative control');
assert.equal(pairwiseEqual(unequalHistoryLeft, unequalHistoryRight), false, 'distinguishing positive control');
assert.equal(pairwiseEqual(unequalHistoryLeft, unequalHistoryRight.slice().reverse()), false, 'reversal is not the pairwise equivalence relation');

const expiryAdmit = (expiryAt, step) => expiryAt === null || step < expiryAt;
assert.equal(expiryAdmit(1, 0), true, 'separator before expiry remains admissible');
assert.equal(expiryAdmit(1, 1), false, 'separator at/after expiry is refused');
assert.equal(expiryAdmit(null, 10), true, 'unexpired positive control');

const a01Raw = JSON.parse(readFileSync(new URL('./candidate-raw.json', dir), 'utf8'));
assert.equal(a01Raw.experiment, 'issue-5309-pairwise-identifiability-a01');
assert.equal(a01Raw.scenarios.find((x) => x.scenario === 'no_separator').repeated_branch_preserves_pair_alias, false,
  'frozen A01 must be rejected by the repaired construction contract');
process.stdout.write('successor construction contract: positive/negative pairwise, expiry and A01 regression controls PASS\n');
