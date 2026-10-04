import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { auditRaw } from './audit.mjs';
import { boundedSummary, payloadFor } from './candidate.mjs';
import spec from './spec.json' with { type: 'json' };

const flood = payloadFor('pipe-capacity-flood');
assert.equal(flood.length, spec.cases[1].stderr_bytes);
assert.deepEqual(boundedSummary(flood), {
  total_bytes: flood.length,
  sha256: (await import('node:crypto')).createHash('sha256').update(flood).digest('hex'),
  prefix_hex: flood.subarray(0, 4096).toString('hex'),
  tail_hex: flood.subarray(-4096).toString('hex'),
  truncated: true,
  retained_bytes: 8192,
});

const expected = {
  schema: spec.schema,
  rows: spec.cases.map((rule, index) => {
    const bytes = payloadFor(rule.id);
    const cap = boundedSummary(bytes);
    return {
      id: rule.id,
      primary: rule.expected_primary,
      ready_event: rule.id === 'ready-success' ? { event: 'ready', fixture: 'finite-fixture-v1' } : null,
      exit_code: rule.expected_exit_code ?? null,
      signal: rule.expected_signal ?? null,
      closed: true,
      elapsed_ms: index + 1,
      stderr: cap,
    };
  }),
};
const audit = auditRaw(expected);
assert.equal(audit.status, 'PASS_METHOD_SCOPED');
assert.deepEqual(audit.corruption_controls.map(row => row.rejected), [true, true, true, true]);

const mutations = [
  raw => { raw.rows[0].stderr = null; },
  raw => { raw.rows[1].stderr.total_bytes -= 1; },
  raw => { raw.rows[2].primary = 'SESSION_EXIT_BEFORE_READY'; },
  raw => { raw.rows[3].ready_event = null; },
];
for (const mutate of mutations) {
  const copy = structuredClone(expected);
  mutate(copy);
  assert.equal(auditRaw(copy).status, 'FAIL_METHOD');
}

const candidateSource = await readFile(new URL('./candidate.mjs', import.meta.url), 'utf8');
const auditorSource = await readFile(new URL('./audit.mjs', import.meta.url), 'utf8');
assert.match(candidateSource, /boundedCollector\(child\.stderr\)/);
assert.doesNotMatch(auditorSource, /from ['"]\.\/candidate\.mjs['"]/);
process.stdout.write('construction_test=PASS fixture_rows=4 audit_errors=0 mutations=4/4 formal_subprocesses=0\n');
