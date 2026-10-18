import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

import { reconcile } from './postrun_reconcile.mjs';

const readJson = async (path) => JSON.parse(await readFile(path, 'utf8'));

test('independent postrun reconciliation matches frozen policy and retained outcomes', async () => {
  const [input, oracle, choices, raw, formalAudit] = await Promise.all([
    readJson(new URL('./candidate-input.json', import.meta.url)),
    readJson(new URL('./oracle.json', import.meta.url)),
    readJson(new URL('./out/candidate-choices.json', import.meta.url)),
    readJson(new URL('./out/candidate-raw.json', import.meta.url)),
    readJson(new URL('./out/audit.json', import.meta.url)),
  ]);
  const result = reconcile(input, oracle, choices, raw, formalAudit);
  assert.equal(result.verdict, 'PASS_POSTRUN_POLICY_AND_RECEIPT_RECONCILIATION');
  assert.equal(result.policy_mismatches, 0);
  assert.equal(result.transition_or_receipt_mismatches, 0);
  assert.equal(result.equal_information_gain, true);
  assert.equal(result.formal_metrics_match, true);
});
