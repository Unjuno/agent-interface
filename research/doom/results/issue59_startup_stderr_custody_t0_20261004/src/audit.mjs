import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import spec from './spec.json' with { type: 'json' };

function expectedBytes(id) {
  if (id === 'short-exit') return Buffer.from('E_IMPORT:missing-fixture\n');
  if (id === 'pipe-capacity-flood') return Buffer.from('E_FLOOD:'.repeat(spec.cases[1].stderr_bytes / 8));
  if (id === 'ready-timeout') return Buffer.from('E_BOOT_WAIT:still-starting\n');
  if (id === 'ready-success') return Buffer.from('E_DIAGNOSTIC:nonfatal\n');
  throw new Error(`unrecognized case ${id}`);
}

function expectedCapture(data) {
  const limit = spec.capture_limit_per_edge_bytes;
  return {
    total_bytes: data.length,
    sha256: createHash('sha256').update(data).digest('hex'),
    prefix_hex: data.subarray(0, limit).toString('hex'),
    tail_hex: data.subarray(Math.max(0, data.length - limit)).toString('hex'),
    truncated: data.length > limit * 2,
    retained_bytes: Math.min(data.length, limit) + Math.max(0, Math.min(data.length - limit, limit)),
  };
}

function auditCore(raw) {
  const errors = [];
  if (raw?.schema !== spec.schema) errors.push('schema mismatch');
  if (!Array.isArray(raw?.rows) || raw.rows.length !== spec.cases.length) return { status: 'FAIL_METHOD', errors: [...errors, 'row count mismatch'] };
  const expectedIds = spec.cases.map(row => row.id);
  if (raw.rows.map(row => row?.id).join('|') !== expectedIds.join('|')) errors.push('ordered case identity mismatch');
  for (let index = 0; index < spec.cases.length; index++) {
    const rule = spec.cases[index];
    const row = raw.rows[index] || {};
    const bytes = expectedBytes(rule.id);
    const capture = expectedCapture(bytes);
    const expectedPrimary = rule.expected_primary;
    if (row.id !== rule.id) errors.push(`${rule.id}: row identity mismatch`);
    if (row.primary !== expectedPrimary) errors.push(`${rule.id}: primary outcome mismatch`);
    if (row.elapsed_ms < 0 || row.elapsed_ms > spec.max_elapsed_ms) errors.push(`${rule.id}: elapsed bound violated`);
    if (row.closed !== true) errors.push(`${rule.id}: child did not close`);
    if (JSON.stringify(row.stderr) !== JSON.stringify(capture)) errors.push(`${rule.id}: stderr capture mismatch`);
    if (Object.hasOwn(rule, 'expected_exit_code') && row.exit_code !== rule.expected_exit_code) errors.push(`${rule.id}: exit code mismatch`);
    if (Object.hasOwn(rule, 'expected_signal') && row.signal !== rule.expected_signal) errors.push(`${rule.id}: signal mismatch`);
    if (rule.id === 'ready-timeout' && row.exit_code !== null) errors.push('ready-timeout: timeout must remain primary over exit code');
    if (rule.id === 'ready-success') {
      if (JSON.stringify(row.ready_event) !== JSON.stringify({ event: 'ready', fixture: 'finite-fixture-v1' })) errors.push('ready-success: event mismatch');
    } else if (row.ready_event !== null) errors.push(`${rule.id}: unexpected ready event`);
  }
  return { status: errors.length ? 'FAIL_METHOD' : 'PASS_METHOD_SCOPED', errors, row_count: raw.rows.length, scenario_count: spec.cases.length };
}

export function auditRaw(raw) {
  const base = auditCore(raw);
  if (base.status !== 'PASS_METHOD_SCOPED') return { ...base, corruption_controls: [] };
  const mutations = [
    ['erase_short_error_diagnostic', copy => { copy.rows[0].stderr = null; }],
    ['forge_flood_byte_count', copy => { copy.rows[1].stderr.total_bytes -= 1; }],
    ['replace_timeout_primary_outcome', copy => { copy.rows[2].primary = 'SESSION_EXIT_BEFORE_READY'; }],
    ['erase_ready_event', copy => { copy.rows[3].ready_event = null; }],
  ];
  const corruptionControls = mutations.map(([id, mutate]) => {
    const copy = structuredClone(raw);
    mutate(copy);
    return { id, rejected: auditCore(copy).status !== 'PASS_METHOD_SCOPED' };
  });
  const errors = corruptionControls.filter(row => !row.rejected).map(row => `mutation accepted: ${row.id}`);
  return {
    ...base,
    status: errors.length ? 'FAIL_METHOD' : 'PASS_METHOD_SCOPED',
    errors,
    corruption_controls: corruptionControls,
  };
}

if (process.argv[1]?.endsWith('/audit.mjs')) {
  const [rawPath, auditPath] = process.argv.slice(2);
  if (!rawPath || !auditPath) throw new Error('usage: audit.mjs RAW AUDIT');
  const raw = JSON.parse(await readFile(rawPath, 'utf8'));
  const result = auditRaw(raw);
  await writeFile(auditPath, `${JSON.stringify(result, null, 2)}\n`, { flag: 'wx' });
  process.stdout.write(`${result.status} rows=${result.row_count || 0} scenarios=${result.scenario_count || 0} errors=${result.errors.length} mutations=${result.corruption_controls.filter(row => row.rejected).length}/${result.corruption_controls.length}\n`);
  if (result.status !== 'PASS_METHOD_SCOPED') process.exitCode = 1;
}
