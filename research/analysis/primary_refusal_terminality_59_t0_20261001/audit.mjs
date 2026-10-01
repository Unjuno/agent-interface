import fs from 'node:fs';
const raw = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const expected = new Set(['explicit_planned_refusal','invalid_envelope_uncertain_delivery']);
const errors = [];
if (raw.schema !== 'issue59-refusal-terminality-t0-v1') errors.push('schema mismatch');
const seen = new Set();
for (const row of raw.rows ?? []) {
  if (seen.has(row.case_id)) errors.push('duplicate case ' + row.case_id);
  seen.add(row.case_id);
  const shouldPreserve = row.case_id === 'explicit_planned_refusal';
  if (row.original_reply_preserved !== shouldPreserve) errors.push(row.case_id + ': original presentation mismatch');
  if (row.caller_state?.stopped == null) errors.push(row.case_id + ': STOP not latched');
  if (row.second?.status !== 'blocked') errors.push(row.case_id + ': effectful retry was not blocked');
  if (row.host_calls?.slice(1).some(c => c.tool !== 'interface_close')) errors.push(row.case_id + ': post-fault effectful host call');
  if (row.close !== 'allowed') errors.push(row.case_id + ': close unavailable');
}
if (seen.size !== expected.size || [...expected].some(x=>!seen.has(x))) errors.push('case inventory mismatch');
process.stdout.write(JSON.stringify({audit:errors.length?'FAIL':'PASS',rows:raw.rows?.length??0,errors})+'\n');
process.exitCode = errors.length ? 1 : 0;
